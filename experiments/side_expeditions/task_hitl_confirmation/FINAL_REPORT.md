# Final Report — ADK Task Mode + Native Tool Confirmation

Side expedition conclusion. Structure follows §13 of the brief.

Companion documents: `README.md` (question, protocol, checkpoints),
`RESULTS.md` (per-run findings and raw traces), `evidence/` (25 session
exports, two execution logs, three environment snapshots).

---

## 1. Exact environment

| Item                    | Value                                                                              |
| ----------------------- | ---------------------------------------------------------------------------------- |
| `google-adk`            | **2.6.3** (pinned; never upgraded or downgraded)                                   |
| `google-genai`          | 2.17.0                                                                             |
| `mcp`                   | 1.29.0 — added for Phase 2 only; absent for all of Phase 1                         |
| Python                  | 3.13.9 (`.venv` at repo root)                                                      |
| pydantic / fastapi      | 2.13.4 / 0.141.1                                                                   |
| Model                   | `gemini-3.5-flash`                                                                 |
| Provider                | Gemini API (`GOOGLE_GENAI_USE_ENTERPRISE=0`, `GOOGLE_API_KEY`)                     |
| OS                      | Windows 11, PowerShell                                                             |
| ADK Web command         | `adk web experiments/side_expeditions/task_hitl_confirmation/variants --port 8932` |
| Phase 1 code under test | commit `acb44e8`                                                                   |

The Phase 2 dependency change was `pip install "google-adk[mcp]==2.6.3"`,
taking the constraint from ADK itself (`mcp>=1.24,<2`). Verified additive by
dry-run before installing and by diff after: six packages added (`mcp`,
`httpx-sse`, `pydantic-settings`, `PyJWT`, `pywin32`, `sse-starlette`), none
upgraded, none removed. Three snapshots bracket it:
`environment_phase1.txt`, `environment_phase2_pre.txt`,
`environment_phase2_post.txt`. Phase 1 variant file hashes were re-checked
after the install and still matched.

---

## 2. Result matrix

| Variant | Composition                                 | Required              | Achieved             |
| ------- | ------------------------------------------- | --------------------- | -------------------- |
| C0      | Root + confirmed FunctionTool               | ≥1 Accept + ≥1 Reject | **1 + 1, both PASS** |
| T0      | Root → task worker, no confirmation         | 3 clean runs          | **3/3 PASS**         |
| T1      | Root → task worker + confirmed FunctionTool | 3 Accept + 2 Reject   | **3/3 + 2/2 PASS**   |
| C1      | Root + confirmed `McpToolset`               | ≥1 Accept + ≥1 Reject | **1 + 1, both PASS** |
| T2      | Root → task worker + confirmed `McpToolset` | 3 Accept + 2 Reject   | **3/3 + 2/2 PASS**   |

Runs not counted toward those totals: **5 INVALID** (all provider 503),
**1 PARTIAL** (A–K passed, 503 at L), **1 exceptional trial** (T1-X01),
**1 discarded session** (duplicate marker, no click).

Per-run detail is the table at the top of `RESULTS.md`.

---

## 3. First missing checkpoint, per failed variant

**None. No variant failed.**

Every required run reached its final checkpoint — checkpoint 7 for the
Root-level variants (C0, C1) and checkpoint L for the task variants (T1, T2).
There is no first-missing-checkpoint to report, and therefore no
confirmation-continuation failure boundary of the kind this expedition set
out to locate.

The only runs that stopped early stopped on provider 503s, outside ADK's
execution path:

| Run               | Stopped at                       | Cause                            |
| ----------------- | -------------------------------- | -------------------------------- |
| T0-02 attempt 1   | Root's first model call          | 503                              |
| T1-A02 attempt 1  | Root's first model call          | 503                              |
| T1-A02 attempt 2  | after K, at L                    | 503 on Root's closing model call |
| T1-A03a attempt 1 | after A, inside the child branch | 503                              |
| T1-A03a attempt 2 | Root's first model call          | 503                              |
| T2-A01 attempt 1  | Root's first model call          | 503                              |

