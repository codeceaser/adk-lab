"""Validation tests for the thought_self_conditioning replay/strip harness.

These run before any model call and prove the arms differ only in the intended
variable. Nothing here contacts a backend.

Covers the nine required proofs:
  1. replay/strip identical after removing the intended thought-text difference
  2. thought_signature byte-identical across arms
  3. function_call and function_response identical across arms
  4. call/response IDs unchanged
  5. tool declarations identical
  6. system instruction identical
  7. strip removes only human-readable thought parts
  8. no signature-bearing or call-bearing part is removed
  9. frozen source evidence is not mutated
"""

import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from google.genai import types

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_PATH = (
    REPO_ROOT
    / "experiments"
    / "side_expeditions"
    / "thought_self_conditioning"
    / "run_replay_probe.py"
)

_spec = importlib.util.spec_from_file_location("run_replay_probe", PROBE_PATH)
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)


@pytest.fixture(scope="module")
def specimen():
    return probe.load_specimen("primary")


@pytest.fixture(scope="module")
def tools():
    return asyncio.run(probe.canonical_tools())


@pytest.fixture(scope="module")
def arms(specimen, tools):
    frozen = specimen["frozen"]
    replay, _ = probe.build_request(frozen, "replay", tools)
    strip, stats = probe.build_request(frozen, "strip", tools)
    return (
        probe.serialize_request(replay),
        probe.serialize_request(strip),
        stats,
    )


def _parts(record, predicate):
    return [p for c in record["contents"] for p in c["parts"] if predicate(p)]


# --- proof 1: identical except the intended variable ----------------------


def test_arms_identical_after_removing_thought_text(arms):
    replay, strip, _ = arms
    diff = probe.arm_diff(replay, strip)

    assert diff["arms_identical_after_removing_thought_text"] is True
    assert diff["residual_differences_after_removing_thought_text"] == []
    assert diff["identical_except"] == ["model_exposed_thought_text"]


def test_the_variable_actually_differs(arms):
    """Guards against a vacuous pass: the arms must differ in thought text."""
    replay, strip, _ = arms
    assert replay["thought_text_part_count"] > 0
    assert strip["thought_text_part_count"] == 0


# --- proofs 2-6: everything else held constant ---------------------------


def test_thought_signature_byte_identical(arms):
    replay, strip, _ = arms
    sig = lambda r: [
        p["raw"]["thought_signature"] for p in _parts(r, lambda x: x["has_thought_signature"])
    ]

    assert sig(replay) == sig(strip)
    assert len(sig(replay)) == 1
    # Byte-for-byte, not merely present.
    replay_bytes = types.Part.model_validate(
        _parts(replay, lambda x: x["has_thought_signature"])[0]["raw"]
    ).thought_signature
    strip_bytes = types.Part.model_validate(
        _parts(strip, lambda x: x["has_thought_signature"])[0]["raw"]
    ).thought_signature
    assert replay_bytes == strip_bytes
    assert hashlib.sha256(replay_bytes).hexdigest() == hashlib.sha256(strip_bytes).hexdigest()


def test_function_call_and_response_identical(arms):
    replay, strip, _ = arms
    call = lambda r: [p["raw"]["function_call"] for p in _parts(r, lambda x: x["has_function_call"])]
    resp = lambda r: [
        p["raw"]["function_response"] for p in _parts(r, lambda x: x["has_function_response"])
    ]

    assert call(replay) == call(strip)
    assert resp(replay) == resp(strip)


def test_function_call_and_response_ids_unchanged(arms, specimen):
    replay, strip, _ = arms
    frozen_call = probe.frozen_function_call(specimen["frozen"])

    call_ids = lambda r: [
        p["raw"]["function_call"].get("id")
        for p in _parts(r, lambda x: x["has_function_call"])
    ]
    resp_ids = lambda r: [
        p["raw"]["function_response"].get("id")
        for p in _parts(r, lambda x: x["has_function_response"])
    ]

    assert call_ids(replay) == call_ids(strip) == [frozen_call["id"]]
    assert resp_ids(replay) == resp_ids(strip) == [frozen_call["id"]]


