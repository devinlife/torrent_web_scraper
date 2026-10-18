# claude-agent-sdk 0.2.163 research notes for Doctor

Checked on 2026-10-18 against the installed source (`.venv/.../claude_agent_sdk/`) and in the `torrent-web-scraper` container (linux/aarch64, Python 3.12). The bundled CLI is version 2.1.286.

## TL;DR

| Question | Answer |
|---|---|
| OAuth token in the container | Works. `CLAUDE_CODE_OAUTH_TOKEN` from `.env` is picked up with no extra wiring. |
| Only our tools | `tools=[]` + `mcp_servers={"doctor": srv}` + `allowed_tools=["mcp__doctor__<name>", ...]` + `permission_mode="dontAsk"` + `strict_mcp_config=True` + `setting_sources=[]`. Verified: the `init` tool list was `['StructuredOutput', 'mcp__doctor__ping']`. |
| Structured output | Supported. `output_format={"type":"json_schema","schema":{...}}`. The parsed dict lands in `ResultMessage.structured_output`. It still works with `tools=[]`. |
| Budget | `max_budget_usd` exists. When the budget is hit you get `ResultMessage(subtype="error_max_budget_usd", is_error=True)` and then the iterator **raises `ResultError`**. |
| `model="sonnet"` | Accepted. It resolved to `claude-sonnet-5-5` in the `init` message. |
| Transmission from the container | **Not reachable.** The container cannot reach any LAN host (Pi, router); it can reach the Mac and the internet. From the Mac host the snippet works: version 2.94, 23 torrents. See section 8. |

## 1. Imports and signatures

```python
from claude_agent_sdk import (
    query, ClaudeSDKClient, ClaudeAgentOptions,
    tool, create_sdk_mcp_server, ToolAnnotations,
    AssistantMessage, UserMessage, SystemMessage, ResultMessage, RateLimitEvent, StreamEvent,
    TextBlock, ToolUseBlock, ToolResultBlock, ThinkingBlock,
    ClaudeSDKError, ProcessError, ResultError, CLINotFoundError,
)

async def query(*, prompt: str | AsyncIterable[dict], options: ClaudeAgentOptions | None = None,
                transport: Transport | None = None) -> AsyncIterator[Message]
class ClaudeSDKClient(options: ClaudeAgentOptions | None = None, transport=None)  # connect/query/receive_response/interrupt/disconnect, async with
def tool(name: str, description: str, input_schema: type | dict, annotations: ToolAnnotations | None = None)
def create_sdk_mcp_server(name: str, version: str = "1.0.0", tools: list[SdkMcpTool] | None = None) -> McpSdkServerConfig
```

Use `query()` for Doctor. It is one-shot, and `ClaudeSDKClient` is only needed for follow-ups and interrupts.

**`@tool` input schema.** There are three accepted forms:
- **Simple dict.** `{"host": str}`. Every key becomes required. Types map as str→string, int→integer, float→number, bool→boolean, list/dict→array/object. To add a description, use `Annotated[str, "desc"]`.
- **TypedDict class.** `NotRequired` fields become optional.
- **Full JSON Schema.** The SDK uses the dict as-is when it has `"type"` (a string) and `"properties"`.

The SDK validates arguments with `jsonschema` before it calls the handler.

**Handler shape and return value.**
- The handler is `async def h(args: dict) -> dict`.
- It returns `{"content": [{"type": "text", "text": "..."}]}`. Add `"is_error": True` to mark a failure.
- If the handler raises, the exception becomes an error result that Claude sees. It does not crash the run.
- `image` content is also accepted.
- `ToolAnnotations(readOnlyHint=True, maxResultSizeChars=N)` raises the size limit for inline tool results. Use it for `browse`, which returns HTML.

