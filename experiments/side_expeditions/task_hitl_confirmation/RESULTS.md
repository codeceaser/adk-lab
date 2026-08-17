# Results: ADK Task Mode + Native Tool Confirmation

Environment: `google-adk` 2.6.3, `google-genai` 2.17.0, Python 3.13.9,
`gemini-3.5-flash` via Gemini API. See `README.md`.

Code under test: commit `acb44e8` (see `evidence/test_start_revision.txt`).

| Variant | Run                         | Accept/Reject         | Last checkpoint                            |                         Tool count | Result                                |
| ------- | --------------------------- | --------------------- | ------------------------------------------ | ---------------------------------: | ------------------------------------- |
| C0      | C0-A01                      | Accept                | 7 — Root continues                         |                 0 before / 1 after | PASS                                  |
| C0      | C0-R01                      | Reject                | 5 — rejection honoured, tool not executed  |                 0 before / 0 after | PASS                                  |
| T0      | T0-01                       | n/a                   | 7 — Root continues after task result       |                                  1 | PASS                                  |
| T0      | T0-02 attempt 1             | n/a                   | 0 — Root's first model call                |                                  0 | INVALID (provider 503)                |
| T0      | T0-02                       | n/a                   | 7 — Root continues after task result       |                                  1 | PASS                                  |
| T0      | T0-03                       | n/a                   | 7 — Root continues after task result       |                                  1 | PASS                                  |
| T1      | T1-A01                      | Accept                | L — Root continues (no missing checkpoint) |                 0 before / 1 after | PASS                                  |
| T1      | T1-A02 attempt 1            | n/a                   | none — Root's first model call             |                                  0 | INVALID (provider 503)                |
| T1      | T1-A02 attempt 2            | Accept                | K — task result returned to Root           |                 0 before / 1 after | PARTIAL (A-K pass, provider 503 at L) |
| T1      | T1-A02                      | Accept                | L — Root continues (no missing checkpoint) |                 0 before / 1 after | PASS                                  |
| T1      | T1-A03a attempt 1           | n/a                   | A — delegation only, 503 in child branch   |                                  0 | INVALID (provider 503)                |
| T1      | T1-A03a attempt 2           | n/a                   | none — Root's first model call             |                                  0 | INVALID (provider 503)                |
| T1      | T1-X01 (exceptional trial)  | Reject ×3 then Accept | L — Root continues (4th cycle)             | 0 after 3 rejects / 1 after accept | EXCEPTIONAL TRIAL (see notes)         |
| T1      | T1-A03d                     | Accept                | L — Root continues (no missing checkpoint) |       0 before / 1 after (derived) | PASS                                  |
| T1      | T1-A03e (Reject run 1 of 2) | Reject                | F — rejection recorded, tool not executed  |                 0 before / 0 after | PASS                                  |
| T1      | T1-R02 (Reject run 2 of 2)  | Reject                | F — rejection recorded, tool not executed  |                 0 before / 0 after | PASS                                  |

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

|                                             | T0-01                 | T0-02                 |
| ------------------------------------------- | --------------------- | --------------------- |
| delegation call id                          | `call_2146904`        | `call_1354044`        |
| child branch                                | `worker@call_2146904` | `worker@call_1354044` |
| worker RESP re-uses delegation id           | yes                   | yes                   |
| payload byte-identical to `finish_task` arg | yes                   | yes                   |
| worker RESP model-authored                  | no                    | no                    |
| `transfer_to_agent` present                 | no                    | no                    |
| distinct branches in session                | `None`, `worker@…`    | `None`, `worker@…`    |

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

|                                        | T0-01                 | T0-02                 | T0-03                 |
| -------------------------------------- | --------------------- | --------------------- | --------------------- |
| delegation call id                     | `call_2146904`        | `call_1354044`        | `call_1505750`        |
| child branch                           | `worker@call_2146904` | `worker@call_1354044` | `worker@call_1505750` |
| worker RESP re-uses delegation id      | yes                   | yes                   | yes                   |
| payload identical to `finish_task` arg | yes                   | yes                   | yes                   |
| worker RESP model-authored             | no                    | no                    | no                    |
| `transfer_to_agent` present            | no                    | no                    | no                    |
| execution count                        | 1                     | 1                     | 1                     |

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

