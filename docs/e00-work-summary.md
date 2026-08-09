# Work Summary — Expedition E0 setup

**Date:** 2026-08-09
**Scope:** initial increment — repository bootstrap plus the E0 "Native ADK Tool
Contracts" laboratory.
**Status:** implemented and validated; the manual A–G prompts have not been run
yet, so the E0 observations are still open.

---

## 1. Task

Stand up the smallest practical Python project that makes native ADK tool
behaviour observable end to end:

1. Python function definition
2. ADK-generated tool contract / schema
3. LLM tool selection
4. LLM-generated tool arguments
5. actual Python function invocation
6. tool result returned to the agent

Explicitly **not** in scope: production architecture, or a complete business
application. Abstraction was forbidden by the brief, not merely unnecessary —
no DI, tool registries, factories, generic wrappers, registration decorators,
agent manifests, custom base classes, custom state, MCP, RAG, databases,
workflow agents, sub-agents, `AgentTool`, callbacks, `ToolContext`, or
persistence frameworks. Repetition was left un-abstracted on purpose.

### What was built

| Area | Delivered |
|---|---|
| Environment | Python 3.13 venv, `google-adk==2.6.3` pinned, `pytest` |
| Domain | `adk_lab/sample_data.py` — two in-memory records (`E1001`, `AU-CARDS`) |
| Tools | `adk_lab/tools.py` — three plain typed functions, deterministic, explicit `status` dicts, `not_found` instead of exceptions |
| Agent | `adk_lab/agent.py` — one `LlmAgent`, short instruction, functions passed straight into `tools=` |
| Tests | `tests/test_tools.py` — 9 deterministic tests, no ADK mocking |
| Experiment note | `experiments/e00_native_tool_contracts/README.md` |
| Config | `pyproject.toml`, `.gitignore`, `.env.example`, `README.md` |

### Validation performed

- `pytest` → **9 passed**. (The 4 warnings are ADK-internal `BaseAgentConfig`
  deprecations, not lab code.)
- Import check → `adk_lab` imports cleanly; `root_agent` is an `LlmAgent` named
  `ida_lab_agent` on `gemini-3.5-flash`; `google-adk` reports `2.6.3`.
- ADK's own `AgentLoader` discovers and loads the agent with all three tools
  attached.
- Live boot: `adk web adk_lab --port 8931` started and `GET /list-apps`
  returned **HTTP 200 `["adk_lab"]`** without any credentials configured.

Nothing was committed or pushed.

---

## 2. Challenges

### 2.1 Decisions that could not be guessed safely

Two configuration choices had no safe default, so both were resolved from
authoritative sources rather than invented:

- **Python version.** Five interpreters are installed locally (3.14, 3.13,
  3.10, 3.6, Anaconda 3.7). PyPI metadata for `google-adk==2.6.3` gives
  `requires-python >=3.10` with classifiers through 3.14. Chose **3.13** —
  inside the supported range, with mature wheels for the whole dependency tree.
- **Model name.** Rather than guess, read ADK 2.6.3's own scaffolder:
  `cli_create.py:156` offers `gemini-3.5-flash` as the option it generates.
  Adopted that.

### 2.2 Native ADK behaviour that contradicted the brief's assumptions

The brief asked for docstrings explaining *what each argument means*. In ADK
2.6.3 that intent does not survive the trip to the model:

- **Per-argument descriptions are dropped.** ADK does not parse the Google-style
  `Args:` block. `google/adk/tools/_automatic_function_calling_util.py:84`
  hardcodes `description=None`, commented *"3. Do not support parameter
  description for now."* Each parameter carries only an auto-derived `title`
  (`assessment_unit_id` → `"Assessment Unit Id"`).
- **The whole docstring becomes one flat blob.** Summary, `Args:` and
  `Returns:` are concatenated verbatim into the single `description` field,
  newlines and indentation intact. Argument documentation reaches the model only
  incidentally, as prose inside that blob.
- **The `-> dict` return annotation contributes nothing.** No response schema is
  emitted; the model infers result shape purely from the `Returns:` prose.

Smaller divergences:

- ADK emits `parameters_json_schema` (JSON Schema), not the older
  `parameters` / `types.Schema` form — behind an experimental feature flag
  `JSON_SCHEMA_FOR_FUNC_DECL` that is **on by default** and emits a
  `UserWarning` whenever a declaration is built.
- `root_agent.tools` holds **raw `function` objects**, not `FunctionTool`
  instances. Wrapping happens lazily inside `canonical_tools()`.
- `GOOGLE_GENAI_USE_VERTEXAI` is deprecated in favour of
  `GOOGLE_GENAI_USE_ENTERPRISE` (`env_utils.py:69-78`). The old name still works
  but logs a warning.

### 2.3 Agent discovery is looser than expected

`AgentLoader.list_agents()` (`agent_loader.py:428`) returns *every* non-hidden
subdirectory of the agents dir. It never checks for `agent.py`, despite a
`is_single_agent_directory()` helper existing that does exactly that check.

