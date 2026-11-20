"""Command-line arguments shared by the GUI client and the AI host."""

import argparse

from mcp_security.config import SERVER_SCRIPT


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "server_script",
        nargs="?",
        default=str(SERVER_SCRIPT),
        help="MCP server script to launch over STDIO (default: run_server.py)",
    )
    return parser.parse_args()
