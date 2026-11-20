from mcp_security.config import AUDIT_LOG_FILE, PERMISSIONS_FILE, SERVER_SCRIPT
from mcp_security.security import AuditLog, PermissionStore

from .base import MCPStdioClient
from .gate import ALLOWED, DENIED, NEEDS_APPROVAL, PermissionGate, ToolOutcome


def create_gate(server_script=SERVER_SCRIPT) -> PermissionGate:
    """Client + permission store + audit log, wired together with the default paths."""
    return PermissionGate(
        MCPStdioClient(server_script),
        PermissionStore(PERMISSIONS_FILE),
        AuditLog(AUDIT_LOG_FILE),
    )


__all__ = [
    "ALLOWED",
    "DENIED",
    "NEEDS_APPROVAL",
    "MCPStdioClient",
    "PermissionGate",
    "ToolOutcome",
    "create_gate",
]
