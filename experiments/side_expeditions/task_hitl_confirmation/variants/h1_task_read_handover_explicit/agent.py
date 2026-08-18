"""H1 - task-boundary handover diagnostic, explicit payload handover.

Characterisation only. The question:

    When a task sub-agent calls a read tool and then finish_task, what
    exactly becomes visible to Root — the read tool's FunctionResponse, or
    only the value the child supplied to finish_task?

    Root LlmAgent
        -> worker  mode="task"
             read_procedure(procedure_id)   FunctionTool, no confirmation
             save_procedure(...)            FunctionTool, require_confirmation=True

The read payload is a fixed, unmistakable constant, so any field that fails to
cross a boundary is visible rather than inferred. `save_procedure` takes every
field as optional and records the arguments verbatim — including which keys
were absent — so an omission is evidence, not a schema artefact forcing the
model to invent values.

H1 replaces H0's default handover line with an explicit instruction to carry
the read payload through `finish_task`. That single instruction line is the
only difference between this file and `h0_task_read_handover`.

Deliberately absent: `output_schema`, callbacks, session-state copying,
payload staging, database state, rejection semantics, retry logic,
`ResumabilityConfig`, MCP wrappers. `finish_task` is injected by ADK for
mode="task"; nothing here adds or wraps it.
"""

from __future__ import annotations

import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

_EXPEDITION_ROOT = Path(__file__).resolve().parents[2]
if str(_EXPEDITION_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXPEDITION_ROOT))

from handover_evidence import record_read  # noqa: E402
from handover_evidence import record_write  # noqa: E402

MODEL = "gemini-3.5-flash"
VARIANT = "h1"

# Held exactly constant across H0 and H1.
PROCEDURE_PAYLOAD = {
    "procedure_id": "P-7291",
    "title": "Task Boundary Test",
    "owner": "Alice Example",
    "control_ids": ["C-17", "C-29"],
    "sentinel": "BOUNDARY-7291-XQZ",
}


def read_procedure(procedure_id: str) -> dict:
    """Retrieves the full record of a procedure by its procedure id."""
    payload = dict(PROCEDURE_PAYLOAD)
    record_read(variant=VARIANT, procedure_id=procedure_id, payload=payload)
    return payload


def save_procedure(
    procedure_id: str = "",
    title: str = "",
    owner: str = "",
    control_ids: list[str] | None = None,
    sentinel: str = "",
) -> dict:
    """Saves a procedure record."""
    # Every field optional and recorded verbatim: a missing field shows up as
    # an empty value rather than pressuring the model to invent one.
    received = {
        "procedure_id": procedure_id,
        "title": title,
        "owner": owner,
        "control_ids": control_ids,
        "sentinel": sentinel,
    }
    record_write(variant=VARIANT, received=received)
    return {"status": "ok", "received": received}


worker = LlmAgent(
    model=MODEL,
    name="worker",
    mode="task",
    description="Reads and saves procedure records.",
    instruction=(
        "When asked to read a procedure, call read_procedure with the"
        " procedure id provided.\n"
        "When asked to save a procedure, call save_procedure.\n"
        # THE ONLY LINE THAT DIFFERS FROM H0.
        "After a read operation succeeds, call finish_task and include the"
        " complete information returned by the read tool. Preserve every"
        " returned field and value; do not merely summarize that the read"
        " succeeded."
    ),
    tools=[read_procedure, FunctionTool(save_procedure, require_confirmation=True)],
)

root_agent = LlmAgent(
    model=MODEL,
    name="root",
    description="Delegates procedure reads and saves to worker.",
    # Deliberately neutral: it must not hint that Root should carry payload
    # fields, since whether it does is part of what is being measured.
    instruction="When the user asks to read or save a procedure, delegate to worker.",
    sub_agents=[worker],
)
