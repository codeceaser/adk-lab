"""C1 - Root LlmAgent + write_value served over MCP, require_confirmation=True.

Separates basic ADK confirmation (established by C0) from MCP-specific
confirmation. The only intended difference from C0 is the transport:

    C0:  FunctionTool(write_value, require_confirmation=True)
    C1:  McpToolset(..., require_confirmation=True)  -> stdio MCP server

`require_confirmation` is passed to `McpToolset` natively. No FunctionTool
wrapper around MCP is used: that would test a wrapper, not ADK's MCP
confirmation path.
"""

from __future__ import annotations

import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp import StdioServerParameters

MODEL = "gemini-3.5-flash"
VARIANT = "c1"

_SERVER = Path(__file__).resolve().parent / "write_value_mcp_server.py"

root_agent = LlmAgent(
    model=MODEL,
    name="c1_root",
    description="Writes a value under a run marker.",
    # Same instruction as C0, so the two differ by transport alone.
    instruction=(
        "When asked to write a value, call write_value with the exact value and"
        " run marker provided."
    ),
    tools=[
        McpToolset(
            # sys.executable keeps the server on this venv's interpreter, so it
            # sees the same installed `mcp` as the agent process.
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=[str(_SERVER)],
                ),
            ),
            # The single variable under test in C1: native MCP confirmation.
            require_confirmation=True,
        )
    ],
)
