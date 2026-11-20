"""The permission gate: every tool call passes through here before reaching the server.

app ──► PermissionGate ──► MCP server
          │  allow → run it
          │  deny  → block it
          │  ask   → return an ApprovalRequest; run only once approved
          └─ every decision is written to the audit log
"""

import json
from dataclasses import dataclass

from mcp_security.security import (
    ALLOW,
    DENY,
    ApprovalRequest,
    AuditLog,
    PermissionStore,
    assess_risk,
)

from .base import MCPStdioClient
from .formatting import content_to_text

ALLOWED, DENIED, NEEDS_APPROVAL = "allowed", "denied", "needs_approval"


@dataclass
class ToolOutcome:
    status: str  # allowed | denied | needs_approval
    text: str
    approval: ApprovalRequest | None = None


class PermissionGate:
    def __init__(self, client: MCPStdioClient, permissions: PermissionStore, audit: AuditLog):
        self.client = client
        self.permissions = permissions
        self.audit = audit

    async def call_tool(self, name: str, arguments: dict, approved: bool = False) -> ToolOutcome:
        """Check the policy, then run, block or ask for approval."""
        policy = self.permissions.check(name, arguments)
        risk = assess_risk(name)
        operation = f"TOOL: {name} {json.dumps(arguments, sort_keys=True)} (risk: {risk.level})"

        if policy == DENY:
            self.audit.record(operation, "DENIED", "Policy: deny")
            return ToolOutcome(DENIED, f"Permission denied for tool: {name}")

        if policy != ALLOW and not approved:
            request = ApprovalRequest(name, arguments, risk)
            self.audit.record(operation, "ASK", "Awaiting approval")
            return ToolOutcome(NEEDS_APPROVAL, request.message, request)

        reason = "Policy: allow" if policy == ALLOW else "Policy: ask - approved by user"
        self.audit.record(operation, "ALLOWED", reason)
        result = await self.client.call_tool(name, arguments)
        return ToolOutcome(ALLOWED, content_to_text(result.content) or "No response")
