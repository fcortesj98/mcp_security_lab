"""Read-only views of the audit log and the permission policies."""

import json

from fastmcp import FastMCP

from mcp_security.security import AuditLog, PermissionStore


def register_resources(mcp: FastMCP, audit: AuditLog, permissions: PermissionStore) -> None:
    @mcp.resource("file://audit/log")
    def get_audit_log() -> str:
        """Get the audit log of all operations."""
        return audit.read()

    @mcp.resource("file://config/permissions")
    def get_permissions_config() -> str:
        """Get the current permissions configuration."""
        return json.dumps(permissions.load(), indent=2)
