"""Probe for the thought_context_replay side expedition.

Records two separate streams for one run:

    <run_id>_events.jsonl        what ADK emitted (Phase A)
    <run_id>_llm_requests.jsonl  what was actually sent back (Phase B)

They are written to distinct files on purpose. The question this expedition
asks is whether a `model_exposed_thought` that appears in an Event also
appears in the *next* `request_context`, so conflating the two streams would
destroy the measurement.

    python experiments/side_expeditions/thought_context_replay/run_probe.py \
        --case COT-02 --mode thoughts_on --run-id COT-02-ON-01

`--mode thoughts_off` is the control. The only variable it changes is
`ThinkingConfig.include_thoughts`; model, tools, instruction, description,
prompts and runner config are held constant by construction -- they are read
from the main lab agent rather than restated here.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence"
APP_NAME = "thought_context_replay"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CASES = {
    "COT-01": "What information do I need for an activity proposal?",
    "COT-02": "Show me information for AU-CARDS.",
    "COT-03": "Tell me about Cards.",
}

MODES = {"thoughts_on": True, "thoughts_off": False}


# --- serialization -------------------------------------------------------
# Deliberately lossless about thought-related fields. `model_dump(mode="json")`
# base64-encodes `thought_signature` (bytes), so the raw part survives intact.


def serialize_part(part) -> dict:
    """One Part: raw dump plus the flags this expedition reads."""
    return {
        "raw": part.model_dump(mode="json", exclude_none=True),
        "text": part.text,
        "thought": bool(part.thought),
        "has_thought_signature": part.thought_signature is not None,
        "thought_signature_len": (
            len(part.thought_signature) if part.thought_signature else 0
        ),
        "has_function_call": part.function_call is not None,
        "has_function_response": part.function_response is not None,
    }


def summarize_parts(parts) -> dict:
    """Counts over a flat list of Parts."""
    parts = list(parts or [])
    thought_text = [p for p in parts if p.thought and (p.text or "").strip()]
    function_calls = [p for p in parts if p.function_call is not None]
    return {
        "thought_text_part_count": len(thought_text),
        "thought_signature_count": sum(
            1 for p in parts if p.thought_signature is not None
        ),
        "function_call_count": len(function_calls),
        "function_response_count": sum(
            1 for p in parts if p.function_response is not None
        ),
        # Phase E: one event/content carrying both at once.
        "mixed_thought_and_function_call": bool(thought_text and function_calls),
    }


def serialize_event(event, *, run_id: str, mode: str, event_index: int) -> dict:
    parts = list(event.content.parts) if event.content and event.content.parts else []
    record = {
        "run_id": run_id,
        "mode": mode,
        "event_index": event_index,
        "event_id": getattr(event, "id", None),
        "invocation_id": getattr(event, "invocation_id", None),
        "branch": getattr(event, "branch", None),
        "author": getattr(event, "author", None),
        "role": event.content.role if event.content else None,
        "parts": [serialize_part(p) for p in parts],
    }
    record.update(summarize_parts(parts))
    return record


def serialize_request(
    llm_request, *, run_id: str, mode: str, request_index: int
) -> dict:
    """Snapshot of the outgoing LlmRequest. Reads only; never mutates."""
    config = getattr(llm_request, "config", None)
    system_instruction = getattr(config, "system_instruction", None) if config else None

    contents = []
    all_parts = []
    for content in llm_request.contents or []:
        parts = list(content.parts or [])
        all_parts.extend(parts)
        entry = {
            "role": content.role,
            "parts": [serialize_part(p) for p in parts],
        }
        entry.update(summarize_parts(parts))
        contents.append(entry)

    record = {
        "run_id": run_id,
        "mode": mode,
        "request_index": request_index,
        "model": getattr(llm_request, "model", None),
        "system_instruction": (
            system_instruction
            if isinstance(system_instruction, str) or system_instruction is None
            else str(system_instruction)
        ),
        "content_count": len(contents),
        "contents": contents,
    }
    record.update(summarize_parts(all_parts))
    return record


def make_before_model_recorder(records: list, *, run_id: str, mode: str):
    """Builds the Phase B observer.

    Returns None on every call, which is what keeps it an observer: at
    `base_llm_flow.py:1391` a falsy return lets the flow proceed with the same
    `llm_request` object, whereas a returned `LlmResponse` would short-circuit
    the model call. The callback only reads the request.
    """

    def record_before_model(callback_context, llm_request):
        records.append(
            serialize_request(
                llm_request,
                run_id=run_id,
                mode=mode,
                request_index=len(records) + 1,
            )
        )
        return None

    return record_before_model


# --- probe ---------------------------------------------------------------


def build_probe_agent(*, include_thoughts: bool, before_model_callback):
    """An isolated agent. The main lab agent is read, never modified."""
    from google.adk.agents import LlmAgent
    from google.adk.planners import BuiltInPlanner
    from google.genai import types

    from adk_lab.agent import root_agent

    return LlmAgent(
        model=root_agent.model,
        name=root_agent.name,
        description=root_agent.description,
        instruction=root_agent.instruction,
        tools=list(root_agent.tools),
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(include_thoughts=include_thoughts)
        ),
        before_model_callback=before_model_callback,
    )


async def run_probe(*, case: str, mode: str, run_id: str, evidence_dir: Path) -> dict:
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    request_records: list = []
    agent = build_probe_agent(
        include_thoughts=MODES[mode],
        before_model_callback=make_before_model_recorder(
            request_records, run_id=run_id, mode=mode
        ),
    )

    runner = InMemoryRunner(agent=agent, app_name=APP_NAME)
    await runner.session_service.create_session(
        app_name=APP_NAME, user_id="user", session_id=run_id
    )

    event_records = []
    async for event in runner.run_async(
        user_id="user",
        session_id=run_id,
        new_message=types.Content(role="user", parts=[types.Part(text=CASES[case])]),
    ):
        event_records.append(
            serialize_event(
                event, run_id=run_id, mode=mode, event_index=len(event_records) + 1
            )
        )

    evidence_dir.mkdir(parents=True, exist_ok=True)
    events_path = evidence_dir / f"{run_id}_events.jsonl"
    requests_path = evidence_dir / f"{run_id}_llm_requests.jsonl"
    for path, rows in ((events_path, event_records), (requests_path, request_records)):
        with path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")

    return {
        "events_path": events_path,
        "requests_path": requests_path,
        "event_records": event_records,
        "request_records": request_records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True, choices=sorted(CASES))
    parser.add_argument("--mode", required=True, choices=sorted(MODES))
    parser.add_argument("--run-id")
    parser.add_argument("--evidence-dir", default=None)
    args = parser.parse_args()

    run_id = args.run_id or (
        f"{args.case}-{args.mode}-"
        f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    )
    evidence_dir = Path(args.evidence_dir) if args.evidence_dir else EVIDENCE_DIR

    from google.adk.cli.utils import envs

    envs.load_dotenv_for_agent("adk_lab", str(REPO_ROOT))

    result = asyncio.run(
        run_probe(
            case=args.case, mode=args.mode, run_id=run_id, evidence_dir=evidence_dir
        )
    )

    print(f"run_id={run_id} case={args.case} mode={args.mode}")
    print(f"prompt: {CASES[args.case]}")
    print(f"wrote {result['events_path']} ({len(result['event_records'])} events)")
    print(
        f"wrote {result['requests_path']} "
        f"({len(result['request_records'])} llm requests)"
    )
    print()
    print("per-request counts (index: thought_text / thought_sig / fcall / fresp):")
    for row in result["request_records"]:
        mixed = "  [mixed]" if row["mixed_thought_and_function_call"] else ""
        print(
            f"  {row['request_index']}: "
            f"{row['thought_text_part_count']} / {row['thought_signature_count']} / "
            f"{row['function_call_count']} / {row['function_response_count']}{mixed}"
        )


if __name__ == "__main__":
    main()
