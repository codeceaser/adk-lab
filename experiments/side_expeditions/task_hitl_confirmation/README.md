# Side Expedition: ADK Task Mode + Native Tool Confirmation

## Question being tested

Can an ADK `mode="task"` LLM agent invoke a tool protected by
`require_confirmation=True`, pause for user confirmation, continue the same
pending tool after approval, receive the tool result, complete its task, and
return the result to the Root LLM agent?

Scope: locate the exact ADK execution boundary that works and the one that
fails. Not a redesign, not a fix.

## Exact environment

| Item                        | Value                                                          |
| --------------------------- | -------------------------------------------------------------- |
| `google-adk`                | 2.6.3                                                          |
| `google-genai`              | 2.17.0                                                         |
| Python                      | 3.13.9                                                         |
| pydantic                    | 2.13.4                                                         |
| fastapi                     | 0.141.1                                                        |
| Model                       | `gemini-3.5-flash`                                             |
| Provider                    | Gemini API (`GOOGLE_GENAI_USE_ENTERPRISE=0`, `GOOGLE_API_KEY`) |
| MCP client lib              | not installed (`mcp` absent) — relevant only to C1/T2          |
| OS                          | Windows 11, PowerShell                                         |
| venv                        | `.venv` at repo root                                           |
| Git commit at scaffold time | `9d5c3d9`                                                      |

ADK is pinned. It is not upgraded or downgraded for this expedition.

## Variants

| Variant | Composition                                                    | Status               |
| ------- | -------------------------------------------------------------- | -------------------- |
| C0      | Root + `write_value` FunctionTool, `require_confirmation=True` | scaffolded (Phase 1) |
| T0      | Root → `mode="task"` worker → `write_value`, no confirmation   | scaffolded (Phase 1) |
| T1      | Root → `mode="task"` worker → confirmed FunctionTool           | scaffolded (Phase 1) |
| C1      | Root + `McpToolset` `write_value`, `require_confirmation=True` | Phase 2              |
| T2      | Root → `mode="task"` worker → confirmed `McpToolset` tool      | Phase 2              |

**Phase 1** (C0/T0/T1) runs in the environment recorded above, unchanged.
**Phase 2** (C1/T2) requires adding the `mcp` dependency; it starts only after
Phase 1 evidence is complete. C1/T2 must use ADK's native `McpToolset`
confirmation path — a `FunctionTool` wrapper around MCP is not a substitute and
would not test the thing in question. `evidence/environment_phase1.txt` holds
the pre-change `pip freeze`, Python version, ADK version and git commit.

Each variant is a standalone ADK app under `variants/`. They share nothing but
`hitl_evidence.py`, which only appends to the tool-side execution log.

## How to start each variant

All variants are served from one agents directory; pick the app in the ADK Web
app selector.

```powershell
.\.venv\Scripts\Activate.ps1
adk web experiments/side_expeditions/task_hitl_confirmation/variants --port 8932
```

App names: `c0_root_function_confirmation`, `t0_task_plain_tool`,
`t1_task_function_confirmation`.

Sessions live in ADK's default in-memory store, so export a run's events before
restarting the server.

Repo-root `.env` is picked up automatically (ADK walks up from the agent
folder).

## How to trigger the test

One prompt, one operation. Use a fresh session per run and a unique run marker.

```text
Write the value alpha with run marker C0-R01
```

Run markers: `C0-A01` / `C0-R01` (A = Accept run, R = Reject run), `T0-01`,
`T1-A01`, `T1-R01`, …

For confirmation variants, record the tool execution count immediately before
and immediately after clicking Accept/Reject:

```powershell
python experiments/side_expeditions/task_hitl_confirmation/hitl_evidence.py C0-R01
```

### Run protocol

1. **A unique marker for every attempt, including retries.** If a run has to
   be repeated, the retry gets its own marker (`T1-A03`, `T1-A03b`,
   `T1-A03c`), never the original one. Execution counts are keyed by marker,
   so a re-used marker makes the count ambiguous and forces timestamp
   attribution after the fact — see the T1-A02 collision in `RESULTS.md`.
