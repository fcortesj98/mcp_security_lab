"""A thin MCP client that launches the server as a subprocess (STDIO transport).

Protocol only: no permissions, no UI, no LLM. Security is added on top by
PermissionGate (see gate.py).
"""

import asyncio
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPStdioClient:
    def __init__(self, server_script: Path):
        self.server_script = Path(server_script)
        self.session: ClientSession | None = None
        self._exit_stack = AsyncExitStack()
        self._connect_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Start the server and open the session once; later calls are no-ops."""
        async with self._connect_lock:
            if self.session is not None:
                return
            params = StdioServerParameters(
                command=sys.executable,  # same Python (and venv) as this app
                args=[str(self.server_script)],
                env=dict(os.environ),  # pass settings such as MCP_DATA_DIR through
            )
            read, write = await self._exit_stack.enter_async_context(stdio_client(params))
            self.session = await self._exit_stack.enter_async_context(ClientSession(read, write))
            await self.session.initialize()

    async def cleanup(self) -> None:
        await self._exit_stack.aclose()
        self.session = None

    # --- tools -----------------------------------------------------------------

    async def list_tools(self):
        await self.connect()
        return (await self.session.list_tools()).tools

    async def call_tool(self, name: str, arguments: dict):
        await self.connect()
        return await self.session.call_tool(name, arguments)

    # --- resources -------------------------------------------------------------

    async def list_resources(self):
        await self.connect()
        return (await self.session.list_resources()).resources

    async def read_resource(self, uri: str):
        await self.connect()
        return await self.session.read_resource(uri)

    # --- prompts ---------------------------------------------------------------

    async def list_prompts(self):
        await self.connect()
        return (await self.session.list_prompts()).prompts

    async def get_prompt(self, name: str, arguments: dict):
        await self.connect()
        return await self.session.get_prompt(name, arguments)
