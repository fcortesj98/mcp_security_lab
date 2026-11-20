"""Permission policies: decide whether a tool call is allowed, denied or needs approval.

permissions.json maps a tool to a policy:

    {"read_file": "allow", "write_file": "ask", "delete_file": "deny"}

A key can also carry arguments. It applies when the call contains those
arguments, and it wins over the tool's general policy:

    {"write_file": "deny", "write_file:{\"filepath\": \"safe.txt\"}": "allow"}
"""

import json
from pathlib import Path

ALLOW, ASK, DENY = "allow", "ask", "deny"
POLICIES = (ALLOW, ASK, DENY)

DEFAULT_PERMISSIONS = {
    "read_file": ALLOW,
    "write_file": ASK,
    "delete_file": DENY,
    "execute_command": DENY,
}


class PermissionStore:
    """Reads and writes permissions.json.

    The file is re-read on every check, so a change saved in the GUI client
    applies straight away, even to the AI host running in another process.
    """

    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return dict(DEFAULT_PERMISSIONS)

    def set_policy(self, rule: str, policy: str) -> None:
        if policy not in POLICIES:
            raise ValueError(f"Policy must be one of: {', '.join(POLICIES)}")
        permissions = self.load()
        permissions[rule] = policy
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(permissions, indent=2))

    def policy_for_tool(self, tool_name: str) -> str:
        """The general policy of a tool (unknown tools default to "ask")."""
        return self.load().get(tool_name, ASK)

    def check(self, tool_name: str, arguments: dict) -> str:
        """Return "allow", "ask" or "deny" for this exact call."""
        permissions = self.load()
        best_match, best_size = None, -1

        for rule, policy in permissions.items():
            rule_args = _rule_arguments(rule, tool_name)
            if rule_args is None:
                continue
            matches = all(arguments.get(k) == v for k, v in rule_args.items())
            if matches and len(rule_args) > best_size:  # most specific rule wins
                best_match, best_size = policy, len(rule_args)

        return best_match or permissions.get(tool_name, ASK)


def _rule_arguments(rule: str, tool_name: str) -> dict | None:
    """For a key like 'write_file:{"filepath": "a.txt"}' return its arguments."""
    prefix = f"{tool_name}:"
    if not rule.startswith(prefix):
        return None
    try:
        args = json.loads(rule[len(prefix) :])
    except json.JSONDecodeError:
        return None
    return args if isinstance(args, dict) else None