All are `google.genai.errors.ServerError: 503 UNAVAILABLE`. Across the whole
server log, `503` appears 13 times and `429`/`RESOURCE_EXHAUSTED`/`quota`
zero times — capacity, not quota.

---

## 4. Relevant raw event sequences

Full traces are in `RESULTS.md` and `evidence/`. The two that carry the
answer:

**T1-A01 — task + confirmed FunctionTool, Accept** (11 events)

```
#2  root    branch=None                 CALL worker       id=call_1728652
#3  worker  branch=worker@call_1728652  CALL write_value  id=call_902796
#4  worker  branch=worker@call_1728652  RESP write_value  id=call_902796  [pending stub]
#5  worker  branch=worker@call_1728652  CALL adk_request_confirmation adk-bbabfe4e-...
      ---- tool execution count: 0 (measured live) ----
#6  user    branch=worker@call_1728652  RESP adk_request_confirmation {"confirmed": true}
#7  worker  branch=worker@call_1728652  RESP write_value  id=call_902796  [REAL RESULT]
#8  worker  branch=worker@call_1728652  CALL finish_task  id=call_2088500
#9  worker  branch=worker@call_1728652  RESP finish_task  "Task completed."
#10 user    branch=None                 RESP worker       id=call_1728652
#11 root    branch=None                 TEXT
      ---- tool execution count: 1 ----
```

**T2-A01 — task + confirmed MCP, Accept** (12 events) — same shape, with the
tool reached over MCP:

```
#2  root    CALL worker       id=call_1317118
#3  worker  CALL write_value  id=call_1682897        branch=worker@call_1317118
#5  worker  CALL adk_request_confirmation adk-db1901eb-...
      ---- MCP execution count: 0 (measured live) ----
#7  user    RESP adk_request_confirmation {"confirmed": true}   branch=worker@call_1317118
#8  worker  RESP write_value  id=call_1682897 -> {"content":[{"type":"text", ...
                                                  MCP_TOOL_EXECUTED ... T2-A01 ...}]}
#9  worker  CALL finish_task  id=call_2288846
#10 worker  RESP finish_task  "Task completed."
#11 user    RESP worker       id=call_1317118
#12 root    TEXT
      ---- MCP execution count: 1 ----
```

In both, the post-Accept `FunctionResponse` carries the **same call id** as
the pending one — continuation, not re-issue.

---

## 5. Tool-side execution counts

Two independent channels. `hitl_evidence.py` records from inside the
FunctionTool body in the agent process; `mcp_evidence.py` records from inside
the MCP server subprocess. Neither is a callback or wrapper, so neither can
perturb ADK's flow.

```
FunctionTool  C0-A01 1, T0-01 1, T0-02 1, T0-03 1,
              T1-A01 1, T1-A02 2, T1-A03c 1, T1-A03d 1     (9 total)
MCP           C1-A01 1, T2-A01 1, T2-A02 1, T2-A03 1       (4 total)
```

Every marker counts exactly **1** except `T1-A02`, whose two lines belong to
two separate sessions run under a re-used marker; attribution by session
window gives one execution each.

- **No run executed the tool body twice.**
- **No Reject run executed it at all** — the seven Reject markers appear
  nowhere in either log.
- Counts were taken before and after every confirmation click. Live
  measurements: C0-A01, C0-R01, C1-A01, C1-R01, T1-A01, T2-A01, T2-A02,
  T2-A03, T2-R01, T2-R02. Derived from timestamps (weaker, labelled per
  run): T1-A02, T1-A03d.

Evidence volume: 25 session exports, 249 events total.

---

## 6. Repeatability

| Behaviour                                     | Runs          | Result                  |
| --------------------------------------------- | ------------- | ----------------------- |
| Task lifecycle without confirmation (T0)      | 3             | identical structure 3/3 |
| Task + FunctionTool confirmation, Accept (T1) | 3             | A–L complete 3/3        |
| Task + MCP confirmation, Accept (T2)          | 3             | A–L complete 3/3        |
| Rejection prevents execution                  | 7             | zero executions 7/7     |
| Reject → model re-issues under a new id       | 5 frozen runs | 5/5                     |
| Concurrent pending confirmations              | 6 T2 runs     | 2/6                     |

