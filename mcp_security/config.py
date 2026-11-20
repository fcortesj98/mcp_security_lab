"""Shared settings. Every value can be overridden with an environment variable."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Folder with the files the tools may touch, plus permissions.json and audit.log.
DATA_DIR = Path(os.getenv("MCP_DATA_DIR", PROJECT_ROOT / "data")).resolve()
PERMISSIONS_FILE = DATA_DIR / "permissions.json"
AUDIT_LOG_FILE = DATA_DIR / "audit.log"

# Script the client launches as the MCP server (STDIO transport).
SERVER_SCRIPT = PROJECT_ROOT / "run_server.py"

# Gradio apps
UI_HOST = os.getenv("UI_HOST", "127.0.0.1")
GUI_CLIENT_PORT = int(os.getenv("GUI_CLIENT_PORT", "7863"))
HOST_APP_PORT = int(os.getenv("HOST_APP_PORT", "7864"))

# LLM (AI host only). The OpenAI SDK also reads OPENAI_API_KEY and OPENAI_BASE_URL.
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-6-luna")
MAX_TOOL_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "5"))
