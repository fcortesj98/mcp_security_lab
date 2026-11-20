"""Gradio chat UI for the permission-aware AI host."""

import gradio as gr

from mcp_security.security import assess_risk

from .agent import Agent


class HostGUI:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.permissions = agent.bridge.gate.permissions

    async def send(self, message: str, history: list):
        if not message.strip():
            return history
        try:
            reply = await self.agent.chat(message)
        except Exception as e:
            reply = f"Error: {e}"
        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": reply},
        ]

    def clear(self):
        self.agent.reset()
        return []

    def permission_summary(self) -> str:
        lines = ["### Current Permission Policies", ""]
        for rule, policy in self.permissions.load().items():
            tool = rule.split(":", 1)[0]
            lines.append(f"- **{rule}**: {policy.upper()} (Risk: {assess_risk(tool).level})")
        return "\n".join(lines)

    def build(self) -> gr.Blocks:
        with gr.Blocks(title="MCP Permission AI Host") as ui:
            gr.Markdown(
                "# MCP Permission AI Host\n"
                f"Chat with **{self.agent.model}** using permission-aware MCP tools.  \n"
                "Every tool call is checked against the permission policies, "
                "risk-assessed and written to the audit log."
            )
            chatbot = gr.Chatbot(label="Conversation", height=500, type="messages")
            with gr.Row():
                msg = gr.Textbox(
                    label="Your message", placeholder="Ask me to use MCP tools...", scale=4
                )
                clear_btn = gr.Button("Clear", scale=1)

            with gr.Accordion("Permission Status", open=False):
                summary = gr.Markdown(self.permission_summary())
                refresh_btn = gr.Button("Refresh", size="sm")

            msg.submit(self.send, inputs=[msg, chatbot], outputs=chatbot).then(
                lambda: "", outputs=msg
            )
            clear_btn.click(self.clear, outputs=chatbot)
            refresh_btn.click(self.permission_summary, outputs=summary)
        return ui