**Messages** (all are dataclasses):
- `AssistantMessage(content: list[ContentBlock], model, parent_tool_use_id, error, usage, message_id, stop_reason, session_id, uuid)`
- `UserMessage(content: str | list[ContentBlock], uuid, parent_tool_use_id, tool_use_result, origin)`. Tool results arrive here as `ToolResultBlock`.
- `SystemMessage(subtype: str, data: dict)`. The first one has `subtype="init"`, with `data["tools"]`, `data["model"]`, `data["mcp_servers"]` and `data["permissionMode"]`.
- `ResultMessage(subtype, duration_ms, duration_api_ms, is_error, num_turns, session_id, stop_reason, total_cost_usd, usage, result, structured_output, model_usage, permission_denials, deferred_tool_use, errors, api_error_status, uuid, terminal_reason, origin)`
- `RateLimitEvent`. It appeared in the stream, so ignore it.
- `StreamEvent`. It only appears with `include_partial_messages=True`.
- Blocks:
  - `TextBlock(text)`
  - `ThinkingBlock(thinking, signature)`
  - `ToolUseBlock(id, name, input)`
  - `ToolResultBlock(tool_use_id, content, is_error)`
  - `ServerToolUseBlock` and `ServerToolResultBlock`

### All 49 `ClaudeAgentOptions` fields

| field | type | default |
|---|---|---|
| `tools` | `list[str] \| ToolsPreset \| None` | `None` (CLI default tools) |
| `allowed_tools` | `list[str]` | `[]` |
| `system_prompt` | `str \| SystemPromptPreset \| SystemPromptCustom \| SystemPromptFile \| None` | `None` (sent as `--system-prompt ""`, i.e. **not** the Claude Code prompt) |
| `mcp_servers` | `dict[str, McpServerConfig] \| str \| Path` | `{}` |
| `strict_mcp_config` | `bool` | `False` |
| `permission_mode` | `Literal["default","acceptEdits","plan","bypassPermissions","dontAsk","auto"] \| None` | `None` |
| `continue_conversation` | `bool` | `False` |
| `resume` | `str \| None` | `None` |
| `session_id` | `str \| None` | `None` |
| `max_turns` | `int \| None` | `None` |
| `max_budget_usd` | `float \| None` | `None` |
| `disallowed_tools` | `list[str]` | `[]` |
| `model` | `str \| None` | `None` |
| `fallback_model` | `str \| None` | `None` |
| `betas` | `list[Literal["context-1m-2025-08-07"]]` | `[]` |
| `permission_prompt_tool_name` | `str \| None` | `None` |
| `cwd` | `str \| Path \| None` | `None` |
| `cli_path` | `str \| Path \| None` | `None` (bundled CLI) |
| `settings` | `str \| None` | `None` |
| `add_dirs` | `list[str \| Path]` | `[]` |
| `env` | `dict[str, str]` | `{}` |
| `extra_args` | `dict[str, str \| None]` | `{}` |
| `max_buffer_size` | `int \| None` | `None` |
| `debug_stderr` | `Any` | `sys.stderr` (deprecated) |
| `stderr` | `Callable[[str], None] \| None` | `None` |
| `can_use_tool` | `CanUseTool \| None` | `None` |
| `hooks` | `dict[HookEvent, list[HookMatcher]] \| None` | `None` |
| `user` | `str \| None` | `None` |
| `include_partial_messages` | `bool` | `False` |
| `include_hook_events` | `bool` | `False` |
| `forward_subagent_text` | `bool` | `False` |
| `verbatim_prompts` | `bool` | `False` |
| `fork_session` | `bool` | `False` |
| `resume_session_at` | `str \| None` | `None` |
| `resume_drops_turn` | `str \| None` | `None` |
| `agents` | `dict[str, AgentDefinition] \| None` | `None` |
| `setting_sources` | `list[Literal["user","project","local"]] \| None` | `None` (loads **all** sources) |
| `skills` | `list[str] \| Literal["all"] \| None` | `None` |
| `sandbox` | `SandboxSettings \| None` | `None` |
| `plugins` | `list[SdkPluginConfig]` | `[]` |
| `max_thinking_tokens` | `int \| None` | `None` (deprecated) |
| `thinking` | `ThinkingConfigAdaptive \| ThinkingConfigEnabled \| ThinkingConfigDisabled \| None` | `None` |
| `effort` | `Literal["low","medium","high","xhigh","max"] \| None` | `None` |
| `output_format` | `dict[str, Any] \| None` | `None` |
| `enable_file_checkpointing` | `bool` | `False` |
| `session_store` | `SessionStore \| None` | `None` |
| `session_store_flush` | `Literal["batched","eager"]` | `"batched"` |
| `load_timeout_ms` | `int` | `60000` |
| `task_budget` | `TaskBudget \| None` (`{"total": int}` tokens) | `None` |

