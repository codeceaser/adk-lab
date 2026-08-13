# Expedition E0 — Native ADK Tool Contracts: Learning Register

## Purpose

This document captures the empirical learning from **Expedition E0 — Native ADK Tool Contracts**.

The objective of E0 is not to define universal agent-development doctrine. It is to establish a trustworthy native-ADK baseline and record what is **actually observed** at runtime before introducing wrappers, state abstractions, MCP, workflow agents, sub-agents, AgentTool, RAG, or custom orchestration.

The governing method is:

> **Architectural intention → native framework contract → observed runtime behavior → retained or revised principle**

A principle is treated as a hypothesis until supported by experiment.

---

## Baseline

- **Repository:** `codeceaser/adk-lab`
- **Baseline commit:** `4bf0e908cd89caea81889afbdbda6fd409b54482`
- **ADK version:** `2.6.3`
- **Backend baseline:** Gemini API
- **Model:** `gemini-3.5-flash`
- **Agent:** `ida_lab_agent`
- **Native tool registration:** plain Python callables supplied directly to `LlmAgent.tools`
- **Custom wrappers/DI/registries:** none
- **State abstraction:** none
- **Workflow abstraction:** none
- **MCP/RAG:** none

### Native tools

```python
get_employee(employee_id: str) -> dict

get_assessment_unit(assessment_unit_id: str) -> dict

validate_proposal_fields(
    title: str,
    description: str,
    managed_geography: str,
    assessment_unit_id: str,
) -> dict
```

---

# 1. Native ADK tool conversion

## Observed

A plain Python callable registered directly with `LlmAgent.tools` is exposed at runtime as an ADK `FunctionTool`.

Runtime trace evidence includes:

```text
gen_ai.tool.type = FunctionTool
```

### Empirical model

```text
Python callable
    ↓
LlmAgent.tools
    ↓
ADK FunctionTool
    ↓
Function declaration sent to model
    ↓
Model generates named tool arguments
    ↓
ADK invokes Python callable
```

## Learning

> **Native callable → FunctionTool conversion works without a custom wrapper.**

This is the control case against which later wrapper/registry/manifest experiments should be compared.

---

# 2. Model-facing input contract

For the baseline tools, the model-facing declaration preserves:

```text
Function name       → preserved
Parameter names     → preserved
Parameter types     → preserved
Required fields     → preserved
```

Example:

```python
def get_employee(employee_id: str) -> dict:
```

produced a structured parameter contract containing approximately:

```json
{
  "properties": {
    "employee_id": {
      "type": "string"
    }
  },
  "required": ["employee_id"],
  "type": "object"
}
```

## Learning

> **The LLM is effectively interacting with a generated named JSON contract, not a positional Python call signature.**

This was reinforced by the multi-argument validation case, where Gemini emitted arguments in a different order from the Python function signature and ADK still mapped them correctly.

---

# 3. Per-argument prose is flattened

## Observed

Python docstrings containing:

```text
Args:
    employee_id: The Employee ID to look up...
```

did **not** result in a structured parameter-level description such as:

```json
"employee_id": {
  "type": "string",
  "description": "The Employee ID to look up..."
}
```

Instead:

- parameter name/type/requiredness were structural;
- the full docstring became a flat function-level description.

## Learning

> **Do not assume rich Python parameter documentation becomes rich structured model-facing parameter documentation.**

For ADK 2.6.3 / Gemini API baseline:

```text
Per-argument prose  → NOT structurally represented
Whole docstring     → flat function description
```

## Engineering implication

Tool descriptions are carrying more semantic responsibility than the parameter schema alone.

This should be measured again after future ADK upgrades.

---

# 4. Response schema is backend/variant-sensitive

## Observed

ADK can derive a response schema from a Python return annotation, but in the current baseline the model request does not contain a `response_json_schema`.

For ADK 2.6.3:

```text
Gemini API path            → response schema removed
Vertex/Enterprise variant  → response schema may be retained
```

