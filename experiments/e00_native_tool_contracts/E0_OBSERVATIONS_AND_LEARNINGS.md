# E0 Expedition — Empirical Observations and Learnings

## Scope

This file records the practical findings from Expedition E0 up through E0.2D.

Important limitation:

- The original E0.1 baseline is preserved in Git.
- Several E0.2 intermediate states were changed manually and were not committed.
- Therefore, the E0.2 findings below are preserved as **observed experimental evidence**, not as fully reproducible historical Git checkpoints.
- Going forward, each material experiment should be committed before the next experimental change.

Baseline:
- ADK: 2.6.3
- Backend: Gemini API
- Model: `gemini-3.5-flash`
- Native direct Python function registration
- No wrappers, DI, MCP, workflow agents, ToolContext, or custom state

---

# E0.1 — Native ADK Tool Contract Baseline

## Core runtime findings

A directly registered Python callable is exposed and executed by ADK as a `FunctionTool`.

Observed runtime path:

```text
Python callable
→ LlmAgent.tools
→ ADK FunctionTool
→ model-facing declaration
→ model-generated named arguments
→ Python invocation
→ tool result
→ model continuation/final response
```

### Model-facing contract

Observed:

```text
Function name       → preserved
Parameter names     → preserved
Parameter types     → preserved
Required fields     → preserved

Per-argument prose  → not structurally represented
Whole docstring     → flattened into function-level description
```

The model interacts with named JSON arguments rather than positional function arguments.

### Response schema

ADK can derive return-schema information, but under the ADK 2.6.3 Gemini API baseline the response schema is not present in the model-facing declaration.

This behavior is backend/variant-sensitive.

The current tools return a plain `dict`, which is structurally weak even when a response schema is available.

### Agent metadata

The agent `description` was observed inside the actual system instruction sent to the model.

Therefore:

> Agent description is not merely invisible delegation metadata; it participates in model context in this runtime.

---

# E0.1 Runtime Cases

## Case A — Direct employee lookup

Prompt:

```text
Find employee E1001.
```

Observed:

```text
get_employee(employee_id="E1001")
→ success
→ grounded final response
```

Finding:

> Explicit native business arguments successfully crossed the model → ADK → Python boundary.

## Case B — Paraphrase robustness

Prompt:

```text
Can you tell me about employee E1001?
```

Observed the same correct `get_employee` tool selection.

Finding:

> Conversational paraphrasing did not disturb clear capability selection in this baseline.

## Case C — Tool abstention

Prompt:

```text
What information do I need for an activity proposal?
```

Observed:
- No tool call.
- LLM answered directly using information available in `validate_proposal_fields` documentation.

Finding:

> Tool descriptions are part of the model's reasoning context and can provide knowledge even when the tool is not called.

## Case D — Similar-tool discrimination

Prompt:

```text
Show me information for AU-CARDS.
```

Observed:

```text
get_assessment_unit(assessment_unit_id="AU-CARDS")
```

Finding:

> Structurally similar tools remained distinguishable when names, parameters, and semantic descriptions were distinct.

## Case E — Ambiguous entity reference

Prompt:

```text
Tell me about Cards.
```

With the original realistic example in the tool description, the model inferred:

```text
Cards → AU-CARDS
```

and successfully retrieved the AU.

It subsequently followed `owner_employee_id=E1001` and called `get_employee`.

Findings:

> Realistic examples in tool descriptions can become inference anchors for generated business arguments.

> A grounded final response can still originate from a weakly supported trajectory.

> Tool results create new affordances for further model-selected tool calls.

## Case F — Multi-argument validation

Observed correct semantic mapping of all four arguments:

```text
title
description
managed_geography
assessment_unit_id
```

Argument order differed from the Python signature, but ADK correctly mapped the named arguments.

Finding:

> Native ADK explicit multi-argument contracts work cleanly for simple typed values in the baseline.

## Case G — Incomplete proposal

The model supplied missing user values as empty strings:

```text
description=""
assessment_unit_id=""
```

The ADK schema was structurally satisfied, and the deterministic validator rejected the values semantically.

Finding:

> Schema validity is not business validity.

Conceptually:

```text
Tool schema:
Did the expected fields/shape exist?

≠

Business validation:
Are the supplied values semantically usable?
```

The ADK missing-required-argument guard was **not** empirically exercised because all required keys were still present.