T0's three runs reduce to a byte-identical
`author:kind:name:model-or-framework` sequence. T1's and T2's Accept runs
agree on every structural property — one tool call, continued under its own
id, Accept landing on the child branch, delegation id re-used on the
synthesized response — while every id and branch differs between runs, so the
agreement is not an artefact of re-used identifiers.

---

## 7. Verified findings

Directly demonstrated by runs. No inference.

1. **Native `require_confirmation=True` works in this environment.** The tool
   body does not execute while a confirmation is pending; the pre-Accept
   response is an error stub, not a result (C0, C1, T1, T2).
2. **Confirmation continuation preserves the pending call.** After Accept,
   the `FunctionResponse` carries the *original* call id in every Accept run
   across all four confirmation variants. Contrast: a model re-issue always
   produces a new id.
3. **The task lifecycle completes and returns control to Root** —
   delegation via an agent-shaped FunctionCall, a bounded child branch keyed
   to the delegation id, `finish_task`, then a synthesized response re-using
   the delegation id whose payload is byte-identical to the `finish_task`
   argument and which carries no model attribution (T0 3/3, T1 3/3, T2 3/3).
4. **Task mode composed with native confirmation works, for both
   transports.** T1 (FunctionTool) and T2 (`McpToolset`) each completed every
   checkpoint A–L in 3/3 Accept runs, executing the tool body exactly once
   per run. Confirmation requests in task mode are authored by the worker on
   the child branch, and the Accept re-enters on that same branch.
5. **Rejection prevents execution and terminates the pending call**, with
   `{"error": "This tool call is rejected."}` against its original id — 7/7
   Reject runs, zero executions, both transports, Root-level and task-level.
6. **After a rejection the model re-issues the call under a new id** — 5/5
   frozen single-rejection runs, across both transports and both
   compositions. Nothing in the variant code retries, and ADK re-executes
   nothing; the new call originates in a model turn (`modelVersion` and
   `usageMetadata` present).
7. **In task mode, rejection does not end the task.** `finish_task` was
   never called and no result returned to Root in any task-mode Reject run
   (T1-A03e, T1-R02, T2-R01, T2-R02). Control stayed inside the child branch.
   T1-X01 showed the loop is escapable by accepting: on the fourth cycle the
   accepted call executed once and the task completed normally.
8. **A task worker can hold multiple confirmations pending simultaneously**
   (T2-A03, T2-R02). The model issued a second `write_value` call ~50–60 ms
   after the first confirmation request, with nothing rejected.
9. **Concurrent pending confirmations are independent.** Accepting one
   executed exactly that call once and left the other a pending stub
   (T2-A03); rejecting one terminated only that call and left its sibling
   untouched (T2-R02). No cascade in either direction. In T2-A03 the task
   completed normally with a confirmation still outstanding.
10. **The MCP result arrives in an envelope**:
    `{"content": [{"type": "text", "text": "<json>"}], "isError": false}`,
    with the tool's return value JSON-encoded inside `content[0].text`,
    where the FunctionTool variants return a plain dict.
11. **Model narration at a pending confirmation is unreliable and inert.**
    C1-A01 produced "I approve this tool call" while the confirmation was
    still pending and nothing had been approved; C1-R01 produced "Please
    approve the tool call". Both are model-authored, neither affected
    execution.

### Answer to the question posed

> In `google-adk` 2.6.3 with `gemini-3.5-flash`, a `mode="task"` LlmAgent
> owning a tool with `require_confirmation=True` paused for confirmation,
> continued the *same* pending call after Accept, received the tool result,
> completed its task via `finish_task`, and returned the result to Root — in
> 3/3 Accept runs with a FunctionTool and 3/3 with a native `McpToolset`,
> executing the tool body exactly once per run. Rejecting prevented execution
> in 7/7 runs.

**This is a negative result against the production hypothesis: the
expedition did not reproduce the CIA failure in any of the five variants,
including T2, the composition closest to production.**

