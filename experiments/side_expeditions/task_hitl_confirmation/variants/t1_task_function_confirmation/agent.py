"""T1 - Root LlmAgent delegating to a mode="task" worker that owns a
`write_value` FunctionTool with require_confirmation=True.

The decisive composition experiment: task delegation + native confirmation.

Control: this file is byte-identical to the T0 variant except for
`require_confirmation` (True here, False in T0) and the VARIANT tag passed to
the evidence recorder. Agent names, descriptions, instructions and the tool
wrapper are deliberately the same, so any T0/T1 difference in behaviour is
attributable to the confirmation flag alone.

`finish_task` is injected by ADK for mode="task" agents; nothing here adds it.
"""

from __future__ import annotations

import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

# See the C0 variant for why the expedition root goes on sys.path.
_EXPEDITION_ROOT = Path(__file__).resolve().parents[2]
if str(_EXPEDITION_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXPEDITION_ROOT))

from hitl_evidence import record_execution  # noqa: E402

MODEL = "gemini-3.5-flash"
VARIANT = "t1"


def write_value(value: str, run_marker: str) -> dict:
    """Writes a value under a run marker."""
    # The count taken before and after the Accept/Reject click is the primary
    # evidence for checkpoint G (did the pending tool actually execute?).
    marker = record_execution(
        variant=VARIANT, tool="write_value", value=value, run_marker=run_marker
    )
    return {"status": "ok", "marker": marker}


worker = LlmAgent(
    model=MODEL,
    name="worker",
    # ADK appends FinishTaskTool to this agent's tools because of mode="task"
    # (verified: worker.tools == [write_value, FinishTaskTool:finish_task]).
    mode="task",
    description="Writes a value under a run marker.",
    instruction=(
        "When asked to write a value, call write_value with the exact value and"
        " run marker provided.\n"
        "After the tool succeeds, complete the task."
    ),
    # The only difference from T0. Confirmation is now owned by the task child
    # rather than by Root, which is the composition this expedition exists to
    # test. Everything else is held constant against T0 on purpose.
    tools=[FunctionTool(write_value, require_confirmation=True)],
)

root_agent = LlmAgent(
    model=MODEL,
    name="root",
    description="Delegates value writing to worker.",
    instruction=(
        "When the user asks to write a value, delegate to worker with the"
        " exact value and run marker provided."
    ),
    # Same delegation wiring as T0: ADK wraps the task agent in _TaskAgentTool.
    sub_agents=[worker],
)