This concerns the **model-facing declaration**, not the actual Python return value.

The Python function still returns the same runtime dictionary.

## Important nuance

The current tools use:

```python
-> dict
```

A bare `dict` is structurally weak even when a response schema is retained.

A future experiment should compare:

```text
dict return
vs
TypedDict / Pydantic model return
```

and:

```text
Gemini API
vs
Vertex/Enterprise backend
```

## Learning

> **Return-contract richness is not determined only by the Python annotation; the backend/declaration variant can change what the model is formally told about tool output.**

---

# 5. Agent `description` participates in model context

## Observed

The runtime system instruction sent to Gemini contains:

- the explicit agent `instruction`;
- the internal agent name;
- the agent `description`.

Conceptually:

```text
explicit instruction
+
ADK-generated agent identity
+
agent description
=
effective system instruction
```

## Learning

> **Agent `description` is not merely invisible delegation metadata; in this runtime it also participates in the LLM context.**

This becomes especially important when sub-agents are introduced.

---

# 6. Tool descriptions are behavioral context, not passive documentation

This is one of the most consequential E0 findings.

## Case C — useful direct reasoning

User:

```text
What information do I need for an activity proposal?
```

Observed:

- no tool was called;
- the root agent answered directly;
- the answer could be derived from the `validate_proposal_fields` tool description.

### Learning

> **Tool descriptions can act as knowledge available to the model even when the tool is not invoked.**

## Case E — inference anchoring from tool examples

User:

```text
Tell me about Cards.
```

The user did **not** provide `AU-CARDS`.

The `get_assessment_unit` documentation contained:

```text
for example "AU-CARDS"
```

Observed trajectory:

```text
"Tell me about Cards."
    ↓
get_assessment_unit("AU-CARDS")
    ↓
owner_employee_id = "E1001"
    ↓
get_employee("E1001")
    ↓
final enriched answer
```

### Working interpretation

The tool example likely acted as an inference anchor when resolving the ambiguous word `"Cards"`.

### Classification

Not classified as a normal factual hallucination because the returned business facts were grounded in successful tool calls.

The questionable point was earlier:

```text
"Cards"
    ↓
infer "AU-CARDS"
```

This is better described as:

> **Unsupported or weakly supported entity resolution through tool-argument generation.**

## Principle candidate

> **Examples in tool descriptions are part of reasoning context and can influence generated business values.**

## Red-flag candidate

> **Do not place realistic business identifiers in tool examples casually.**

Better nuanced guidance:

> **Examples may improve semantic comprehension, but realistic examples can become inference anchors. Use deliberately and test ambiguous user inputs.**

---

# 7. Explicit business arguments work in the clean native baseline

## Case A

User:

```text
Find employee E1001.
```

Observed:

```text
get_employee(employee_id="E1001")
```

Tool response:

```json
{
  "status": "success",
  "employee": {
    "employee_id": "E1001",
    "name": "Anita Shah",
    "managed_geography": "CANADA",
    "assessment_units": ["AU-CARDS", "AU-DIGITAL"]
  }
}
```

## Case F

User supplied four business values.

Observed tool arguments:

```json
{
  "assessment_unit_id": "AU-CARDS",
  "managed_geography": "CANADA",
  "title": "AI Compliance Assistant",
  "description": "Helps reviewers prepare reports"
}
```

The order differed from the Python function signature, but semantic mapping remained correct.

## Learning

> **Explicit cohesive business arguments work through native ADK FunctionTool invocation under the clean baseline.**

Qualified scope:

- simple string parameters;
- distinct names;
- direct callable registration;
- no wrappers;
- no manifest assembly;
- no generic state-based input substitution.

This creates the control point for later ARTHUR-style wrapper experiments.

---

# 8. Structural schema validity is not business validity

## Case G

User supplied:

```text
Title: AI Compliance Assistant
Managed Geography: CANADA
```

