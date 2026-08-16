"""Exports raw ADK Web session events for one run, as evidence.

Read-only: it calls the ADK Web REST API that the UI itself uses, so it does
not touch execution. Run it while `adk web` is still up.

    python experiments/side_expeditions/task_hitl_confirmation/export_session.py \
        --app t0_task_plain_tool --session <session_id> --run-marker T0-R01

Omit --session to list the sessions for the app and exit.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence"


def _get(url: str):
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8932")
    parser.add_argument("--app", required=True)
    parser.add_argument("--user", default="user")
    parser.add_argument("--session")
    parser.add_argument("--run-marker", required=False)
    args = parser.parse_args()

    root = f"{args.base_url}/apps/{args.app}/users/{args.user}/sessions"

    if not args.session:
        for session in _get(root):
            print(session.get("id"), session.get("lastUpdateTime"))
        return

    session = _get(f"{root}/{args.session}")
    name = args.run_marker or args.session
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    session_path = EVIDENCE_DIR / f"{name}_session.json"
    session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")

    events_path = EVIDENCE_DIR / f"{name}_events.jsonl"
    with events_path.open("w", encoding="utf-8") as fh:
        for event in session.get("events", []):
            fh.write(json.dumps(event) + "\n")

    print(f"wrote {session_path}")
    print(f"wrote {events_path} ({len(session.get('events', []))} events)")


if __name__ == "__main__":
    main()