## 2. Hermetic agent with only our tools

```python
srv = create_sdk_mcp_server("doctor", tools=[dns_tls_check, browse, run_parser, probe_domains])
opts = ClaudeAgentOptions(
    tools=[],                         # --tools ""  -> removes ALL built-ins (Bash, Read, WebFetch, ...)
    mcp_servers={"doctor": srv},
    allowed_tools=[f"mcp__doctor__{n}" for n in ("dns_tls_check", "browse", "run_parser", "probe_domains")],
    permission_mode="dontAsk",        # anything not pre-approved is denied, never prompts
    strict_mcp_config=True,           # ignore .mcp.json / user / plugin MCP servers
    setting_sources=[],               # REQUIRED for hermetic: default None loads user+project+local and CLAUDE.md
    system_prompt=DOCTOR_PROMPT,      # plain str = fully custom prompt
)
```

- **Tool naming.** Tools are named `mcp__<mcp_servers key>__<tool name>`. The tool's name comes from the dict key, not from the `create_sdk_mcp_server` name. Keep the two names the same.
- **`tools=[]` is the real block.** It removes the built-in tools from the model's context. `disallowed_tools` is not needed.
- **`allowed_tools` only auto-approves.** It does not restrict which tools are available. Wildcards were not tested, so list the four names explicitly.
- **`StructuredOutput` is still present** when `output_format` is set, even with `tools=[]`. That is expected.
- **The container already has nothing in `~/.claude`.** Still pass `setting_sources=[]`. Otherwise running the app on the Mac outside Docker would pick up the user's settings, CLAUDE.md, hooks and plugins.

## 3. Structured output

This version supports it. `output_format={"type": "json_schema", "schema": SCHEMA}` becomes the CLI flag `--json-schema`. The model calls a synthetic `StructuredOutput` tool. You get the parsed **dict** in `ResultMessage.structured_output`, and `ResultMessage.result` holds the same JSON as text.

Two things to account for:
- `StructuredOutput` **counts as a turn**. The ping test used `num_turns=3`: ping, then StructuredOutput, then the final turn. Leave headroom, so `max_turns=15` means about 13 diagnostic tool calls.
- When the run ends on an error (budget or turns), `structured_output` is `None`. Store the verdict as `error` in that case.

## 4. Limits

- `max_turns: int` maps to `--max-turns`.
- `max_budget_usd: float` maps to `--max-budget-usd`.
- `task_budget={"total": tokens}` is optional. It makes the model aware of its remaining tokens.
- `model="sonnet"` resolved to `claude-sonnet-5-5`. `"opus"` is the same alias mechanism (plan section 2 already verified it).
- Haiku also shows up in `model_usage` (`claude-haiku-4-5-*`). It is used for the CLI's own small background calls, and it counts toward the cost and the budget.

**What happens when the budget is hit.** The verified sequence, with `max_budget_usd=0.0001`:
1. The stream yields `ResultMessage(subtype="error_max_budget_usd", is_error=True, terminal_reason="budget_exhausted", total_cost_usd=0.000967)`.
2. The iterator then raises `ResultError` with `.subtype == "error_max_budget_usd"` and `.errors == ['Reached maximum budget ($0.0001)']`.

The max-turns case looks the same, with `subtype="error_max_turns"`. Always catch `ResultError` and keep the last `ResultMessage` so the real cost gets saved. The budget check runs between turns, so the actual cost can go somewhat over the cap.

## 5. Progress streaming and full Doctor runner skeleton

```python
import json
from claude_agent_sdk import (query, AssistantMessage, UserMessage, ResultMessage,
                              TextBlock, ToolUseBlock, ToolResultBlock, ResultError)

def _brief(d: dict, n: int = 80) -> str:
    s = json.dumps(d, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"

async def run_doctor(prompt: str, opts, emit) -> tuple[dict | None, ResultMessage | None]:
    """emit(str) appends a progress line (DB row / SSE / htmx poll)."""
    last = None
    try:
        async for m in query(prompt=prompt, options=opts):
            if isinstance(m, AssistantMessage):
                for b in m.content:
                    if isinstance(b, ToolUseBlock) and b.name != "StructuredOutput":
                        emit(f"tool: {b.name.removeprefix('mcp__doctor__')} {_brief(b.input)}")
                    elif isinstance(b, TextBlock) and b.text.strip():
                        emit(f"say: {b.text.strip()[:200]}")
            elif isinstance(m, UserMessage) and isinstance(m.content, list):
                for b in m.content:
                    if isinstance(b, ToolResultBlock) and b.is_error:
                        emit(f"tool error: {str(b.content)[:120]}")
            elif isinstance(m, ResultMessage):
                last = m
    except ResultError as e:            # budget / max turns / API error; `last` already holds the result
        emit(f"stopped: {e.subtype} {e.errors}")
    return (last.structured_output if last and not last.is_error else None), last
```

