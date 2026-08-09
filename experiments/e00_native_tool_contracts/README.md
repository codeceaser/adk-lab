# Expedition E0 — Native ADK Tool Contracts

## Experiment question

When three ordinary typed Python functions are handed directly to a native ADK
`LlmAgent`, what actually happens at each hop?

1. Python function definition
2. ADK-generated tool contract / schema
3. LLM tool selection
4. LLM-generated tool arguments
5. actual Python function invocation
6. tool result returned to the agent

We want to see this by observation, not by reasoning about the docs.

## Initial hypotheses

H1. ADK derives the tool name from the Python function name, verbatim.

H2. ADK derives the tool description from the function docstring.

H3. The Google-style `Args:` block becomes a per-parameter description in the
    generated schema, so the model sees each argument documented separately.

H4. Type hints (`str`) become the JSON types in the parameter schema, and
    parameters without defaults are marked required.

H5. The `-> dict` return annotation contributes a return/response schema to the
    contract.

H6. Given an exact ID (prompt A / D), the model calls the matching tool with the
    ID copied verbatim.

H7. Given a natural-language name rather than an ID (prompt E), the model has no
    lookup-by-name capability, so it must either ask, guess an ID, or answer
    from its own prior — we do not predict which.

H8. Given a partial proposal (prompt G), the model must either ask for the
    missing fields or call `validate_proposal_fields` with invented/empty
    values — we do not predict which.

H9. Prompt C ("what information do I need") needs no tool at all, since the
    answer is visible in the tool contract itself.

## What has been implemented

- `adk_lab/sample_data.py` — two in-memory records (`E1001`, `AU-CARDS`) in
  plain dicts. No I/O.
- `adk_lab/tools.py` — three plain typed functions:
  - `get_employee(employee_id: str) -> dict`
  - `get_assessment_unit(assessment_unit_id: str) -> dict`
  - `validate_proposal_fields(title, description, managed_geography, assessment_unit_id) -> dict`
  Each is deterministic, calls no LLM, reads no session state, and returns a
  dict with an explicit `status`. Unknown IDs return `status: "not_found"`
  rather than raising.
- `adk_lab/agent.py` — one `LlmAgent`, short instruction, the three functions
  passed straight into `tools=`. No wrapper, registry, factory or decorator.
- `tests/test_tools.py` — deterministic unit tests for the Python functions
  only. ADK is not mocked and not involved.

## Pre-run static observations (from the generated contract, no model calls)

These were read off the declarations ADK builds from the functions, before any
prompt was run. They bear on H1–H5.

- H1 holds: tool names are `get_employee`, `get_assessment_unit`,
  `validate_proposal_fields`.
- H2 holds, but bluntly: the **entire** docstring becomes one flat
  `description` string — summary, `Args:` block and `Returns:` block included,
  newlines and indentation intact.
- **H3 is false.** ADK 2.6.3 does not parse the `Args:` block. In
  `google/adk/tools/_automatic_function_calling_util.py` the per-parameter
  description is hardcoded to `None` ("3. Do not support parameter description
  for now"). Each property carries only an auto-generated `title` derived from
  the parameter name (`assessment_unit_id` → `"Assessment Unit Id"`). Argument
  documentation reaches the model only because it is embedded in the flat
  description blob.
- H4 holds: `str` → `"type": "string"`, and all parameters without defaults are
  listed in `required`.
- **H5 is false.** No return or response schema is emitted. The `-> dict`
  annotation is not part of the contract the model sees; the model learns the
  result shape only from the `Returns:` prose inside the description.
- ADK 2.6.3 emits `parameters_json_schema` (JSON Schema) rather than the older
  `parameters` (`types.Schema`) form, behind the experimental feature flag
  `JSON_SCHEMA_FOR_FUNC_DECL`, which is **on by default** and prints a
  `UserWarning` when the declaration is built.
- `root_agent.tools` still holds the **raw Python function objects**
  (`type(...).__name__ == 'function'`). ADK wraps them in `FunctionTool` lazily,
  inside `canonical_tools()`.

Reproduce with:

```
adk web adk_lab
```

or dump the contracts directly:

```python
import asyncio, json
from adk_lab.agent import root_agent

async def main():
    for tool in await root_agent.canonical_tools():
        print(json.dumps(tool._get_declaration().model_dump(exclude_none=True), indent=2))

asyncio.run(main())
```

## Initial manual test cases

Run with `adk web adk_lab` from the repository root, then send each prompt in a
fresh session.

| # | Prompt |
|---|--------|
| A | Find employee E1001. |
| B | Can you tell me about employee E1001? |
| C | What information do I need for an activity proposal? |
| D | Show me information for AU-CARDS. |
| E | Tell me about Cards. |
| F | Validate this proposal: Title: AI Compliance Assistant; Description: Helps reviewers prepare reports; Managed Geography: CANADA; Assessment Unit: AU-CARDS. |
| G | Validate this proposal: Title: AI Compliance Assistant; Managed Geography: CANADA. |

For each, record: which tool was selected (if any), the exact arguments the
model generated, the tool result, and what the agent said back.

---

## Observations

### A. "Find employee E1001."

- Tool selected:
- Arguments generated:
- Tool result:
- Agent response:
- Notes:

### B. "Can you tell me about employee E1001?"

- Tool selected:
- Arguments generated:
- Tool result:
- Agent response:
- Notes:

### C. "What information do I need for an activity proposal?"

- Tool selected:
- Arguments generated:
- Tool result:
- Agent response:
- Notes:

### D. "Show me information for AU-CARDS."

- Tool selected:
- Arguments generated:
- Tool result:
- Agent response:
- Notes:

### E. "Tell me about Cards."

- Tool selected:
- Arguments generated:
- Tool result:
- Agent response:
- Notes:

### F. Full proposal

- Tool selected:
- Arguments generated:
- Tool result:
- Agent response:
- Notes:

### G. Partial proposal

- Tool selected:
- Arguments generated:
- Tool result:
- Agent response:
- Notes:

---

## Hypothesis verdicts

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1 | confirmed | static contract dump |
| H2 | confirmed (whole docstring, unparsed) | static contract dump |
| H3 | **refuted** | static contract dump |
| H4 | confirmed | static contract dump |
| H5 | **refuted** | static contract dump |
| H6 | | |
| H7 | | |
| H8 | | |
| H9 | | |

## Open questions raised by this run

_(fill in after the manual prompts)_

## What to try in E1

_(fill in after the manual prompts)_
