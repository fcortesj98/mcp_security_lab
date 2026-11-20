"""Keep every file operation inside the data folder."""

from pathlib import Path

# Tools must never change their own permissions or erase the audit trail.
PROTECTED_FILES = {"permissions.json", "audit.log"}


class DataDir:
    """The data folder the server's file tools are limited to."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative_path: str) -> Path:
        """Absolute path inside the data folder, or PermissionError.

        Blocks escapes such as "/etc/passwd" or "../../secret.txt".
        """
        path = (self.root / relative_path).resolve()
        if not path.is_relative_to(self.root):
            raise PermissionError("Access denied - path is outside the data directory")
        return path

    def resolve_writable(self, relative_path: str) -> Path:
        """Like resolve(), but also refuses the protected security files."""
        path = self.resolve(relative_path)
        if path.parent == self.root and path.name in PROTECTED_FILES:
            raise PermissionError(f"Access denied - {path.name} is protected")
        return path