## Case A-error — Negative business outcome

Prompt:

```text
Find employee E9999.
```

Observed:

```text
valid tool invocation
→ tool executes successfully
→ status=not_found
```

Finding:

> Execution success with a negative business outcome is not the same as tool/runtime failure.

Useful distinction:

```text
1. execution success / business success
2. execution success / business negative
3. execution failure
4. partial success
```

---

# E0.2A — Remove Concrete Examples

## Question

Do realistic example values inside tool descriptions influence model-generated arguments under ambiguity?

The concrete examples such as:

```text
E1001
AU-CARDS
CANADA
```

were removed while the underlying tool implementations remained unchanged.

## Ambiguous prompt

```text
Tell me about Cards.
```

Five fresh-session runs were performed.

Observed:
- The model no longer invented `AU-CARDS`.
- It still inferred `Cards` as a possible identifier and invoked tools.
- Some runs tried `get_assessment_unit("Cards")`.
- One run also tried `get_employee("Cards")`.
- One run retried `get_assessment_unit("CARDS")`.

Findings:

> Removing concrete examples removed the observed example-anchoring behavior.

> Removing examples did **not** eliminate speculative tool invocation.

> Deterministic tools prevented speculative orchestration from turning into fabricated authoritative records.

New behavior categories observed:
- speculative tool exploration;
- model-initiated argument repair;
- additional capability exploration after `not_found`.

Important distinction:

```text
Factual reliability
≠
Trajectory reliability
≠
Scope/efficiency reliability
```

---

# E0.2B — Capability Applicability / Preconditions

The following applicability-oriented description produced consistently strong abstention behavior:

```text
Retrieve an authoritative Assessment Unit record using an exact
Assessment Unit ID supplied or established in the current context.

Use this tool only when an Assessment Unit ID is available.
Do not infer an Assessment Unit ID from an Assessment Unit name,
partial name, business label, or example.
If an exact ID is not available, ask the user for clarification.

Args:
    assessment_unit_id: The Assessment Unit ID to look up

Returns:
    On a match, a dict with status "success" and an "assessment_unit"
    record holding assessment_unit_id, name, managed_geography and
    owner_employee_id. When no record exists, a dict with status
    "not_found", the assessment_unit_id that was looked up, and an
    error_message describing what was not found.
```

## Ambiguous prompt

```text
Tell me about Cards.
```

Observed across repeated fresh sessions:
- No tool invocation.
- LLM requested an exact identifier.

Normal explicit-ID tool usage remained correct.

Finding:

> In this baseline, explicit applicability/precondition language materially constrained speculative tool use without requiring workflow logic in the root-agent prompt.

Additional finding:

> Removing concrete examples reduced ambiguity anchoring without degrading explicit tool usage.

---

# E0.2C — Minimum Sufficient Tool Description

## Question

Can the E0.2B behavior be preserved after compressing tool descriptions and removing prose that appears redundant?

## Observed

Happy-path capability correctness remained strong:
- explicit AU lookup still worked;
- complete proposal validation still called only `validate_proposal_fields`.

However, behavioral consistency degraded under ambiguity.

For:

```text
Tell me about Cards.
```

Observed:
- most runs again invoked `get_assessment_unit("Cards")`;
- one run abstained and asked for an exact ID.

For explicit AU lookup:

```text
Show me information for AU-CARDS.
```

some runs stopped after AU retrieval, while at least one run autonomously followed the owner ID with `get_employee`.

Finding:

> Description compression preserved basic capability correctness but weakened trajectory consistency when semantically important applicability constraints were reduced.

Principle candidate:

> The minimum sufficient tool description is not the shortest description. It is the smallest description that preserves capability semantics and important preconditions.

Another useful distinction:

> Optimize for semantic density, not minimum token count.

Token savings were not measured, so no efficiency claim is made for E0.2C.

---

# E0.2D — Procedural Contamination

## D1 — Post-success choreography

A procedural instruction was added to the tool description instructing the model to call `get_employee` after a successful AU lookup when `owner_employee_id` was available.

Prompt:

```text
Show me information for AU-CARDS.
```

Observed repeatedly:

```text
get_assessment_unit("AU-CARDS")
→ get_employee("E1001")
→ enriched response
```

Finding:

