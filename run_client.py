"""Start the GUI client (permission management, tools, resources, prompts, audit log).

Usage: python run_client.py [server_script]
"""

from mcp_security.cli import parse_args
from mcp_security.client import create_gate
from mcp_security.config import GUI_CLIENT_PORT, UI_HOST
from mcp_security.gui import ClientGUI

if __name__ == "__main__":
    args = parse_args("MCP permission GUI client")
    gate = create_gate(args.server_script)
    ClientGUI(gate).build().queue().launch(server_name=UI_HOST, server_port=GUI_CLIENT_PORT)
