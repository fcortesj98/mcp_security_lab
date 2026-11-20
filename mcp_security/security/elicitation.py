"""Elicitation: ask the user for structured input before a sensitive action.

The request follows the shape of MCP's `elicitation/create`: a message for the
user plus a JSON schema describing the answer we expect. In this lab the
answer is collected by the apps themselves (the "Approve & Execute" button in
the GUI client, or typing "yes" in the AI host) instead of a protocol round trip.
"""

import json
from dataclasses import dataclass

from .risk import RiskAssessment

APPROVAL_SCHEMA = {
    "type": "object",
    "properties": {
        "approved": {"type": "boolean", "description": "Run this operation?"},
    },
    "required": ["approved"],
}


@dataclass
class ApprovalRequest:
    tool: str
    arguments: dict
    risk: RiskAssessment

    @property
    def message(self) -> str:
        return (
            f"Permission required for tool: {self.tool}\n"
            f"Risk: {self.risk}\n"
            f"Arguments: {json.dumps(self.arguments, indent=2)}\n"
            "This tool requires approval before execution."
        )

    def as_elicitation(self) -> dict:
        """The request as it would be sent with MCP elicitation/create."""
        return {
            "method": "elicitation/create",
            "params": {"message": self.message, "requestedSchema": APPROVAL_SCHEMA},
        }