Per the brief's decision matrix, the entries "T0 PASS, T1 FAIL",
"C0 PASS, C1 FAIL" and "T1 PASS, T2 FAIL" all fail to apply. The matrix's
remaining conclusion holds: **the production failure must involve another
integration variable** beyond task mode, native confirmation, MCP transport,
or their composition.

---

## 8. Hypotheses and inferences

Explicitly *not* findings. None is demonstrated by a run.

**Inference — task mode is a bounded child branch, not a conversational
handover.** Root makes an agent-shaped tool call and stays owner of the turn;
the child executes on a branch keyed to the delegation call id; `finish_task`
closes it; ADK synthesises the response satisfying the original delegation
call. Best supported by the synthesis evidence (id re-use, byte-identical
payload, no model attribution). Weakest link: that `finish_task` *causes*
the branch to close — the traces show it preceding the return, not causing
it, and no run omitted `finish_task`, so causation is not isolated.

**Inference — the reject-then-retry loop follows from the instruction, not
the framework.** The worker instruction under test is:

```
When asked to write a value, call write_value with the exact value and run marker provided.
After the tool succeeds, complete the task.
```

It authorises completion only *after success* and is silent on failure, so on
rejection the model has no instructed route to `finish_task` and retries
instead. Untested alternatives that would explain the same traces: a
framework-level rejection-to-task-termination path that exists but was never
triggered here; model-specific retry behaviour another model would not
exhibit. The experiment did not vary the instruction — ground rule 9 barred
changing it mid-expedition.

**Both have since been addressed, after this report was first written.** The
framework-level alternative is eliminated by the source reading in §10: no
such path exists in 2.6.3. The inference itself was then tested directly by
the follow-on experiments in §11, which varied the instruction and found the
retry stops — leaving only the model-specific alternative untested, since
every run used one model.

**Consequence, if that inference holds** (also inference): at Root level a
post-rejection retry merely leaves a pending prompt, whereas inside task mode
it means control never returns to Root. T2-R02 showed the accumulation can
compound — one rejection produced two new calls and left three confirmations
outstanding.

**Open question, not investigated.** Whether ADK provides any path by which a
rejection terminates a task and returns control to Root. Its absence from
these traces is not evidence that none exists. Answering it means reading ADK
source, which ground rule 9 deferred until the expedition concluded — that
constraint is now lifted.

---

## 9. Method notes and limitations

- **Single model, single provider.** All 26 sessions ran on
  `gemini-3.5-flash` via the Gemini API. Model-dependent behaviours —
  the retry loop, concurrent calls, narration — may not generalise.
- **Provider instability shaped the run schedule.** 13 × 503 across the
  session; six runs were invalidated by them. None altered event structure
  or execution counts, only timing and completion.
- **Two pre-click counts are derived, not measured** (T1-A02, T1-A03d),
  labelled as such per run. The other ten are live measurements.
- **`author="user"` does not prove a UI click.** ADK labels UI-originated
  and API-posted confirmation responses identically. What the event record
  *can* rule out is the model, via `modelVersion`/`usageMetadata`. This
  mattered once, in C1-A01.
- **T2 shares C1's MCP server file**, so its log lines read `variant=c1`.
  Attribution throughout is by `run_marker`.
- **One marker collision** (`T1-A02`, three sessions) required timestamp
  attribution; the unique-marker-per-attempt rule was adopted afterwards.
- **Ground rules held throughout**: no `AgentTool` written by hand, no
  `ResumabilityConfig`, no retries, no callbacks, no custom confirmation
  code, no prompt tricks, no ADK version change, no production code or
  prompts. Failures were frozen and exported, never repaired. Instructions
  were kept minimal.

No workaround is proposed here; none was requested.

---

## 10. Post-hoc source explanation

**Added after the expedition concluded.** Ground rule 9 barred reading ADK
source during the runs, to keep explanation from contaminating observation.
Nothing in §§1–9 depends on this section. Everything here is a reading of
`google-adk` 2.6.3 source, checked against the traces already recorded.

### The confirmation gate

Both tool types implement the same three-way gate inside `run_async`
(`tools/function_tool.py:293-314`, `tools/mcp_tool/mcp_tool.py:349-365`):

