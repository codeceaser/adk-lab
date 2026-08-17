"""T2 - Root LlmAgent delegating to a mode="task" worker that owns a
`write_value` tool served over MCP with require_confirmation=True.

The final composition: task delegation + native MCP confirmation.

Two controls hold this variant in place:

1. Topology is T1's. Agent names, descriptions and instructions are identical
   to `t1_task_function_confirmation`; only the tool changes. The controlled
   difference from T1 is exactly:

       FunctionTool(write_value, require_confirmation=True)
         ->  McpToolset(..., require_confirmation=True)

2. The tool implementation is C1's. This points at
   `c1_root_mcp_confirmation/write_value_mcp_server.py` itself rather than a
   copy, so C1 and T2 exercise byte-identical server code. Consequence worth
   knowing when reading evidence: lines that server appends to
   `evidence/mcp_tool_executions.jsonl` carry `variant=c1` even on T2 runs,
   because the tag is the server's. Attribution is by `run_marker`, which is
   unique per run, exactly as everywhere else in this expedition.

No FunctionTool wrapper, no rejection-handling instructions, no
ResumabilityConfig, callbacks, retries or continuation logic. `finish_task`
is injected by ADK for mode="task" agents; nothing here adds it.
"""

from __future__ import annotations

import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp import StdioServerParameters

MODEL = "gemini-3.5-flash"
VARIANT = "t2"

# The C1 server, shared rather than duplicated.
_SERVER = (
    Path(__file__).resolve().parents[1]
    / "c1_root_mcp_confirmation"
    / "write_value_mcp_server.py"
)

worker = LlmAgent(
    model=MODEL,
    name="worker",
    # ADK appends FinishTaskTool to this agent's tools because of mode="task".
    mode="task",
    description="Writes a value under a run marker.",
    instruction=(
        "When asked to write a value, call write_value with the exact value and"
        " run marker provided.\n"
        "After the tool succeeds, complete the task."
    ),
    # The only difference from T1: the confirmed tool now reaches the worker
    # over MCP instead of as a FunctionTool. Confirmation is still owned by the
    # task child, and require_confirmation is still native.
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
    instruction=(
        "When the user asks to write a value, delegate to worker with the"
        " exact value and run marker provided."
    ),
    # Same delegation wiring as T0/T1: ADK wraps the task agent in
    # _TaskAgentTool. No AgentTool is written by hand.
    sub_agents=[worker],
)
