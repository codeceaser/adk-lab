# Side Expedition: Thought Context Replay

## Question being tested

When `include_thoughts=True`, do human-readable `thought_summary` parts become
part of subsequent LLM `request_context`, and therefore have the opportunity to
influence later reasoning?

Separately, and independently: is `thought_signature` preserved regardless of
whether human-readable thought text is replayed?

This is **not** a chain-of-thought capture experiment. The vocabulary used
throughout is `model_exposed_thought`, `thought_summary`, `thought_signature`,
and `request_context`.

### The three things being distinguished

1. **`model_exposed_thought`** — `Part(thought=True, text=...)`
2. **`thought_signature`** — opaque Gemini reasoning-continuity metadata
   (`Part.thought_signature`, `Optional[bytes]`)
3. **ordinary `request_context`** — user messages, assistant messages,
   `function_call`, `function_response`

### Outcomes to adjudicate

The probe is built to separate these three, not to decide between them:

| | `thought_summary` in Event | `thought_summary` in next LlmRequest |
| --- | --- | --- |
| **A** | present | absent |
| **B** | present | present |
| **C** | absent | `thought_signature` present, thought text absent |

**C** would be the cleanest separation of reasoning continuity from
observability. Which of A/B/C holds is for the experiment owners to determine
from the evidence; this harness does not assert it.

## Exact environment

| Item | Value |
| --- | --- |
| `google-adk` | 2.6.3 |
| Model | `gemini-3.5-flash` |
| Provider | Gemini API (`GOOGLE_API_KEY` from repo-root `.env`) |
| Runner | `InMemoryRunner` |
| OS | Windows 11, PowerShell |
| venv | `.venv` at repo root |

## Source-level observation this expedition tests at runtime

In ADK 2.6.3, `flows/llm_flows/contents.py:291` defines:

```python
def _is_part_invisible(p, *, include_thoughts: bool = False) -> bool:
    if p.function_call or p.function_response:
        return False
    return (p.thought and not include_thoughts) or not (p.text or ...)
```

A thought-only part is therefore eligible for exclusion by default. But the
`include_thoughts` argument is only ever passed as
`include_thoughts_from_other_agents and _is_other_agent_reply(...)`
(`contents.py:737`), and `RunConfig.include_thoughts_from_other_agents`
defaults to `False` (`run_config.py:394`).

This leaves the **mixed-event question** open at source level: if one event
holds both a `Part(thought=True, text=...)` and a `function_call`, the function
call keeps the event alive — does the thought text then get copied into the
next `LlmRequest`?

That is the question this probe answers by runtime measurement rather than by
reading source.

## Instrumentation points

Two, both read-only.

**Phase A — events.** The `async for event in runner.run_async(...)` loop.
Every emitted `Event` is serialized as it arrives. Consuming the generator is
what a caller normally does; it does not alter execution.

**Phase B — outgoing requests.** `before_model_callback` on the probe agent.
ADK invokes it at `base_llm_flow.py:1391` with the live `LlmRequest`,
immediately before the model call:

```python
if response := await self._handle_before_model_callback(
    invocation_context, llm_request, model_response_event
):
    yield response
    return
```

The callback **always returns `None`**. A falsy return means the walrus
assignment is false and the flow proceeds with the same `llm_request` object
(`base_llm_flow.py:247`); a returned `LlmResponse` would short-circuit the
model call entirely. The callback only reads the request and serializes a
snapshot.

No monkey-patching is used. No supported hook was found to be insufficient.

### Instrumentation that could itself alter the measurement

Stated explicitly, since these are the ways this probe could lie:

- **The callback receives the live, mutable `LlmRequest`.** Mutating it would
  change the thing being measured. The recorder only reads;
  `test_recorder_is_non_altering` asserts the request is byte-identical
  (`model_dump`) after the callback runs, and that the return is `None`.
- **Snapshot timing.** The snapshot is taken inside the callback chain, so it
  reflects the request *after* `contents.py` assembly and *before* the model
  call. ADK sets `llm_request.config.labels` after the callback returns
  (`base_llm_flow.py:1397`), so that field is absent from the snapshot. It does
  not affect any thought-related field.
- **Registering a callback at all.** `before_model_callback` is not part of
  request assembly and does not add to `contents`. It is present in *both*
  arms, so it cannot differentiate them.
- **The probe agent is not the main lab agent.** It sets its own planner per
  arm, so the planner committed on `adk_lab/agent.py` does not leak into either
  arm. `adk_lab/agent.py` is read, never modified.

## Control

`--mode thoughts_off` sets `ThinkingConfig(include_thoughts=False)`.

Held constant across arms by construction — read from `adk_lab.agent.root_agent`
rather than restated, so the two arms cannot drift:

- model, tools, instruction, description, backend, prompts, runner config

Changed variable: `include_thoughts` only. No model or backend change is needed
to enable thought summaries on this model, so the experiment is cleanly
controlled.

No thinking budget is set. `ThinkingConfig.thinking_budget` stays `None`, so
thinking depth is model-chosen and is a free variable across runs.

## Test cases

| Case | Prompt | Purpose |
| --- | --- | --- |
| COT-01 | `What information do I need for an activity proposal?` | thought-only / normal-answer path |
| COT-02 | `Show me information for AU-CARDS.` | thought + `function_call` + `function_response` + next model invocation — the most important case |
| COT-03 | `Tell me about Cards.` | ambiguous tool-selection / abstention decision |

COT-03 behavior is not auto-interpreted.

## How to run

Thoughts OFF (control):

```powershell
.venv\Scripts\python.exe experiments\side_expeditions\thought_context_replay\run_probe.py --case COT-02 --mode thoughts_off --run-id COT-02-OFF-01
```

Thoughts ON (treatment):

```powershell
.venv\Scripts\python.exe experiments\side_expeditions\thought_context_replay\run_probe.py --case COT-02 --mode thoughts_on --run-id COT-02-ON-01
```

`--run-id` is optional; it defaults to `<case>-<mode>-<UTC timestamp>`.
`--evidence-dir` redirects output away from `evidence/`.

Each run makes real model calls against the key in the repo-root `.env`, loaded
via ADK's own `envs.load_dotenv_for_agent`.

## Evidence files

Two per run, kept distinct:

| File | Contents |
| --- | --- |
| `evidence/<run_id>_events.jsonl` | one line per ADK `Event` (Phase A) |
| `evidence/<run_id>_llm_requests.jsonl` | one line per outgoing `LlmRequest` (Phase B) |

Every line carries `run_id`, `mode`, raw serialized parts, and these counts:

```
thought_text_part_count
thought_signature_count
function_call_count
function_response_count
mixed_thought_and_function_call
```

Each part is recorded as both a raw `model_dump(mode="json")` and explicit
flags (`thought`, `has_thought_signature`, `thought_signature_len`,
`has_function_call`, `has_function_response`). `thought_signature` is `bytes`;
`mode="json"` base64-encodes it, so it survives serialization intact.

The load-bearing read is `thought_text_part_count` on
`<run_id>_llm_requests.jsonl` for `request_index >= 2` — that is thought text
present in a *subsequent* request, versus `thought_signature_count` on the same
rows.

## Phase E — mixed events

If a run naturally produces an event holding both a `thought=True` text part
and a `function_call`, `mixed_thought_and_function_call` is `true` on that
record. Events are not synthesized or manipulated to force this. If no mixed
event occurs, the correct report is **NOT OBSERVED**.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest tests\test_thought_context_replay.py -q
```

These cover the instrumentation only and make no model calls. `evidence/` is
empty apart from `.gitkeep`; all evidence is generated by running the probe.
