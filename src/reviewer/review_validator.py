import json

from src.reviewer.review_contract import ReviewResult


VALID_DECISIONS = {
    "APPROVED",
    "CORRECTION_NEEDED",
    "BLOCKED",
    "REPLAN"
}


VALID_NEXT_ACTIONS = {
    "NEXT_PHASE",
    "RETRY_PHASE",
    "STOP",
    "REPLAN"
}


def validate_review_response(response):

    try:
        data = json.loads(response)

    except json.JSONDecodeError:
        raise ValueError(
            "Reviewer response is not valid JSON"
        )

    required_fields = [
        "review_id",
        "decision",
        "phase_completed",
        "summary",
        "issues",
        "next_action",
        "next_phase"
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(
                f"Missing required field: {field}"
            )

    if data["decision"] not in VALID_DECISIONS:
        raise ValueError(
            f"Invalid decision: {data['decision']}"
        )

    if data["next_action"] not in VALID_NEXT_ACTIONS:
        raise ValueError(
            f"Invalid next action: {data['next_action']}"
        )

    if not isinstance(data["issues"], list):
        raise ValueError(
            "Issues must be a list"
        )

    # =========================
    # VALIDATE NEXT PHASE
    # =========================

    next_phase = data["next_phase"]

    if data["next_action"] == "NEXT_PHASE":

        if next_phase is None:
            raise ValueError(
                "next_phase is required when "
                "next_action is NEXT_PHASE"
            )

        if not isinstance(next_phase, dict):
            raise ValueError(
                "next_phase must be an object"
            )

        required_next_phase_fields = [
            "objective",
            "instructions",
            "files_allowed",
            "acceptance_criteria"
        ]

        for field in required_next_phase_fields:
            if field not in next_phase:
                raise ValueError(
                    f"Missing next_phase field: {field}"
                )

        if not isinstance(
            next_phase["instructions"],
            list
        ):
            raise ValueError(
                "next_phase instructions must be a list"
            )

        if not isinstance(
            next_phase["files_allowed"],
            list
        ):
            raise ValueError(
                "next_phase files_allowed must be a list"
            )

        if not isinstance(
            next_phase["acceptance_criteria"],
            list
        ):
            raise ValueError(
                "next_phase acceptance_criteria "
                "must be a list"
            )

    else:

        if next_phase is not None:
            raise ValueError(
                "next_phase must be null when "
                "next_action is not NEXT_PHASE"
            )

    return ReviewResult(
        review_id=data["review_id"],
        decision=data["decision"],
        phase_completed=data["phase_completed"],
        summary=data["summary"],
        issues=data["issues"],
        next_action=data["next_action"],
        next_phase=next_phase
    )