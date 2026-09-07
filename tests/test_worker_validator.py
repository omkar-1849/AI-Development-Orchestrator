from src.worker.worker_validator import (
    validate_worker_response,
    WorkerValidationError,
)


def test_valid_response():

    print("\n--- TEST 1 - VALID RESPONSE ---")

    response = """
{
    "implementation_summary": "Calculator module implemented successfully",
    "files_modified": [
        "calculator.py",
        "test_calculator.py"
    ],
    "changes_made": [
        "Added arithmetic functions",
        "Added division by zero handling"
    ],
    "acceptance_check": [
        "Addition works",
        "Subtraction works",
        "Division by zero handled"
    ],
    "blockers": "NONE"
}
"""

    try:
        result = validate_worker_response(response)

        print("ACCEPTED")
        print("Summary:", result.implementation_summary)

    except WorkerValidationError as error:
        print("REJECTED")
        print("Reason:", error)


def test_invalid_json():

    print("\n--- TEST 2 - INVALID JSON ---")

    response = """
{
    "implementation_summary": "Test"
    "files_modified": []
}
"""

    try:
        validate_worker_response(response)
        print("ERROR: Invalid response accepted")

    except WorkerValidationError as error:
        print("REJECTED")
        print("Reason:", error)


def test_missing_fields():

    print("\n--- TEST 3 - MISSING FIELDS ---")

    response = """
{
    "implementation_summary": "Test",
    "files_modified": []
}
"""

    try:
        validate_worker_response(response)
        print("ERROR: Invalid response accepted")

    except WorkerValidationError as error:
        print("REJECTED")
        print("Reason:", error)


def test_wrong_type():

    print("\n--- TEST 4 - WRONG TYPE ---")

    response = """
{
    "implementation_summary": "Test",
    "files_modified": "calculator.py",
    "changes_made": [],
    "acceptance_check": [],
    "blockers": "NONE"
}
"""

    try:
        validate_worker_response(response)
        print("ERROR: Invalid response accepted")

    except WorkerValidationError as error:
        print("REJECTED")
        print("Reason:", error)


if __name__ == "__main__":

    test_valid_response()
    test_invalid_json()
    test_missing_fields()
    test_wrong_type()