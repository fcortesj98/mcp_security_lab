"""Start the permission-aware AI host (LLM chat with approval requests).

Usage: python run_host.py [server_script]
"""

from mcp_security.cli import parse_args
from mcp_security.client import create_gate
from mcp_security.config import HOST_APP_PORT, LLM_MODEL, UI_HOST
from mcp_security.host import Agent, HostGUI, ToolBridge

if __name__ == "__main__":
    args = parse_args("MCP permission AI host")
    agent = Agent(ToolBridge(create_gate(args.server_script)), model=LLM_MODEL)
    HostGUI(agent).build().queue().launch(server_name=UI_HOST, server_port=HOST_APP_PORT)
