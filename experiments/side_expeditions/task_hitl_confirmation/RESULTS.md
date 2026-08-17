# Results: ADK Task Mode + Native Tool Confirmation

Environment: `google-adk` 2.6.3, `google-genai` 2.17.0, Python 3.13.9,
`gemini-3.5-flash` via Gemini API. See `README.md`.

Code under test: commit `acb44e8` (see `evidence/test_start_revision.txt`).

| Variant | Run | Accept/Reject | Last checkpoint | Tool count | Result |
| ------- | --- | ------------- | --------------- | ---------: | ------ |
| C0 | C0-A01 | Accept | 7 — Root continues | 0 before / 1 after | PASS |
| C0 | C0-R01 | Reject | 5 — rejection honoured, tool not executed | 0 before / 0 after | PASS |
| T0 | T0-01 | n/a | 7 — Root continues after task result | 1 | PASS |
| T0 | T0-02 attempt 1 | n/a | 0 — Root's first model call | 0 | INVALID (provider 503) |
| T0 | T0-02 | n/a | 7 — Root continues after task result | 1 | PASS |
| T0 | T0-03 | n/a | 7 — Root continues after task result | 1 | PASS |

Discarded sessions (not runs): `d06e8ea5-2c11-41b9-adad-e2ee04cd551c`
(c0 app) re-used the marker `C0-A01`; abandoned at the confirmation request
with no Accept/Reject response and 0 executions, to keep per-marker counts
unambiguous.

## Verified Findings

**C0-A01 (Accept) — PASS.** Session
`cea562c6-eaf9-484d-8ece-8cb277fda553`, 7 events, exported to
`evidence/C0-A01_events.jsonl`.

```
21:27:33  user     "Use write_value ... run marker C0-A01"
21:27:33  c0_root  CALL write_value  id=call_2340699 {run_marker:C0-A01, value:alpha}
21:27:36  c0_root  RESP write_value  id=call_2340699
                     -> {"error": "This tool call requires confirmation, ..."}
                     event.actions.requestedToolConfirmations set
21:27:36  c0_root  CALL adk_request_confirmation id=adk-dbbdee2a-328d-4533-8046-6c1d6130cb46
                     args.originalFunctionCall = {id: call_2340699, name: write_value, ...}
          ---- tool execution count for C0-A01: 0 ----
21:27:55  user     RESP adk_request_confirmation id=adk-dbbdee2a-...
                     -> {"confirmed": true, "payload": {run_marker:C0-A01, value:alpha}}
21:27:55  TOOL     TOOL_EXECUTED variant=c0 tool=write_value run_marker=C0-A01 value=alpha
21:27:55  c0_root  RESP write_value  id=call_2340699 -> {"status":"ok","marker":"TOOL_EXECUTED ..."}
21:27:55  c0_root  TEXT "I have successfully written the value "alpha" ..."
          ---- tool execution count for C0-A01: 1 ----
```

Directly demonstrated by this run:

- Native `require_confirmation=True` produces a confirmation request in this
  environment, and ADK Web presents it.
- The tool body did not execute while the confirmation was pending: the
  pre-Accept response for `call_2340699` is an error stub, not a tool result.
- Accepting continued the *same* pending call — the post-Accept
  `FunctionResponse` carries the original id `call_2340699`.
- The tool body executed exactly once (one line in `tool_executions.jsonl`).
- Root received the tool result and produced a subsequent response.

**C0-R01 (Reject) — PASS.** Session
`04768bd1-fbd2-450b-9f7f-66db272914a4`, 9 events, single invocation
`e-9dbe5530-2131-45f2-9896-92e6c652db34`, `branch=None` throughout. Exported to
`evidence/C0-R01_events.jsonl`. Frozen at the state below and not modified;
the frozen export is byte-identical to the live session (same 9 event ids,
sha256 over the event list `f09c84f676c6cf5e2d31585dedd87a40`).

