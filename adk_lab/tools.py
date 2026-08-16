"""Business tools for Expedition E0.

Ordinary typed Python functions. They are handed to the ADK agent as-is, so
whatever ADK derives from these signatures and docstrings is exactly what the
model sees. Every function is deterministic, calls no LLM, reads no session
state, and returns a dict carrying an explicit status.
"""

from .sample_data import ASSESSMENT_UNITS, EMPLOYEES


def get_employee(employee_id: str) -> dict:
    """Retrieve an authoritative Employee record by Employee ID.

    Args:
        employee_id: The Employee ID to look up, for example "E1001".

    Returns:
        On a match, a dict with status "success" and an "employee" record
        holding employee_id, name, managed_geography and the list of
        assessment_units the employee is associated with. When no record
        exists, a dict with status "not_found", the employee_id that was
        looked up, and an error_message describing what was not found.
    """
    employee = EMPLOYEES.get(employee_id)
    if employee is None:
        return {
            "status": "not_found",
            "employee_id": employee_id,
            "error_message": (
                f"No Employee record exists for employee_id '{employee_id}'."
            ),
        }
    return {"status": "success", "employee": dict(employee)}


def get_assessment_unit(assessment_unit_id: str) -> dict:
    """Retrieve an authoritative Assessment Unit record by Assessment Unit ID.

    Args:
        assessment_unit_id: The Assessment Unit ID to look up, for example
            "AU-CARDS".

    Returns:
        On a match, a dict with status "success" and an "assessment_unit"
        record holding assessment_unit_id, name, managed_geography and
        owner_employee_id. When no record exists, a dict with status
        "not_found", the assessment_unit_id that was looked up, and an
        error_message describing what was not found.
    """
    assessment_unit = ASSESSMENT_UNITS.get(assessment_unit_id)
    if assessment_unit is None:
        return {
            "status": "not_found",
            "assessment_unit_id": assessment_unit_id,
            "error_message": (
                "No Assessment Unit record exists for assessment_unit_id"
                f" '{assessment_unit_id}'."
            ),
        }
    return {"status": "success", "assessment_unit": dict(assessment_unit)}


def validate_proposal_fields(
    title: str,
    description: str,
    managed_geography: str,
    assessment_unit_id: str,
) -> dict:
    """Check whether the four required Activity Proposal fields hold usable values.

    A field is usable when it is a non-empty string containing something other
    than whitespace. This is a presence check only: it does not confirm that
    the Assessment Unit exists or that the geography is a recognised value.

    Args:
        title: Proposed title of the Activity Proposal.
        description: Proposed description of the Activity Proposal.
        managed_geography: Managed geography the proposal belongs to, for
            example "CANADA".
        assessment_unit_id: Assessment Unit ID the proposal belongs to, for
            example "AU-CARDS".

    Returns:
        A dict with status "valid" when all four fields are usable and
        "invalid" otherwise, a "missing_fields" list naming the unusable
        fields, and a "checked_fields" map from each field name to whether it
        was usable.
    """
    candidate_fields = {
        "title": title,
        "description": description,
        "managed_geography": managed_geography,
        "assessment_unit_id": assessment_unit_id,
    }
    checked_fields = {
        name: bool(value and value.strip())
        for name, value in candidate_fields.items()
    }
    missing_fields = [name for name, usable in checked_fields.items() if not usable]
    return {
        "status": "invalid" if missing_fields else "valid",
        "missing_fields": missing_fields,
        "checked_fields": checked_fields,
    }
