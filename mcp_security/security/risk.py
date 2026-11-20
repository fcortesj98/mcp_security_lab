"""Risk levels: tell the user how dangerous a tool is before it runs."""

from dataclasses import dataclass

RISK_LEVELS = {
    "read_file": "low",
    "write_file": "medium",
    "delete_file": "high",
    "execute_command": "critical",
}

RISK_DESCRIPTIONS = {
    "low": "Safe operation with minimal impact",
    "medium": "Moderate impact - modifies data",
    "high": "High impact - destructive operation",
    "critical": "Critical impact - system-level operation",
}


@dataclass
class RiskAssessment:
    tool: str
    level: str
    description: str

    def __str__(self) -> str:
        return f"{self.level.upper()} - {self.description}"


def assess_risk(tool_name: str) -> RiskAssessment:
    """Unknown tools are treated as medium risk."""
    level = RISK_LEVELS.get(tool_name, "medium")
    return RiskAssessment(tool_name, level, RISK_DESCRIPTIONS[level])
