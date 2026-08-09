"""Deterministic unit tests for the three Python tools.

These call the plain Python functions directly. ADK is not involved and
nothing is mocked.
"""

from adk_lab.tools import (
    get_assessment_unit,
    get_employee,
    validate_proposal_fields,
)


def test_get_employee_known_id():
    result = get_employee("E1001")

    assert result["status"] == "success"
    assert result["employee"] == {
        "employee_id": "E1001",
        "name": "Anita Shah",
        "managed_geography": "CANADA",
        "assessment_units": ["AU-CARDS", "AU-DIGITAL"],
    }


def test_get_employee_unknown_id():
    result = get_employee("E9999")

    assert result["status"] == "not_found"
    assert result["employee_id"] == "E9999"
    assert "E9999" in result["error_message"]
    assert "employee" not in result


def test_get_assessment_unit_known_id():
    result = get_assessment_unit("AU-CARDS")

    assert result["status"] == "success"
    assert result["assessment_unit"] == {
        "assessment_unit_id": "AU-CARDS",
        "name": "Canada Cards",
        "managed_geography": "CANADA",
        "owner_employee_id": "E1001",
    }


def test_get_assessment_unit_unknown_id():
    result = get_assessment_unit("AU-NOPE")

    assert result["status"] == "not_found"
    assert result["assessment_unit_id"] == "AU-NOPE"
    assert "AU-NOPE" in result["error_message"]
    assert "assessment_unit" not in result


def test_get_assessment_unit_id_is_case_sensitive():
    # AU-DIGITAL is listed on the employee record but has no Assessment Unit
    # record of its own, so it must not resolve.
    assert get_assessment_unit("AU-DIGITAL")["status"] == "not_found"
    assert get_assessment_unit("au-cards")["status"] == "not_found"


def test_validate_proposal_fields_all_present():
    result = validate_proposal_fields(
        title="AI Compliance Assistant",
        description="Helps reviewers prepare reports",
        managed_geography="CANADA",
        assessment_unit_id="AU-CARDS",
    )

    assert result["status"] == "valid"
    assert result["missing_fields"] == []
    assert all(result["checked_fields"].values())


def test_validate_proposal_fields_one_field_empty():
    result = validate_proposal_fields(
        title="AI Compliance Assistant",
        description="",
        managed_geography="CANADA",
        assessment_unit_id="AU-CARDS",
    )

    assert result["status"] == "invalid"
    assert result["missing_fields"] == ["description"]
    assert result["checked_fields"]["description"] is False
    assert result["checked_fields"]["title"] is True


def test_validate_proposal_fields_several_fields_empty_or_whitespace():
    result = validate_proposal_fields(
        title="   ",
        description="",
        managed_geography="CANADA",
        assessment_unit_id="",
    )

    assert result["status"] == "invalid"
    assert result["missing_fields"] == ["title", "description", "assessment_unit_id"]
    assert result["checked_fields"]["managed_geography"] is True


def test_validate_proposal_fields_does_not_check_existence():
    # The Assessment Unit does not exist, but the presence check still passes.
    result = validate_proposal_fields(
        title="Anything",
        description="Anything",
        managed_geography="ATLANTIS",
        assessment_unit_id="AU-DOES-NOT-EXIST",
    )

    assert result["status"] == "valid"
