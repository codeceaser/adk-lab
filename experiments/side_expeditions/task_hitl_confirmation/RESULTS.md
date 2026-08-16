# Results: ADK Task Mode + Native Tool Confirmation

Environment: `google-adk` 2.6.3, `google-genai` 2.17.0, Python 3.13.9,
`gemini-3.5-flash` via Gemini API. See `README.md`.

Code under test: commit `acb44e8` (see `evidence/test_start_revision.txt`).

| Variant | Run | Accept/Reject | Last checkpoint | Tool count | Result |
| ------- | --- | ------------- | --------------- | ---------: | ------ |
| C0 | C0-A01 | Accept | 7 — Root continues | 0 before / 1 after | PASS |
| C0 | C0-R01 | Reject | 5 — rejection honoured, tool not executed | 0 before / 0 after | PASS |

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

## Failures Observed

_(none yet)_

## Interpretation

_(empty — anything here is explicitly labelled as inference, never mixed into
Verified Findings)_
