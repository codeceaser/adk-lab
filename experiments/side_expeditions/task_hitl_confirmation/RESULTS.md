# Results: ADK Task Mode + Native Tool Confirmation

Environment: `google-adk` 2.6.3, `google-genai` 2.17.0, Python 3.13.9,
`gemini-3.5-flash` via Gemini API. See `README.md`.

Code under test: commit `acb44e8` (see `evidence/test_start_revision.txt`).

| Variant | Run                          | Accept/Reject           | Last checkpoint                            |                         Tool count | Result                                   |
| ------- | ---------------------------- | ----------------------- | ------------------------------------------ | ---------------------------------: | ---------------------------------------- |
| C0      | C0-A01                       | Accept                  | 7 — Root continues                         |                 0 before / 1 after | PASS                                     |
| C0      | C0-R01                       | Reject                  | 5 — rejection honoured, tool not executed  |                 0 before / 0 after | PASS                                     |
| T0      | T0-01                        | n/a                     | 7 — Root continues after task result       |                                  1 | PASS                                     |
| T0      | T0-02 attempt 1              | n/a                     | 0 — Root's first model call                |                                  0 | INVALID (provider 503)                   |
| T0      | T0-02                        | n/a                     | 7 — Root continues after task result       |                                  1 | PASS                                     |
| T0      | T0-03                        | n/a                     | 7 — Root continues after task result       |                                  1 | PASS                                     |
| T1      | T1-A01                       | Accept                  | L — Root continues (no missing checkpoint) |                 0 before / 1 after | PASS                                     |
| T1      | T1-A02 attempt 1             | n/a                     | none — Root's first model call             |                                  0 | INVALID (provider 503)                   |
| T1      | T1-A02 attempt 2             | Accept                  | K — task result returned to Root           |                 0 before / 1 after | PARTIAL (A-K pass, provider 503 at L)    |
| T1      | T1-A02                       | Accept                  | L — Root continues (no missing checkpoint) |                 0 before / 1 after | PASS                                     |
| T1      | T1-A03a attempt 1            | n/a                     | A — delegation only, 503 in child branch   |                                  0 | INVALID (provider 503)                   |
| T1      | T1-A03a attempt 2            | n/a                     | none — Root's first model call             |                                  0 | INVALID (provider 503)                   |
| T1      | T1-X01 (exceptional trial)   | Reject ×3 then Accept   | L — Root continues (4th cycle)             | 0 after 3 rejects / 1 after accept | EXCEPTIONAL TRIAL (see notes)            |
| T1      | T1-A03d                      | Accept                  | L — Root continues (no missing checkpoint) |       0 before / 1 after (derived) | PASS                                     |
| T1      | T1-A03e (Reject run 1 of 2)  | Reject                  | F — rejection recorded, tool not executed  |                 0 before / 0 after | PASS                                     |
| T1      | T1-R02 (Reject run 2 of 2)   | Reject                  | F — rejection recorded, tool not executed  |                 0 before / 0 after | PASS                                     |
| C1      | C1-A01                       | Accept                  | 7 — Root continues                         |                 0 before / 1 after | PASS                                     |
| C1      | C1-R01                       | Reject                  | 5 — rejection honoured, tool not executed  |                 0 before / 0 after | PASS                                     |
| T2      | T2-A01 attempt 1             | n/a                     | none — Root's first model call             |                                  0 | INVALID (provider 503)                   |
| T2      | T2-A01                       | Accept                  | L — Root continues (no missing checkpoint) |                 0 before / 1 after | PASS                                     |
| T2      | T2-A02                       | Accept                  | L — Root continues (no missing checkpoint) |                 0 before / 1 after | PASS                                     |
| T2      | T2-A03                       | Accept (1 of 2 pending) | L — Root continues (no missing checkpoint) |                 0 before / 1 after | PASS (see concurrent-confirmations note) |
| T2      | T2-R01 (Reject run 1 of 2)   | Reject                  | F — rejection recorded, tool not executed  |                 0 before / 0 after | PASS                                     |
| T2      | T2-R02 (Reject run 2 of 2)   | Reject (1 of 2 pending) | F — rejection recorded, tool not executed  |                 0 before / 0 after | PASS                                     |
| R0      | R0-R01 (delegation 1)        | Reject                  | finish_task with cancelled result          |                 0 before / 0 after | PASS (per-delegation scope)              |
| R0      | R0-R01 (session)             | Reject                  | Root re-delegated instead of responding    |                 0 before / 0 after | FAIL — semantic retry (session scope)    |
| R0.1    | R0.1-R01                     | Reject                  | Root responded with a cancellation         |                 0 before / 0 after | PASS (all 8 conditions)                  |
| R0.1    | R0.1-A01 (Accept regression) | Accept                  | Root responded with success                |                 0 before / 1 after | PASS (no regression)                     |
| R0.1    | R0.1-R02                     | Reject                  | Root responded with a cancellation         |                 0 before / 0 after | PASS (all 8 conditions)                  |
| R0.1    | R0.1-R03                     | Reject                  | Root responded with a cancellation         |                 0 before / 0 after | PASS (all 8; degraded model turn at #6)  |
| R0.1    | R0.1-A02 (abandoned)         | none — not clicked      | abandoned at pending confirmation          |                                  0 | NOT A RUN (same session as R0.1-R03)     |
| R0.1    | R0.1-A02b                    | Accept                  | Root responded with success                |       0 before (derived) / 1 after | PASS (no regression)                     |
| R0.1    | R0.1-A03                     | Accept                  | Root responded with success                |       0 before (derived) / 1 after | PASS (no regression)                     |

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

### Reject behaviour: the three FunctionTool single-rejection runs

Written when these were the only frozen Reject runs. Scope later widened by
"Reject behaviour: 4/4 frozen single-rejection runs agree" below, which adds
C1-R01 over MCP. This table is kept for the per-run detail (event counts,
call ids, branches) that the 4/4 summary does not repeat.

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
in C0-R01, and later in C1-R01 over MCP.** In all three the model then re-issued the call under a new id,
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

This addresses the FunctionTool half of the question only. See the Phase 2
entry below for C1; T2 remains unrun.

### Phase 2 status — C1 complete

| Variant | Required by protocol                   | Achieved                     |
| ------- | -------------------------------------- | ---------------------------- |
| C1      | ≥1 Accept + ≥1 Reject                  | 1 Accept PASS, 1 Reject PASS |
| T2      | 3 Accept + 2 Reject, only if T1 passed | not scaffolded, not run      |

Decision-matrix position: the brief's "C0 PASS, C1 FAIL → MCP confirmation
path is the problem" entry **does not apply**. Native
`McpToolset(require_confirmation=True)` behaved as C0 did — confirmation
requested, tool withheld while pending, exactly one execution on Accept
continuing the original call id, zero executions on Reject.

T1 passed, so T2 is in scope by the brief's own condition.

**C1-A01 (Accept) — PASS.** First Phase 2 run: Root + native
`McpToolset(require_confirmation=True)` over a stdio MCP server. Session
`b86a1702-a3fc-4938-b7c1-8ab9cbf83f55`, 8 events, single invocation
`e-3d482689-16d6-4125-b18e-3c0c12517bb5`, exported to
`evidence/C1-A01_events.jsonl`. Pre-click count measured live at the pending
state.

```
#1 12:49:37.477  user     framework  TEXT "Use write_value ... run marker C1-A01."
#2 12:49:38.413  c1_root  MODEL      CALL write_value  id=call_2659067
                            args={"value":"alpha","run_marker":"C1-A01"}
#3 12:49:40.867  c1_root  framework  RESP write_value  id=call_2659067
                            -> {"error":"This tool call requires confirmation, ..."}
#4 12:49:40.867  c1_root  framework  CALL adk_request_confirmation
                            id=adk-fe95ab00-0c14-493b-a99d-6583115e19bc
                            args.originalFunctionCall.id = call_2659067
#5 12:49:40.901  c1_root  MODEL      TEXT "I approve this tool call to write the value ..."
      ---- MCP tool execution count for C1-A01: 0 (measured live, pre-click) ----
#6 12:50:25.231  user     framework  RESP adk_request_confirmation
                            -> {"confirmed": true, "payload": {...}}
#7 12:50:25.262  c1_root  framework  RESP write_value  id=call_2659067
                            -> {"content":[{"type":"text","text":"{... MCP_TOOL_EXECUTED ... C1-A01 ...}"}],
                                "isError": false}
#8 12:50:25.278  c1_root  MODEL      TEXT "I have successfully written the value ..."
      ---- MCP tool execution count for C1-A01: 1 ----
```

Directly demonstrated by this run:

- Native `McpToolset(require_confirmation=True)` produces a confirmation
  request, and ADK Web presents it. No `FunctionTool` wrapper is involved.
- The MCP tool body did not execute while the confirmation was pending
  (count measured live at 0; the pre-Accept response is an error stub).
- Accepting continued the *same* pending call: the session contains exactly
  one `write_value` FunctionCall (`call_2659067`) and both the pre-Accept
  stub and the post-Accept real result carry that id.
- The MCP implementation executed **exactly once**, recorded independently
  in the server subprocess (`mcp_tool_executions.jsonl`, pid 23024,
  `12:50:25.258465Z`). The Phase 1 FunctionTool log stayed at 9 lines,
  confirming the two evidence channels do not cross.
- Root received the result and produced a subsequent response.

Two differences from C0 worth recording, neither affecting the checkpoints:

1. **The tool result arrives in an MCP envelope**, not as the plain dict C0
   returned:
   `{"content": [{"type": "text", "text": "<json>"}], "isError": false}`
   — the tool's own return value is JSON-encoded inside `content[0].text`.
2. **Event #5: the model emitted a text turn announcing "I approve this tool
   call"** while the confirmation was still pending. C0 has no equivalent.
   It is model-authored (`modelVersion` and `usageMetadata` both present) and
   causally inert: the tool did not execute at #5, the count was still 0
   afterwards, and execution followed only the genuine confirmation response
   at #6 forty-five seconds later.

On #6's provenance: the confirmation response is authored by `user` with no
`modelVersion` and no `usageMetadata` — the same signature as C0-A01's
click, and unlike every model-authored event in this session (#2, #5, #8).
The operator confirmed they clicked Accept after being shown the pending
state. Recorded because #5 made the run momentarily look as though approval
had occurred without operator action; it had not. Note for future runs: the
event record cannot by itself distinguish a UI click from an
API-posted confirmation response, since ADK labels both `author="user"`.

**C1-R01 (Reject) — PASS.** Session
`8dd8c502-ffeb-46aa-bc70-ca4d574b677c`, 11 events, exported to
`evidence/C1-R01_events.jsonl`. Frozen after a single rejection with the
follow-up confirmation unanswered, matching C0-R01, T1-A03e and T1-R02.
Byte-identical to the live session (same 11 event ids, sha256
`a2d24d3ad6f050d89c991b3832bf8ae9`). Pre-click count measured live.

```
#1  13:07:34.603  user     framework  TEXT "Use write_value ... run marker C1-R01."
#2  13:07:34.626  c1_root  MODEL      CALL write_value  id=call_744348
#3  13:07:36.900  c1_root  framework  RESP write_value  id=call_744348
                             -> {"error":"This tool call requires confirmation, ..."}
#4  13:07:36.900  c1_root  framework  CALL adk_request_confirmation
                             id=adk-2fe1ad64-bfa1-4367-8a28-8e21957889dd
                             originalFunctionCall.id = call_744348
                             toolConfirmation.confirmed = False
                             longRunningToolIds=['adk-2fe1ad64-...']
#5  13:07:36.928  c1_root  MODEL      TEXT "... Please approve the tool call ..."
      ---- MCP execution count for C1-R01: 0 (measured live, pre-click) ----
#6  13:08:55.491  user     framework  RESP adk_request_confirmation
                             -> {"confirmed": false, "payload": {...}}
#7  13:08:55.506  c1_root  framework  RESP write_value  id=call_744348
                             -> {"error": "This tool call is rejected."}
      ---- MCP execution count for C1-R01: 0 ----
#8  13:08:55.522  c1_root  MODEL      CALL write_value  id=call_1531628   <- NEW id
#9  13:08:58.409  c1_root  framework  RESP write_value  id=call_1531628
                             -> {"error":"This tool call requires confirmation, ..."}
#10 13:08:58.409  c1_root  framework  CALL adk_request_confirmation
                             id=adk-15c9c921-da0d-4e73-b4c1-556065b62419
                             (left unanswered; session frozen here)
#11 13:08:58.438  c1_root  MODEL      TEXT "... Please approve the tool call ..."
```

Directly demonstrated by this run:

- Rejecting a native `McpToolset` confirmation records
  `{"confirmed": false, ...}` and ADK terminates the pending call with
  `{"error": "This tool call is rejected."}` against its original id.
- The MCP tool body executed **zero** times, corroborated from both sides:
  the string `C1-R01` does not occur in `mcp_tool_executions.jsonl` at all
  (the file still holds only C1-A01's single line), and no `write_value`
  response in the session carries an `MCP_TOOL_EXECUTED` marker.
- The model re-issued under a **new** id (`call_1531628` vs `call_744348`),
  producing a second confirmation request.

### Reject behaviour: 4/4 frozen single-rejection runs agree

| Run     | Composition         | `write_value` calls | first call rejected | tool executed |
| ------- | ------------------- | ------------------: | ------------------- | ------------- |
| C0-R01  | Root / FunctionTool |                   2 | yes                 | no            |
| T1-A03e | task / FunctionTool |                   2 | yes                 | no            |
| T1-R02  | task / FunctionTool |                   2 | yes                 | no            |
| C1-R01  | Root / MCP          |                   2 | yes                 | no            |

Rejection semantics are identical across both transports and both
compositions, and the model's re-issue under a new id follows every
rejection observed in this expedition.

Model narration at the pending confirmation is **not Accept-specific**: C1-A01
produced "I approve this tool call" (#5) and C1-R01 produced "Please approve
the tool call" (#5, #11). Both are model-authored and causally inert, and
their wording carries no information about the outcome.

**T2-A01 (Accept) — PASS. Checkpoints A-L all occurred; no missing
checkpoint.** The composition the expedition was built to test: task
delegation + native MCP confirmation. Session
`bdf11910-99a9-4ca1-9629-362e84d89cbe`, 12 events, exported to
`evidence/T2-A01_events.jsonl`. Pre-click count measured live at the pending
state.

```
#1  14:59:47.826  user    branch=None                 framework  TEXT "... run marker T2-A01."
#2  14:59:47.855  root    branch=None                 MODEL      CALL worker       id=call_1317118
#3  14:59:51.831  worker  branch=worker@call_1317118  MODEL      CALL write_value  id=call_1682897
#4  14:59:54.459  worker  branch=worker@call_1317118  framework  RESP write_value  id=call_1682897
                             -> {"error":"This tool call requires confirmation, ..."}
#5  14:59:54.460  worker  branch=worker@call_1317118  framework  CALL adk_request_confirmation
                             id=adk-db1901eb-96a1-4b16-9e3f-a92c0e7ad797
                             originalFunctionCall.id = call_1682897
#6  14:59:54.507  worker  branch=worker@call_1317118  MODEL      TEXT "I have initiated the request ..."
      ---- MCP execution count for T2-A01: 0 (measured live, pre-click) ----
#7  15:00:43.655  user    branch=worker@call_1317118  framework  RESP adk_request_confirmation
                             -> {"confirmed": true, "payload": {...}}
#8  15:00:43.682  worker  branch=worker@call_1317118  framework  RESP write_value  id=call_1682897
                             -> {"content":[{"type":"text","text":"{... MCP_TOOL_EXECUTED ... T2-A01 ...}"}]}
#9  15:00:43.706  worker  branch=worker@call_1317118  MODEL      CALL finish_task  id=call_2288846
#10 15:00:46.340  worker  branch=worker@call_1317118  framework  RESP finish_task  -> "Task completed."
#11 15:00:46.358  user    branch=None                 framework  RESP worker       id=call_1317118
#12 15:00:46.382  root    branch=None                 MODEL      TEXT "The value "alpha" has been ..."
      ---- MCP execution count for T2-A01: 1 ----
```

Checkpoint mapping: A=#2, B=#3, C=#5, D=observed live pre-click, E=#7, F=#7,
G=MCP server log, H=#8, I=#9, J=#10, K=#11, L=#12.

Directly demonstrated by this run:

- Confirmation continuation held across the MCP boundary *inside* a task
  child: exactly one `write_value` call in the session (`call_1682897`), with
  both the pre-Accept stub and the post-Accept real result carrying that id.
- The Accept re-entered on the child branch `worker@call_1317118`; the
  session contains exactly two branch values.
- The MCP implementation executed exactly once, recorded independently in the
  server subprocess.
- `finish_task` succeeded and the delegation call was satisfied by a
  synthesized response re-using id `call_1317118`, payload byte-identical to
  the `finish_task` argument.

Structural agreement with the T1 Accept runs, every id differing:

| Run     | Composition         | calls | continued same id | Accept on child branch | delegation id re-used |
| ------- | ------------------- | ----: | ----------------- | ---------------------- | --------------------- |
| T1-A01  | task / FunctionTool |     1 | yes               | yes                    | yes                   |
| T1-A02  | task / FunctionTool |     1 | yes               | yes                    | yes                   |
| T1-A03d | task / FunctionTool |     1 | yes               | yes                    | yes                   |
| T2-A01  | task / MCP          |     1 | yes               | yes                    | yes                   |

**T2-A01 attempt 1 — INVALID (provider 503).** Session
`9716135c-35b0-44e1-aef8-21d5f7a1adb5`, 2 events, preserved as
`evidence/T2-A01-INVALID-503-pre_events.jsonl`. Died on Root's first model
call before any delegation, MCP connection or tool call; 0 executions. The
successful run above re-used the marker `T2-A01` rather than taking a fresh
one as the protocol prescribes; counting stays unambiguous only because this
attempt executed the tool zero times. Both session ids are recorded here so
the pairing is explicit.

**Evidence note — the `variant=c1` tag on T2 runs.** T2 points at C1's
`write_value_mcp_server.py` itself rather than a copy, so the two variants
exercise byte-identical server code. The tag in
`mcp_tool_executions.jsonl` is therefore the server's, and T2 runs appear as
`variant=c1`. Attribution is by `run_marker`, which is unique per run. The
log currently reads:

```
C1-A01   1
T2-A01   1
```

**T2-A02 (Accept) — PASS. Checkpoints A-L all occurred.** Session
`b1b09008-212f-4d7d-9639-5304fc516e39`, 12 events, exported to
`evidence/T2-A02_events.jsonl`. Pre-click count measured live at the pending
state; MCP log total was 2 at that moment and 3 afterwards.

```
#1  15:03:48.661  user    branch=None                framework  TEXT "... run marker T2-A02."
#2  15:03:48.681  root    branch=None                MODEL      CALL worker       id=call_435485
#3  15:03:51.698  worker  branch=worker@call_435485  MODEL      CALL write_value  id=call_335245
#4  15:03:54.227  worker  branch=worker@call_435485  framework  RESP write_value  id=call_335245
                             -> {"error":"This tool call requires confirmation, ..."}
#5  15:03:54.227  worker  branch=worker@call_435485  framework  CALL adk_request_confirmation
                             id=adk-cd98d6de-7eba-48c9-aafc-0db98bdd1639
                             originalFunctionCall.id = call_335245
#6  15:03:54.270  worker  branch=worker@call_435485  MODEL      TEXT "I have initiated the process ..."
      ---- MCP execution count for T2-A02: 0 (measured live, pre-click) ----
#7  15:05:08.134  user    branch=worker@call_435485  framework  RESP adk_request_confirmation
                             -> {"confirmed": true, "payload": {...}}
#8  15:05:08.160  worker  branch=worker@call_435485  framework  RESP write_value  id=call_335245
                             -> {"content":[{"type":"text","text":"{... MCP_TOOL_EXECUTED ... T2-A02 ...}"}]}
#9  15:05:08.180  worker  branch=worker@call_435485  MODEL      CALL finish_task  id=call_1851608
#10 15:05:10.771  worker  branch=worker@call_435485  framework  RESP finish_task  -> "Task completed."
#11 15:05:10.789  user    branch=None                framework  RESP worker       id=call_435485
#12 15:05:10.820  root    branch=None                MODEL      TEXT "The value "alpha" has been ..."
      ---- MCP execution count for T2-A02: 1 ----
```

Reproduces T2-A01 with entirely different ids: one `write_value` call
(`call_335245`) continued under its own id, Accept re-entering on the child
branch `worker@call_435485`, `finish_task` succeeding, and the delegation
call satisfied by a synthesized response re-using `call_435485` with a
payload byte-identical to the `finish_task` argument. Two branch values in
the session.

MCP execution log after this run: `C1-A01` 1, `T2-A01` 1, `T2-A02` 1 — one
execution per run, none doubled.

**T2-A03 (Accept) — PASS, and the first run with two concurrent pending
confirmations.** Session `90082084-409a-43a5-bd8e-a06e5902d4a6`, 15 events,
exported to `evidence/T2-A03_events.jsonl`. Pre-click count measured live at
the two-pending state.

The worker issued a **second** `write_value` call while the first
confirmation was still pending, with nothing rejected — 51 ms after the first
confirmation request, on the same child branch:

```
#3  15:06:52.323  worker  MODEL      CALL write_value  id=call_3093561
#4  15:06:55.243  worker  framework  RESP write_value  id=call_3093561  [pending stub]
#5  15:06:55.244  worker  framework  CALL adk_request_confirmation adk-a5a4fd0d-...
                             originalFunctionCall.id = call_3093561
#6  15:06:55.295  worker  MODEL      CALL write_value  id=call_1769898   <- NEW call, nothing rejected
#7  15:06:59.403  worker  framework  RESP write_value  id=call_1769898  [pending stub]
#8  15:06:59.404  worker  framework  CALL adk_request_confirmation adk-ef5a2fa5-...
                             originalFunctionCall.id = call_1769898
#9  15:06:59.436  worker  MODEL      TEXT "I have attempted to write ... but the tool cal..."
      ---- MCP execution count for T2-A03: 0, with TWO confirmations pending ----
#10 15:08:47.313  user    framework  RESP adk_request_confirmation adk-ef5a2fa5-...
                             -> {"confirmed": true, ...}          (the second one)
#11 15:08:47.339  worker  framework  RESP write_value  id=call_1769898  [REAL RESULT]
#12 15:08:47.361  worker  MODEL      CALL finish_task  id=call_2026550
#13 15:08:49.973  worker  framework  RESP finish_task  -> "Task completed."
#14 15:08:49.993  user    framework  RESP worker       id=call_204964
#15 15:08:50.019  root    MODEL      TEXT "The value "alpha" has been successfully written ..."
      ---- MCP execution count for T2-A03: 1 ----
```

Operator action was deliberate and recorded in advance: of the three options
put to them (accept one, accept both, freeze), they accepted exactly one —
`adk-ef5a2fa5`, targeting `call_1769898`.

Directly demonstrated by this run:

- **A `mode="task"` worker can hold two confirmations pending at once.** Two
  `write_value` calls, two confirmation requests, both on branch
  `worker@call_204964`. Every previous re-issue in this expedition followed a
  rejection; this one did not.
- **Accepting one pending confirmation executed exactly that call, exactly
  once.** The real result carries `call_1769898`; `call_3093561`'s response
  remained a pending stub.
- **The unanswered confirmation was neither executed nor rejected.**
  `adk-a5a4fd0d` was simply abandoned. Execution count for the marker is 1,
  not 2.
- **The task completed with a confirmation still outstanding.**
  `finish_task` succeeded, the delegation call `call_204964` was satisfied by
  a synthesized response, and Root produced its closing text — none of it
  blocked by the orphaned pending confirmation.

### T2 Accept repeatability: 3/3

| Run    | events | `write_value` calls | conf. requests | conf. responses | executed | continued same id | delegation id re-used |
| ------ | -----: | ------------------: | -------------: | --------------: | -------: | ----------------- | --------------------- |
| T2-A01 |     12 |                   1 |              1 |               1 |        1 | yes               | yes                   |
| T2-A02 |     12 |                   1 |              1 |               1 |        1 | yes               | yes                   |
| T2-A03 |     15 |                   2 |              2 |               1 |        1 | yes               | yes                   |

All three executed the MCP tool exactly once and completed A-L. T2-A03
differs only in the model's extra call, which produced an extra confirmation
request rather than an extra execution.

MCP execution log after the three Accepts: `C1-A01` 1, `T2-A01` 1,
`T2-A02` 1, `T2-A03` 1 — one execution per marker, none doubled.

**T2-R01 (Reject) — PASS.** First of the two planned T2 Reject runs. Session
`e692c00e-1659-455d-97f8-5aaf538964eb`, 12 events, exported to
`evidence/T2-R01_events.jsonl`. Frozen after a single rejection with the
follow-up confirmation unanswered. Byte-identical to the live session (same
12 event ids, sha256 `815320faf3c1e619521a80170feceaf7`). Pre-click count
measured live; a single confirmation was pending, so this run is directly
comparable to the other four Reject runs.

```
#2  15:11:51.750  root    branch=None                 MODEL      CALL worker       id=call_1153707
#3  15:11:54.812  worker  branch=worker@call_1153707  MODEL      CALL write_value  id=call_3301875
#4  15:11:57.493  worker  branch=worker@call_1153707  framework  RESP write_value  [pending stub]
#5  15:11:57.494  worker  branch=worker@call_1153707  framework  CALL adk_request_confirmation
                             id=adk-838ee66a-6de3-4e6d-a814-17acdb0d2a2b -> call_3301875
      ---- MCP execution count for T2-R01: 0 (measured live, pre-click) ----
#7  15:12:31.426  user    branch=worker@call_1153707  framework  RESP adk_request_confirmation
                             -> {"confirmed": false, "payload": {...}}
#8  15:12:31.447  worker  branch=worker@call_1153707  framework  RESP write_value  id=call_3301875
                             -> {"error": "This tool call is rejected."}
      ---- MCP execution count for T2-R01: 0 ----
#9  15:12:31.470  worker  branch=worker@call_1153707  MODEL      CALL write_value  id=call_348286  <- NEW id
#11 15:12:35.449  worker  branch=worker@call_1153707  framework  CALL adk_request_confirmation
                             id=adk-c8a0a80f-8b81-4e54-a3f1-1d17cce0d46c -> call_348286
                             (left unanswered; session frozen here)
```

Directly demonstrated by this run:

- Rejecting a confirmation owned by a `mode="task"` child and served over MCP
  records `{"confirmed": false, ...}` on the child branch, and ADK terminates
  the pending call against its original id.
- The MCP tool body executed **zero** times: the string `T2-R01` does not
  occur in `mcp_tool_executions.jsonl` (total unchanged at 4), and no
  `write_value` response in the session carries an `MCP_TOOL_EXECUTED`
  marker.
- The worker re-issued under a **new** id (`call_348286`), producing a second
  confirmation request.
- `finish_task` calls: **0**. Responses to Root: **0**. Control did not
  return to Root — the same as T1-A03e and T1-R02, now over MCP.

### Reject behaviour: 5/5 frozen single-rejection runs agree

| Run     | Composition         | `write_value` calls | tool executed | `finish_task` | resp. to Root |
| ------- | ------------------- | ------------------: | ------------- | ------------: | ------------: |
| C0-R01  | Root / FunctionTool |                   2 | no            |           n/a |           n/a |
| T1-A03e | task / FunctionTool |                   2 | no            |             0 |             0 |
| T1-R02  | task / FunctionTool |                   2 | no            |             0 |             0 |
| C1-R01  | Root / MCP          |                   2 | no            |           n/a |           n/a |
| T2-R01  | task / MCP          |                   2 | no            |             0 |             0 |

The `finish_task` and response-to-Root columns are marked n/a for the two
Root-level runs: those variants have no task, so zeros there would be
trivially true rather than informative. The meaningful comparison for those
two columns is among the three task-mode runs, where all three show the task
failing to complete after a rejection.

Rejection semantics are identical across both transports and both
compositions: `confirmed:false` recorded, the pending call terminated against
its original id, zero executions, and the model re-issuing under a new id.

**T2-R02 (Reject) — PASS.** Second planned T2 Reject run, and the last run of
the experiment. Session `30902f69-3b52-4796-8005-104ac5089628`, 18 events,
exported to `evidence/T2-R02_events.jsonl`. Byte-identical to the live
session (same 18 event ids, sha256 `a959f212480eed912cbba128c036cae3`).
Pre-click count measured live.

Two confirmations were already pending when the operator was shown the
state — the concurrent-pending behaviour first seen in T2-A03, now
reproduced. The operator stated in advance that they would reject one and
leave the other, and did so.

```
#3  15:15:25.311  worker  MODEL      CALL write_value  id=call_1659641
#5  15:15:27.988  worker  framework  CALL adk_request_confirmation adk-ac05f14d-... -> call_1659641
#6  15:15:28.047  worker  MODEL      CALL write_value  id=call_643600    <- 59ms later, nothing rejected
#8  15:15:34.329  worker  framework  CALL adk_request_confirmation adk-ec7426df-... -> call_643600
      ---- MCP execution count for T2-R02: 0, with TWO confirmations pending ----
#10 15:17:05.585  user    framework  RESP adk_request_confirmation adk-ac05f14d-...
                             -> {"confirmed": false, ...}        (the first one)
#11 15:17:05.609  worker  framework  RESP write_value  id=call_1659641
                             -> {"error": "This tool call is rejected."}
#12 15:17:05.630  worker  MODEL      CALL write_value  id=call_2210177   <- NEW
#14 15:17:09.233  worker  framework  CALL adk_request_confirmation adk-dc16f0c7-... -> call_2210177
#15 15:17:09.276  worker  MODEL      CALL write_value  id=call_2629216   <- NEW again
#17 15:17:13.280  worker  framework  CALL adk_request_confirmation adk-c3428eb6-... -> call_2629216
#18 15:17:13.314  worker  MODEL      TEXT "I attempted to write ... but the too..."
                             (frozen here; three confirmations outstanding)
      ---- MCP execution count for T2-R02: 0 ----
```

Final state of the four `write_value` calls:

| Call           | Status                                   |
| -------------- | ---------------------------------------- |
| `call_1659641` | rejected — the one the operator clicked  |
| `call_643600`  | pending stub, untouched by the rejection |
| `call_2210177` | pending stub, issued after the rejection |
| `call_2629216` | pending stub, issued after the rejection |

Directly demonstrated by this run:

- The MCP tool body executed **zero** times: `T2-R02` never appears in
  `mcp_tool_executions.jsonl` (total unchanged at 4) and no response carries
  an `MCP_TOOL_EXECUTED` marker.
- **Rejecting one pending call left its sibling untouched.** `call_643600`
  remained a pending stub — the rejection did not cascade to other
  outstanding confirmations. This mirrors T2-A03, where accepting one call
  left the other pending and unexecuted.
- **The retry after a rejection produced two new calls, not one**
  (`call_2210177` then `call_2629216`), leaving three confirmations
  outstanding at freeze. Every earlier Reject run produced exactly one
  re-issue.
- `finish_task` calls: **0**. Responses to Root: **0**. Control did not
  return to Root.

Final execution logs for the whole experiment:

```
MCP           C1-A01 1, T2-A01 1, T2-A02 1, T2-A03 1
FunctionTool  C0-A01 1, T0-01 1, T0-02 1, T0-03 1, T1-A01 1,
              T1-A02 2, T1-A03c 1, T1-A03d 1
```

Every marker counts 1 except `T1-A02`, whose 2 lines belong to two separate
sessions under a re-used marker and are attributed per session above.

---

## R0 — semantic rejection handling (follow-on experiment)

R0 is a separate, narrower experiment run after the expedition concluded. It
copies the T2 topology exactly and changes **only the worker instruction**,
adding an explicit rejection path. Comparing 18 model-visible and wiring
fields between `t2_task_mcp_confirmation` and
`r0_task_mcp_rejection_semantics`, `worker.instruction` is the only field
that differs. No callbacks, no `ResumabilityConfig`, no state flags, no
retry or continuation logic, no FunctionTool wrapper; the MCP server is the
same shared file. Root's instruction is unchanged from T2, deliberately.

R0 worker instruction, verbatim:

```text
When asked to write a value, call write_value with the exact value and run marker provided.
If write_value succeeds, complete the task with a success result.
If write_value is rejected by the user:
- treat the requested write as cancelled;
- do not call write_value again;
- do not request confirmation again;
- complete the task with a cancelled result.
Do not retry a rejected write unless the human user later issues a new, explicit write request in a new interaction.
```

**R0-R01 (Reject) — PASS at delegation scope, FAIL at session scope.**
Session `7f9045f2-4f91-4b3d-b314-c042d7c792fb`, 16 events, exported to
`evidence/R0-R01_events.jsonl`, frozen with a confirmation still pending and
byte-identical to the live session (sha256
`4897b6b06fe7688c2a14db43e17ac753`). Pre-click count measured live.

```
#1  15:43:56  user    TEXT "... run marker R0-R01."
#2  15:43:56  root    CALL worker       id=call_1874514              <- delegation 1
#3  15:44:01  worker  CALL write_value  id=call_2455728   branch=worker@call_1874514
#4  15:44:04  worker  RESP write_value  -> "requires confirmation"
#5  15:44:04  worker  CALL adk_request_confirmation adk-7ef68dbb-... -> call_2455728
#6  15:44:04  worker  TEXT "Please approve or reject this action"
      ---- MCP execution count for R0-R01: 0 (measured live, pre-click) ----
#7  15:44:39  user    RESP adk_request_confirmation -> {"confirmed": false, ...}
#8  15:44:39  worker  RESP write_value  id=call_2455728 -> {"error": "This tool call is rejected."}
#9  15:44:39  worker  CALL finish_task  id=call_1191359  args={"result": "cancelled"}   <- decisive
#10 15:44:42  worker  RESP finish_task  -> {"result": "Task completed."}
#11 15:44:42  user    RESP worker       id=call_1874514 -> {"result": "cancelled"}
#12 15:44:42  root    CALL worker       id=call_2657493              <- delegation 2
#13 15:44:44  worker  CALL write_value  id=call_3677550   branch=worker@call_2657493
#15 15:44:47  worker  CALL adk_request_confirmation adk-46db3558-... -> call_3677550
#16 15:44:47  worker  TEXT "Please approve the tool call ..."
                        (left unanswered; session frozen here)
      ---- MCP execution count for R0-R01: 0 ----
```

### Acceptance criteria at both scopes

| # | Criterion | Delegation 1 (#1-#11) | Whole session |
| - | --------- | --------------------- | ------------- |
| 1 | exactly one `write_value` call | PASS (1) | FAIL (2) |
| 2 | exactly one confirmation request | PASS (1) | FAIL (2) |
| 3 | Reject produced `confirmed=false` | PASS | PASS |
| 4 | MCP execution count 0 | PASS | PASS |
| 5 | no second `write_value` call | PASS | FAIL |
| 6 | no second confirmation request | PASS | FAIL |
| 7 | worker called `finish_task` | PASS | PASS |
| 8 | task result indicates cancellation | PASS (`{"result": "cancelled"}`) | PASS |
| 9 | worker result returned to Root | PASS | PASS |
| 10 | Root produced a final response | PASS (returned control) | FAIL (re-delegated) |

Both classifications are recorded because they answer different questions.
**Per-delegation: PASS.** **Per-session, the classification defined in the R0
brief §9: FAIL — semantic retry**, since a second `write_value` FunctionCall
did appear after the Reject.

### Directly demonstrated by this run

- **The hypothesis holds at the worker.** Event #9 is the decisive one: in
  all five prior Reject runs the event after
  `{"error": "This tool call is rejected."}` was a fresh `CALL:write_value`;
  here it is `CALL:finish_task` with `{"result": "cancelled"}`. Instructions
  alone changed the worker's interpretation of a rejection, with no
  callback, state machine, retry guard or framework change.
- **The MCP tool executed zero times** — `R0-R01` never appears in
  `mcp_tool_executions.jsonl` (total unchanged at 4).
- **The cancelled result reached Root**, `{"result": "cancelled"}` at #11,
  re-using delegation id `call_1874514`.
- **The retry relocated rather than disappeared.** Root re-delegated the
  identical request at #12 (`args.request` byte-identical to #2), creating a
  second child branch, a second `write_value` call and a second confirmation
  request. The session holds three branches: `None`,
  `worker@call_1874514`, `worker@call_2657493`.
- Criterion 10 failed for a different reason than the T1/T2 Reject runs. In
  those the task never completed and control never reached Root; here it
  completed, control reached Root, and Root chose to start again.

Not claimed: that Root's re-delegation is caused by its instruction lacking a
cancellation path. R0 did not vary Root's instruction — it was held identical
to T2 by design (R0 brief §3) — so that remains untested.

---

## R0.1 — terminal cancellation semantics at Root

R0.1 copies R0 exactly and changes **only the Root instruction**. Comparing
18 model-visible and wiring fields between `r0_task_mcp_rejection_semantics`
and `r0_1_task_mcp_root_semantics`, `root.instruction` is the only field that
differs; `worker.instruction` is byte-identical. No callbacks, state flags,
state machine, retry guards, `ResumabilityConfig`, structured task output or
MCP change; both agents have `planner`, `output_schema` and `output_key`
unset, and the only tools present are ADK-injected.

R0.1 Root instruction, verbatim (line 1 is R0's Root instruction unchanged):

```text
When the user asks to write a value, delegate to worker with the exact value and run marker provided.
If the worker reports that the operation was cancelled or rejected by the user, that is the final outcome for this request:
- do not delegate the same write again;
- do not attempt the operation by any other means;
- tell the user the operation was cancelled.
Attempt the write again only after the user makes a new, explicit request.
```

**R0.1-R01 (Reject) — PASS, all eight conditions.** Session
`f8bbab44-f2f2-4ac0-a324-157db9351691`, 12 events, exported to
`evidence/R0.1-R01_events.jsonl`, byte-identical to the live session (sha256
`caa0f4a1aee5a8c0e532e841c93d3f37`). Pre-click count measured live.

```
#1  16:07:30.371  user    branch=None                 framework  TEXT "... run marker R0.1-R01."
#2  16:07:30.405  root    branch=None                 MODEL      CALL worker       id=call_1776588
#3  16:07:34.269  worker  branch=worker@call_1776588  MODEL      CALL write_value  id=call_4046227
#4  16:07:36.786  worker  branch=worker@call_1776588  framework  RESP write_value  [pending stub]
#5  16:07:36.787  worker  branch=worker@call_1776588  framework  CALL adk_request_confirmation
                             id=adk-4112b9ec-70a3-4a52-87f8-7385788169ab -> call_4046227
#6  16:07:36.829  worker  branch=worker@call_1776588  MODEL      TEXT "Civic approval is required ..."
      ---- MCP execution count for R0.1-R01: 0 (measured live, pre-click) ----
#7  16:08:48.395  user    branch=worker@call_1776588  framework  RESP adk_request_confirmation
                             -> {"confirmed": false, "payload": {...}}
#8  16:08:48.414  worker  branch=worker@call_1776588  framework  RESP write_value  id=call_4046227
                             -> {"error": "This tool call is rejected."}
#9  16:08:48.436  worker  branch=worker@call_1776588  MODEL      CALL finish_task  id=call_2308211
                             args={"result": "cancelled"}
#10 16:08:51.321  worker  branch=worker@call_1776588  framework  RESP finish_task -> "Task completed."
#11 16:08:51.337  user    branch=None                 framework  RESP worker id=call_1776588
                             -> {"result": "cancelled"}
#12 16:08:51.365  root    branch=None                 MODEL      TEXT "The operation to write the value
                             "alpha" with run marker "R0.1-R01" was cancelled."     <- decisive
      ---- MCP execution count for R0.1-R01: 0 ----
```

| # | Condition | Result |
| - | --------- | ------ |
| 1 | exactly one Root→worker delegation | PASS (`call_1776588`) |
| 2 | exactly one `write_value` call | PASS (`call_4046227`) |
| 3 | exactly one confirmation request | PASS (`adk-4112b9ec`) |
| 4 | MCP execution count 0 | PASS (log unchanged at 4) |
| 5 | worker `finish_task` with cancelled outcome | PASS (`{"result": "cancelled"}`) |
| 6 | cancelled result reaches Root | PASS (#11) |
| 7 | Root does not re-delegate | PASS |
| 8 | Root produces a final cancellation response | PASS (#12) |

### Directly demonstrated by this run

- **Event #12 is the one that changed.** In R0-R01 that slot held
  `CALL worker id=call_2657493`, a second delegation. Here it is a
  user-facing cancellation message and the session ends.
- The session contains **two** branch values (`None`,
  `worker@call_1776588`) against three in R0-R01.
- The MCP tool executed **zero** times; `R0.1-R01` never appears in
  `mcp_tool_executions.jsonl`.
- The worker half behaved exactly as in R0-R01 — `finish_task` with
  `{"result": "cancelled"}` immediately after the rejection, no retry —
  confirming the R0 instruction still works with the Root instruction
  changed underneath it.

The user-visible shape is now the target one: one write attempt, one
confirmation, Reject, task ends.

### Progression across the three variants

| Variant | Worker after rejection                | Root after cancelled result |
| ------- | ------------------------------------- | --------------------------- |
| T2      | re-issues `write_value`               | never reached               |
| R0      | `finish_task({"result":"cancelled"})` | re-delegates                |
| R0.1    | `finish_task({"result":"cancelled"})` | responds and stops          |

Each variant closed the gap the previous one exposed, using instruction text
alone.

**Caveat: n=1.** R0.1-R01 is a single run. R0's worker semantics also held on
their first run and the failure simply moved up a level, and the retry
behaviour being suppressed is model-driven and varied between runs elsewhere
in this expedition (T2 produced concurrent pending calls in 2 of 6 runs).
`R0.1-R02` and `R0.1-R03` remain outstanding.

**R0.1-A01 (Accept regression) — PASS. No regression.** Session
`8ad59542-2353-462b-89d2-edd7f8fd0b59`, 12 events, exported to
`evidence/R0.1-A01_events.jsonl`, byte-identical to the live session (sha256
`4b875234e2618dafe2aedd10b9fa0280`). Pre-click count measured live.

This run existed because both R0 and R0.1 rewrote the *success* line as well
as adding rejection semantics: T2's "After the tool succeeds, complete the
task" became "If write_value succeeds, complete the task with a success
result". The Accept path had not been exercised under either instruction set,
so a regression here would have invalidated the approach regardless of how
well rejection behaved.

```
#2  16:14:53.148  root    branch=None                MODEL      CALL worker       id=call_994336
#3  16:14:56.049  worker  branch=worker@call_994336  MODEL      CALL write_value  id=call_1105826
#5  16:14:58.838  worker  branch=worker@call_994336  framework  CALL adk_request_confirmation
                             id=adk-ec29d328-d92c-496b-aab4-d3cb3b32ae6e -> call_1105826
#6  16:14:58.872  worker  branch=worker@call_994336  MODEL      TEXT "Please approve the tool execution ..."
      ---- MCP execution count for R0.1-A01: 0 (measured live, pre-click) ----
#7  16:47:22.713  user    branch=worker@call_994336  framework  RESP adk_request_confirmation
                             -> {"confirmed": true, "payload": {...}}
#8  16:47:22.749  worker  branch=worker@call_994336  framework  RESP write_value  id=call_1105826
                             -> {"content":[{"type":"text","text":"{... MCP_TOOL_EXECUTED ... R0.1-A01 ...}"}]}
#9  16:47:22.776  worker  branch=worker@call_994336  MODEL      CALL finish_task  id=call_3007243
                             args={"result": "Successfully wrote the value \"alpha\" under the run marker \"R0.1-A01\"."}
#10 16:47:26.474  worker  branch=worker@call_994336  framework  RESP finish_task -> "Task completed."
#11 16:47:26.492  user    branch=None                framework  RESP worker id=call_994336 -> success result
#12 16:47:26.526  root    branch=None                MODEL      TEXT "The value "alpha" has been successfully
                             written with the run marker "R0.1-A01"."
      ---- MCP execution count for R0.1-A01: 1 ----
```

| Check                                         | Result                                        |
| --------------------------------------------- | --------------------------------------------- |
| confirmation prompts = 1                      | PASS                                          |
| MCP executions = 1                            | PASS (log 4 → 5)                              |
| same pending call continued                   | PASS (`call_1105826` on both stub and result) |
| exactly one `write_value` call                | PASS                                          |
| `finish_task` succeeded with a success result | PASS (not `cancelled`)                        |
| worker returned to Root                       | PASS                                          |
| exactly one delegation                        | PASS                                          |
| Root produced a final response                | PASS                                          |

Both anticipated failure modes are ruled out: the rewritten worker
instruction routed success correctly rather than reporting `cancelled`, and
Root's four lines of cancellation semantics did not misfire on a success
result — it produced a success message and did not re-delegate. Two branch
values in the session.

The Accept path is structurally identical to T2's three Accept runs: one
`write_value` call continued under its own id, one execution, delegation id
re-used on the synthesized response.

Incidental observation, not a tested property: the confirmation sat pending
for **32 minutes** (16:14:58 to 16:47:22), far longer than any other run in
this expedition, and completed normally. A long-pending confirmation did not
time out or lose the pending call. Single observation.

**R0.1-R02 (Reject) — PASS, all eight conditions.** Session
`374bc5fa-b211-498c-a4a8-6f1ba5263b02`, 12 events, exported to
`evidence/R0.1-R02_events.jsonl`, byte-identical to the live session (sha256
`f39feae19800b8f9faa6ca96deeb4c59`). Pre-click count measured live.

```
#2  17:17:33.317  root    branch=None                MODEL      CALL worker       id=call_251898
#3  17:17:35.944  worker  branch=worker@call_251898  MODEL      CALL write_value  id=call_999487
#5  17:17:38.793  worker  branch=worker@call_251898  framework  CALL adk_request_confirmation
                             id=adk-814d47eb-e2c3-43e5-80bf-061ab3ef42f8 -> call_999487
      ---- MCP execution count for R0.1-R02: 0 (measured live, pre-click) ----
#7  17:18:45.984  user    branch=worker@call_251898  framework  RESP adk_request_confirmation
                             -> {"confirmed": false, "payload": {...}}
#8  17:18:45.997  worker  branch=worker@call_251898  framework  RESP write_value  id=call_999487
                             -> {"error": "This tool call is rejected."}
#9  17:18:46.022  worker  branch=worker@call_251898  MODEL      CALL finish_task  id=call_3077952
                             args={"result": "cancelled"}
#10 17:18:48.596  worker  branch=worker@call_251898  framework  RESP finish_task -> "Task completed."
#11 17:18:48.614  user    branch=None                framework  RESP worker id=call_251898
                             -> {"result": "cancelled"}
#12 17:18:48.645  root    branch=None                MODEL      TEXT "The operation was cancelled."
      ---- MCP execution count for R0.1-R02: 0 ----
```

### R0.1 Reject path: 2/2, every identifier differing

|                       | R0.1-R01                                                                             | R0.1-R02                       |
| --------------------- | ------------------------------------------------------------------------------------ | ------------------------------ |
| delegation call id    | `call_1776588`                                                                       | `call_251898`                  |
| `write_value` call id | `call_4046227`                                                                       | `call_999487`                  |
| confirmation id       | `adk-4112b9ec`                                                                       | `adk-814d47eb`                 |
| `finish_task` args    | `{"result": "cancelled"}`                                                            | `{"result": "cancelled"}`      |
| Root final text       | "The operation to write the value "alpha" with run marker "R0.1-R01" was cancelled." | "The operation was cancelled." |
| MCP executions        | 0                                                                                    | 0                              |
| branch values         | 2                                                                                    | 2                              |

Both decisive slots held again: **#9** is `finish_task` rather than a
re-issued `write_value`, and **#12** is a user-facing cancellation rather
than a second delegation. Every identifier is fresh between the two runs, so
the agreement is not an artefact of re-used ids.

Two observations about the *content* of the model's output, as distinct from
its behaviour:

- The `finish_task` argument was the literal string `"cancelled"` in both
  Reject runs, where the Accept run produced a full sentence. Consistent
  across two samples; too thin a base for a downstream consumer to depend on
  the exact string.
- Root's wording varied between the two runs while the behaviour did not.
  Expected for model-generated text, and worth separating from the
  structural result.

**R0.1-R03 (Reject) — PASS, all eight conditions, with a degraded model turn
mid-flight.** Session `6581ef28-aed7-4b10-91fa-8277e7f6ecc1`, events #1-#12,
exported to `evidence/R0.1-R03_events.jsonl`. Pre-click count measured live.

Correction to the original wording, which said the export was byte-identical
to the live session: that held when written, but the same session was later
re-used for an abandoned `R0.1-A02` turn and is now 18 events. The 12-event
export remains an exact record of the R0.1-R03 turn — its events hash to
`f505a3c39e0eadd071ad7ec129fcc236`, identical to the first 12 events of the
live session — and the full 18-event session is preserved separately as
`evidence/R0.1-R03-session-with-abandoned-A02_events.jsonl`. See the
abandoned-turn note after this entry.

```
#2  17:35:00.191  root    branch=None                 MODEL      CALL worker       id=call_2316437
#3  17:35:03.090  worker  branch=worker@call_2316437  MODEL      CALL write_value  id=call_1858985
#5  17:35:05.718  worker  branch=worker@call_2316437  framework  CALL adk_request_confirmation
                             id=adk-db8c2029-4697-4dd9-a2d7-9c31902300bd -> call_1858985
#6  17:35:05.745  worker  branch=worker@call_2316437  MODEL      ERROR MODEL_RETURNED_NO_CONTENT
                             "The model returned no content (finish_reason=STOP with empty parts)."
                             content={}, usageMetadata present
      ---- MCP execution count for R0.1-R03: 0 (measured live, pre-click) ----
#7  17:37:43.776  user    branch=worker@call_2316437  framework  RESP adk_request_confirmation
                             -> {"confirmed": false, "payload": {...}}
#8  17:37:43.793  worker  branch=worker@call_2316437  framework  RESP write_value  id=call_1858985
                             -> {"error": "This tool call is rejected."}
#9  17:37:43.811  worker  branch=worker@call_2316437  MODEL      CALL finish_task  id=call_1759296
                             args={"result": "cancelled"}
#10 17:37:46.694  worker  branch=worker@call_2316437  framework  RESP finish_task -> "Task completed."
#11 17:37:46.704  user    branch=None                 framework  RESP worker id=call_2316437
                             -> {"result": "cancelled"}
#12 17:37:46.726  root    branch=None                 MODEL      TEXT "The operation to write the value
                             "alpha" with run marker "R0.1-R03" was cancelled."
      ---- MCP execution count for R0.1-R03: 0 ----
```

Event #6 landed in the slot where the other R0.1 runs produced narration —
the MCP summarisation turn, which exists only because `McpTool` does not set
`skip_summarization` (see the post-hoc source reading in Interpretation).
The model was called and billed (`usageMetadata` present) and returned
`finish_reason=STOP` with empty parts; ADK recorded an error event.

It did not touch the confirmation path. The request `adk-db8c2029` retained
its `longRunningToolIds`, had zero responses, and still targeted
`call_1858985` at the moment of the pre-click measurement.

This makes the run **stronger** evidence than a clean one: the worker had an
error event in its context where narration normally sits, and still reached
`finish_task({"result": "cancelled"})` on its next model turn. The rejection
semantics survived a failed intermediate turn.

`MODEL_RETURNED_NO_CONTENT` had not appeared anywhere else in this
expedition. It is benign here, but that is one observation, and the same
turn was used to emit a *tool call* in 2 of 6 T2 runs — so no general claim
about it being harmless is made.

### R0.1 Reject path: 3/3, every identifier differing

|                       | R0.1-R01                  | R0.1-R02                  | R0.1-R03                          |
| --------------------- | ------------------------- | ------------------------- | --------------------------------- |
| delegation call id    | `call_1776588`            | `call_251898`             | `call_2316437`                    |
| `write_value` call id | `call_4046227`            | `call_999487`             | `call_1858985`                    |
| confirmation id       | `adk-4112b9ec`            | `adk-814d47eb`            | `adk-db8c2029`                    |
| `finish_task` args    | `{"result": "cancelled"}` | `{"result": "cancelled"}` | `{"result": "cancelled"}`         |
| MCP executions        | 0                         | 0                         | 0                                 |
| branch values         | 2                         | 2                         | 2                                 |
| anomalies             | —                         | —                         | `MODEL_RETURNED_NO_CONTENT` at #6 |

**Abandoned turn: `R0.1-A02` in session `6581ef28` — not a run.** The A02
prompt was issued into the session that already held R0.1-R03 rather than a
fresh one, so events #13-#18 are an Accept attempt appended to a session
already containing a rejected-and-cancelled turn. It was abandoned at the
pending confirmation with **0 executions**; `R0.1-A02` never appears in
`mcp_tool_executions.jsonl`. It does not count toward the Accept total,
because it does not replicate R0.1-A01's fresh-session conditions — both
agents carried the earlier cancellation in context. Preserved rather than
discarded, in `evidence/R0.1-R03-session-with-abandoned-A02_events.jsonl`.

Worth recording despite being abandoned, because it exercised a clause no
run had tested: both instructions end with "Attempt the write again only
after the user makes a new, explicit request." A new explicit request was
made at #13, and both agents correctly re-attempted — Root delegated
(`call_671132`), the worker called `write_value` (`call_1173887`) and a
confirmation was raised (`adk-0b4d0892`). So the earlier cancellation was
not treated as permanently binding. First and only evidence of that clause
working; one observation, from an abandoned turn.

**R0.1-A02b (Accept) — PASS. Fresh session, no regression.** Session
`215e6632-5dc7-46cd-ba97-20fa649600dd`, 12 events, exported to
`evidence/R0.1-A02b_events.jsonl`, byte-identical to the live session
(sha256 `c39d13c8ce8764ad62657b88f7bea82e`). Re-run of the abandoned A02 in a
clean session.

```
#2  18:03:39.583  root    MODEL      CALL worker       id=call_1616199
#3  18:03:42.571  worker  MODEL      CALL write_value  id=call_2153751
#5  18:03:45.155  worker  framework  CALL adk_request_confirmation adk-b9c30443-... -> call_2153751
#6  18:03:45.182  worker  MODEL      TEXT "I have requested to write ... approve or reject"
#7  18:04:33.781  user    framework  RESP adk_request_confirmation -> {"confirmed": true, ...}
#8  18:04:33.815  worker  framework  RESP write_value  id=call_2153751
                             -> {"content":[{"type":"text","text":"{... MCP_TOOL_EXECUTED ... R0.1-A02b ...}"}]}
#9  18:04:33.833  worker  MODEL      CALL finish_task  id=call_2361472
                             args={"result": "Success: Value 'alpha' was successfully written under run marker 'R0.1-A02b'."}
#10 18:04:36.950  worker  framework  RESP finish_task -> "Task completed."
#11 18:04:36.963  user    framework  RESP worker id=call_1616199 -> success result
#12 18:04:36.992  root    MODEL      TEXT "The value "alpha" has been successfully written ..."
```

One delegation, one `write_value` call continued under its own id, one
confirmation, one MCP execution (log 5 → 6), `finish_task` with a success
result, delegation id re-used on the synthesized response, Root responding
with success. Two branch values.

**Evidence-strength note: the pre-click count here is derived, not measured.**
The confirmation was answered before a live reading could be taken, so the
zero is reconstructed from timestamps — no execution is logged between the
confirmation request (18:03:45) and its response (18:04:33). Same weaker
standard as T1-A02 and T1-A03d. R0.1-A01's pre-click zero was measured live.

**R0.1-A03 (Accept) — PASS. Fresh session, no regression.** Session
`224ace85-539a-476c-8952-768e771d5c34`, 12 events, exported to
`evidence/R0.1-A03_events.jsonl`, byte-identical to the live session (sha256
`ae7b7bf1bb82556aa5b5d7e6b5386122`).

One delegation (`call_3066670`), one `write_value` call (`call_1635200`)
continued under its own id, one confirmation (`adk-12905cb2`), one MCP
execution (log 6 → 7), `finish_task` with `{"result": "Success: The value
'alpha' has been successfully written under run marker 'R0.1-A03'."}`,
delegation id re-used on the synthesized response, and Root closing with
"I have successfully written the value "alpha" with the run marker
"R0.1-A03"." Two branch values.

**Evidence-strength note: pre-click count derived, not measured.** The
attempt to read it live returned 1, meaning the confirmation had already
been answered. Reconstructed from timestamps instead: no execution is logged
between the confirmation request (18:13:05) and its response (18:13:37).

### R0.1 Accept path: 3/3

|                       | R0.1-A01                         | R0.1-A02b                                           | R0.1-A03                                                     |
| --------------------- | -------------------------------- | --------------------------------------------------- | ------------------------------------------------------------ |
| delegation call id    | `call_994336`                    | `call_1616199`                                      | `call_3066670`                                               |
| `write_value` call id | `call_1105826`                   | `call_2153751`                                      | `call_1635200`                                               |
| confirmation id       | `adk-ec29d328`                   | `adk-b9c30443`                                      | `adk-12905cb2`                                               |
| MCP executions        | 1                                | 1                                                   | 1                                                            |
| pre-click count       | **measured live**                | derived                                             | derived                                                      |
| branch values         | 2                                | 2                                                   | 2                                                            |
| `finish_task` args    | "Successfully wrote the value …" | "Success: Value 'alpha' was successfully written …" | "Success: The value 'alpha' has been successfully written …" |

Every success result is a full sentence, against the terse literal
`"cancelled"` in all three Reject runs — an asymmetry holding across all six
R0.1 runs.

**R0.1 status: 3/3 Reject PASS, 3/3 Accept PASS.** Both paths now meet the
three-run bar the earlier variants were held to, with every identifier
differing between runs.

Asymmetry in evidence strength worth carrying forward: all three Reject runs
have a **live** pre-click count, while only one of the three Accept runs
does — A02b and A03 were both answered before a reading could be taken, so
their zeros are reconstructed from timestamps. The Accept-side conclusion
therefore rests on a weaker measurement of the property that matters most,
namely that nothing executed while the confirmation was pending.

The `finish_task` argument was the literal string `"cancelled"` in all three
Reject runs. Three samples, still a model-chosen string rather than a
contract.

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

Untested alternatives that could equally explain the loop: ~~a
framework-level rejection-to-task-termination path that exists but was not
triggered here~~ — **eliminated by source reading, see below**;
model-specific retry behaviour that another model would not exhibit —
**still untested**.

### Post-hoc source reading (added after the expedition concluded)

Ground rule 9 barred reading ADK source during the runs. With the results
recorded and pushed, `google-adk` 2.6.3 was then read. This is a *source
reading checked against the traces*, not a run observation and not pure
inference; it belongs here rather than in Verified Findings because no
experiment tested it. Full version in `FINAL_REPORT.md` §10.

**The confirmation gate is identical in both tool types**
(`tools/function_tool.py:293-314`, `tools/mcp_tool/mcp_tool.py:349-365`):

```text
if require_confirmation:
    if not tool_context.tool_confirmation:
        tool_context.request_confirmation(hint=...)
        # FunctionTool ONLY: tool_context.actions.skip_summarization = True
        return {'error': 'This tool call requires confirmation, please approve or reject.'}
    elif not tool_context.tool_confirmation.confirmed:
        return {'error': 'This tool call is rejected.'}
return await self._invoke_callable(...)     # execute
```

**1. A rejection is an ordinary tool error response, not a control signal.**
It sets no `escalate`, no `finish_task`, no `end_invocation`.
`tool_confirmation.confirmed` is read in exactly four places in the package,
all tool implementations — `bash_tool.py:175`, `computer_use_tool.py:131`,
`function_tool.py:313`, `mcp_tool.py:364`. Nothing in `agents/llm/task/`,
`tools/agent_tool.py`, `workflow/_llm_agent_wrapper.py` or the flows
inspects it. **ADK 2.6.3 therefore has no rejection-terminates-task path**,
which is why the first untested alternative above is struck out: its absence
from the traces was not a sampling gap. The rejected call is closed, the
agent loop continues, and the next move is the model's.

**2. One `skip_summarization` asymmetry explains two behaviours previously
recorded without explanation.** `FunctionTool` sets it on the *pending*
branch (`function_tool.py:306`); `McpTool` never sets it; neither sets it on
the *rejected* branch. It suppresses the follow-up model call that would
otherwise summarise a tool response. Checked against all 14 confirmation
runs:

| Tool type                     | pending stub `skip_summarization` | model turn while pending |
| ----------------------------- | --------------------------------- | ------------------------ |
| FunctionTool (C0, T1), 7 runs | `True`                            | no, 7/7                  |
| MCP (C1, T2), 7 runs          | unset                             | yes, 7/7                 |

- Model narration at a pending confirmation, seen only in C1 and T2, is that
  extra summarisation turn.
- Concurrent pending confirmations are the same turn used differently: it is
  a full LLM turn, so the model can emit another `write_value` call instead
  of text. T2-A03 and T2-R02 show `CALL:write_value` where the other five MCP
  runs show `TEXT`. This is why they were reachable in the MCP path and never
  appeared in T1.
- The rejected branch sets `skip_summarization` in neither tool type, so a
  model turn always follows a rejection — confirmed 6/6, every frozen Reject
  run has a model-authored fresh `CALL:write_value` immediately after the
  rejected response.

The reading retrodicts 14/14 runs. It was not tested by varying the code;
doing so — for instance setting `skip_summarization` on the MCP pending
branch, or varying the worker instruction — would be a separate controlled
experiment. The instruction-side half of the inference above remains
untested; the framework-side half is now settled.
