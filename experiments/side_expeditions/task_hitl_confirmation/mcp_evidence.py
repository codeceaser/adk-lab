"""Server-side execution recorder for the MCP variants (C1, later T2).

Deliberately parallel to, and independent of, `hitl_evidence.py`:

- It writes to a *different* file (`evidence/mcp_tool_executions.jsonl`), so an
  MCP tool invocation can never be confused with a FunctionTool one.
- It runs inside the MCP server process, which ADK spawns as a separate
  subprocess over stdio. The count therefore comes from the implementation
  side of the MCP boundary, not from anything in the agent process.

`hitl_evidence.py` is Phase 1 code and is not modified.

Counting helper (run before and after clicking Accept/Reject):

    python experiments/side_expeditions/task_hitl_confirmation/mcp_evidence.py C1-A01
"""

from __future__ import annotations

import json
import os
import sys
import threading
from datetime import datetime
from datetime import timezone
from pathlib import Path

EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence"
EXECUTION_LOG = EVIDENCE_DIR / "mcp_tool_executions.jsonl"

_LOCK = threading.Lock()


def record_execution(*, variant: str, tool: str, value: str, run_marker: str) -> str:
    """Appends one line of evidence that an MCP tool body really executed."""
    marker = (
        f"MCP_TOOL_EXECUTED variant={variant} tool={tool}"
        f" run_marker={run_marker} value={value}"
    )
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "variant": variant,
        "tool": tool,
        "transport": "mcp-stdio",
        "value": value,
        "run_marker": run_marker,
        "pid": os.getpid(),
        "marker": marker,
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with EXECUTION_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    # stderr, not stdout: stdout is the MCP stdio transport and must carry
    # nothing but protocol frames. ADK surfaces the server's stderr via errlog.
    print(marker, file=sys.stderr, flush=True)
    return marker


def count_executions(run_marker: str | None = None) -> int:
    """Counts recorded MCP tool-body executions, optionally for one marker."""
    if not EXECUTION_LOG.exists():
        return 0
    count = 0
    with EXECUTION_LOG.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if run_marker is None or entry.get("run_marker") == run_marker:
                count += 1
    return count


if __name__ == "__main__":
    marker = sys.argv[1] if len(sys.argv) > 1 else None
    print(count_executions(marker))
