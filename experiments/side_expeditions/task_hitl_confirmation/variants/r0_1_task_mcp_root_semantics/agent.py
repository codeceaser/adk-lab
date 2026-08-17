"""R0.1 - R0 plus an explicit cancellation path in the ROOT instruction.

R0-R01 established that worker-level rejection semantics work: after the
rejected `write_value` result the worker called
`finish_task({"result": "cancelled"})`, returned the cancelled result to
Root, and did not retry within that delegation. The remaining retry happened
at Root, which re-delegated the identical request.

R0.1 tests whether Root can be given the matching terminal semantics by
instruction alone. The controlled difference from
`r0_task_mcp_rejection_semantics` is **the Root instruction and nothing
else** — the worker instruction is unchanged, as are both agent names,
descriptions, the model, the MCP server file, the tool schema and
`require_confirmation=True`.

No callbacks, no state flags or state machine, no MCP changes, no retry
guards, no `ResumabilityConfig`, no structured task output. `finish_task` is
injected by ADK for mode="task" agents; nothing here adds it.

Evidence note, inherited from T2/R0: this points at C1's
`write_value_mcp_server.py` itself, so C1, T2, R0 and R0.1 all exercise
byte-identical server code, and its log lines carry `variant=c1`.
Attribution is by `run_marker`, unique per run.
"""

from __future__ import annotations

import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp import StdioServerParameters

MODEL = "gemini-3.5-flash"
VARIANT = "r0_1"

# The C1 server, shared rather than duplicated — as in T2 and R0.
_SERVER = (
    Path(__file__).resolve().parents[1]
    / "c1_root_mcp_confirmation"
    / "write_value_mcp_server.py"
)

worker = LlmAgent(
    model=MODEL,
    name="worker",
    mode="task",
    description="Writes a value under a run marker.",
    # UNCHANGED from R0. R0-R01 showed this half already works.
    instruction=(
        "When asked to write a value, call write_value with the exact value"
        " and run marker provided.\n"
        "If write_value succeeds, complete the task with a success result.\n"
        "If write_value is rejected by the user:\n"
        "- treat the requested write as cancelled;\n"
        "- do not call write_value again;\n"
        "- do not request confirmation again;\n"
        "- complete the task with a cancelled result.\n"
        "Do not retry a rejected write unless the human user later issues a"
        " new, explicit write request in a new interaction."
    ),
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=[str(_SERVER)],
                ),
            ),
            require_confirmation=True,
        )
    ],
)

root_agent = LlmAgent(
    model=MODEL,
    name="root",
    description="Delegates value writing to worker.",
    # THE ONLY VARIABLE UNDER TEST. R0's instruction is the first line;
    # everything after makes a cancelled worker result terminal for the
    # current request.
    instruction=(
        "When the user asks to write a value, delegate to worker with the"
        " exact value and run marker provided.\n"
        "If the worker reports that the operation was cancelled or rejected"
        " by the user, that is the final outcome for this request:\n"
        "- do not delegate the same write again;\n"
        "- do not attempt the operation by any other means;\n"
        "- tell the user the operation was cancelled.\n"
        "Attempt the write again only after the user makes a new, explicit"
        " request."
    ),
    sub_agents=[worker],
)
