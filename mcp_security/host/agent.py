"""The LLM agent loop, with a human-in-the-loop approval step.

1. The LLM asks for tools; each call goes through the permission gate.
2. If a call needs approval, the agent stops and shows the request.
3. The user answers "yes" (run it) or "no" (cancel). Any other message
   cancels the request, so an old approval can never be triggered later.
"""

import json

from openai import AsyncOpenAI

from mcp_security.config import MAX_TOOL_ROUNDS
from mcp_security.security import ApprovalRequest

from .tool_bridge import ToolBridge

YES = {"yes", "y", "approve", "ok", "confirm"}
NO = {"no", "n", "deny", "cancel"}


class Agent:
    def __init__(self, bridge: ToolBridge, model: str, llm: AsyncOpenAI | None = None):
        self.bridge = bridge
        self.model = model
        self.llm = llm or AsyncOpenAI()
        self.history: list[dict] = []
        self.pending: list[ApprovalRequest] = []

    def reset(self) -> None:
        self.history = []
        self.pending = []

    async def chat(self, user_message: str) -> str:
        answer = user_message.strip().lower()
        if self.pending and answer in YES:
            return await self._run_approved(user_message)
        if self.pending:
            self._cancel_pending("User declined" if answer in NO else "Superseded by new message")
            if answer in NO:
                return self._exchange(user_message, "Operation cancelled by user.")

        self.history.append({"role": "user", "content": user_message})
        return await self._tool_loop()

    # --- the normal LLM + tools loop ----------------------------------------------

    async def _tool_loop(self) -> str:
        tools = await self.bridge.openai_tools()

        for _ in range(MAX_TOOL_ROUNDS):
            message = await self._complete(tools)
            if not message.tool_calls:
                return self._remember(message.content)

            self.history.append(_assistant_tool_calls(message))
            for call in message.tool_calls:
                outcome = await self.bridge.execute(call.function.name, call.function.arguments)
                self.history.append(
                    {"role": "tool", "tool_call_id": call.id, "content": outcome.text}
                )
                if outcome.approval:
                    self.pending.append(outcome.approval)

            if self.pending:  # stop and let the user decide
                requests = "\n\n".join(r.message for r in self.pending)
                return self._remember(f"{requests}\n\nType 'yes' to approve or 'no' to cancel.")

        return self._remember((await self._complete(tools=None)).content)

    async def _complete(self, tools: list[dict] | None):
        kwargs = {"model": self.model, "messages": self.history}
        if tools:
            kwargs.update(tools=tools, tool_choice="auto")
        response = await self.llm.chat.completions.create(**kwargs)
        return response.choices[0].message

    # --- approval answers ----------------------------------------------------------

    async def _run_approved(self, user_message: str) -> str:
        requests, self.pending = self.pending, []
        results = []
        for request in requests:
            outcome = await self.bridge.gate.call_tool(
                request.tool, request.arguments, approved=True
            )
            results.append(outcome.text)
        return self._exchange(
            user_message, "Operation approved and executed.\n\n" + "\n".join(results)
        )

    def _cancel_pending(self, reason: str) -> None:
        for request in self.pending:
            operation = f"TOOL: {request.tool} {json.dumps(request.arguments, sort_keys=True)}"
            self.bridge.gate.audit.record(operation, "CANCELLED", reason)
        self.pending = []

    # --- history helpers -----------------------------------------------------------

    def _exchange(self, user_message: str, reply: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        return self._remember(reply)

    def _remember(self, text: str | None) -> str:
        text = text or "(no response)"
        self.history.append({"role": "assistant", "content": text})
        return text


def _assistant_tool_calls(message) -> dict:
    return {
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.function.name, "arguments": call.function.arguments},
            }
            for call in message.tool_calls
        ],
    }