**T1-A01 (Accept) — PASS. Checkpoints A-L all occurred; no missing
checkpoint.** Session `4095d974-a5e9-46e0-a489-0496614d0b92`, 11 events,
single invocation `e-58828342-4f94-4a40-b1fe-db28f6fca9e1`, exported to
`evidence/T1-A01_events.jsonl`.

The 5-event pre-click state was captured live before the Accept was
submitted, so the pre-click count is a measurement rather than a
reconstruction.

```
#1  00:43:18.940  user    branch=None                 model=NO   TEXT "... run marker T1-A01."
#2  00:43:18.960  root    branch=None                 model=yes  CALL worker       id=call_1728652
#3  00:43:37.206  worker  branch=worker@call_1728652  model=yes  CALL write_value  id=call_902796
                            args={"run_marker":"T1-A01","value":"alpha"}
#4  00:43:56.672  worker  branch=worker@call_1728652  model=NO   RESP write_value  id=call_902796
                            -> {"error":"This tool call requires confirmation, ..."}
                            event.actions.requestedToolConfirmations = ['call_902796']
#5  00:43:56.672  worker  branch=worker@call_1728652  model=NO   CALL adk_request_confirmation
                            id=adk-bbabfe4e-cf31-4685-b64b-fad076d712db
                            args.originalFunctionCall.id = call_902796
                            longRunningToolIds=['adk-bbabfe4e-...']
      ---- tool execution count for T1-A01: 0 (measured live, pre-click) ----
#6  00:50:09.460  user    branch=worker@call_1728652  model=NO   RESP adk_request_confirmation
                            id=adk-bbabfe4e-...  -> {"confirmed": true, "payload": {...}}
#7  00:50:09.480  worker  branch=worker@call_1728652  model=NO   RESP write_value  id=call_902796
                            -> {"status":"ok","marker":"TOOL_EXECUTED variant=t1 ... T1-A01 ..."}
#8  00:50:09.501  worker  branch=worker@call_1728652  model=yes  CALL finish_task  id=call_2088500
#9  00:50:44.940  worker  branch=worker@call_1728652  model=NO   RESP finish_task  id=call_2088500
                            -> {"result":"Task completed."}
#10 00:50:44.951  user    branch=None                 model=NO   RESP worker       id=call_1728652
#11 00:50:44.972  root    branch=None                 model=yes  TEXT "The value "alpha" has been ..."
      ---- tool execution count for T1-A01: 1 ----
```

Checkpoint mapping: A=#2, B=#3, C=#5, D=observed live pre-click, E=#6,
F=#6, G=tool log `00:50:09.479462Z`, H=#7, I=#8, J=#9, K=#10, L=#11.

Directly demonstrated by this run:

