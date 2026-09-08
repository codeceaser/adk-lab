# Side Expedition: Thought Self-Conditioning

## Question being tested

Does replaying human-readable `model_exposed_thought` text materially change
the model's **next** reasoning/action when all other prior-state information is
held constant?

This is **not** a chain-of-thought experiment, and the exposed text is not
"full chain of thought" — it is a `thought_summary` the model chose to expose.

### What the previous expedition established

`thought_context_replay` (harness `7e72dee`, evidence `fa019fe`) established
that with `include_thoughts=True` a thought summary appears both in the Event
and in the subsequent `LlmRequest`, and that `thought_signature` is present in
both modes. This expedition isolates the effect of the readable summary itself.

## Design

One **frozen** prior trajectory is replayed as two continuation requests:

| Arm | Contents sent |
| --- | --- |
| **R — replay** | user text + `thought_summary` text + `function_call`(+signature) + `function_response` |
| **S — strip** | user text + `function_call`(+signature) + `function_response` |

The first model step is **not regenerated per arm**. It is read from committed
evidence, so no stochastic first-step variation enters the comparison. Both
arms are built by the same builder from the same frozen record; ARM S is ARM R
minus the readable thought parts, and nothing else.

Held identical across arms: `function_call` id and args, the exact recorded
`thought_signature` bytes, `function_response` and its id, system instruction,
tool declarations, model, backend, generation config.

Neither arm sets `temperature` or `seed`. `GenerateContentConfig` exposes both,
but a seed was deliberately **not** added: it would suppress the run-to-run
variation this experiment is measuring, and adding it to one arm only would
break the control.

## Frozen specimens

Provenance is recorded on every evidence row.

| | Primary | Secondary |
| --- | --- | --- |
| `specimen_id` | `COT-03-ON-01#2` | `COT-02-ON-01#2` |
| `source_commit` | `fa019fe267a5f1b931b9d0d82d6aa115541a85f7` | same |
| `source_file` | `thought_context_replay/evidence/COT-03-ON-01_llm_requests.jsonl` | `…/COT-02-ON-01_llm_requests.jsonl` |
| `source_run_id` | `COT-03-ON-01` | `COT-02-ON-01` |
| `source_request_index` | 2 | 2 |
| Path | ambiguous lookup, `status=not_found` | explicit `AU-CARDS` lookup, successful |

The primary specimen's frozen state is:

```
user   : "Tell me about Cards."
model  : Part(text=<2390 chars>, thought=True)
         Part(function_call={id: call_139767, name: get_assessment_unit,
                             args: {assessment_unit_id: "Cards"}},
              thought_signature=<3199 bytes>)
user   : Part(function_response={id: call_139767, name: get_assessment_unit,
               response: {status: "not_found", assessment_unit_id: "Cards", …}})
```

The exposed thought text is not rewritten, paraphrased, shortened or
normalized. The source evidence files are opened read-only and never modified.

Note the part layout, which is what makes the strip surgically clean: the
readable thought text and the `function_call` are **separate parts**, and the
3199-byte signature sits on the `function_call` part. Removing the thought text
therefore removes no signature and no action.

## Model invocation

`Gemini.generate_content_async(llm_request, stream=False)` — the narrowest
supported ADK 2.6.3 entry point that accepts a constructed `LlmRequest`. The
adapter is obtained via `root_agent.canonical_model`, so it is the same adapter
and backend the lab uses. No provider or client path is bypassed.

Verified in ADK 2.6.3 source before implementing:

- `_preprocess_request` (`google_llm.py:506`) touches only `inline_data`,
  `file_data`, `config.labels` and computer-use tools. It does not read or
  modify `thought`, thought text, or `thought_signature`.
- The one thought-exclusion in `google_llm.py:665` lives inside
  `_build_response_log`, a **response logging** helper. It is not in the send
  path and cannot affect outgoing contents.
- `generate_content_async` mutates the request in place (nulls `config.labels`
  on the Gemini API backend, merges tracking headers), so a **fresh request is
  built for every continuation** rather than reused.

## Direct API send verification

Every continuation records `request_before_send` and `request_after_send`. The
latter is the same object after the adapter has run, so the pair proves
mechanically what the adapter did rather than inferring it from the builder.

Expected and observed:

| Arm | thought text | signature | adapter changed contents |
| --- | --- | --- | --- |
| replay | present | present | no |
| strip | absent | present | no |

## Behavioral classification

The immediate **next** action only, classified mechanically:

| Category | Rule |
| --- | --- |
| `RETRY_SAME_TOOL` | one `function_call`, same name, args equal to the frozen call |
| `RETRY_MUTATED_ARGUMENT` | one `function_call`, same name, different args |
| `CALL_OTHER_TOOL` | one `function_call`, different name |
| `ASK_CLARIFICATION` | no `function_call`, non-empty text containing `?` |
| `DIRECT_ANSWER` | no `function_call`, non-empty text without `?` |
| `OTHER` | no `function_call`, no text |
| `NEEDS_HUMAN_REVIEW` | more than one `function_call` |

The tool categories are structural. The `ASK_CLARIFICATION` / `DIRECT_ANSWER`
split is a fixed **lexical** rule, not a semantic judgement — no model
adjudicates it. The complete raw response is preserved in the evidence, so the
experiment owners can re-classify under any other rule.

No category is treated as better than another.

## Validation

`tests/test_thought_self_conditioning.py` runs before any model call and proves
the nine required properties: arms identical after removing the intended
difference (with a non-vacuous check that the difference exists), byte-identical
`thought_signature` (compared by SHA-256), identical `function_call` /
`function_response`, unchanged call and response IDs, identical tool
declarations and system instruction, strip removing only readable thought
parts, no signature-, call- or response-bearing part ever removed, and the
frozen source file unchanged (SHA-256 before/after).

The machine-readable proof is written to
`evidence/COT-03-ON-01-2_arm_diff.json`, and the probe **refuses to make model
calls** if `arms_identical_after_removing_thought_text` is false.

## How to run

Arm-difference proof only, no model calls:

```powershell
.venv\Scripts\python.exe experiments\side_expeditions\thought_self_conditioning\run_replay_probe.py --specimen primary --arm-diff-only
```

Primary specimen, 20 continuations per arm:

```powershell
.venv\Scripts\python.exe experiments\side_expeditions\thought_self_conditioning\run_replay_probe.py --specimen primary --reps 20
```

Secondary specimen:

```powershell
.venv\Scripts\python.exe experiments\side_expeditions\thought_self_conditioning\run_replay_probe.py --specimen secondary --reps 10
```

Tests:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_thought_self_conditioning.py -q
```

## Evidence files

| File | Contents |
| --- | --- |
| `evidence/<specimen>_arm_diff.json` | arm-difference proof, no model calls |
| `evidence/<specimen>_continuations_<UTC>.jsonl` | one row per continuation |

Each continuation row carries `run_id`, `specimen_id`, provenance
(`source_commit` / `source_file` / `source_run_id` / `source_request_index`),
`arm`, `rep`, `model`, `backend`, `latency_ms`, `classification`,
`request_before_send`, `request_after_send`, and the full `response` including
`raw_responses`, `finish_reason` and `usage_metadata`.

## Scope

This harness reports raw counts. It does not conclude whether thought replay is
good or bad, does not recommend or implement any production callback, does not
alter the main agent, and claims no causality beyond the single controlled
variable. Small-N results carry no statistical significance claim.