```
#1 21:39:15.372  user     TEXT "... run marker C0-R01."
#2 21:39:15.400  c0_root  CALL write_value              id=call_1219303
#3 21:39:18.076  c0_root  RESP write_value              id=call_1219303
                            -> {"error": "This tool call requires confirmation, ..."}
                            event.actions.requestedToolConfirmations set
#4 21:39:18.076  c0_root  CALL adk_request_confirmation id=adk-7e8b49db-e5b9-4751-882a-40ac9276dc44
                            args.originalFunctionCall.id = call_1219303
     ---- tool execution count for C0-R01: 0 ----
#5 21:39:33.225  user     RESP adk_request_confirmation id=adk-7e8b49db-...
                            -> {"confirmed": false, "payload": {run_marker:C0-R01, value:alpha}}
#6 21:39:33.244  c0_root  RESP write_value              id=call_1219303
                            -> {"error": "This tool call is rejected."}
     ---- tool execution count for C0-R01: 0 ----
#7 21:39:33.265  c0_root  CALL write_value              id=call_1090589   <- NEW call id
#8 21:39:36.712  c0_root  RESP write_value              id=call_1090589
                            -> {"error": "This tool call requires confirmation, ..."}
#9 21:39:36.712  c0_root  CALL adk_request_confirmation id=adk-077d6df8-5d17-43cb-9577-78a769b47722
                            args.originalFunctionCall.id = call_1090589
                            (left unanswered; session frozen here)
```

Directly demonstrated by this run:

