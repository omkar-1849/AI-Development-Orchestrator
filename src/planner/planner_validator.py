import json

from src.planner.planner_contract import PlannerTask
from src.utils.json_extractor import extract_json_object, JsonExtractionError


REQUIRED_FIELDS = [
    "task_id",
    "status",
    "objective",
    "instructions",
    "files_allowed",
    "acceptance_criteria",
]


def validate_planner_response(response: str) -> PlannerTask:
    """
    Convert a raw Planner AI JSON response into a validated
    PlannerTask object.

    Raises ValueError if the response does not follow the contract.
    """

    try:
        data = extract_json_object(response)

    except JsonExtractionError as error:
        raise ValueError(
            f"Planner response is not valid JSON: {error}"
        )

    # Validate required fields
    missing_fields = []

    for field in REQUIRED_FIELDS:
        if field not in data:
            missing_fields.append(field)

    if missing_fields:
        raise ValueError(
            "Planner response is missing required fields: "
            + ", ".join(missing_fields)
        )

    # Validate basic field types
    if not isinstance(data["task_id"], str):
        raise ValueError("task_id must be a string")

    if not isinstance(data["status"], str):
        raise ValueError("status must be a string")

    if not isinstance(data["objective"], str):
        raise ValueError("objective must be a string")

    if not isinstance(data["instructions"], list):
        raise ValueError("instructions must be a list")

    if not isinstance(data["files_allowed"], list):
        raise ValueError("files_allowed must be a list")

    if not isinstance(data["acceptance_criteria"], list):
        raise ValueError(
            "acceptance_criteria must be a list"
        )

    # Create validated task
    task = PlannerTask(
        task_id=data["task_id"],
        status=data["status"],
        objective=data["objective"],
        instructions=data["instructions"],
        files_allowed=data["files_allowed"],
        acceptance_criteria=data["acceptance_criteria"],
    )

    return task