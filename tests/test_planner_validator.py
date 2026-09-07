import json

from src.planner.planner_validator import (
    validate_planner_response,
)


def run_test(name, response):

    print(f"\n--- {name} ---")

    try:
        task = validate_planner_response(response)

        print("ACCEPTED")
        print(f"Task ID: {task.task_id}")

    except ValueError as error:
        print("REJECTED")
        print(f"Reason: {error}")


def main():

    # --------------------------------
    # TEST 1: Valid response
    # --------------------------------

    valid_response = json.dumps({
        "task_id": "TASK-001",
        "status": "READY",
        "objective": "Test objective",
        "instructions": [
            "Do something"
        ],
        "files_allowed": [
            "src/test.py"
        ],
        "acceptance_criteria": [
            "It works"
        ]
    })

    run_test(
        "TEST 1 - VALID RESPONSE",
        valid_response
    )

    # --------------------------------
    # TEST 2: Invalid JSON
    # --------------------------------

    invalid_json = """
    {
        "task_id": "TASK-002",
        "status": "READY"
    """

    run_test(
        "TEST 2 - INVALID JSON",
        invalid_json
    )

    # --------------------------------
    # TEST 3: Missing fields
    # --------------------------------

    missing_fields = json.dumps({
        "task_id": "TASK-003",
        "status": "READY",
        "objective": "Incomplete task"
    })

    run_test(
        "TEST 3 - MISSING FIELDS",
        missing_fields
    )

    # --------------------------------
    # TEST 4: Wrong type
    # --------------------------------

    wrong_type = json.dumps({
        "task_id": "TASK-004",
        "status": "READY",
        "objective": "Wrong type test",
        "instructions": "This should be a list",
        "files_allowed": [],
        "acceptance_criteria": []
    })

    run_test(
        "TEST 4 - WRONG TYPE",
        wrong_type
    )


if __name__ == "__main__":
    main()