Save `last.total_cost_usd`, `last.num_turns` and `last.subtype` with the report.

## 6. Concurrency and runtime

- **Event loop.** `query()` is an async generator built on **anyio**, with an anyio subprocess. It runs natively on the asyncio loop that uvicorn uses. Trio is not involved. Run it inside a normal `asyncio.create_task(...)` started from the endpoint, and fully consume the iterator.
- **Cancellation.** Cleanup is shielded for anyio cancellation. A raw `asyncio.wait_for` or `task.cancel()` can skip the terminate escalation, and the SDK has an atexit reaper as a backstop. Rely on `max_turns` / `max_budget_usd` instead of wrapping the call in a timeout.
- **Early exit is safe.** If you `break`, the SDK's `finally` calls `aclose()` and kills the CLI.
- **`ClaudeSDKClient` caveat.** Its source says it must stay in the async context where it connected. This does not matter for `query()`.
- **CLI binary.** The SDK spawns the bundled CLI at `claude_agent_sdk/_bundled/claude`. In the image that is `/app/.venv/lib/python3.12/site-packages/claude_agent_sdk/_bundled/claude`. It is about 225 MB and comes from the platform wheel, so no Node is needed. Its fallback is `shutil.which("claude")`.
- **HOME must be writable.** After one run the container's HOME contained `/root/.claude.json` and `/root/.claude/{projects,sessions,backups,policy-limits.json,remote-settings.json}`. The container runs as root with `HOME=/root`, which is fine. Do not make the root filesystem read-only without a writable HOME.
- **`cwd`.** It is optional, and the process cwd is used if unset. Set `cwd="/tmp"` (or `/data/doctor`) so session transcripts don't key off `/app`. It must exist, or the SDK raises.
- **Environment.** The CLI inherits the full parent environment, minus `CLAUDECODE`. That is how `CLAUDE_CODE_OAUTH_TOKEN` from `env_file` reaches it. The CLI also inherits `TRANSMISSION_PASSWORD`, but with no Bash or Read tool the model cannot read it. To be strict, pass `env={"TRANSMISSION_PASSWORD": ""}`. Overrides are merged over the inherited set.

## 7. End-to-end test in the container (passed)

Run with: `docker compose run --rm --no-deps -v $SCRATCH:/work scraper python /work/sdk_ping.py`

```python
import asyncio, json, os, sys
from claude_agent_sdk import (
    query, tool, create_sdk_mcp_server, ClaudeAgentOptions,
    AssistantMessage, UserMessage, SystemMessage, ResultMessage,
    TextBlock, ToolUseBlock, ToolResultBlock, ResultError,
)

@tool("ping", "Health check. Returns 'pong'.", {})
async def ping(args):
    return {"content": [{"type": "text", "text": "pong"}]}

SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}

async def main():
    opts = ClaudeAgentOptions(
        model="sonnet", max_turns=3, max_budget_usd=0.25,
        tools=[],
        mcp_servers={"doctor": create_sdk_mcp_server("doctor", tools=[ping])},
        allowed_tools=["mcp__doctor__ping"],
        permission_mode="dontAsk", strict_mcp_config=True, setting_sources=[],
        system_prompt="You are a test agent.",
        output_format={"type": "json_schema", "schema": SCHEMA},
        cwd="/tmp",
        stderr=lambda l: print("STDERR:", l[:200], file=sys.stderr),
    )
    seen, last = [], None
    try:
        async for m in query(prompt='Call the ping tool once, then reply with JSON {"ok": true}.', options=opts):
            seen.append(type(m).__name__ + (f"({m.subtype})" if hasattr(m, "subtype") else ""))
            if isinstance(m, SystemMessage) and m.subtype == "init":
                print("init model:", m.data.get("model"), "tools:", m.data.get("tools"))
            elif isinstance(m, AssistantMessage):
                for b in m.content:
                    if isinstance(b, ToolUseBlock): print("tool_use:", b.name, json.dumps(b.input))
            elif isinstance(m, ResultMessage):
                last = m
    except ResultError as e:
        print("ResultError:", e.subtype, e.terminal_reason, e.errors)
    print("order:", seen)
    print(last.subtype, last.is_error, last.total_cost_usd, last.num_turns, last.structured_output)

asyncio.run(main())
```