> Tool descriptions can function as hidden orchestration instructions even when the root-agent prompt contains no such workflow.

## D2 — Retry / fallback choreography

Procedural guidance was added to retry with a case variation and then try another capability after failure.

Observed trajectories included:

```text
get_assessment_unit("Cards")
→ not_found
→ get_assessment_unit("CARDS")
→ not_found
→ get_employee("Cards")
```

When both procedural contaminations were present, trajectories became still more expansive.

Finding:

> Procedural instructions inside tool descriptions are semantically composed by the model rather than executed like deterministic workflow code.

This can produce expanded or unexpected trajectories when multiple procedural rules interact.

Useful term:

> **Procedural Composition Drift**

---

# E0.2 Overall Learning

The progression is:

```text
E0.2A
Concrete examples influence generated values.

E0.2B
Applicability constraints improve abstention/tool-use discipline.

E0.2C
Over-compression weakens that discipline.

E0.2D
Procedural descriptions become hidden orchestration and can interact unpredictably.
```

Current design heuristic:

> **Tool descriptions should be semantically rich about capability, authority, and applicability, but procedurally poor about cross-tool workflow.**

Current principle candidate:

> **Describe applicability; do not encode choreography.**

Healthy tool-description territory:

```text
- what capability is provided
- what authoritative thing it returns/does
- what inputs are semantically required
- when the capability applies
- when it does not apply
- meaningful success / negative-result semantics
```

Red-flag territory:

```text
- after this tool succeeds call tool B
- if B fails retry C
- normalize and retry
- then invoke another capability
- perform subsequent workflow steps
```

---

# Additional E0 Learnings

## Deterministic tools vs deterministic orchestration

> A deterministic tool contract does not guarantee deterministic orchestration.

The model may still:
- explore speculative interpretations;
- retry altered arguments;
- call additional tools;
- enrich beyond the requested scope.

Tool reliability and trajectory reliability are separate engineering concerns.

## Tool descriptions are part of the effective instruction surface

The effective decision environment is closer to:

```text
Agent instruction
+
Agent description
+
Tool names
+
Tool schemas
+
Tool descriptions
+
Examples
+
Tool results
+
Conversation history
=
LLM decision environment
```

Therefore, system-prompt length alone is not a meaningful measure of instruction complexity.

## Prompt saturation is responsibility saturation

The danger is not only token count.

As procedural responsibilities accumulate across prompts and tool descriptions, the number of semantic interactions between instructions increases.

Therefore:

> Prompt/tool-description saturation is primarily responsibility and interaction saturation, not merely token saturation.

---

# Experimental Hygiene Note

One E0.2D run experienced unusually high latency while Gemini API throttling / 429 behavior and account changes were occurring.

That latency measurement should not be used as architecture evidence.

Future latency comparisons should record at least:

```text
model
backend
tool-call count
LLM-call count
total latency
429/retry observed?
provider backoff observed?
```

---

# Current Strongest E0 Principles

1. **Native first.**  
   Experience the ADK primitive natively before introducing abstraction.

2. **Explicit business contracts are viable.**  
   Native ADK preserved simple explicit arguments cleanly in the baseline.

3. **Schema validity is not business validity.**  
   Deterministic domain validation remains necessary.

4. **Tool descriptions are behavioral context.**  
   They influence reasoning, tool selection, argument generation, and direct answers.

5. **Describe applicability; do not encode choreography.**  
   Capability/precondition guidance improved discipline, while procedural cross-tool guidance created hidden orchestration.

6. **Semantic density matters more than minimum length.**  
   Compressing away meaningful applicability guidance degraded consistency.

7. **Evaluate trajectories, not only final answers.**  
   Grounded answers can still originate from weak or inefficient trajectories.

8. **Deterministic tools do not imply deterministic orchestration.**  
   Factual reliability, trajectory reliability, and scope reliability are distinct.

---

# What Remains Open After E0.2

Still untested or incomplete:
- wrapper/registry preservation of native tool contracts;
- ToolContext and implicit state versus explicit business arguments;
- complex/nested argument objects;
- typed return schemas;
- direct runtime exercise of ADK missing-required-argument guard;
- MCP behavior;
- callback interactions;
- workflow primitives;
- sub-agent vs AgentTool;
- HITL;
- retries/idempotency;
- model comparison;
- backend comparison;
- version-to-version ADK behavior.
