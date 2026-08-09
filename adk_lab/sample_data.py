"""In-memory sample data for the E0 experiment.

Two records, held in plain dicts. There is no database, no file I/O and no
network access anywhere in this module. Keeping the data this small makes it
obvious which values the model could only have obtained from a tool call.
"""

EMPLOYEES = {
    "E1001": {
        "employee_id": "E1001",
        "name": "Anita Shah",
        "managed_geography": "CANADA",
        "assessment_units": ["AU-CARDS", "AU-DIGITAL"],
    },
}

ASSESSMENT_UNITS = {
    "AU-CARDS": {
        "assessment_unit_id": "AU-CARDS",
        "name": "Canada Cards",
        "managed_geography": "CANADA",
        "owner_employee_id": "E1001",
    },
}
