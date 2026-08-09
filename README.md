# adk-lab

An empirical learning laboratory for the Google Agent Development Kit (ADK).

This repository is deliberately small. It is not an architecture and not a
business application. Each "expedition" adds the smallest thing that makes one
aspect of native ADK behaviour observable.

Current expedition: **E0 — Native ADK Tool Contracts**
(see `experiments/e00_native_tool_contracts/README.md`).

## Ground rules

Native ADK only. No dependency injection, tool registries, factories, generic
wrappers, registration decorators, agent manifests, custom base classes, custom
state management, MCP, RAG, databases, workflow agents, sub-agents, AgentTool,
callbacks, `ToolContext` or persistence frameworks. Repetition is left
un-abstracted on purpose, so ADK's own behaviour stays visible.

## Layout

```
adk_lab/
    __init__.py       from . import agent   (ADK package convention)
    agent.py          the single root_agent
    tools.py          three plain typed Python functions
    sample_data.py    two in-memory records
tests/
    test_tools.py     deterministic tests for the Python functions
experiments/
    e00_native_tool_contracts/README.md
docs/
    e00-work-summary.md   task, challenges, assumptions, recommendations
```

## Setup

Requires Python 3.10+; this lab was built and verified on **Python 3.13**.

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install "google-adk==2.6.3" pytest
```

The package is not installed into the venv — `adk_lab` is imported from the
repository root. `pyproject.toml` records the pinned dependencies and points
pytest at the root via `pythonpath`.

## Credentials

The tools need no credentials. The **agent** does, because it calls a Gemini
model.

1. Copy `.env.example` to `.env` in the repository root.
2. Fill in the values. ADK walks up from `adk_lab/` to find `.env`, so one file
   at the root is enough.

You must supply **one** of:

- **Gemini API key** — set `GOOGLE_GENAI_USE_ENTERPRISE=0` and
  `GOOGLE_API_KEY=<your key>` (create one at <https://aistudio.google.com/apikey>).
- **Vertex AI** — set `GOOGLE_GENAI_USE_ENTERPRISE=1`, `GOOGLE_CLOUD_PROJECT`
  and `GOOGLE_CLOUD_LOCATION`, and run `gcloud auth application-default login`.

`.env` is git-ignored. No key is stored in this repository.

## Run

```powershell
.venv\Scripts\adk.exe web adk_lab
```

Passing `adk_lab` (rather than `.`) puts ADK in single-agent mode. Pointing it
at the repository root also works, but ADK lists *every* non-hidden subdirectory
as a candidate agent — `tests` and `experiments` show up in the dropdown and
fail when selected.

Terminal alternative: `.venv\Scripts\adk.exe run adk_lab`.

## Test

```powershell
.venv\Scripts\python.exe -m pytest
```

The tests exercise the plain Python functions only. ADK is not mocked and no
model is called, so they run without credentials.
