"""C0 - Root LlmAgent + write_value FunctionTool with require_confirmation=True.

Baseline: does native ADK confirmation work in this environment at all, with no
task mode involved?
"""

from __future__ import annotations

import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

# ADK loads each variant as a top-level package from `variants/`, so the shared
# evidence recorder one level up is not importable by relative import. Put the
# expedition root on sys.path instead of duplicating the recorder per variant.
_EXPEDITION_ROOT = Path(__file__).resolve().parents[2]
if str(_EXPEDITION_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXPEDITION_ROOT))

from hitl_evidence import record_execution  # noqa: E402

MODEL = "gemini-3.5-flash"
VARIANT = "c0"


def write_value(value: str, run_marker: str) -> dict:
    """Writes a value under a run marker."""
    # Recording happens inside the tool body, never in a callback or wrapper, so
    # the count reflects real executions and cannot perturb ADK's own flow.
    marker = record_execution(
        variant=VARIANT, tool="write_value", value=value, run_marker=run_marker
    )
    return {"status": "ok", "marker": marker}


root_agent = LlmAgent(
    model=MODEL,
    name="c0_root",
    description="Writes a value under a run marker.",
    # Minimal instruction on purpose: the experiment measures ADK execution, not
    # prompt quality. Anything more would be a prompt trick under the ground rules.
    instruction=(
        "When asked to write a value, call write_value with the exact value and"
        " run marker provided."
    ),
    # The single variable under test in C0: native confirmation at Root level,
    # with no task mode anywhere in the tree.
    tools=[FunctionTool(write_value, require_confirmation=True)],
)
