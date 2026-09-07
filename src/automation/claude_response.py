import pyperclip
from src.automation.claude_sender import _ensure_desktop_access


def capture_latest_response(claude):
    """
    Find and extract the latest Claude response directly
    from the accessibility tree.

    Also copies the extracted response to the system clipboard.
    """
    _ensure_desktop_access()
    print("Locating latest Claude response...")

    claude_responses = []

    # Fast path: search Text elements directly
    try:
        for element in claude.descendants(control_type="Text"):
            try:
                info = element.element_info
                name = (info.name or "").strip()
                if name.startswith("Claude responded:"):
                    claude_responses.append(element)
            except Exception:
                continue
    except Exception:
        pass

    # Fallback: search all descendants if needed
    if not claude_responses:
        for element in claude.descendants():
            try:
                info = element.element_info
                if info.control_type != "Text":
                    continue
                name = (info.name or "").strip()
                if name.startswith("Claude responded:"):
                    claude_responses.append(element)
            except Exception:
                continue

    print(f"Found {len(claude_responses)} Claude response markers.")

    if not claude_responses:
        raise RuntimeError("No Claude responses found")

    # Get latest Claude response
    latest_marker = claude_responses[-1]

    print("Latest Claude response marker found.")

    try:
        parent = latest_marker.parent()

        print(
            f"Response container: "
            f"{parent.element_info.control_type} - "
            f"{parent.element_info.name}"
        )

        texts = []

        # Extract all text from this response container
        for child in parent.descendants():
            try:
                info = child.element_info
                if info.control_type == "Text":
                    text = (info.name or "").strip()
                    if text:
                        texts.append(text)
            except Exception:
                continue

        if not texts:
            raise RuntimeError(
                "Response container contains no text"
            )

        print("Extracting response text...")

        # Remove accessibility marker text
        actual_texts = []
        for text in texts:
            if text.startswith("Claude responded:"):
                continue
            actual_texts.append(text)

        # Extract response
        if actual_texts:
            response = "\n".join(actual_texts).strip()
        else:
            # Fallback: extract directly from marker
            marker_text = latest_marker.element_info.name.strip()
            response = marker_text.replace(
                "Claude responded:",
                "",
                1
            ).strip()

        if not response:
            raise RuntimeError(
                "Could not extract actual response text"
            )

        # ------------------------------------------
        # CLEAN RESPONSE FOR PLANNER JSON
        # ------------------------------------------

        # Extract JSON object if present
        start = response.find("{")
        end = response.rfind("}")

        if start != -1 and end != -1 and end > start:
            response = response[start:end + 1]
        else:
            # Remove known Claude UI metadata
            ui_metadata = {
                "just now",
                "now",
                "Read aloud",
                "Good response",
                "Bad response",
                "Retry",
                "Copy",
            }

            clean_lines = []
            for line in response.splitlines():
                if line.strip().lower() in {
                    item.lower() for item in ui_metadata
                }:
                    continue
                clean_lines.append(line)

            response = "\n".join(clean_lines).strip()

        # ------------------------------------------
        # COPY TO SYSTEM CLIPBOARD
        # ------------------------------------------

        print("Copying Claude response to clipboard...")
        pyperclip.copy(response)

        print(
            "Claude response extracted and copied "
            "to clipboard successfully."
        )

        return response

    except Exception as e:
        raise RuntimeError(
            f"Failed to extract Claude response: {e}"
        )