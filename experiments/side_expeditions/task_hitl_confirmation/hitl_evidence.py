"""Tool-side execution recorder for the task + HITL confirmation side expedition.

This module's only job is to prove, from the *implementation* side, how many
times a tool body actually ran. It appends one JSON line per real execution and
prints the same marker to stderr (visible in the ADK Web server console).

It is deliberately NOT a callback, NOT a tool wrapper and NOT an ADK plugin.
It is called from inside the tool body, so it cannot alter ADK execution.

Counting helper (run before and after clicking Accept/Reject):

    python experiments/side_expeditions/task_hitl_confirmation/hitl_evidence.py T1-R01
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
EXECUTION_LOG = EVIDENCE_DIR / "tool_executions.jsonl"

_LOCK = threading.Lock()


def record_execution(
    *,
    variant: str,
    tool: str,
    value: str,
    run_marker: str,
    transport: str = "function",
) -> str:
    """Appends one line of evidence that a tool body really executed.

    Returns the marker string so the tool can also return it to the model.
    """
    marker = (
        f"TOOL_EXECUTED variant={variant} tool={tool}"
        f" run_marker={run_marker} value={value}"
    )
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "variant": variant,
        "tool": tool,
        "transport": transport,
        "value": value,
        "run_marker": run_marker,
        "pid": os.getpid(),
        "marker": marker,
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with EXECUTION_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    print(marker, file=sys.stderr, flush=True)
    return marker


def count_executions(run_marker: str | None = None) -> int:
    """Counts recorded tool-body executions, optionally for one run marker."""
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