Output:
```
init model: claude-sonnet-5-5   tools: ['StructuredOutput', 'mcp__doctor__ping']
init mcp: [{'name': 'doctor', 'status': 'connected', 'source': 'sdk'}]   permissionMode: dontAsk
tool_use: mcp__doctor__ping {}
tool_result: [{'type': 'text', 'text': 'pong'}]
tool_use: StructuredOutput {"ok": true}
order: [SystemMessage(init), RateLimitEvent, AssistantMessage, UserMessage, AssistantMessage, UserMessage, ResultMessage(success)]
subtype=success is_error=False terminal_reason=completed total_cost_usd=0.005314 num_turns=3
structured_output={'ok': True} (dict)   result='{"ok":true}'   permission_denials=[]
```

## 8. Transmission RPC (stdlib only)

```python
import base64, json, os, urllib.request, urllib.error

URL = os.environ["TRANSMISSION_URL"]
AUTH = "Basic " + base64.b64encode(
    f'{os.environ["TRANSMISSION_USER"]}:{os.environ["TRANSMISSION_PASSWORD"]}'.encode()).decode()
_sid = ""

def rpc(method, **arguments):
    global _sid
    body = json.dumps({"method": method, "arguments": arguments}).encode()
    for _ in range(2):
        req = urllib.request.Request(URL, data=body, headers={
            "Authorization": AUTH, "Content-Type": "application/json",
            "X-Transmission-Session-Id": _sid})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                resp = json.load(r)
                if resp.get("result") != "success":
                    raise RuntimeError(f"transmission: {resp.get('result')}")
                return resp["arguments"]
        except urllib.error.HTTPError as e:
            if e.code != 409:
                raise
            _sid = e.headers["X-Transmission-Session-Id"]  # stale/missing session id -> retry once
    raise RuntimeError("transmission: 409 twice")

# rpc("session-get") ; rpc("torrent-get", fields=["id","name","addedDate"])
# add: rpc("torrent-add", filename=magnet)  -> {"torrent-added": {...}} or {"torrent-duplicate": {...}}
```

`urllib.request` is blocking, so call it with `await asyncio.to_thread(rpc, ...)` from FastAPI.

**Results**

| Where | Result |
|---|---|
| Mac host | Reachable. `version` 2.94 (d8e60ee44f), `rpc-version` 15, `download-dir` `/home/pi/S_Samba/X_Torrent/temp_bucket`, `torrent-get` count 23. |
| Container | **Not reachable.** `URLError: timed out` on TCP connect to `192.168.0.10:59090`. |

What the container network checks showed:

| Target | Result |
|---|---|
| `192.168.0.10:59090` (Pi Transmission) | timeout |
| `192.168.0.10:22` (Pi SSH) | timeout |
| `192.168.0.1` (router) | timeout |
| `1.1.1.1:443` (internet) | ok |
| Mac `192.168.0.74`, `host.docker.internal` | connection refused, which means the host is reachable |

- The same timeout happens with `--network host`, which in OrbStack means the VM itself.
- There is no subnet clash: the Docker networks are 192.168.97–215.x and the LAN is 192.168.0.0/24.

**Diagnosis.** The OrbStack VM is blocked from the Mac's local network, while internet traffic goes through. This is most likely the macOS **Local Network privacy** permission: System Settings → Privacy & Security → Local Network → enable OrbStack, then restart OrbStack. A less likely cause is that the Mac has two interfaces on 192.168.0.0/24 (en1 Wi-Fi .76 and en10 Ethernet .74). I did not change any system setting. Re-run `/work/tr.py` in the container after the fix.
