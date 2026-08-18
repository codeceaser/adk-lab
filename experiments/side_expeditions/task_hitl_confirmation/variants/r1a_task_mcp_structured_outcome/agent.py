"""R1a - R0.1 plus a typed task outcome contract.

R0.1 established that prompt semantics alone make Reject terminal: 3/3 Reject
PASS and 3/3 Accept PASS. Its weakness is that the outcome is carried by a
model-chosen string — all three Reject runs happened to produce exactly
`{"result": "cancelled"}`, but nothing enforced it, so a consumer keying on
that string would depend on unenforced model behaviour.

R1a replaces that with a structured contract. The controlled difference from
`r0_1_task_mcp_root_semantics` is **the worker's `output_schema` and nothing
else** — both instructions are byte-identical to R0.1, as are both agent
names, descriptions, the model, `mode="task"`, the MCP server file, the tool
schema and `require_confirmation=True`.

ADK derives the `finish_task` declaration from the task agent's
`output_schema` (`agents/llm/task/_finish_task_tool.py`), so setting it here
is what makes `finish_task` enforce the contract. Nothing in this file calls
or wraps `finish_task`.

Deliberately still absent, per the R1a brief: callbacks, lifecycle state
store, retry guard, `ResumabilityConfig`, MCP or backend idempotency changes.

Evidence note, inherited from T2/R0/R0.1: this points at C1's
`write_value_mcp_server.py` itself, so all MCP variants exercise
byte-identical server code and its log lines carry `variant=c1`. Attribution
is by `run_marker`, unique per run.
"""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp import StdioServerParameters
from pydantic import BaseModel
from pydantic import Field

MODEL = "gemini-3.5-flash"
VARIANT = "r1a"


class TaskStatus(str, Enum):
    """Terminal outcome of a requested operation."""

    SUCCEEDED = "SUCCEEDED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class TaskOutcome(BaseModel):
    """Structured result the task agent must return when completing."""

    action_id: str = Field(
        description=(
            "Identifier of the requested operation. In this lab it is the run"
            " marker supplied with the request."
        )
    )
    status: TaskStatus = Field(
        description=(
            "SUCCEEDED if the operation completed; CANCELLED if the user"
            " rejected it; FAILED if it could not be completed for any other"
            " reason."
        )
    )
    message: str | None = Field(
        default=None, description="Optional human-readable detail."
    )


# The C1 server, shared rather than duplicated — as in T2, R0 and R0.1.
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
    # UNCHANGED from R0.1, byte for byte.
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
    # THE ONLY VARIABLE UNDER TEST. ADK builds the finish_task declaration
    # from this, so completing the task now has to satisfy TaskOutcome.
    output_schema=TaskOutcome,
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
    # UNCHANGED from R0.1, byte for byte.
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