```python
if require_confirmation:
    if not tool_context.tool_confirmation:
        tool_context.request_confirmation(hint=...)
        # FunctionTool ONLY: tool_context.actions.skip_summarization = True
        return {'error': 'This tool call requires confirmation, please approve or reject.'}
    elif not tool_context.tool_confirmation.confirmed:
        return {'error': 'This tool call is rejected.'}
return await self._invoke_callable(...)     # execute
```

This accounts for finding 1 (the body cannot run while pending — the gate
returns before `_invoke_callable`) and finding 5 (the rejection message).

### Why a rejection does not end a task

**A rejection is an ordinary tool error response, not a control signal.** It
sets no `escalate`, no `finish_task`, no `end_invocation` — it returns a dict
with an `error` key, exactly like any other tool failure.

`tool_confirmation.confirmed` is read in only four places in the entire
package, all of them tool implementations:
`bash_tool.py:175`, `computer_use_tool.py:131`, `function_tool.py:313`,
`mcp_tool.py:364`. Nothing in the task machinery
(`agents/llm/task/`, `tools/agent_tool.py`, `workflow/_llm_agent_wrapper.py`)
or in the flows inspects it.

So **ADK 2.6.3 has no rejection-terminates-task path.** This answers the open
question left in §8: its absence from the traces was not a sampling gap. A
rejected call is closed, the agent loop continues, and what happens next is
entirely the model's choice. Findings 6 and 7 follow: the model gets a turn,
and with an instruction that authorises completion only after success it
retries rather than calling `finish_task`.

### Why the MCP variants narrated and the FunctionTool variants did not

`FunctionTool` sets `skip_summarization = True` on the *pending* branch
(`function_tool.py:306`). `McpTool` never sets it at all. Neither sets it on
the *rejected* branch. `skip_summarization` suppresses the follow-up model
call that would otherwise summarise a tool response.

That single asymmetry predicts behaviour we had recorded as unexplained.
Checked against all 14 confirmation runs:

|                                | pending stub `skip_summarization` | model turn while pending? |
| ------------------------------ | --------------------------------- | ------------------------- |
| FunctionTool (C0, T1) — 7 runs | `True`                            | **no**, 7/7               |
| MCP (C1, T2) — 7 runs          | *unset*                           | **yes**, 7/7              |

- Finding 11 (model narration at a pending confirmation, seen only in C1 and
  T2) is that extra summarisation turn.
- Finding 8 (concurrent pending confirmations, 2 of 6 T2 runs) is the same
  turn used differently: it is a full LLM turn, so the model can emit another
  `write_value` call instead of text. In T2-A03 and T2-R02 it did exactly
  that — `['CALL:write_value']` where the other five MCP runs show
  `['TEXT']`. Concurrent pending confirmations are therefore reachable in the
  MCP path and not in the FunctionTool path, which is why T1 never showed
  them.
- The rejected branch sets `skip_summarization` in **neither** tool type, so
  a model turn always follows a rejection. Confirmed 6/6: in every frozen
  Reject run the event after the rejected response is model-authored and is
  a fresh `CALL:write_value`. This is why finding 6 held across both
  transports.

### Status of this section

This is a source reading that retrodicts 14/14 runs, not an experimental
result. It was not tested by varying the code — doing so (for instance
setting `skip_summarization` on the MCP pending branch) would be a separate
controlled experiment. What this section settles is **the framework side**
of the §8 inference: ADK genuinely leaves the post-rejection decision to the
model. The instruction side was untested when this was written; §11 tests
it.

---

## 11. Follow-on experiments R0 and R0.1 — semantic rejection handling

**Added after §§1–10.** These are follow-on experiments, not part of the
original expedition, and they change none of its results. They test the §8
inference directly: that the retry loop follows from the worker instruction
having no defined completion path after a rejection.

Both copy the T2 topology — Root → `mode="task"` worker → native
`McpToolset(require_confirmation=True)` → the same shared MCP server — and
change **only instruction text**. Verified by comparing 18 model-visible and
wiring fields per step: R0 differs from T2 in `worker.instruction` alone;
R0.1 differs from R0 in `root.instruction` alone. No callbacks, state flags,
state machine, retry guards, `ResumabilityConfig`, structured task output or
MCP change; `planner`, `output_schema` and `output_key` unset on both agents
throughout.