Consequence: `adk web .` from the repo root lists `tests`, `experiments` and
`docs` as selectable agents, each of which fails when clicked. Resolved by
documenting `adk web adk_lab` (single-agent mode), which was verified to list
only `['adk_lab']`.

### 2.4 Packaging

`pyproject.toml` deliberately has no `[build-system]`. With a flat layout,
setuptools auto-discovery would see `adk_lab`, `tests`, `experiments` and
`docs` as competing top-level packages and fail. Adding build configuration to
work around that would have been structure for no experimental gain, so the
project is **not installed** into the venv — `pythonpath = ["."]` points pytest
at the repo root and `adk` is run from there.

### 2.5 Tooling friction (outside the lab)

Repeated Claude Code permission prompts had two causes worth recording, since
they will recur:

1. Chained commands re-prompt. A rule like `PowerShell(py *)` matches only the
   segments it covers; `py -3.13 -m venv .venv && .venv\Scripts\python.exe --version`
   prompts again for the second half.
2. `.claude/settings.local.json` is rewritten from Claude Code's in-memory copy
   on every "don't ask again" click, silently discarding rules added to that
   file during the same session.

Fixed by moving durable rules into `.claude/settings.json`, which the approval
flow does not rewrite, and by keeping shell commands single-purpose.

---

## 3. Assumptions

| # | Assumption | Basis / risk |
|---|---|---|
| A1 | Python 3.13 is the right target | Inside ADK 2.6.3's `>=3.10` range; 3.14 is classified as supported but has thinner wheel coverage. Low risk. |
| A2 | `gemini-3.5-flash` is an appropriate model | Taken from ADK 2.6.3's own scaffolder, not invented. Change it in `agent.py` if your account has different access. |
| A3 | A single `.env` at the repo root is sufficient | Verified against `envs.py` — ADK walks up from the agent folder to find it. |
| A4 | The project need not be pip-installable | See §2.4. Revisit only if something outside the repo root must import `adk_lab`. |
| A5 | Returning `dict(record)` copies is acceptable | Shallow copy prevents the agent mutating sample data. Not an abstraction; one word of defensiveness. |
| A6 | `main.py` and `.idea/` are out of scope | Both pre-existing. `.idea/` is now gitignored; `main.py` is untouched and still staged in git. See §4.4. |
| A7 | Tool ID lookups are case-sensitive | Implemented as plain dict lookup, and asserted in tests. If IDA semantics require case-insensitive matching, this is wrong — but it is deliberately visible rather than hidden behind normalisation. |

---

## 4. Recommendations

### 4.1 Immediate — finish E0

The build is done; the experiment is not. Run the seven manual prompts (A–G)
via `adk web adk_lab` and fill the blank observation sections in
`experiments/e00_native_tool_contracts/README.md`. For each, record which tool
was selected, the exact arguments generated, the tool result, and the agent's
reply.

H1, H2, H4 are already confirmed and **H3 and H5 refuted** from static contract
inspection. H6–H9 need live runs. Prompts **E** ("Tell me about Cards") and
**G** (partial proposal) are the interesting ones — deliberately no expected
answer was encoded for either.

### 4.2 Highest-value follow-up experiment (E1 candidate)

The §2.2 finding is the sharpest lead this increment produced: **argument
semantics reach the model only as unparsed prose**. That is directly testable.

Suggested E1: vary *only* the docstring while holding signatures and data
constant, and measure argument-generation quality. For example — full Google
style vs. a one-line summary with no `Args:` block vs. no docstring at all. If
behaviour barely changes, the flat blob is doing little work and the `Args:`
convention is cargo cult here; if it changes sharply, docstring discipline is
load-bearing and should become a lab standard.

A second candidate: since no return schema is emitted, test whether the
`Returns:` prose actually governs how the agent interprets `status: "not_found"`
— e.g. does it correctly refuse to invent a record, or does it paraphrase the
error as if it were data?

### 4.3 Operational

- Always launch with `adk web adk_lab`, never `adk web .` (§2.3). This gets
  worse as `docs/`, `experiments/` and future folders accumulate.
- Expect the `JSON_SCHEMA_FOR_FUNC_DECL` `UserWarning` on every declaration
  build. It is ADK-internal and can be ignored; do not suppress it, since the
  flag being experimental is itself a fact worth tracking across ADK versions.
- Keep `google-adk` pinned at `2.6.3`. Several findings here are version-
  specific — particularly the dropped parameter descriptions, which read as a
  temporary limitation ("for now") and may change. Re-run the static contract
  dump before adopting any newer ADK version.

### 4.4 Housekeeping (your call, not done)

- `main.py` is the leftover PyCharm sample and is currently staged in git. It
  will land in the first commit unless removed. Recommend deleting it.
- `.claude/settings.local.json` has accumulated several dead entries — exact
  full command strings from earlier "don't ask again" clicks that can never
  match again. Safe to delete; the file is now gitignored.
- Nothing has been committed yet. When you are ready, the first commit should
  cover the whole scaffold as one baseline.

### 4.5 Standing constraint

Resist improving this. Every abstraction that would make the code "better"
would also hide the behaviour E0 exists to measure. If something looks like it
needs a layer, record the observation instead of building the layer.
