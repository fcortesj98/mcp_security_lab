"""Bridge between MCP and OpenAI function calling.

Real MCP tools go through the PermissionGate. Four synthetic functions let the
LLM reach resources and prompts too; they only read data, so they skip the gate.
"""

import json

from mcp_security.client import ALLOWED, PermissionGate, ToolOutcome
from mcp_security.client.formatting import (
    content_to_text,
    format_prompt_result,
    format_prompts,
    format_resources,
)
from mcp_security.security import assess_risk


def _function(name: str, description: str, properties: dict | None = None, required=None) -> dict:
    parameters = {"type": "object", "properties": properties or {}}
    if required:
        parameters["required"] = required
    return {
        "type": "function",
        "function": {"name": name, "description": description, "parameters": parameters},
    }


SYNTHETIC_TOOLS = [
    _function("mcp_list_resources", "List all available resources from the MCP server"),
    _function(
        "mcp_read_resource",
        "Read a specific resource by URI from the MCP server",
        {"uri": {"type": "string", "description": "Resource URI, e.g. 'file://audit/log'"}},
        required=["uri"],
    ),
    _function("mcp_list_prompts", "List all available prompt templates from the MCP server"),
    _function(
        "mcp_get_prompt",
        "Get a rendered prompt template from the MCP server",
        {
            "name": {"type": "string", "description": "The name of the prompt template"},
            "arguments": {"type": "object", "description": "Arguments for the prompt template"},
        },
        required=["name"],
    ),
]


class ToolBridge:
    def __init__(self, gate: PermissionGate):
        self.gate = gate
        self.client = gate.client

    async def openai_tools(self) -> list[dict]:
        """MCP tools (with their permission and risk) + the synthetic tools."""
        tools = []
        for tool in await self.client.list_tools():
            schema = tool.inputSchema or {}
            policy = self.gate.permissions.policy_for_tool(tool.name)
            risk = assess_risk(tool.name).level
            description = f"{tool.description or tool.name} (Permission: {policy}, Risk: {risk})"
            tools.append(
                _function(tool.name, description, schema.get("properties"), schema.get("required"))
            )
        return tools + SYNTHETIC_TOOLS

    async def execute(self, name: str, arguments_json: str) -> ToolOutcome:
        """Run one tool call from the LLM."""
        try:
            args = json.loads(arguments_json or "{}")
            handler = self._synthetic_handlers().get(name)
            if handler:
                return ToolOutcome(ALLOWED, await handler(args))
            return await self.gate.call_tool(name, args)
        except Exception as e:
            return ToolOutcome(ALLOWED, f"Error executing {name}: {e}")

    # --- synthetic tool handlers ---------------------------------------------------

    def _synthetic_handlers(self) -> dict:
        return {
            "mcp_list_resources": self._list_resources,
            "mcp_read_resource": self._read_resource,
            "mcp_list_prompts": self._list_prompts,
            "mcp_get_prompt": self._get_prompt,
        }

    async def _list_resources(self, _args: dict) -> str:
        return "Available resources:\n" + format_resources(await self.client.list_resources())

    async def _read_resource(self, args: dict) -> str:
        if not args.get("uri"):
            return "Error: URI is required"
        result = await self.client.read_resource(args["uri"])
        return content_to_text(result.contents) or "No content"

    async def _list_prompts(self, _args: dict) -> str:
        return "Available prompts:\n" + format_prompts(await self.client.list_prompts())

    async def _get_prompt(self, args: dict) -> str:
        if not args.get("name"):
            return "Error: Prompt name is required"
        result = await self.client.get_prompt(args["name"], args.get("arguments") or {})
        return format_prompt_result(result)
