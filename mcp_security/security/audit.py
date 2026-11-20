"""Audit log: one timestamped line per security decision or file change."""

from datetime import datetime
from pathlib import Path


class AuditLog:
    """Append-only text log shared by the client (decisions) and server (actions)."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def record(self, operation: str, decision: str = "", reason: str = "") -> None:
        entry = f"[{datetime.now().isoformat(timespec='seconds')}] {operation}"
        if decision:
            entry += f" - Decision: {decision}"
        if reason:
            entry += f" - Reason: {reason}"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(entry + "\n")

    def read(self) -> str:
        if not self.path.exists() or not self.path.read_text().strip():
            return "No audit log entries yet."
        return self.path.read_text()