def test_tool_declarations_identical_and_present(arms):
    replay, strip, _ = arms
    assert replay["tool_declarations"] == strip["tool_declarations"]
    assert replay["tool_declarations"], "tool declarations must not be empty"


def test_system_instruction_identical_and_present(arms):
    replay, strip, _ = arms
    assert replay["system_instruction"] == strip["system_instruction"]
    assert replay["system_instruction"]


def test_model_and_generation_config_identical(arms):
    replay, strip, _ = arms
    assert replay["model"] == strip["model"]
    assert replay["generation_config"] == strip["generation_config"]


# --- proofs 7-8: strip removes only what it should ------------------------


def test_strip_removes_only_thought_text_parts(arms):
    replay, strip, stats = arms

    assert stats["stripped_thought_text_parts"] == replay["thought_text_part_count"]
    # Nothing else lost.
    assert replay["function_call_count"] == strip["function_call_count"]
    assert replay["function_response_count"] == strip["function_response_count"]
    assert replay["thought_signature_count"] == strip["thought_signature_count"]
    assert replay["content_count"] == strip["content_count"]


def test_signature_bearing_part_is_never_stripped():
    part = types.Part(text="reasoning", thought=True, thought_signature=b"sig")
    assert probe.is_strippable_thought_part(part) is False


def test_function_call_bearing_thought_part_is_never_stripped():
    part = types.Part(
        text="reasoning",
        thought=True,
        function_call=types.FunctionCall(name="t", args={}),
    )
    assert probe.is_strippable_thought_part(part) is False


def test_function_response_bearing_thought_part_is_never_stripped():
    part = types.Part(
        text="reasoning",
        thought=True,
        function_response=types.FunctionResponse(name="t", response={}),
    )
    assert probe.is_strippable_thought_part(part) is False


def test_plain_text_part_is_never_stripped():
    assert probe.is_strippable_thought_part(types.Part(text="answer")) is False


def test_strippable_part_is_the_readable_thought():
    assert probe.is_strippable_thought_part(types.Part(text="why", thought=True)) is True


# --- proof 9: frozen source is not mutated -------------------------------


def test_frozen_source_evidence_not_mutated(specimen, tools):
    path = REPO_ROOT / specimen["source_file"]
    before = hashlib.sha256(path.read_bytes()).hexdigest()

    frozen = specimen["frozen"]
    probe.build_request(frozen, "replay", tools)
    probe.build_request(frozen, "strip", tools)

    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_building_strip_arm_does_not_mutate_frozen_dict(specimen, tools):
    frozen = specimen["frozen"]
    before = json.dumps(frozen, sort_keys=True)

    probe.build_request(frozen, "strip", tools)
    probe.build_request(frozen, "replay", tools)

    assert json.dumps(frozen, sort_keys=True) == before


# --- filler arm ----------------------------------------------------------
# Token counting is stubbed so these stay offline and deterministic. The real
# token match is asserted at runtime and recorded in arm_diff.json.


def _fake_counter(text):
    """One token per whitespace-separated word."""
    return len(text.split())


@pytest.fixture(scope="module")
def filler_arms(specimen, tools):
    frozen = specimen["frozen"]
    text, achieved = probe.build_filler_text(50, _fake_counter)
    replay, _ = probe.build_request(frozen, "replay", tools)
    strip, _ = probe.build_request(frozen, "strip", tools)
    filler, stats = probe.build_request(frozen, "filler", tools, filler_text=text)
    return (
        probe.serialize_request(replay),
        probe.serialize_request(filler),
        probe.serialize_request(strip),
        stats,
        text,
        achieved,
    )


def test_build_filler_text_matches_target_length():
    text, achieved = probe.build_filler_text(50, _fake_counter)
    assert achieved == 50
    assert _fake_counter(text) == 50


def test_build_filler_text_handles_awkward_targets():
    for target in (1, 2, 7, 613):
        _, achieved = probe.build_filler_text(target, _fake_counter)
        assert achieved == target


def test_filler_arm_keeps_one_thought_part(filler_arms):
    replay, filler, strip, stats, _, _ = filler_arms
    assert filler["thought_text_part_count"] == replay["thought_text_part_count"] == 1
    assert strip["thought_text_part_count"] == 0
    assert stats["replaced_thought_text_parts"] == 1


