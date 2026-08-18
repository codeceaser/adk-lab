"""Payload recorders for the task-boundary handover diagnostic (H0, H1).

The question is which fields survive each boundary, so these recorders capture
**whole payloads**, not just counts. Two separate files, for the same reason
the other channels are separate: a read must never be countable as a write.

    evidence/handover_reads.jsonl    what the read tool returned
    evidence/handover_writes.jsonl   what the write tool actually received

The write recorder stores the arguments verbatim, including which keys were
absent, so a dropped or mutated field is visible rather than inferred.

Inspect:

    python experiments/side_expeditions/task_hitl_confirmation/handover_evidence.py
"""

from __future__ import annotations

import json
import os
import sys
import threading
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence"
READ_LOG = EVIDENCE_DIR / "handover_reads.jsonl"
WRITE_LOG = EVIDENCE_DIR / "handover_writes.jsonl"

_LOCK = threading.Lock()


def _append(path: Path, entry: dict[str, Any]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")


def record_read(*, variant: str, procedure_id: str, payload: dict[str, Any]) -> str:
    """Records that the read tool ran, and exactly what it returned."""
    marker = f"HANDOVER_READ variant={variant} procedure_id={procedure_id}"
    _append(
        READ_LOG,
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "variant": variant,
            "tool": "read_procedure",
            "kind": "read",
            "procedure_id": procedure_id,
            "payload": payload,
            "pid": os.getpid(),
            "marker": marker,
        },
    )
    print(marker, file=sys.stderr, flush=True)
    return marker


def record_write(*, variant: str, received: dict[str, Any]) -> str:
    """Records that the write tool ran, and exactly what arguments arrived."""
    marker = f"HANDOVER_WRITE variant={variant} keys={sorted(received.keys())}"
    _append(
        WRITE_LOG,
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "variant": variant,
            "tool": "save_procedure",
            "kind": "write",
            "received": received,
            "received_keys": sorted(received.keys()),
            "pid": os.getpid(),
            "marker": marker,
        },
    )
    print(marker, file=sys.stderr, flush=True)
    return marker


def _dump(path: Path, label: str) -> None:
    print(f"--- {label} ({path.name}) ---")
    if not path.exists():
        print("  (no entries)")
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            body = entry.get("payload", entry.get("received"))
            print(f"  {entry['ts']}  {entry['variant']}  {json.dumps(body)}")


if __name__ == "__main__":
    _dump(READ_LOG, "reads")
    _dump(WRITE_LOG, "writes")
