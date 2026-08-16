"""T0 - Root LlmAgent delegating to a mode="task" worker, no confirmation.

Tests the task lifecycle on its own: delegation, tool execution inside the task,
task completion, and return of the task result to Root.

`finish_task` is injected by ADK for mode="task" agents; nothing here adds it.
"""

from __future__ import annotations

import sys
from pathlib import Path

from google.adk.agents import LlmAgent

# See the C0 variant for why the expedition root goes on sys.path.
_EXPEDITION_ROOT = Path(__file__).resolve().parents[2]
if str(_EXPEDITION_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXPEDITION_ROOT))

from hitl_evidence import record_execution  # noqa: E402

MODEL = "gemini-3.5-flash"
VARIANT = "t0"


def write_value(value: str, run_marker: str) -> dict:
    """Writes a value under a run marker."""
    # Recorded from inside the tool body so the count is evidence of real
    # execution, not of ADK merely deciding to call the tool.
    marker = record_execution(
        variant=VARIANT, tool="write_value", value=value, run_marker=run_marker
    )
    return {"status": "ok", "marker": marker}


worker = LlmAgent(
    model=MODEL,
    name="t0_worker",
    # The variable under test in T0: the task lifecycle on its own. ADK appends
    # FinishTaskTool to this agent's tools because of mode="task" (verified:
    # worker.tools == [write_value, FinishTaskTool:finish_task]).
    mode="task",
    description="Writes a value under a run marker.",
    instruction=(
        "When asked to write a value, call write_value with the exact value and"
        " run marker provided.\n"
        "After the tool succeeds, complete the task."
    ),
    # Plain function, no confirmation. T1 is this variant plus confirmation.
    tools=[write_value],
)

root_agent = LlmAgent(
    model=MODEL,
    name="t0_root",
    description="Delegates value writing to t0_worker.",
    instruction=(
        "When the user asks to write a value, delegate to t0_worker with the"
        " exact value and run marker provided."
    ),
    # Declaring the task agent as a sub-agent is the whole delegation wiring:
    # ADK wraps it in an internal _TaskAgentTool on this Root agent. No
    # AgentTool is written by hand here (see the ground rules).
    sub_agents=[worker],
)