Missing:

```text
description
assessment_unit_id
```

Gemini generated:

```json
{
  "assessment_unit_id": "",
  "title": "AI Compliance Assistant",
  "managed_geography": "CANADA",
  "description": ""
}
```

Therefore all schema-required keys were structurally present.

ADK invoked the function.

The deterministic tool returned:

```json
{
  "status": "invalid",
  "missing_fields": [
    "description",
    "assessment_unit_id"
  ]
}
```

## Learning

> **Schema validity is not business validity.**

Conceptually:

```text
Tool schema:
"Did you provide the required shape?"

        ≠

Business validator:
"Are the provided values semantically usable?"
```

Examples:

```text
proposal_id present     ≠ proposal exists
country present         ≠ supported jurisdiction
employee_id present     ≠ authorized employee
status present          ≠ valid state transition
amount present          ≠ permitted amount
```

This is a foundational separation for agentic tool design.

---

# 9. ADK missing-mandatory-argument guard is NOT yet empirically proven

Current ledger:

```text
Documentation/source evidence : YES
Runtime experiment             : NOT YET
```

Case G did not trigger the guard because Gemini supplied all required keys using empty strings.

To exercise the runtime guard, the actual function call must omit required keys entirely, for example:

```json
{
  "title": "AI Compliance Assistant",
  "managed_geography": "CANADA"
}
```

## Learning discipline

> **Source inspection tells us what ADK is implemented to do. The laboratory tells us what actually occurred. Do not promote source expectations into empirical findings prematurely.**

---

# 10. Successful execution can produce a negative business result

## Case A-error

User:

```text
Find employee E9999.
```

Observed:

```text
get_employee(employee_id="E9999")
```

Tool executed successfully and returned:

```json
{
  "status": "not_found",
  "employee_id": "E9999",
  "error_message": "No Employee record exists..."
}
```

## Learning

A robust system should distinguish at least:

```text
1. Execution success / business success

2. Execution success / negative business outcome
   e.g. not_found

3. Execution failure
   e.g. exception, timeout, unavailable service, malformed call

4. Partial business success
   future example: save succeeded, refresh failed
```

> **A negative business result is not the same thing as a tool/runtime failure.**

This distinction will be important for workflows, retries, HITL, and audit semantics.

---

# 11. Tool results create new affordances

Case E demonstrated that after:

```text
get_assessment_unit("AU-CARDS")
```

returned:

```text
owner_employee_id = "E1001"
```

the LLM autonomously decided to call:

```text
get_employee("E1001")
```

and enriched the final answer.

## Learning

> **A tool result does not necessarily terminate reasoning; it can create new opportunities for additional tool use.**

Runtime pattern:

```text
tool result
    ↓
control returns to LLM
    ↓
all available tools remain available
    ↓
LLM may answer OR continue tool use
```

This behavior is potentially useful but creates future risks:

- tool wandering;
- unnecessary enrichment;
- scope expansion;
- unexpected cost/latency;
- longer trajectories;
- additional failure opportunities.

---

# 12. Final-answer correctness is not sufficient

Case E produced a grounded final answer, but the initial mapping:

```text
"Cards" → "AU-CARDS"
```

was not directly supplied by the user.

This demonstrates:

```text
Grounded final facts
        ≠
Correct trajectory
        ≠
Correct business interpretation
```

## Learning

> **Agent evaluation must inspect trajectory as well as final response.**

Future metrics should include:

- correct tool-selection rate;
- tool-argument validity;
- entity-resolution correctness;
- unnecessary-tool-call rate;
- task-scope adherence;
- workflow adherence;
- groundedness;
- final task success.

---

# 13. Tool abstention is a first-class behavior

Case C demonstrated that a good agent does not merely select the correct tool.

It can also decide:

```text
No tool is required.
```

## Learning

> **Tool-selection quality includes knowing when not to call a tool.**

Future metric:

