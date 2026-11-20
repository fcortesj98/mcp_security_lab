"""Four tools, one per risk level: read (low), write (medium), delete (high), execute (critical)."""

from fastmcp import FastMCP

from mcp_security.security import AuditLog

from .sandbox import DataDir


def register_tools(mcp: FastMCP, data: DataDir, audit: AuditLog) -> None:
    @mcp.tool()
    def read_file(filepath: str) -> str:
        """Read a file from the data directory. (Risk: LOW)"""
        try:
            path = data.resolve(filepath)
            if not path.is_file():
                return f"Error: File {filepath} not found"
            return path.read_text()
        except PermissionError as e:
            audit.record(f"BLOCKED READ: {filepath}", reason=str(e))
            return f"Error: {e}"
        except Exception as e:
            return f"Error reading file: {e}"

    @mcp.tool()
    def write_file(filepath: str, content: str) -> str:
        """Write content to a file in the data directory. (Risk: MEDIUM)"""
        try:
            path = data.resolve_writable(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            audit.record(f"WRITE: {filepath}")
            return f"Successfully wrote to {filepath}"
        except PermissionError as e:
            audit.record(f"BLOCKED WRITE: {filepath}", reason=str(e))
            return f"Error: {e}"
        except Exception as e:
            return f"Error writing file: {e}"

    @mcp.tool()
    def delete_file(filepath: str) -> str:
        """Delete a file from the data directory. (Risk: HIGH)"""
        try:
            path = data.resolve_writable(filepath)
            if not path.is_file():
                return f"Error: File {filepath} not found"
            path.unlink()
            audit.record(f"DELETE: {filepath}")
            return f"Successfully deleted {filepath}"
        except PermissionError as e:
            audit.record(f"BLOCKED DELETE: {filepath}", reason=str(e))
            return f"Error: {e}"
        except Exception as e:
            return f"Error deleting file: {e}"

    @mcp.tool()
    def execute_command(command: str) -> str:
        """Execute a system command. (Risk: CRITICAL) Simulation only: nothing is run."""
        audit.record(f"EXECUTE (simulated): {command}")
        return (
            f"Simulated execution of command: {command}\n(Actual execution disabled for security)"
        )
