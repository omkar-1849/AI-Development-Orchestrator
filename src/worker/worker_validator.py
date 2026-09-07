import json

from src.worker.worker_response import WorkerResponse


class WorkerValidationError(Exception):
    """Raised when the Worker response is invalid."""
    pass


def validate_worker_response(response: str) -> WorkerResponse:
    """
    Parse and validate a Worker response.

    Returns:
        WorkerResponse

    Raises:
        WorkerValidationError
    """

    try:
        data = json.loads(response)

    except json.JSONDecodeError as error:
        raise WorkerValidationError(
            f"Worker response is not valid JSON: {error}"
        )

    required_fields = {
        "implementation_summary",
        "files_modified",
        "changes_made",
        "acceptance_check",
        "blockers",
    }

    missing_fields = (
        required_fields - data.keys()
    )

    if missing_fields:
        raise WorkerValidationError(
            "Worker response is missing required fields: "
            + ", ".join(missing_fields)
        )

    if not isinstance(
        data["implementation_summary"],
        str
    ):
        raise WorkerValidationError(
            "implementation_summary must be a string"
        )

    if not isinstance(
        data["files_modified"],
        list
    ):
        raise WorkerValidationError(
            "files_modified must be a list"
        )

    if not isinstance(
        data["changes_made"],
        list
    ):
        raise WorkerValidationError(
            "changes_made must be a list"
        )

    if not isinstance(
        data["acceptance_check"],
        list
    ):
        raise WorkerValidationError(
            "acceptance_check must be a list"
        )

    if not isinstance(
        data["blockers"],
        str
    ):
        raise WorkerValidationError(
            "blockers must be a string"
        )

    return WorkerResponse(
        implementation_summary=data[
            "implementation_summary"
        ],
        files_modified=data[
            "files_modified"
        ],
        changes_made=data[
            "changes_made"
        ],
        acceptance_check=data[
            "acceptance_check"
        ],
        blockers=data[
            "blockers"
        ],
    )