```text
Unnecessary Tool Call Rate
```

A system can have technically successful tool calls and still be poorly designed if it invokes capabilities unnecessarily.

---

# 14. Tool chaining introduces scope-discipline questions

Case E introduced another future metric:

```text
Task-Scope Adherence
```

Distinguish:

```text
wrong tool call
≠
unnecessary tool call
≠
useful optional enrichment
≠
out-of-scope exploration
```

There may not always be an absolute rule, but the distinction is necessary when evaluating enterprise-agent behavior.

---

# 15. LLM round-trips dominate simple-tool latency

Observed examples show the deterministic tools executing in sub-millisecond time while complete requests take multiple seconds.

Typical path:

```text
LLM call #1
    ↓
~0.5 ms deterministic lookup
    ↓
LLM call #2
```

In Case E:

```text
LLM
→ tool
→ LLM
→ tool
→ LLM
```

produced noticeably longer latency.

## Learning

> **For simple business operations, model round-trips may dominate end-to-end latency rather than the underlying business service.**

This will matter for:

- model routing;
- workflow design;
- deterministic orchestration;
- cost;
- latency;
- tool-chaining policies.

---

# 16. Tool descriptions have recurring token/context cost

The post-tool LLM call again receives:

- agent instruction;
- agent name/description;
- all tool declarations;
- original user input;
- prior function call;
- tool response.

Therefore tool documentation is not paid only once.

## Learning

> **Tool-description richness must be evaluated against both reliability benefit and recurring context/token cost.**

Do not prematurely optimize descriptions for brevity.

Future experiment should compare:

```text
description quality
vs
tool-selection reliability
vs
ambiguity behavior
vs
token footprint
vs
latency
```

---

# 17. Root prompt, tool metadata, and runtime workflow are separate responsibility surfaces

E0 strengthens the architectural separation:

```text
Agent instruction
→ role, objective, authority, reasoning boundaries, selection principles

Tool description/schema
→ capability, applicability, input contract, output/failure semantics

Workflow definition
→ known ordering, branching, retry, parallelism, checkpoints

Business services
→ deterministic domain rules and transactions

Knowledge source
→ current domain facts, policy, regulation, organizational data

Evaluation suite
→ expected trajectory and outcome
```

E0 also adds a warning:

> Tool descriptions participate directly in model reasoning, so they can accidentally become a hidden second prompt layer.

---

# 18. Current principle candidates

These are **not universal doctrines yet**.

### P1 — Native first

> **Do not abstract an ADK primitive until its native behavior is experienced, its limitation is observed, and the abstraction proves it preserves the native contract.**

### P2 — Explicit business inputs

> **Business inputs should normally be explicit; runtime/framework facilities should normally come from context.**

Still to be challenged later with ToolContext/state experiments.

### P3 — Distinctive tool shapes

> **Tools should expose cohesive, semantically distinct capabilities and contracts.**

Still to be stress-tested with deliberately overlapping tools.

### P4 — Schema vs business validation

> **Structured tool-call validity does not replace deterministic business validation.**

Strongly supported by Case G.

### P5 — Documentation is behavioral context

> **Tool descriptions are part of the model's reasoning environment, not passive developer documentation.**

Strongly supported by Cases C and E.

### P6 — Evaluate trajectories

> **A grounded final response can still originate from a wrong or weakly supported trajectory.**

Strongly supported by Case E.

---

# 19. Current red-flag candidates

These require more experiments before becoming absolute rules.

### RF-01 — Realistic identifiers in tool examples

Risk:

```text
example value
→ inference anchor
→ generated business argument
```

Observed in Case E.

### RF-02 — Tool descriptions becoming workflow code

Not yet directly tested in E0, but Case C/E establish the mechanism by which tool descriptions influence reasoning.

Future experiment should compare concise capability descriptions with overloaded procedural descriptions.

### RF-03 — Chained tool enrichment without explicit scope constraints

