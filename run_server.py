"""The MCP server (STDIO transport).

You normally don't run this yourself: the GUI client and the AI host start it
as a subprocess. Running it directly just waits for MCP messages on stdin.
"""

import warnings

from mcp_security.config import DATA_DIR
from mcp_security.server import create_server

warnings.filterwarnings("ignore", category=DeprecationWarning)

if __name__ == "__main__":
    create_server(DATA_DIR).run(transport="stdio", show_banner=False)