- **Confirmation continuation preserved the pending call.** The session
  contains exactly **one** `write_value` FunctionCall (`call_902796`), and
  both the pre-Accept stub (#4) and the post-Accept real result (#7) carry
  that same id. The pending call was continued, not re-issued. Contrast
  C0-R01, where the model's own retry produced a *new* id `call_1090589`.
- **Execution stayed on the original child branch.** Exactly one child
  branch exists in the session, `worker@call_1728652`, derived from the
  delegation call id. Events #3-#9 all carry it.
- **The Accept re-entered on the child branch.** Event #6 is authored by
  `user` but carries `branch=worker@call_1728652`, not `branch=None`. Its
  id matches the confirmation request id.
- The confirmation request itself (#5) is authored by `worker`, on the child
  branch, and is marked as a long-running tool
  (`longRunningToolIds=['adk-bbabfe4e-...']`). In C0 the equivalent request
  was authored by `c0_root` at `branch=None`.
- **Task completion and return to Root behaved as in T0.** `finish_task`
  call (#8, model-authored) and response (#9, `"Task completed."`); the
  delegation call is satisfied at #10 by a response re-using id
  `call_1728652`, payload byte-identical to the `finish_task` argument and
  carrying no `modelVersion`.
- Root produced the subsequent user-facing response (#11).

Caveat: n=1, Accept path only. T1-A02, T1-A03, T1-R01 and T1-R02 remain
outstanding. A composition can succeed once and fail on repetition, so no
conclusion about T1 is drawn from this run alone.

**T1-A02 — PASS**, on the third attempt. Provider 503s aborted the first two,
so three sessions carry the marker `T1-A02`. All three are preserved.

| Attempt | Session                                | Events | Outcome                                                |
| ------- | -------------------------------------- | -----: | ------------------------------------------------------ |
| 1       | `ec048411-c0ed-4d60-bab1-a65d80cc2179` |      2 | 503 on Root's first model call — INVALID, 0 executions |
| 2       | `bf59806a-82bd-4ef4-a155-40df97322801` |     11 | A-K pass, then 503 at L — PARTIAL, 1 execution         |
| 3       | `c4d0da5b-8e5d-4173-a8b0-6a640957eef0` |     11 | complete A-L — **PASS**, 1 execution                   |

Exported as `T1-A02-INVALID-503-pre`, `T1-A02-attempt2-503-at-L` and
`T1-A02` respectively.

**Marker collision — read the counts carefully.** `tool_executions.jsonl`
holds **2** lines under the marker `T1-A02` (`01:02:14.406707Z` and
`01:04:14.723342Z`). This is *not* a double execution. Attributing each
execution to the session whose event window contains it:

```
attempt 2  window 01:01:11-01:03:05   execs=1   before Accept=0   after=1
attempt 3  window 01:03:18-01:04:33   execs=1   before Accept=0   after=1
```

Each session executed the body exactly once. Per-marker counting is only
unambiguous when markers are unique per attempt; later runs should use a
distinct marker per attempt.

Evidence-strength note: unlike T1-A01, whose pre-click count of 0 was
measured live at the pending-confirmation state, these pre-click zeros are
**derived** — no execution is logged between each confirmation request and
its confirmation response. Weaker evidence, though corroborated by the
pre-Accept `write_value` response being an error stub in both sessions.

Continuation signature held in both completed attempts, matching T1-A01
across three independent id sets:

|                                  | T1-A01                | T1-A02 attempt 2      | T1-A02 (attempt 3)    |
| -------------------------------- | --------------------- | --------------------- | --------------------- |
| `write_value` CALLs in session   | 1 (`call_902796`)     | 1 (`call_1869450`)    | 1 (`call_1307347`)    |
| stub + real result share that id | yes                   | yes                   | yes                   |
| child branch                     | `worker@call_1728652` | `worker@call_2862498` | `worker@call_1700817` |
| Accept event branch              | child branch          | child branch          | child branch          |

**Attempt 2 separates checkpoints A-K from Root's closing turn.** The 503 hit
Root's final model call *after* the task had completed and returned:

```
#6  01:02:14  user    branch=worker@call_2862498  RESP adk_request_confirmation (Accept)
#7  01:02:14  worker  branch=worker@call_2862498  RESP write_value  id=call_1869450 (real result)
#8  01:02:14  worker  branch=worker@call_2862498  CALL finish_task  id=call_667781
#9  01:02:35  worker  branch=worker@call_2862498  RESP finish_task  -> "Task completed."
#10 01:02:35  user    branch=None                 RESP worker       id=call_2862498
#11 01:03:05  user    branch=None                 ERROR ServerError 503 UNAVAILABLE
```

Directly demonstrated by this session:

- Checkpoints A-K completed without Root's closing model turn; the task
  result reached Root (#10) before the model was next needed.
- The tool body executed **exactly once** despite the invocation ending in
  an error. The 503 did not cause re-execution, duplication or retry of the
  already-completed side effect.

Classification: **PARTIAL — A-K pass, provider 503 at L.**

`PARTIAL` is a fourth class, added deliberately beyond the brief's
PASS/FAIL/INVALID scheme, because attempt 2 fits none of the three.
`INVALID` is defined as the intended path never being entered, yet this run
entered it and ran to K. `FAIL` is defined as a framework path that begins
and then stops, yet the stop was a provider 503, not an ADK execution-path
defect. `PASS` would overstate it, since checkpoint L never occurred.

What PARTIAL asserts here: every ADK-owned checkpoint of the composition
under test — delegation, confirmation request, confirmation continuation,
tool execution, tool-result propagation, task completion and return to Root
— completed successfully. What failed afterwards was Root's closing model
call, which is outside ADK's execution path and attributable to the
provider.

Counting rule: PARTIAL runs do **not** count toward the three Accept runs
the protocol requires, so this run is not one of T1's clean Accepts. Its A-K
evidence is retained above as corroboration, and it is the only run in the
expedition that isolates checkpoints A-K from Root's closing turn.

Provider errors in this expedition are 503 `UNAVAILABLE` ("model is currently
experiencing high demand"), not 429/quota: across the full ADK Web server log
503 occurs 13 times and `UNAVAILABLE` 12 times, while `429`,
`RESOURCE_EXHAUSTED` and `quota` occur zero times. All recorded error events
carry `errorCode=ServerError` with the identical 503 payload.

**T1-A03a attempts 1 and 2 — INVALID (provider 503).** Both preserved,
0 executions for the marker `T1-A03a`.

- Attempt 1, session `ea00ddfd-c86c-4fe6-b565-d8881f9cc00f`, 3 events,
  exported as `T1-A03a-attempt1-503-at-B`. Checkpoint **A occurred** —
  Root delegated with `CALL worker id=call_2389435` — and the 503 then hit
  *inside the child branch* (`branch=worker@call_2389435`) before the worker
  could emit its `write_value` call, so **B never occurred**. The child
  branch was created before the provider failed.
- Attempt 2, session `705f46ab-c7ae-409c-aebc-015faa796624`, 2 events,
  exported as `T1-A03a-attempt2-503-pre`. Died on Root's first model call,
  as T0-02 attempt 1 and T1-A02 attempt 1 did.

Both re-used the marker `T1-A03a`, contrary to the unique-marker protocol
now recorded in `README.md`. Harmless here only because both executed the
tool zero times.

**T1-X01 — EXCEPTIONAL TRIAL: three rejections, then an accept, in one
session.** Session `20122284-a0bf-4170-8399-6bc678dd5ed6`.

Provenance, stated plainly: this run was launched under the marker
`T1-A03c`, intended as an Accept run, and the in-session tool arguments
still read `T1-A03c` — those are raw evidence and are not rewritten. What
was actually performed was three Rejects followed by one Accept. It is
recorded as an exceptional trial rather than discarded, per ground rule 8
and §6 ("Do not hide inconsistent results"). **It does not count toward the
two planned T1 Reject runs**, which are still outstanding.

Two artefacts are preserved, and they differ deliberately:

| Artefact               | Events | State                                                                                     |
| ---------------------- | -----: | ----------------------------------------------------------------------------------------- |
| `T1-X01-reject-loop_*` |     20 | live snapshot taken while the 4th confirmation was pending; pre-click count measured at 0 |
| `T1-X01-final_*`       |     26 | the completed session after the 4th confirmation was accepted                             |

Four confirmation cycles, each with its own ids:

| Cycle | `write_value` id | confirmation id | `confirmed` | outcome for that call                      |
| ----- | ---------------- | --------------- | ----------- | ------------------------------------------ |
| 1     | `call_1445394`   | `adk-4adac5ce`  | false       | `{"error": "This tool call is rejected."}` |
| 2     | `call_2361529`   | `adk-9e40ed31`  | false       | `{"error": "This tool call is rejected."}` |
| 3     | `call_2871783`   | `adk-8838ba22`  | false       | `{"error": "This tool call is rejected."}` |
| 4     | `call_977291`    | `adk-3d64e046`  | **true**    | executed; `TOOL_EXECUTED ... T1-A03c`      |

Execution count: **0** across all three rejections (measured live at the
20-event state), **1** after the Accept. Total for the marker: 1.

Directly demonstrated by this trial:

- **Rejection is honoured inside task mode.** Each rejected call is
  terminated by ADK against its own pending id, and the tool body did not
  execute for any of the three.
- **Each retry is a new call, not ADK re-presenting a pending one.** Four
  distinct `write_value` ids, four distinct confirmation ids, each
  confirmation's `originalFunctionCall.id` pointing at its own cycle's
  call. The re-issues at #8, #13 and #18 carry `modelVersion` — they are
  worker LLM turns.
- **Every cycle stayed on one child branch.** The session contains exactly
  two branch values: `None` (only the user prompt and Root's delegation) and
  `worker@call_1021090` (everything else, all four cycles).
- **Rejection terminates the call, not the task.** Through 20 events there
  were 0 `finish_task` calls, 0 responses to Root, and 1 Root-authored event
  (the initial delegation). Control never returned to Root while rejections
  continued.
- **The Accept ended the loop and completed the task normally.** The
  executed call `call_977291` was the last pending call, continued under its
  own id (#22), followed by `finish_task` (#23, model-authored), its
  response (#24), the synthesized `worker` response re-using delegation id
  `call_1021090` (#25) and Root's closing text (#26) — checkpoints A-L on
  the fourth cycle.

Not observed, and therefore not claimed: any path in which a *rejection*
terminates the task and returns control to Root. Its absence from this trace
is not proof that ADK provides none.

**T1-A03d (Accept) — PASS. Checkpoints A-L all occurred.** Session
`10b04331-fb5e-4dc8-9d09-bb3ba476b3ee`, 11 events, exported to
`evidence/T1-A03d_events.jsonl`. Execution count for `T1-A03d`: **1**.

```
#1  02:30:54  user    branch=None                 framework  TEXT "... run marker T1-A03d."
#2  02:30:54  root    branch=None                 MODEL      CALL worker       id=call_1346097
#3  02:31:02  worker  branch=worker@call_1346097  MODEL      CALL write_value  id=call_2339869
#4  02:31:14  worker  branch=worker@call_1346097  framework  RESP write_value  id=call_2339869
                        -> {"error":"This tool call requires confirmation, ..."}
#5  02:31:14  worker  branch=worker@call_1346097  framework  CALL adk_request_confirmation
                        id=adk-6417f692-df7a-4430-8d26-26a9d079d8b5
#6  02:31:33  user    branch=worker@call_1346097  framework  RESP adk_request_confirmation
                        -> {"confirmed": true, ...}
#7  02:31:33  worker  branch=worker@call_1346097  framework  RESP write_value  id=call_2339869
                        -> {"status":"ok","marker":"TOOL_EXECUTED variant=t1 ... T1-A03d ..."}
#8  02:31:33  worker  branch=worker@call_1346097  MODEL      CALL finish_task  id=call_1766659
#9  02:31:41  worker  branch=worker@call_1346097  framework  RESP finish_task  -> "Task completed."
#10 02:31:41  user    branch=None                 framework  RESP worker       id=call_1346097
#11 02:31:41  root    branch=None                 MODEL      TEXT "I have successfully written ..."
```

Evidence-strength note: the pre-click count here is **derived**, not measured
live — the run had already completed when the count was taken. No execution
is logged between the confirmation request (#5) and its response (#6), and
the pre-Accept response at #4 is an error stub. Of T1's three clean Accepts,
only T1-A01 carries a live pre-click measurement.

### T1 Accept repeatability: 3/3

| Property                               | T1-A01                | T1-A02                | T1-A03d               |
| -------------------------------------- | --------------------- | --------------------- | --------------------- |
| `write_value` CALLs in session         | 1                     | 1                     | 1                     |
| that call id                           | `call_902796`         | `call_1307347`        | `call_2339869`        |
| post-Accept result continues that id   | yes                   | yes                   | yes                   |
| delegation call id                     | `call_1728652`        | `call_1700817`        | `call_1346097`        |
| child branch                           | `worker@call_1728652` | `worker@call_1700817` | `worker@call_1346097` |
| Accept event on child branch           | yes                   | yes                   | yes                   |
| worker RESP re-uses delegation id      | yes                   | yes                   | yes                   |
| payload identical to `finish_task` arg | yes                   | yes                   | yes                   |
| distinct branches in session           | 2                     | 2                     | 2                     |
| execution count                        | 1                     | 1                     | 1                     |

Every id and branch differs across the three runs while every structural
property holds, so the agreement is not an artefact of re-used identifiers.

**T1 Accept conclusion: task delegation composed with native
`require_confirmation=True` completed all checkpoints A-L in 3/3 clean runs,
executing the tool body exactly once per run.** No checkpoint was missing in
any Accept run. The two planned T1 Reject runs remain outstanding.

**T1-A03e (Reject) — PASS.** First of the two planned T1 Reject runs.
Session `586d0b8e-a252-4df8-86ae-178f80a2befe`, 10 events, exported to
`evidence/T1-A03e-reject_events.jsonl`. Frozen after a single rejection with
the follow-up confirmation left unanswered, mirroring C0-R01 so the two are
comparable. The export is byte-identical to the live session (same 10 event
ids, sha256 over the event list `31ccde6a2e009683ae50eb1ad46b2433`).

Marker note: the run was issued under `T1-A03e`, an Accept-series name, but
a single Reject was performed. The marker is unique and the evidence is
unambiguous, so it is recorded as a Reject run under its issued name rather
than relabelled; the in-session tool arguments read `T1-A03e`.

```
#1  02:34:14.696  user    branch=None                 framework  TEXT "... run marker T1-A03e."
#2  02:34:14.718  root    branch=None                 MODEL      CALL worker       id=call_1817880
#3  02:34:28.248  worker  branch=worker@call_1817880  MODEL      CALL write_value  id=call_746209
#4  02:34:34.503  worker  branch=worker@call_1817880  framework  RESP write_value  id=call_746209
                            -> {"error":"This tool call requires confirmation, ..."}
#5  02:34:34.503  worker  branch=worker@call_1817880  framework  CALL adk_request_confirmation
                            id=adk-63b53eb5-fefb-44f5-bfbb-cab526c3123f
                            args.originalFunctionCall.id = call_746209
      ---- tool execution count for T1-A03e: 0 ----
#6  02:34:38.986  user    branch=worker@call_1817880  framework  RESP adk_request_confirmation
                            -> {"confirmed": false, "payload": {...}}
#7  02:34:39.000  worker  branch=worker@call_1817880  framework  RESP write_value  id=call_746209
                            -> {"error": "This tool call is rejected."}
      ---- tool execution count for T1-A03e: 0 ----
#8  02:34:39.015  worker  branch=worker@call_1817880  MODEL      CALL write_value  id=call_1659000  <- NEW id
#9  02:34:50.037  worker  branch=worker@call_1817880  framework  RESP write_value  id=call_1659000
                            -> {"error":"This tool call requires confirmation, ..."}
#10 02:34:50.038  worker  branch=worker@call_1817880  framework  CALL adk_request_confirmation
                            id=adk-ac44e2ae-dd21-4e7b-915a-65b023f679e5
                            args.originalFunctionCall.id = call_1659000
                            (left unanswered; session frozen here)
```

Directly demonstrated by this run:

- A Reject inside task mode records `{"confirmed": false, ...}` on the child
  branch (#6) and ADK terminates the pending call with
  `{"error": "This tool call is rejected."}` against its original id (#7).
- The `write_value` body executed **zero** times, corroborated from both
  sides: the string `T1-A03e` does not occur in `tool_executions.jsonl` at
  all, and all three `write_value` responses in the session are error stubs,
  none carrying a `TOOL_EXECUTED` marker.
- The worker then re-issued the call under a **new** id (`call_1659000` vs
  `call_746209`, #8, model-authored) producing a new confirmation request
  (#10) — the same retry seen once at Root level in C0-R01 and three times
  in T1-X01.
- `finish_task` calls: **0**. Responses to Root: **0**. Control did not
  return to Root.
- Two branch values only: `None` (prompt and delegation) and
  `worker@call_1817880` (everything from #3 on).

This reproduces T1-X01's first cycle exactly, with different ids, in a run
that was frozen deliberately rather than continued.

**T1-R02 (Reject) — PASS.** Second of the two planned T1 Reject runs, and the
last run of Phase 1. Session `3ede7af1-aba3-4411-9643-39acae43ae65`,
10 events, exported to `evidence/T1-R02_events.jsonl`. Frozen after a single
rejection with the follow-up confirmation unanswered. Byte-identical to the
live session (same 10 event ids, sha256 `099acb6e0112d8f6b04614ca4da1d95c`).

```
#1  02:38:51.834  user    branch=None                framework  TEXT "... run marker T1-R02."
#2  02:38:51.854  root    branch=None                MODEL      CALL worker       id=call_801667
#3  02:39:07.518  worker  branch=worker@call_801667  MODEL      CALL write_value  id=call_1226970
#4  02:39:27.610  worker  branch=worker@call_801667  framework  RESP write_value  id=call_1226970
                            -> {"error":"This tool call requires confirmation, ..."}
#5  02:39:27.611  worker  branch=worker@call_801667  framework  CALL adk_request_confirmation
                            id=adk-52fb93d2-b962-4755-93d5-6338c5d59aa9
                            args.originalFunctionCall.id = call_1226970
      ---- tool execution count for T1-R02: 0 ----
#6  02:39:46.683  user    branch=worker@call_801667  framework  RESP adk_request_confirmation
                            -> {"confirmed": false, "payload": {...}}
#7  02:39:46.702  worker  branch=worker@call_801667  framework  RESP write_value  id=call_1226970
                            -> {"error": "This tool call is rejected."}
      ---- tool execution count for T1-R02: 0 ----
#8  02:39:46.716  worker  branch=worker@call_801667  MODEL      CALL write_value  id=call_859286  <- NEW id
#9  02:40:08.823  worker  branch=worker@call_801667  framework  RESP write_value  id=call_859286
                            -> {"error":"This tool call requires confirmation, ..."}
#10 02:40:08.823  worker  branch=worker@call_801667  framework  CALL adk_request_confirmation
                            id=adk-3eb1b0c1-7339-420f-9d0b-3e6e75aa0c5d
                            (left unanswered; session frozen here)
```

The string `T1-R02` does not occur in `tool_executions.jsonl` at all.

### Reject behaviour: 3/3 frozen single-rejection runs agree

| Property            | C0-R01 (Root)                  | T1-A03e (task)                | T1-R02 (task)                 |
| ------------------- | ------------------------------ | ----------------------------- | ----------------------------- |
| events              | 9                              | 10                            | 10                            |
| `write_value` calls | `call_1219303`, `call_1090589` | `call_746209`, `call_1659000` | `call_1226970`, `call_859286` |
| rejected call       | first only                     | first only                    | first only                    |
| tool body executed  | no                             | no                            | no                            |
| `finish_task` calls | 0                              | 0                             | 0                             |
| branches            | `None`                         | `None`, `worker@call_1817880` | `None`, `worker@call_801667`  |

**T1 Reject conclusion: rejecting a confirmation owned by a `mode="task"`
child prevented tool execution in 2/2 runs, exactly as it did at Root level
in C0-R01.** In all three the model then re-issued the call under a new id,
and in both task-mode runs `finish_task` was never reached, so control did
not return to Root.

The only structural difference between the Root-level and task-level Reject
runs is the branch the confirmation lives on. The rejection semantics —
`confirmed:false` recorded, pending call terminated against its original id,
zero executions, model re-issues under a new id — are identical.

### Phase 1 complete — required runs and decision-matrix position

| Variant | Required by protocol  | Achieved                         |
| ------- | --------------------- | -------------------------------- |
| C0      | ≥1 Accept + ≥1 Reject | 1 Accept PASS, 1 Reject PASS     |
| T0      | 3 clean runs          | 3/3 PASS                         |
| T1      | 3 Accept + 2 Reject   | 3/3 Accept PASS, 2/2 Reject PASS |

Not counted toward those totals: 4 INVALID runs (provider 503), 1 PARTIAL
(A-K pass, 503 at L), 1 exceptional trial (T1-X01), 1 discarded session
(duplicate marker, no click).

Applying the brief's decision matrix to what the runs demonstrate:

- C0 PASS → native confirmation works in this environment.
- C0 PASS + T0 PASS → the basic task lifecycle is reliable here, so a T1
  failure could not have been attributed to delegation or task completion
  alone.
- **T0 PASS + T1 PASS** → the matrix entry "T0 PASS, T1 FAIL" does not apply.
  Task delegation composed with native `require_confirmation=True`
  completed every checkpoint A-L. There is no failed checkpoint to report
  for T1, and therefore no confirmation-continuation failure boundary of the
  kind this expedition set out to locate.

Stated precisely, and confined to what was run: **in google-adk 2.6.3 with
`gemini-3.5-flash`, a `mode="task"` LlmAgent owning a FunctionTool with
`require_confirmation=True` paused for confirmation, continued the same
pending call after Accept, received the tool result, completed its task via
`finish_task`, and returned the result to Root — in 3/3 Accept runs, with
the tool body executing exactly once each. Rejecting prevented execution in
2/2 runs.**

This addresses the FunctionTool half of the question only. C1 and T2 (native
`McpToolset` confirmation) are Phase 2 and have not been run; nothing here
should be read as evidence about the MCP path.

## Failures Observed

_(none yet. The 503s above are provider-side, not failures of an ADK
execution path: two are INVALID because the run died on Root's first model
call before entering the test path, and one is PARTIAL because every
ADK-owned checkpoint passed and only Root's closing model call failed.)_

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

### Inference: rejection ends a call; only finish_task ends a task

Based on T1-X01 (one session, four cycles) and C0-R01:

A rejection is terminal for the *call* it targets — ADK closes it with
`{"error": "This tool call is rejected."}` and the body never runs. It does
not appear to be terminal for the *task*. In every completed run so far,
return-to-Root was driven by `finish_task`, and in T1-X01 no `finish_task`
occurred while rejections continued, so control stayed inside the child
branch across three cycles.

The worker instruction under test is:

```
When asked to write a value, call write_value with the exact value and run marker provided.
After the tool succeeds, complete the task.
```

It authorises completion only after success and is silent on failure. A
plausible reading is that the model, having no instructed route to
`finish_task` after a rejection, retries instead. C0-R01 is consistent: Root
also re-issued once after a Reject, at Root level.

If that reading is right, the structural consequence differs by composition:
at Root level a post-rejection retry leaves a pending prompt in front of the
user, whereas inside task mode it means control never returns to Root at
all. This is inference, not a finding — the experiment did not vary the
instruction, and doing so mid-expedition is barred by ground rule 9.

Untested alternatives that could equally explain the loop: a framework-level
rejection-to-task-termination path that exists but was not triggered here;
model-specific retry behaviour that another model would not exhibit.