Observed harmlessly in Case E.

Needs later scale/complexity testing.

---

# 20. What E0 has NOT established

Do not overgeneralize the baseline.

Still open:

- run-to-run statistical consistency;
- behavior with many tools;
- overlapping tool semantics;
- poor descriptions;
- procedural/overloaded descriptions;
- complex nested argument objects;
- typed response models;
- ToolContext behavior;
- state coupling;
- wrapper/registry metadata preservation;
- MCP tool behavior;
- callback interactions;
- workflow primitives;
- HITL;
- retries and idempotency;
- sub-agent vs AgentTool;
- different models;
- Gemini API vs Vertex/Enterprise behavior;
- ADK version-to-version declaration changes;
- missing-required-argument guard at runtime.

---

# 21. Baseline case register

| Case | Input | Observed behavior | Learning |
|---|---|---|---|
| A | `Find employee E1001.` | Correct `get_employee` call | Basic native explicit argument path works |
| B | `Can you tell me about employee E1001?` | Same tool/correct argument | Paraphrase did not disturb selection |
| C | `What information do I need for an activity proposal?` | No tool call | Tool metadata can support direct reasoning and abstention |
| D | `Show me information for AU-CARDS.` | Correct `get_assessment_unit` call | Similar structural tools remained semantically distinguishable |
| E | `Tell me about Cards.` | Inferred `AU-CARDS`, then chained `get_employee` | Tool examples can anchor inference; tool outputs create new affordances |
| F | Complete proposal | Correct four-argument validator call | Named semantic mapping survives independent of argument order |
| G | Incomplete proposal | Empty strings supplied, validator reports missing fields | Structural requiredness ≠ business validity |
| A-error | `Find employee E9999.` | Tool executes and returns `not_found` | Negative business result ≠ runtime/tool failure |

---

# 22. Recommended next experiment

## E0.2 — Tool Description as Behavioral Context

Hold constant:

- model;
- agent instruction;
- Python implementation;
- schemas;
- sample data.

Vary only tool-description content.

Candidate variants:

```text
A. Rich description + realistic examples
   Current baseline

B. Rich description without realistic identifiers

C. Minimal but precise capability description

D. Overloaded procedural description
```

Replay selected prompts:

```text
Tell me about Cards.
What information do I need for an activity proposal?
Show me information for AU-CARDS.
Find employee E1001.
```

Measure:

- tool-selection behavior;
- direct reasoning;
- generated arguments;
- ambiguous entity resolution;
- unnecessary tool calls;
- trajectory length;
- token usage;
- latency;
- run-to-run consistency.

---

# 23. Evidence-preservation rule

For each important experiment/version, preserve:

```text
experiments/
└── <experiment>/
    ├── README.md
    ├── <version>_tool_declarations.json
    └── <version>_observations.md
```

Important metadata:

```text
experiment
source commit
ADK version
backend variant
model
date
```

This allows future comparisons such as:

```text
ADK 2.6.3 / Gemini API
vs
future ADK / Gemini API
```

and separately:

```text
ADK 2.6.3 / Gemini API
vs
ADK 2.6.3 / Vertex/Enterprise
```

without accidentally mixing experimental variables.

---

# Closing E0 learning

The strongest E0 lesson is not that native tools “work.”

It is that even a tiny three-tool agent already reveals several independent control surfaces:

```text
user intent
+
agent instruction
+
agent metadata
+
tool descriptions
+
structured schemas
+
model judgment
+
ADK runtime behavior
+
deterministic business logic
+
tool results
+
subsequent model reasoning
```

A reliable enterprise agent will require clear responsibility boundaries across these surfaces.

The working North Star remains:

> **Code what the business already knows. Prompt what requires judgment. Retrieve what changes by context. Escalate what requires authority.**

E0 adds an empirical qualifier:

> **Trust principles as hypotheses, documentation as intended behavior, source as implementation evidence, and experiments as observed behavior.**
