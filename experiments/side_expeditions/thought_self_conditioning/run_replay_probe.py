"""Controlled replay/strip probe for the thought_self_conditioning expedition.

Takes ONE frozen prior trajectory and builds two continuation requests that
differ only in whether the human-readable `model_exposed_thought` text part is
present:

    ARM R (replay)  user + thought text + function_call(+signature) + response
    ARM S (strip)   user +              function_call(+signature) + response

Everything else -- function_call id and args, the exact recorded
`thought_signature` bytes, the function_response and its id, the system
instruction, tool declarations, model, backend and generation config -- is
byte-identical across arms, because both arms are built by the same builder
from the same frozen source and ARM S is ARM R minus the thought-text parts.

The first model step is NOT regenerated per arm; it is frozen from prior
evidence, so no stochastic first-step variation enters the comparison.

    python experiments/side_expeditions/thought_self_conditioning/run_replay_probe.py \
        --specimen primary --reps 20

    python experiments/side_expeditions/thought_self_conditioning/run_replay_probe.py \
        --specimen primary --arm-diff-only

Source evidence is opened read-only and never rewritten.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import sys
import time
from datetime import datetime
from datetime import timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Provenance is explicit: every specimen names the commit, file, run and
# request index it was frozen from.
SPECIMENS = {
    "primary": {
        "specimen_id": "COT-03-ON-01#2",
        "source_commit": "fa019fe267a5f1b931b9d0d82d6aa115541a85f7",
        "source_file": (
            "experiments/side_expeditions/thought_context_replay/evidence/"
            "COT-03-ON-01_llm_requests.jsonl"
        ),
        "source_run_id": "COT-03-ON-01",
        "source_request_index": 2,
        "note": "ambiguous 'Cards' lookup that returned status=not_found",
    },
    "secondary": {
        "specimen_id": "COT-02-ON-01#2",
        "source_commit": "fa019fe267a5f1b931b9d0d82d6aa115541a85f7",
        "source_file": (
            "experiments/side_expeditions/thought_context_replay/evidence/"
            "COT-02-ON-01_llm_requests.jsonl"
        ),
        "source_run_id": "COT-02-ON-01",
        "source_request_index": 2,
        "note": "explicit AU-CARDS lookup on the successful path",
    },
}

ARMS = ("replay", "strip")

CATEGORIES = (
    "ASK_CLARIFICATION",
    "RETRY_SAME_TOOL",
    "RETRY_MUTATED_ARGUMENT",
    "CALL_OTHER_TOOL",
    "DIRECT_ANSWER",
    "OTHER",
    "NEEDS_HUMAN_REVIEW",
)


# --- frozen specimen -----------------------------------------------------


def load_specimen(specimen_key: str, repo_root: Path = REPO_ROOT) -> dict:
    """Reads the frozen request row. Read-only; the source file is never written."""
    spec = dict(SPECIMENS[specimen_key])
    path = repo_root / spec["source_file"]
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    matching = [r for r in rows if r["request_index"] == spec["source_request_index"]]
    if not matching:
        raise ValueError(
            f"request_index {spec['source_request_index']} not found in {path}"
        )
    spec["frozen"] = matching[0]
    return spec


def frozen_function_call(frozen: dict) -> dict:
    """The function_call recorded in the frozen trajectory, for classification."""
    for content in frozen["contents"]:
        for part in content["parts"]:
            call = part["raw"].get("function_call")
            if call:
                return call
    raise ValueError("frozen specimen contains no function_call")


# --- arm construction ----------------------------------------------------


def contents_from_frozen(frozen: dict):
    """Rebuilds Contents from the frozen record. Round-trips losslessly."""
    from google.genai import types

    contents = []
    for content in frozen["contents"]:
        parts = [types.Part.model_validate(p["raw"]) for p in content["parts"]]
        contents.append(types.Content(role=content["role"], parts=parts))
    return contents


def is_strippable_thought_part(part) -> bool:
    """True only for a human-readable thought part that carries nothing else.

    The guards matter. A part bearing a `function_call`, a `function_response`
    or a `thought_signature` is never stripped, so ARM S cannot lose an action,
    a result, or reasoning-continuity metadata -- only readable text.
    """
    return bool(
        part.thought
        and (part.text or "").strip()
        and part.function_call is None
        and part.function_response is None
        and part.thought_signature is None
    )


def strip_thought_text(contents) -> tuple[list, dict]:
    """Removes only human-readable thought parts. Returns (contents, stats)."""
    from google.genai import types

    stripped = 0
    retained_signature_bearing = 0
    out = []
    for content in contents:
        kept = []
        for part in content.parts or []:
            if is_strippable_thought_part(part):
                stripped += 1
                continue
            if part.thought and (part.text or "").strip():
                # A thought part that also carries a signature/call/response.
                retained_signature_bearing += 1
            kept.append(part)
        out.append(types.Content(role=content.role, parts=kept))
    return out, {
        "stripped_thought_text_parts": stripped,
        "retained_thought_parts_bearing_other_payload": retained_signature_bearing,
    }


async def canonical_tools():
    """The same BaseTool objects the lab agent uses; declarations come from ADK."""
    from adk_lab.agent import root_agent

    return await root_agent.canonical_tools()


def build_request(frozen: dict, arm: str, tools: list):
    """Builds a fresh LlmRequest for one arm.

    Fresh per call on purpose: `generate_content_async` mutates the request in
    place (it nulls `config.labels` and merges tracking headers), so reusing one
    object across continuations would let those mutations accumulate.
    """
    from google.adk.models.llm_request import LlmRequest
    from google.genai import types

    if arm not in ARMS:
        raise ValueError(f"unknown arm: {arm}")

    contents = contents_from_frozen(frozen)
    stats = {"stripped_thought_text_parts": 0}
    if arm == "strip":
        contents, stats = strip_thought_text(contents)

    request = LlmRequest(
        model=frozen["model"],
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=frozen["system_instruction"],
        ),
    )
    # Declarations are built by ADK's own append_tools, identically for both arms.
    request.append_tools(tools)
    return request, stats


# --- serialization -------------------------------------------------------


def serialize_part(part) -> dict:
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
    parts = list(parts or [])
    return {
        "thought_text_part_count": sum(
            1 for p in parts if p.thought and (p.text or "").strip()
        ),
        "thought_signature_count": sum(
            1 for p in parts if p.thought_signature is not None
        ),
        "function_call_count": sum(1 for p in parts if p.function_call is not None),
        "function_response_count": sum(
            1 for p in parts if p.function_response is not None
        ),
    }


def serialize_request(request) -> dict:
    config = getattr(request, "config", None)
    contents = []
    all_parts = []
    for content in request.contents or []:
        parts = list(content.parts or [])
        all_parts.extend(parts)
        entry = {"role": content.role, "parts": [serialize_part(p) for p in parts]}
        entry.update(summarize_parts(parts))
        contents.append(entry)

    record = {
        "model": request.model,
        "system_instruction": getattr(config, "system_instruction", None),
        "tool_declarations": (
            [t.model_dump(mode="json", exclude_none=True) for t in (config.tools or [])]
            if config
            else []
        ),
        "generation_config": (
            config.model_dump(mode="json", exclude_none=True, exclude={"tools"})
            if config
            else {}
        ),
        "content_count": len(contents),
        "contents": contents,
    }
    record.update(summarize_parts(all_parts))
    return record


def _payload_parts(record: dict, predicate) -> list:
    return [
        p["raw"]
        for c in record["contents"]
        for p in c["parts"]
        if predicate(p)
    ]


def arm_diff(replay_record: dict, strip_record: dict) -> dict:
    """Machine-readable proof that the arms differ only in thought text."""
    sig = lambda r: _payload_parts(r, lambda p: p["has_thought_signature"])
    call = lambda r: _payload_parts(r, lambda p: p["has_function_call"])
    resp = lambda r: _payload_parts(r, lambda p: p["has_function_response"])

    # Strip the intended variable out of the replay record, then require the
    # two records to be identical.
    replay_minus_thoughts = copy.deepcopy(replay_record)
    for content in replay_minus_thoughts["contents"]:
        content["parts"] = [
            p
            for p in content["parts"]
            if not (
                p["thought"]
                and (p["text"] or "").strip()
                and not p["has_function_call"]
                and not p["has_function_response"]
                and not p["has_thought_signature"]
            )
        ]
    for record in (replay_minus_thoughts,):
        for content in record["contents"]:
            content.update(
                {
                    "thought_text_part_count": sum(
                        1 for p in content["parts"] if p["thought"] and (p["text"] or "").strip()
                    ),
                    "thought_signature_count": sum(
                        1 for p in content["parts"] if p["has_thought_signature"]
                    ),
                    "function_call_count": sum(
                        1 for p in content["parts"] if p["has_function_call"]
                    ),
                    "function_response_count": sum(
                        1 for p in content["parts"] if p["has_function_response"]
                    ),
                }
            )
        record.update(
            {
                "thought_text_part_count": 0,
                "thought_signature_count": strip_record["thought_signature_count"],
                "function_call_count": strip_record["function_call_count"],
                "function_response_count": strip_record["function_response_count"],
            }
        )

    residual = []
    for key in sorted(set(replay_minus_thoughts) | set(strip_record)):
        if replay_minus_thoughts.get(key) != strip_record.get(key):
            residual.append(key)

    return {
        "identical_except": ["model_exposed_thought_text"],
        "thought_signature_equal": sig(replay_record) == sig(strip_record),
        "function_call_equal": call(replay_record) == call(strip_record),
        "function_response_equal": resp(replay_record) == resp(strip_record),
        "system_instruction_equal": (
            replay_record["system_instruction"] == strip_record["system_instruction"]
        ),
        "tool_declarations_equal": (
            replay_record["tool_declarations"] == strip_record["tool_declarations"]
        ),
        "model_equal": replay_record["model"] == strip_record["model"],
        "generation_config_equal": (
            replay_record["generation_config"] == strip_record["generation_config"]
        ),
        "replay_thought_text_part_count": replay_record["thought_text_part_count"],
        "strip_thought_text_part_count": strip_record["thought_text_part_count"],
        "residual_differences_after_removing_thought_text": residual,
        "arms_identical_after_removing_thought_text": not residual,
    }


# --- classification ------------------------------------------------------


def classify_response(response_record: dict, frozen_call: dict) -> str:
    """Deterministic classification of the immediate NEXT action only.

    Structural for the tool-calling categories. The ASK_CLARIFICATION /
    DIRECT_ANSWER split is a fixed *lexical* rule -- presence of '?' in the
    non-thought text -- not a semantic judgement, and no model adjudicates it.
    The raw response text is preserved in the evidence so the experiment owners
    can re-classify by any other rule.
    """
    calls = response_record.get("function_calls") or []
    if len(calls) > 1:
        return "NEEDS_HUMAN_REVIEW"
    if calls:
        call = calls[0]
        if call.get("name") != frozen_call.get("name"):
            return "CALL_OTHER_TOOL"
        if call.get("args") == frozen_call.get("args"):
            return "RETRY_SAME_TOOL"
        return "RETRY_MUTATED_ARGUMENT"

    text = (response_record.get("text") or "").strip()
    if not text:
        return "OTHER"
    return "ASK_CLARIFICATION" if "?" in text else "DIRECT_ANSWER"


def serialize_response(llm_responses: list) -> dict:
    """Flattens the adapter's responses into one record, keeping raw content."""
    text_chunks = []
    thought_chunks = []
    function_calls = []
    finish_reason = None
    usage = None
    raw = []

    for response in llm_responses:
        raw.append(response.model_dump(mode="json", exclude_none=True))
        if getattr(response, "finish_reason", None) is not None:
            finish_reason = str(response.finish_reason)
        if getattr(response, "usage_metadata", None) is not None:
            usage = response.usage_metadata.model_dump(mode="json", exclude_none=True)
        content = getattr(response, "content", None)
        for part in (content.parts if content and content.parts else []):
            if part.function_call is not None:
                function_calls.append(
                    part.function_call.model_dump(mode="json", exclude_none=True)
                )
            elif part.text is not None:
                (thought_chunks if part.thought else text_chunks).append(part.text)

    return {
        "text": "".join(text_chunks),
        "model_exposed_thought": "".join(thought_chunks),
        "model_exposed_thought_present": bool(thought_chunks),
        "function_calls": function_calls,
        "finish_reason": finish_reason,
        "usage_metadata": usage,
        "raw_responses": raw,
    }


