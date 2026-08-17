"""R0 - T2 topology with an explicit rejection path in the worker instruction.

Tests one narrow hypothesis: can instructions give Reject a business meaning
— "cancel this proposed operation and complete the task" — without any
callback, state machine, retry guard or framework customisation?

The controlled difference from `t2_task_mcp_confirmation` is **the worker
instruction and nothing else**. Same Root and worker names, same model, same
MCP server file, same `write_value(value, run_marker)` schema, same
`require_confirmation=True`, same evidence logging. No FunctionTool wrapper,
no ResumabilityConfig, no callbacks, no continuation logic, no retry logic,
no state flags.

The instruction describes intent in business terms only. It says nothing
about how ADK confirmation works internally, and never mentions FunctionCall
ids or framework events — R0 tests semantic behaviour, not whether the model
can be taught ADK internals.

`finish_task` is injected by ADK for mode="task" agents; nothing here adds it.

Evidence note, inherited from T2: this points at C1's
`write_value_mcp_server.py` itself rather than a copy, so C1, T2 and R0 all
exercise byte-identical server code. Lines that server appends to
`evidence/mcp_tool_executions.jsonl` therefore carry `variant=c1`.
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
VARIANT = "r0"

# The C1 server, shared rather than duplicated — as in T2.
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
    # THE ONLY VARIABLE UNDER TEST. T2's instruction is the first two lines;
    # everything after gives rejection a defined completion path.
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
    # Identical to T2. R0 tests whether the task worker can terminate its own
    # bounded task correctly, so no rejection logic is added at Root.
    instruction=(
        "When the user asks to write a value, delegate to worker with the"
        " exact value and run marker provided."
    ),
    sub_agents=[worker],
)