- A Reject in ADK Web produces a confirmation `FunctionResponse` carrying
  `{"confirmed": false, ...}` (#5).
- The rejected call is terminated by ADK with
  `{"error": "This tool call is rejected."}` against the original id (#6).
- The `write_value` body executed **zero** times for marker `C0-R01`,
  corroborated independently from both evidence sides:
  `tool_executions.jsonl` contains no line with that marker (the string
  `C0-R01` does not occur in the file at all), and all three `write_value`
  `FunctionResponse`s in the session are error stubs — none carries a
  `TOOL_EXECUTED` marker, which is generated only inside the function body.
- Events #7 and #9 are a **new** tool call and a **new** confirmation
  request, not continuation of the original: the call id changes
  (`call_1090589` vs `call_1219303`), the confirmation id changes
  (`adk-077d6df8` vs `adk-7e8b49db`) and its `originalFunctionCall.id`
  points at the new call, and the original call had already reached a
  terminal response at #6. For contrast, confirmation continuation in
  C0-A01 preserved the id `call_2340699` across the pending and executed
  responses.
- After the rejection the model re-issued the identical call on its own
  initiative. No retry logic exists in the variant code, and ADK did not
  re-execute anything; the second call originates from the model's turn.

**T0-01 (no confirmation) — PASS.** Session
`d92ae890-e3b9-4fc2-9f04-a1b16c5af7ea`, 8 events, exported to
`evidence/T0-01_events.jsonl`. All seven T0 checkpoints occurred in order.

```
#1 21:57:36.198  user    branch=None                 TEXT "... run marker T0-01."
#2 21:57:36.218  root    branch=None                 CALL worker       id=call_2146904
                           args={"request": "Write the value \"alpha\" with run marker \"T0-01\"."}
#3 21:57:39.096  worker  branch=worker@call_2146904  CALL write_value  id=call_641140
                           args={"value":"alpha","run_marker":"T0-01"}
#4 21:57:41.442  worker  branch=worker@call_2146904  RESP write_value  id=call_641140
                           -> {"status":"ok","marker":"TOOL_EXECUTED variant=t0 ... T0-01 ..."}
#5 21:57:41.473  worker  branch=worker@call_2146904  CALL finish_task  id=call_2234004
                           args={"result":"Value 'alpha' successfully written under run marker 'T0-01'."}
#6 21:57:43.793  worker  branch=worker@call_2146904  RESP finish_task  id=call_2234004
                           -> {"result":"Task completed."}
#7 21:57:43.809  user    branch=None                 RESP worker       id=call_2146904
                           -> {"result":"Value 'alpha' successfully written under run marker 'T0-01'."}
#8 21:57:43.834  root    branch=None                 TEXT "I have successfully written the value ..."
```

Tool-side log records one execution at `21:57:41.440542Z`. Execution count
for `T0-01`: **1**.

Directly demonstrated by this run:

- Root delegates via an agent-shaped FunctionCall named `worker`
  (id `call_2146904`). `transfer_to_agent` does not occur anywhere in the
  session.
- Child events carry `branch="worker@call_2146904"`, derived from the
  delegation call id; Root's events carry `branch=None`.
- `finish_task` is exposed in the trace as a call (#5) and a response (#6,
  `"Task completed."`).
- The delegation call is satisfied by a FunctionResponse re-using the
  original id `call_2146904` (#7), whose payload is byte-identical to the
  `finish_task` argument.
- Event #7 carries no `modelVersion` and no `usageMetadata`, unlike the
  model turns at #2/#3/#5/#8. Model-authored: #2, #3, #5, #8. Not
  model-authored: #4, #6, #7.
- Root, not the worker, produces the user-facing text (#8).

Caveat at time of writing: n=1. Superseded — see "T0 repeatability: 3/3"
below; the lifecycle reproduced identically in T0-02 and T0-03.

Methodological note: inter-event gaps do not cleanly bracket model latency
(#5 is model-authored but lands 31 ms after #4, while non-model #6 lands
2.3 s later). Attribution in this file therefore relies on
`modelVersion`/`usageMetadata`, not on timing.

**T0-02 (no confirmation) — PASS.** Session
`42581fbf-5117-4b59-8ac3-c76cc12a8e62`, 8 events, exported to
`evidence/T0-02_events.jsonl`. All seven T0 checkpoints occurred in order.

```
#1 23:20:01.752  user    branch=None                 model=NO   TEXT "... run marker T0-02."
#2 23:20:01.776  root    branch=None                 model=yes  CALL worker       id=call_1354044
#3 23:20:08.350  worker  branch=worker@call_1354044  model=yes  CALL write_value  id=call_1218251
                           args={"run_marker":"T0-02","value":"alpha"}
#4 23:20:14.792  worker  branch=worker@call_1354044  model=NO   RESP write_value  id=call_1218251
                           -> {"status":"ok","marker":"TOOL_EXECUTED variant=t0 ... T0-02 ..."}
#5 23:20:14.814  worker  branch=worker@call_1354044  model=yes  CALL finish_task  id=call_3715607
                           args={"result":"Successfully wrote the value \"alpha\" with run marker \"T0-02\"."}
#6 23:20:22.479  worker  branch=worker@call_1354044  model=NO   RESP finish_task  id=call_3715607
                           -> {"result":"Task completed."}
#7 23:20:22.490  user    branch=None                 model=NO   RESP worker       id=call_1354044
                           -> {"result":"Successfully wrote the value \"alpha\" with run marker \"T0-02\"."}
#8 23:20:22.518  root    branch=None                 model=yes  TEXT "I have successfully written ..."
```

Tool-side log records one execution at `23:20:14.791139Z`. Execution count
for `T0-02`: **1** (the aborted attempt below contributed none).

T0-02 reproduces every structural landmark recorded for T0-01, with new ids:

| | T0-01 | T0-02 |
| --- | --- | --- |
| delegation call id | `call_2146904` | `call_1354044` |
| child branch | `worker@call_2146904` | `worker@call_1354044` |
| worker RESP re-uses delegation id | yes | yes |
| payload byte-identical to `finish_task` arg | yes | yes |
| worker RESP model-authored | no | no |
| `transfer_to_agent` present | no | no |
| distinct branches in session | `None`, `worker@…` | `None`, `worker@…` |

**T0-02 attempt 1 — INVALID (provider 503).** Session
`2184c025-2acb-4314-85b1-c246a2dfc448`, 2 events, preserved at
`evidence/T0-02-INVALID-503_events.jsonl` rather than discarded.

```
#1 22:50:44.556  user  branch=None  TEXT "Write the value "alpha" with run marker "T0-02"."
#2 22:50:48.653  root  branch=None  content=null  errorCode=ServerError
                         errorMessage=503 UNAVAILABLE. "This model is currently
                         experiencing high demand. Spikes in demand are usually
                         temporary. Please try again later."
```

Classified INVALID, not FAIL: the run terminated on Root's first model call,
before any delegation, tool call or tool execution, so the intended test path
was never entered. Execution count: 0. The exception is
`google.genai.errors.ServerError` raised from the provider inside
`google/genai/errors.py`, surfaced through ADK's node runner; it is not an
ADK execution-path failure. The marker `T0-02` was re-used by the successful
retry ~30 minutes later; per-marker counting stays unambiguous only because
this attempt executed the tool zero times.

**T0-03 (no confirmation) — PASS.** Session
`f94c615c-8c90-4950-b42e-2461c87c40c7`, 8 events, exported to
`evidence/T0-03_events.jsonl`. All seven T0 checkpoints occurred in order.

```
#1 00:31:40.215  user    branch=None                 model=NO   TEXT "... run marker T0-03."
#2 00:31:40.261  root    branch=None                 model=yes  CALL worker       id=call_1505750
#3 00:32:19.513  worker  branch=worker@call_1505750  model=yes  CALL write_value  id=call_2797296
#4 00:32:38.951  worker  branch=worker@call_1505750  model=NO   RESP write_value  id=call_2797296
                           -> {"status":"ok","marker":"TOOL_EXECUTED variant=t0 ... T0-03 ..."}
#5 00:32:38.966  worker  branch=worker@call_1505750  model=yes  CALL finish_task  id=call_969880
#6 00:33:14.652  worker  branch=worker@call_1505750  model=NO   RESP finish_task  id=call_969880
                           -> {"result":"Task completed."}
#7 00:33:14.662  user    branch=None                 model=NO   RESP worker       id=call_1505750
                           -> {"result":"Successfully wrote the value \"alpha\" with run marker \"T0-03\"."}
#8 00:33:14.687  root    branch=None                 model=yes  TEXT "I have successfully written ..."
```

Execution count for `T0-03`: **1**. Counts across the variant: T0-01 = 1,
T0-02 = 1, T0-03 = 1. Total lines in `tool_executions.jsonl` = 4 (three T0
plus one C0-A01); no run executed the body twice, and none executed it zero
times.

### T0 repeatability: 3/3

Reducing each session to `author:kind:name:model-or-framework` yields a
byte-identical sequence for all three runs:

```
user:TEXT:F -> root:CALL:worker:M -> worker:CALL:write_value:M
  -> worker:RESP:write_value:F -> worker:CALL:finish_task:M
  -> worker:RESP:finish_task:F -> user:RESP:worker:F -> root:TEXT:M
```

`T0-01 == T0-02` and `T0-01 == T0-03`, compared programmatically.

| | T0-01 | T0-02 | T0-03 |
| --- | --- | --- | --- |
| delegation call id | `call_2146904` | `call_1354044` | `call_1505750` |
| child branch | `worker@call_2146904` | `worker@call_1354044` | `worker@call_1505750` |
| worker RESP re-uses delegation id | yes | yes | yes |
| payload identical to `finish_task` arg | yes | yes | yes |
| worker RESP model-authored | no | no | no |
| `transfer_to_agent` present | no | no | no |
| execution count | 1 | 1 | 1 |

Every id and branch differs between runs while the structure is constant, so
the agreement is not an artefact of re-used identifiers.

Model latency in T0-03 was markedly degraded (39 s between #2 and #3, 36 s
between #5 and #6, versus 2-3 s in T0-01) during the same provider load that
produced the 503 above. It changed the timing, not the event structure or the
execution count.

**T0 conclusion: the task lifecycle completed 3/3 and returned control to
Root in every run.** Under the decision matrix, T0 PASS means the basic task
lifecycle is reliable in this environment, so a T1 failure could not be
attributed to task delegation or task completion alone.

## Failures Observed

_(none yet — the 503 above is classified INVALID, not a failure of an ADK
execution path)_

## Interpretation

Everything in this section is **inference**. It is a reading of the observations
above, not an additional observation, and it must not be cited as a finding.

### Inference: task mode is a bounded child branch, not a conversational handover

Based on T0-01, T0-02 and T0-03 (3/3, identical structure, distinct ids), the
`mode="task"` lifecycle appears to work like this:

```
Root turn            CALL worker(request=...)      id=call_2146904   [model]
   |                 branch=None
   v
child branch         CALL write_value              [model]
branch=worker@       RESP write_value              [not model]
call_2146904         CALL finish_task              [model]
   |                 RESP finish_task              [not model]
   v
back at Root         RESP worker  id=call_2146904  [not model]
                     payload == finish_task args, verbatim
                     TEXT to user                  [model]
```

1. **Root does not hand the conversation over.** It makes an agent-shaped
   tool call and stays the owner of the turn. Support: the delegation is a
   FunctionCall, no `transfer_to_agent` occurs, and Root authors the final
   user-facing text.
2. **The child executes on a bounded branch** keyed to the delegation call
   id. Support: `branch=worker@call_2146904` on every child event versus
   `branch=None` on Root's.
3. **`finish_task` closes that branch.** Support: it is the last child event
   before control returns. *Weakest link in the chain* — the trace shows
   `finish_task` preceding the return, not that it causes it. No run has yet
   omitted `finish_task`, so causation is not isolated. Settling this means
   reading ADK source, which ground rule 9 defers until the expedition
   concludes.
4. **ADK synthesises the FunctionResponse that satisfies the original
   delegation call.** Support: #7 re-uses id `call_2146904`, its payload is
   byte-identical to the `finish_task` argument, and it carries neither
   `modelVersion` nor `usageMetadata` while every genuine model turn in the
   session carries both. No model turn produced it.

Point 4 is the most strongly evidenced; point 3 is the most speculative.

Scope limit: this is three runs of one variant on one model, all without
confirmation. It says nothing about what happens when a confirmation has to
cross the child-branch boundary — that is exactly what T1 tests, and no
expectation about the T1 outcome is recorded here.