### Result matrix

| Variant       | Change                   | Reject                                                                                            | Accept       |
| ------------- | ------------------------ | ------------------------------------------------------------------------------------------------- | ------------ |
| T2 (baseline) | —                        | worker re-issues `write_value`; `finish_task` never called; control never returns to Root         | 3/3 PASS     |
| R0            | worker rejection path    | worker calls `finish_task({"result":"cancelled"})` and does not retry — but **Root re-delegates** | not run      |
| R0.1          | + Root cancellation path | **3/3 PASS** — one attempt, one confirmation, task ends                                           | **3/3 PASS** |

R0-R01 is recorded at two scopes in `RESULTS.md`: PASS per-delegation (all
ten acceptance criteria within delegation 1), FAIL per-session under the R0
brief's own definition, since a second `write_value` call did appear after
the Reject. Both are recorded because they answer different questions.

### What the runs demonstrate

- **The §8 inference holds.** In all five original Reject runs the event
  after `{"error": "This tool call is rejected."}` was a fresh
  `CALL:write_value`. Under the R0 worker instruction it is
  `CALL:finish_task` with a cancelled result. Instruction text alone changed
  the worker's interpretation of a rejection.
- **The retry relocated before it disappeared.** R0 fixed the worker and
  exposed the same gap one level up: Root received `{"result": "cancelled"}`
  and re-delegated the identical request, byte-identical `args.request`,
  producing a second child branch and a second confirmation. R0.1's Root
  instruction closed that.
- **Neither path regressed.** R0.1 Accept runs are structurally identical to
  T2's: one `write_value` call continued under its own id, one MCP
  execution, delegation id re-used on the synthesized response.
- **Reject held through a degraded turn.** R0.1-R03 hit
  `MODEL_RETURNED_NO_CONTENT` on the MCP summarisation turn — the turn §10
  identifies as existing only because `McpTool` omits `skip_summarization` —
  and still reached `finish_task` with a cancelled result on the next model
  turn.
- **Concurrent pending confirmations did not recur.** The behaviour seen in
  2 of 6 T2 runs appeared in none of the six R0.1 runs. Not claimed as
  caused by the instruction change; six runs is too few, and the behaviour
  was intermittent in T2 as well.

### Limits

- **Single model and provider**, as throughout: `gemini-3.5-flash` via the
  Gemini API. The behaviour being suppressed is model-driven, so this does
  not transfer to another model without re-testing.
- **`"cancelled"` is a model-chosen string, not a contract.** All three
  Reject runs produced exactly `{"result": "cancelled"}` and all three
  Accept runs produced a full sentence, but nothing enforces either. A
  consumer keying on that string would be depending on unenforced model
  behaviour. Introducing a structured task output was explicitly out of
  scope for R0/R0.1.
- **Uneven measurement strength on the Accept side.** All three Reject runs
  have a live pre-click execution count; only one of the three Accept runs
  does. A02b and A03 were answered before a reading could be taken, so their
  zeros are reconstructed from timestamps.
- **One abandoned turn is preserved and excluded.** An `R0.1-A02` attempt
  was issued into the session already holding R0.1-R03 rather than a fresh
  one; it executed nothing and does not count toward the Accept total. It
  did supply the only evidence for the final clause of both instructions —
  on a new explicit user request, both agents correctly re-attempted rather
  than treating the earlier cancellation as permanently binding. One
  observation, from an abandoned turn.
- **Not a production solution.** R0/R0.1 establish that prompt semantics
  alone are sufficient to make Reject terminal in this composition. Whether
  that is *robust enough* for production — against instruction drift, model
  changes, or adversarial inputs — is not tested here, and mechanisms such
  as structured task output or callback-enforced cancellation were
  deliberately excluded.

### Relation to the original conclusion

§7 concluded that the production failure must involve another integration
variable, since all five variants passed. That stands. R0/R0.1 do not
identify the production failure; they address the separate usability problem
the expedition surfaced along the way — that a rejected confirmation left the
task uncompleted and control never returned to Root.
