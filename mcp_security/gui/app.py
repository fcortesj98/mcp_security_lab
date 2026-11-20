"""Gradio GUI: call tools under permission rules, edit policies and read the audit log."""

import json

import gradio as gr

from mcp_security.client import PermissionGate
from mcp_security.client.formatting import (
    content_to_text,
    format_prompt_result,
    format_prompts,
    format_resources,
)
from mcp_security.security import POLICIES, assess_risk


def _parse_json(text: str) -> dict:
    return json.loads(text) if text and text.strip() else {}


class ClientGUI:
    def __init__(self, gate: PermissionGate):
        self.gate = gate
        self.client = gate.client
        self.permissions = gate.permissions
        self.audit = gate.audit

    # --- tools -----------------------------------------------------------------

    async def list_tools(self):
        tools = await self.client.list_tools()
        lines, choices = [], []
        for tool in tools:
            policy = self.permissions.policy_for_tool(tool.name)
            lines.append(
                f"• {tool.name}\n"
                f"  Permission: {policy.upper()} | Risk: {assess_risk(tool.name).level.upper()}\n"
                f"  {tool.description}"
            )
            choices.append((f"{tool.name} ({policy})", tool.name))  # (label, value)
        return "\n\n".join(lines), gr.update(choices=choices)

    async def call_tool(self, name: str, args_json: str, approved: bool = False) -> str:
        if not name:
            return "Please select a tool first"
        try:
            outcome = await self.gate.call_tool(name, _parse_json(args_json), approved)
        except json.JSONDecodeError as e:
            return f"Invalid JSON in arguments: {e}"
        except Exception as e:
            return f"Error: {e}"
        if outcome.approval:
            return outcome.text + "\nClick 'Approve & Execute' to proceed."
        return outcome.text

    async def approve_tool(self, name: str, args_json: str) -> str:
        return await self.call_tool(name, args_json, approved=True)

    # --- resources & prompts -------------------------------------------------------

    async def list_resources(self) -> str:
        return format_resources(await self.client.list_resources())

    async def read_resource(self, uri: str) -> str:
        if not uri.strip():
            return "Please enter a resource URI"
        try:
            return content_to_text((await self.client.read_resource(uri)).contents)
        except Exception as e:
            return f"Error: {e}"

    async def list_prompts(self):
        prompts = await self.client.list_prompts()
        return format_prompts(prompts), gr.update(choices=[p.name for p in prompts])

    async def get_prompt(self, name: str, args_json: str) -> str:
        if not name:
            return "Please select a prompt first"
        try:
            return format_prompt_result(await self.client.get_prompt(name, _parse_json(args_json)))
        except json.JSONDecodeError as e:
            return f"Invalid JSON in arguments: {e}"
        except Exception as e:
            return f"Error: {e}"

    # --- permissions & audit ---------------------------------------------------------

    async def load_tool_names(self):
        return gr.update(choices=[t.name for t in await self.client.list_tools()])

    def save_permission(self, rule: str, policy: str) -> str:
        if not rule:
            return "Please choose a tool (or type an argument-specific rule)"
        try:
            self.permissions.set_policy(rule, policy)
        except ValueError as e:
            return str(e)
        return f"Permission updated: {rule} = {policy}\nSaved to {self.permissions.path}"

    def view_audit_log(self) -> str:
        return self.audit.read()

    # --- layout ----------------------------------------------------------------

    def build(self) -> gr.Blocks:
        with gr.Blocks(title="MCP Permission Client") as ui:
            gr.Markdown(
                "# MCP Permission Client\n"
                "Manage permissions, view audit logs, and interact with MCP tools securely."
            )
            with gr.Tabs():
                self._tools_tab()
                self._resources_tab()
                self._prompts_tab()
                self._permissions_tab()
        return ui

    def _tools_tab(self):
        with gr.Tab("Tools"):
            with gr.Row():
                with gr.Column():
                    list_btn = gr.Button("List Tools", variant="primary")
                    listing = gr.Textbox(label="Available Tools", lines=12)
                with gr.Column():
                    tool = gr.Dropdown(label="Select Tool", choices=[], interactive=True)
                    args = gr.Textbox(
                        label="Arguments (JSON)", placeholder='{"filepath": "test.txt"}', lines=3
                    )
                    with gr.Row():
                        call_btn = gr.Button("Call Tool", variant="primary")
                        approve_btn = gr.Button("Approve & Execute", variant="secondary")
                    result = gr.Textbox(label="Result", lines=10)

            list_btn.click(self.list_tools, outputs=[listing, tool])
            call_btn.click(self.call_tool, inputs=[tool, args], outputs=result)
            approve_btn.click(self.approve_tool, inputs=[tool, args], outputs=result)

    def _resources_tab(self):
        with gr.Tab("Resources"):
            with gr.Row():
                with gr.Column():
                    list_btn = gr.Button("List Resources", variant="primary")
                    listing = gr.Textbox(label="Available Resources", lines=10)
                with gr.Column():
                    uri = gr.Textbox(label="Resource URI", placeholder="file://audit/log")
                    read_btn = gr.Button("Read Resource", variant="primary")
                    content = gr.Textbox(label="Resource Content", lines=10)

            list_btn.click(self.list_resources, outputs=listing)
            read_btn.click(self.read_resource, inputs=uri, outputs=content)

    def _prompts_tab(self):
        with gr.Tab("Prompts"):
            with gr.Row():
                with gr.Column():
                    list_btn = gr.Button("List Prompts", variant="primary")
                    listing = gr.Textbox(label="Available Prompts", lines=5)
                with gr.Column():
                    prompt = gr.Dropdown(label="Select Prompt", choices=[], interactive=True)
                    args = gr.Textbox(
                        label="Arguments (JSON)",
                        placeholder='{"operation": "write_file", "risk_level": "MEDIUM"}',
                        lines=2,
                    )
                    get_btn = gr.Button("Get Prompt", variant="primary")
                    result = gr.Textbox(label="Prompt Messages", lines=10)

            list_btn.click(self.list_prompts, outputs=[listing, prompt])
            get_btn.click(self.get_prompt, inputs=[prompt, args], outputs=result)

    def _permissions_tab(self):
        with gr.Tab("Permissions"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown(
                        "**Configure Tool Permission**  \n"
                        'Pick a tool, or type a rule such as `write_file:{"filepath": "safe.txt"}`.'
                    )
                    load_btn = gr.Button("Load Tools", size="sm")
                    rule = gr.Dropdown(label="Tool Name", choices=[], allow_custom_value=True)
                    policy = gr.Radio(
                        choices=list(POLICIES), label="Permission Policy", value="ask"
                    )
                    save_btn = gr.Button("Save Permission", variant="primary")
                    save_result = gr.Textbox(label="Result", lines=3)
                with gr.Column():
                    gr.Markdown("**Audit Log**")
                    audit_btn = gr.Button("View Audit Log", variant="secondary")
                    audit_log = gr.Textbox(label="Audit Log", lines=15)

            load_btn.click(self.load_tool_names, outputs=rule)
            save_btn.click(self.save_permission, inputs=[rule, policy], outputs=save_result)
            audit_btn.click(self.view_audit_log, outputs=audit_log)
