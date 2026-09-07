from src.automation.claude_sender import send_prompt
from src.automation.claude_waiter import wait_for_response
from src.automation.claude_response import capture_latest_response

from src.worker._legacy.worker_prompt import build_worker_prompt
from src.worker._legacy.worker_validator import validate_worker_response


def execute_worker(claude, worker_task):
    """
    Execute a Worker task using the AI model.

    Returns a validated WorkerResponse.
    """

    print("\nBuilding Worker prompt...")

    worker_prompt = build_worker_prompt(
        worker_task
    )

    print("\nSending task to Worker...")

    send_prompt(
        claude,
        worker_prompt
    )

    print("\nWaiting for Worker response...")

    wait_for_response(
        claude
    )

    print("\nCapturing Worker response...")

    response = capture_latest_response(
        claude
    )

    if not response:
        raise RuntimeError(
            "Failed to capture Worker response"
        )

    print("\n--- RAW WORKER RESPONSE ---\n")
    print(response)

    print("\nValidating Worker response...")

    worker_response = validate_worker_response(
        response
    )

    print("WORKER RESPONSE ACCEPTED")

    return worker_response, worker_prompt, response
