"""Minimal local MCP server exposing one tool: write_value(value, run_marker).

Runs as a stdio subprocess spawned by ADK's McpToolset. It is deliberately the
smallest thing that can serve one tool:

- one tool, same conceptual payload as C0's FunctionTool
- no external side effect
- its own append-only execution log, written from inside this process, so the
  count is evidence from the MCP implementation side of the boundary

stdout belongs to the MCP stdio transport. Nothing here may print to it; the
recorder writes to stderr, which ADK surfaces through McpToolset's errlog.

Run directly for a smoke test:  python write_value_mcp_server.py
(it will sit waiting for MCP frames on stdin; Ctrl-C to exit)
"""

from __future__ import annotations

import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# The expedition root holds mcp_evidence.py. This server is spawned as its own
# process with an arbitrary working directory, so locate it from __file__.
_EXPEDITION_ROOT = Path(__file__).resolve().parents[2]
if str(_EXPEDITION_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXPEDITION_ROOT))

from mcp_evidence import record_execution  # noqa: E402

VARIANT = "c1"

mcp = FastMCP("write-value-server")


@mcp.tool()
def write_value(value: str, run_marker: str) -> dict:
    """Writes a value under a run marker."""
    # Recorded from inside the tool body in the server process: this line is
    # proof the MCP implementation ran, independent of anything the agent
    # process observed.
    marker = record_execution(
        variant=VARIANT, tool="write_value", value=value, run_marker=run_marker
    )
    return {"status": "ok", "marker": marker}


if __name__ == "__main__":
    mcp.run(transport="stdio")
