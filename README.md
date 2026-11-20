# MCP Security: Permissions, Elicitation and Audit Logging

A client-server project built on the **Model Context Protocol (MCP)** that shows how to control what tools are allowed to do. A FastMCP server offers four file tools, each with a different risk level. Every call passes through a **permission gate** on the client side before it reaches the server:

- **GUI client**: a Gradio app for calling tools, editing permission policies and reading the audit log.
- **AI host**: a Gradio chat where an LLM uses the tools and asks you before it does anything sensitive.

Both apps start the server for you as a subprocess (**STDIO transport**).

## Security features

| Feature | What it does |
|---|---|
| **Permission policies** | Each tool is set to `allow` (runs at once), `ask` (needs your approval) or `deny` (always blocked), in `data/permissions.json`. |
| **Argument-specific rules** | A rule such as `write_file:{"filepath": "safe.txt"}` overrides the tool's general policy for matching calls. |
| **Elicitation (approval)** | `ask` calls return an approval request with the tool, its arguments and its risk. Nothing runs until you click **Approve & Execute** (GUI) or type `yes` (AI host). |
| **Risk levels** | `read_file` low, `write_file` medium, `delete_file` high, `execute_command` critical (simulated, never really run). |
| **Audit log** | Every decision (ALLOWED, DENIED, ASK, CANCELLED) and every file change is written to `data/audit.log`. |
| **Sandbox** | The server can only touch files inside `data/`. Paths like `../../etc/passwd` are blocked, and tools cannot change `permissions.json` or `audit.log`. |

## Project structure

```
mcp_security_lab/
├── run_server.py            # the MCP server (started by the apps)
├── run_client.py            # GUI client  → port 7863
├── run_host.py              # AI host     → port 7864
├── data/                    # files the tools can use, plus permissions.json and audit.log
└── mcp_security/
    ├── config.py            # paths, ports and model (overridable by env vars)
    ├── security/            # shared by the server and the apps
    │   ├── permissions.py   #   PermissionStore: load, save and check policies
    │   ├── elicitation.py   #   ApprovalRequest (the "please approve" message + schema)
    │   ├── risk.py          #   risk levels and descriptions
    │   └── audit.py         #   AuditLog
    ├── server/              # FastMCP server
    │   ├── sandbox.py       #   keeps file access inside data/
    │   ├── tools.py         #   read_file, write_file, delete_file, execute_command
    │   ├── resources.py     #   file://audit/log, file://config/permissions
    │   └── prompts.py       #   security_review
    ├── client/
    │   ├── base.py          #   MCPStdioClient: protocol only
    │   ├── gate.py          #   PermissionGate: allow / ask / deny + audit
    │   └── formatting.py    #   MCP results → readable text
    ├── gui/app.py           # GUI client
    └── host/
        ├── tool_bridge.py   #   MCP tools → OpenAI functions
        ├── agent.py         #   chat loop with the yes/no approval step
        └── app.py           #   chat UI
```

## Setup

Requires Python 3.11+.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The AI host uses the OpenAI SDK. In the IBM Skills Network lab it works as is. Anywhere else, set your own key and model:

```bash
export OPENAI_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini      # default: gpt-6-luna (lab model)
```

## Usage

Run the commands from the project folder. You don't need to start the server yourself.

### GUI client → http://127.0.0.1:7863

```bash
python run_client.py
```

1. **Allow**: in the **Tools** tab, click **List Tools**, choose `read_file` and use `{"filepath": "test.txt"}`. The file is read straight away.
2. **Deny**: `delete_file` with `{"filepath": "test.txt"}` returns *Permission denied*.
3. **Ask**: `write_file` with `{"filepath": "new_file.txt", "content": "Test content"}` shows an approval request. Click **Approve & Execute** to run it.
4. **Permissions** tab: change any policy, add an argument-specific rule, and click **View Audit Log** to see every decision.

### AI host → http://127.0.0.1:7864

```bash
python run_host.py
```

Try these messages:
- `Read the contents of test.txt` (allowed, runs at once)
- `Delete the file test.txt` (denied by policy)
- `Write a new file called greeting.txt with the content "Hello, world!"`, then reply `yes` to approve or `no` to cancel

Any other reply cancels a pending request, so an old approval can never be run later by mistake. Open **Permission Status** to see the current policies, and click **Refresh** after you change them in the GUI client.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `MCP_DATA_DIR` | `./data` | Folder for files, `permissions.json` and `audit.log` |
| `GUI_CLIENT_PORT` / `HOST_APP_PORT` | `7863` / `7864` | Gradio ports |
| `LLM_MODEL` | `gpt-6-luna` | Model used by the AI host |
| `MAX_TOOL_ROUNDS` | `5` | Maximum tool-call rounds per chat message |

## Acknowledgements

Built as part of the IBM RAG and Agentic AI Professional Certificate, offered by IBM through Coursera. The certificate covers LangChain, LangGraph, RAG pipelines, vector databases, multimodal AI, and agentic frameworks such as CrewAI, AG2, BeeAI, and the Model Context Protocol. Model access is provided by IBM watsonx.ai.