# --- run -----------------------------------------------------------------


async def run_continuation(model, frozen: dict, arm: str, tools: list) -> dict:
    request, strip_stats = build_request(frozen, arm, tools)
    before = serialize_request(request)

    started = time.perf_counter()
    responses = []
    async for response in model.generate_content_async(request, stream=False):
        responses.append(response)
    latency_ms = round((time.perf_counter() - started) * 1000, 2)

    # The adapter mutates the request in place, so this is its post-send state.
    after = serialize_request(request)

    return {
        "arm": arm,
        "latency_ms": latency_ms,
        "strip_stats": strip_stats,
        "request_before_send": before,
        "request_after_send": after,
        "response": serialize_response(responses),
    }


async def main_async(args) -> None:
    from google.adk.cli.utils import envs

    envs.load_dotenv_for_agent("adk_lab", str(REPO_ROOT))

    from adk_lab.agent import root_agent

    spec = load_specimen(args.specimen)
    frozen = spec["frozen"]
    frozen_call = frozen_function_call(frozen)
    tools = await canonical_tools()
    evidence_dir = Path(args.evidence_dir) if args.evidence_dir else EVIDENCE_DIR
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # Arm-difference proof, written before any model call.
    replay_request, _ = build_request(frozen, "replay", tools)
    strip_request, strip_stats = build_request(frozen, "strip", tools)
    diff = arm_diff(serialize_request(replay_request), serialize_request(strip_request))
    diff.update(
        {
            "specimen_id": spec["specimen_id"],
            "source_commit": spec["source_commit"],
            "source_file": spec["source_file"],
            "source_run_id": spec["source_run_id"],
            "source_request_index": spec["source_request_index"],
            **strip_stats,
        }
    )
    diff_path = evidence_dir / f"{spec['specimen_id'].replace('#', '-')}_arm_diff.json"
    diff_path.write_text(json.dumps(diff, indent=2), encoding="utf-8")
    print(f"wrote {diff_path}")
    print(f"  arms_identical_after_removing_thought_text: "
          f"{diff['arms_identical_after_removing_thought_text']}")
    print(f"  thought_signature_equal: {diff['thought_signature_equal']}")
    print(f"  replay thought_text parts: {diff['replay_thought_text_part_count']} "
          f"| strip: {diff['strip_thought_text_part_count']}")

    if args.arm_diff_only:
        return
    if not diff["arms_identical_after_removing_thought_text"]:
        raise SystemExit(
            "arms differ by more than the thought text; refusing to run. "
            f"residual: {diff['residual_differences_after_removing_thought_text']}"
        )

    model = root_agent.canonical_model
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = (
        evidence_dir
        / f"{spec['specimen_id'].replace('#', '-')}_continuations_{stamp}.jsonl"
    )

    rows = []
    with out_path.open("w", encoding="utf-8") as fh:
        for rep in range(1, args.reps + 1):
            for arm in ARMS:
                record = await run_continuation(model, frozen, arm, tools)
                record.update(
                    {
                        "run_id": f"{spec['specimen_id']}-{arm}-{rep:02d}",
                        "specimen_id": spec["specimen_id"],
                        "source_commit": spec["source_commit"],
                        "source_file": spec["source_file"],
                        "source_run_id": spec["source_run_id"],
                        "source_request_index": spec["source_request_index"],
                        "rep": rep,
                        "model": frozen["model"],
                        "backend": str(model._api_backend),
                        "classification": classify_response(
                            record["response"], frozen_call
                        ),
                    }
                )
                fh.write(json.dumps(record) + "\n")
                rows.append(record)
                print(
                    f"  rep {rep:02d} {arm:<6} -> {record['classification']:<22}"
                    f" {record['latency_ms']:>8.0f}ms"
                )

    print(f"\nwrote {out_path} ({len(rows)} continuations)")
    report_counts(rows)


