"""Turn MCP protocol objects into plain text (shared by the GUI client and the AI host)."""


def content_to_text(items) -> str:
    """Join the text parts of a tool result or resource contents list."""
    return "\n".join(item.text for item in items if hasattr(item, "text"))


def format_resources(resources) -> str:
    lines = []
    for r in resources:
        line = f"• {r.uri}"
        if r.description:
            line += f": {r.description}"
        lines.append(line)
    return "\n".join(lines) or "No resources available"


def format_prompts(prompts) -> str:
    lines = []
    for p in prompts:
        line = f"• {p.name}: {p.description}"
        if p.arguments:
            line += f" (args: {', '.join(a.name for a in p.arguments)})"
        lines.append(line)
    return "\n".join(lines) or "No prompts available"


def format_prompt_result(result) -> str:
    lines = [f"--- Prompt: {result.description} ---", ""]
    for msg in result.messages:
        lines.append(f"[{msg.role}]: {getattr(msg.content, 'text', msg.content)}")
    return "\n".join(lines)
