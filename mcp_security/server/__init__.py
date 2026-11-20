"""The permission-aware MCP server, assembled from its tools, resources and prompts."""

import logging
from pathlib import Path

from fastmcp import FastMCP

from mcp_security.security import AuditLog, PermissionStore

from .prompts import register_prompts
from .resources import register_resources
from .sandbox import DataDir
from .tools import register_tools

logging.getLogger("fastmcp").setLevel(logging.WARNING)


def create_server(data_dir: Path) -> FastMCP:
    mcp = FastMCP("Permission-Aware MCP Server")
    data = DataDir(data_dir)
    audit = AuditLog(data.root / "audit.log")
    permissions = PermissionStore(data.root / "permissions.json")

    register_tools(mcp, data, audit)
    register_resources(mcp, audit, permissions)
    register_prompts(mcp)
    return mcp


__all__ = ["create_server"]
