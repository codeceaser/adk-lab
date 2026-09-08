"""Tests for the thought_context_replay probe instrumentation.

These test the recorder, not the model. Nothing here calls a backend.

The load-bearing test is `test_recorder_is_non_altering`: the probe's whole
claim is that it observes the outgoing request without changing it, so that
claim is asserted rather than assumed.
"""

import importlib.util
from pathlib import Path

from google.adk.models.llm_request import LlmRequest
from google.genai import types

PROBE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "side_expeditions"
    / "thought_context_replay"
    / "run_probe.py"
)

_spec = importlib.util.spec_from_file_location("run_probe", PROBE_PATH)
run_probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_probe)


def _thought_text_part():
    return types.Part(text="considering the unit", thought=True)


def _function_call_part():
    return types.Part(
        function_call=types.FunctionCall(name="get_assessment_unit", args={"au": "X"})
    )


def test_serialize_part_preserves_thought_fields():
    part = types.Part(text="why", thought=True, thought_signature=b"\xff\x00sig")
    record = run_probe.serialize_part(part)

    assert record["thought"] is True
    assert record["text"] == "why"
    assert record["has_thought_signature"] is True
    assert record["thought_signature_len"] == 5
    # Binary signature survives serialization rather than crashing it.
    assert "thought_signature" in record["raw"]


def test_serialize_part_distinguishes_signature_from_thought():
    """A signature-only part is not a model_exposed_thought."""
    part = types.Part(text="answer", thought_signature=b"sig")
    record = run_probe.serialize_part(part)

    assert record["thought"] is False
    assert record["has_thought_signature"] is True


def test_summarize_parts_counts_each_kind():
    parts = [
        _thought_text_part(),
        _function_call_part(),
        types.Part(
            function_response=types.FunctionResponse(
                name="get_assessment_unit", response={"ok": True}
            )
        ),
        types.Part(text="plain", thought_signature=b"sig"),
    ]
    counts = run_probe.summarize_parts(parts)

    assert counts["thought_text_part_count"] == 1
    assert counts["thought_signature_count"] == 1
    assert counts["function_call_count"] == 1
    assert counts["function_response_count"] == 1


def test_summarize_parts_flags_mixed_thought_and_function_call():
    """Phase E: the mixed-event shape must be detectable, not inferred."""
    counts = run_probe.summarize_parts([_thought_text_part(), _function_call_part()])
    assert counts["mixed_thought_and_function_call"] is True


def test_summarize_parts_does_not_flag_mixed_when_separate():
    assert (
        run_probe.summarize_parts([_thought_text_part()])[
            "mixed_thought_and_function_call"
        ]
        is False
    )
    assert (
        run_probe.summarize_parts([_function_call_part()])[
            "mixed_thought_and_function_call"
        ]
        is False
    )


def test_thought_only_part_without_text_is_not_counted_as_thought_text():
    counts = run_probe.summarize_parts([types.Part(text="   ", thought=True)])
    assert counts["thought_text_part_count"] == 0


def test_serialize_request_counts_across_contents():
    request = LlmRequest(
        model="test-model",
        contents=[
            types.Content(role="user", parts=[types.Part(text="hi")]),
            types.Content(
                role="model", parts=[_thought_text_part(), _function_call_part()]
            ),
        ],
    )
    record = run_probe.serialize_request(
        request, run_id="R", mode="thoughts_on", request_index=2
    )

    assert record["request_index"] == 2
    assert record["content_count"] == 2
    assert record["thought_text_part_count"] == 1
    assert record["function_call_count"] == 1
    assert record["mixed_thought_and_function_call"] is True


def test_recorder_is_non_altering():
    """The observer must return None and leave the request untouched.

    A truthy return would short-circuit the model call at
    `base_llm_flow.py:1391`; a mutated request would change the very thing
    being measured.
    """
    parts = [_thought_text_part(), _function_call_part()]
    request = LlmRequest(
        model="test-model",
        contents=[types.Content(role="model", parts=parts)],
    )
    before = request.model_dump(mode="json")

    records = []
    callback = run_probe.make_before_model_recorder(
        records, run_id="R", mode="thoughts_on"
    )
    result = callback(callback_context=None, llm_request=request)

    assert result is None
    assert request.model_dump(mode="json") == before
    assert len(records) == 1


def test_recorder_numbers_requests_in_sequence():
    records = []
    callback = run_probe.make_before_model_recorder(
        records, run_id="R", mode="thoughts_off"
    )
    request = LlmRequest(model="m", contents=[])

    callback(callback_context=None, llm_request=request)
    callback(callback_context=None, llm_request=request)

    assert [r["request_index"] for r in records] == [1, 2]


def test_cases_and_modes_are_the_declared_matrix():
    assert sorted(run_probe.CASES) == ["COT-01", "COT-02", "COT-03"]
    assert run_probe.MODES == {"thoughts_on": True, "thoughts_off": False}