def test_filler_content_differs_from_replay(filler_arms):
    replay, filler, _, _, text, _ = filler_arms
    replay_text = [
        p["text"] for c in replay["contents"] for p in c["parts"] if p["thought"]
    ]
    filler_text = [
        p["text"] for c in filler["contents"] for p in c["parts"] if p["thought"]
    ]
    assert filler_text == [text]
    assert filler_text != replay_text


def test_filler_identical_to_replay_apart_from_thought_content(filler_arms):
    replay, filler, strip, _, _, achieved = filler_arms
    diff = probe.filler_diff(replay, filler, strip, 50, achieved)

    assert diff["filler_identical_to_replay_after_normalizing_thought_text"] is True
    assert diff["residual_differences_after_normalizing_thought_text"] == []
    assert diff["thought_text_content_differs_from_replay"] is True
    assert diff["thought_signature_equal_to_replay"] is True
    assert diff["function_call_equal_to_replay"] is True
    assert diff["function_response_equal_to_replay"] is True
    assert diff["system_instruction_equal_to_replay"] is True
    assert diff["tool_declarations_equal_to_replay"] is True
    assert diff["generation_config_equal_to_replay"] is True
    assert diff["thought_text_part_count_differs_from_strip"] is True


def test_filler_arm_preserves_signature_and_ids(filler_arms):
    replay, filler, _, _, _, _ = filler_arms
    for predicate in (
        lambda p: p["has_thought_signature"],
        lambda p: p["has_function_call"],
        lambda p: p["has_function_response"],
    ):
        assert _parts(replay, predicate) == _parts(filler, predicate)


def test_filler_arm_requires_filler_text(specimen, tools):
    with pytest.raises(ValueError):
        probe.build_request(specimen["frozen"], "filler", tools)


def test_filler_arm_is_a_declared_arm():
    assert probe.ARMS == ("replay", "strip", "filler")


# --- classifier ----------------------------------------------------------


FROZEN_CALL = {"name": "get_assessment_unit", "args": {"assessment_unit_id": "Cards"}}


def test_classify_retry_same_tool():
    record = {"function_calls": [dict(FROZEN_CALL)], "text": ""}
    assert probe.classify_response(record, FROZEN_CALL) == "RETRY_SAME_TOOL"


def test_classify_retry_mutated_argument():
    record = {
        "function_calls": [
            {"name": "get_assessment_unit", "args": {"assessment_unit_id": "AU-CARDS"}}
        ],
        "text": "",
    }
    assert probe.classify_response(record, FROZEN_CALL) == "RETRY_MUTATED_ARGUMENT"


def test_classify_call_other_tool():
    record = {"function_calls": [{"name": "get_employee", "args": {}}], "text": ""}
    assert probe.classify_response(record, FROZEN_CALL) == "CALL_OTHER_TOOL"


def test_classify_ask_clarification():
    record = {"function_calls": [], "text": "Which assessment unit did you mean?"}
    assert probe.classify_response(record, FROZEN_CALL) == "ASK_CLARIFICATION"


def test_classify_direct_answer():
    record = {"function_calls": [], "text": "No record exists for that unit."}
    assert probe.classify_response(record, FROZEN_CALL) == "DIRECT_ANSWER"


def test_classify_other_when_empty():
    record = {"function_calls": [], "text": "   "}
    assert probe.classify_response(record, FROZEN_CALL) == "OTHER"


def test_classify_needs_human_review_for_parallel_calls():
    record = {
        "function_calls": [dict(FROZEN_CALL), {"name": "get_employee", "args": {}}],
        "text": "",
    }
    assert probe.classify_response(record, FROZEN_CALL) == "NEEDS_HUMAN_REVIEW"


# --- provenance ----------------------------------------------------------


def test_specimen_provenance_is_recorded(specimen):
    for field in (
        "specimen_id",
        "source_commit",
        "source_file",
        "source_run_id",
        "source_request_index",
    ):
        assert specimen[field]
    assert specimen["source_run_id"] == "COT-03-ON-01"
    assert specimen["source_request_index"] == 2