2. **Capture the pre-click execution count live wherever possible.** Pause at
   the pending confirmation and take the count before clicking. A count
   derived afterwards from timestamps is weaker evidence, and the difference
   is recorded per run.
3. **Preserve failed sessions; never repair them.** A session that dies on a
   provider error is exported as evidence and left alone. Retry in a *fresh*
   session under a new marker rather than re-driving the failed one.
4. **No automatic retry or backoff anywhere in the experiment.** Retries are
   manual, one deliberate run at a time. Adding retry or backoff logic would
   change the execution path under test, and is out of bounds like the other
   repairs listed in the ground rules.

### Result classes

`PASS`, `FAIL` and `INVALID` come from the brief. `PARTIAL` was added during
T1 for a case none of the three described.

| Class   | Meaning                                                                                                                                                                                                    |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PASS    | Every checkpoint occurred, in order.                                                                                                                                                                       |
| FAIL    | An ADK execution path began correctly and then stopped. Record the first missing checkpoint.                                                                                                               |
| INVALID | The intended test path was never entered — the model chose another tool, or a provider error hit before delegation. Repeat the run.                                                                        |
| PARTIAL | Every ADK-owned checkpoint passed, but the run ended from a cause outside ADK's execution path, such as a provider 503 on Root's closing model call. Does not count toward a variant's required run total. |

## Evidence

- `evidence/tool_executions.jsonl` — one append-only line per *real* tool-body
  execution (`TOOL_EXECUTED variant=… run_marker=… value=…`). The same marker is
  printed to the ADK Web server console.
- `evidence/<RUN>_events.jsonl` / `<RUN>_session.json` — raw session events
  exported from the ADK Web REST API:

```powershell
python experiments/side_expeditions/task_hitl_confirmation/export_session.py --app t0_task_plain_tool
python experiments/side_expeditions/task_hitl_confirmation/export_session.py --app t0_task_plain_tool --session <id> --run-marker T0-R01
```

No callbacks or wrappers are used for evidence collection. The recorder is
called from inside the tool body and cannot alter ADK execution.

## Checkpoint definitions

Terminology: *delegation*, *tool call*, *tool execution*, *confirmation
request*, *confirmation continuation*, *task completion*, *return to Root*.
"Handoff/transfer" is reserved for `mode="chat"` transfers. "Resume" is never
used unqualified.

### C0 / C1 (Root-level confirmation)

```text
1. Root emits write_value FunctionCall
2. ADK emits confirmation request
3. Tool has NOT executed (count = 0)
4. User accepts (or rejects)
5. Accept → tool executes exactly once / Reject → count stays 0
6. Root receives tool result
7. Root continues
```

### T0 (task lifecycle, no confirmation)

```text
1. Root delegates to the task worker
2. Worker emits write_value FunctionCall
3. write_value actually executes
4. Worker receives the FunctionResponse
5. Task completes (finish_task succeeds)
6. Root receives the task result
7. Root produces a subsequent response
```

### T1 / T2 (task + confirmation)

```text
A. Root delegates task
B. Worker emits write_value FunctionCall
C. ADK emits confirmation request
D. ADK Web presents Accept / Reject
E. User accepts
F. Confirmation response is recorded
G. write_value implementation executes
H. Worker receives write_value FunctionResponse
I. Worker continues
J. finish_task occurs successfully
K. Task result returns to Root
L. Root continues
```

Every run is classified `PASS`, `FAIL`, or `INVALID`. `INVALID` means the
intended path was never entered (e.g. the model never selected the test tool);
such runs are repeated. A path that starts correctly and then stops is `FAIL`,
and the first missing checkpoint is recorded.

## Constraints held in this expedition

No `AgentTool` written by us, no `ResumabilityConfig`, no retries, no
callbacks, no custom confirmation code, no prompt tricks, no ADK version change,
no production code/prompts/services. Failures are frozen and recorded, not
repaired.

Note on the installed version: ADK itself wraps a `mode="task"` sub-agent in an
internal `_TaskAgentTool` and injects the `finish_task` tool
(`google/adk/agents/llm_agent.py:1123`). That is the native task contract under
test, not something added here.