def report_counts(rows: list) -> None:
    import statistics

    for arm in ARMS:
        subset = [r for r in rows if r["arm"] == arm]
        if not subset:
            continue
        print(f"\n{arm.upper()} (N={len(subset)})")
        for category in CATEGORIES:
            n = sum(1 for r in subset if r["classification"] == category)
            if n:
                print(f"  {category:<24} {n}/{len(subset)}")
        prompt = [
            r["response"]["usage_metadata"].get("prompt_token_count", 0)
            for r in subset
            if r["response"]["usage_metadata"]
        ]
        completion = [
            r["response"]["usage_metadata"].get("candidates_token_count", 0)
            for r in subset
            if r["response"]["usage_metadata"]
        ]
        latency = [r["latency_ms"] for r in subset]
        for label, values in (
            ("prompt tokens", prompt),
            ("completion tokens", completion),
            ("latency ms", latency),
        ):
            if values:
                print(
                    f"  {label:<24} mean {statistics.mean(values):>9.1f}"
                    f"  median {statistics.median(values):>9.1f}"
                )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--specimen", default="primary", choices=sorted(SPECIMENS))
    parser.add_argument("--reps", type=int, default=20)
    parser.add_argument("--evidence-dir", default=None)
    parser.add_argument(
        "--arm-diff-only",
        action="store_true",
        help="Write the arm-difference proof and exit without model calls.",
    )
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
