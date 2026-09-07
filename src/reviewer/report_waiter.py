import time
from pathlib import Path


REPORT_END_MARKER = "<!-- REPORT_END -->"


def wait_for_report(
    project_path,
    report_path,
    timeout=300,
    poll_interval=2
):
    full_path = Path(project_path) / report_path

    print(
        f"\nWaiting for report: {full_path}"
    )

    start_time = time.time()

    while True:

        if full_path.exists():

            try:
                content = full_path.read_text(
                    encoding="utf-8"
                )

                if REPORT_END_MARKER in content:

                    print(
                        "Report completed successfully."
                    )

                    return content

            except Exception as error:
                print(
                    f"Error reading report: {error}"
                )

        if time.time() - start_time >= timeout:
            raise TimeoutError(
                f"Timed out waiting for report: "
                f"{full_path}"
            )

        time.sleep(poll_interval)