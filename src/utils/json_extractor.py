import json
import re


class JsonExtractionError(ValueError):
    """Raised when JSON extraction fails."""
    pass


def _sanitize_control_characters(candidate: str) -> str:
    """
    Convert literal newline, carriage-return and tab characters occurring
    INSIDE JSON string values into valid JSON escape sequences.

    Do not modify structural whitespace outside JSON strings.
    Do not alter already valid escape sequences.
    """
    result = []
    in_string = False
    escape_next = False

    for char in candidate:
        if not in_string:
            if char == '"':
                in_string = True
            result.append(char)
        else:
            if escape_next:
                escape_next = False
                result.append(char)
            elif char == '\\':
                escape_next = True
                result.append(char)
            elif char == '"':
                in_string = False
                result.append(char)
            elif char == '\n':
                result.append('\\n')
            elif char == '\r':
                result.append('\\r')
            elif char == '\t':
                result.append('\\t')
            else:
                result.append(char)

    return "".join(result)


def extract_json_object(text: str) -> dict:
    """
    Extract a JSON object from text that may include markdown fences,
    conversational wrappers, or whitespace.

    Uses a state-aware brace scanner that respects quoted strings
    and escaped characters.

    Args:
        text: Raw text possibly containing a JSON object.

    Returns:
        dict: The parsed JSON object.

    Raises:
        JsonExtractionError: If no valid JSON object can be extracted.
    """
    if not isinstance(text, str) or not text.strip():
        raise JsonExtractionError("Input text is empty or invalid.")

    # 1. Try strict parsing of raw text first
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    cleaned = text.strip()

    # 2 & 3. Unwrap markdown fenced code blocks anywhere in the text
    fence_pattern = re.compile(
        r"```(?:json)?\s*\n(.*?)```",
        re.DOTALL,
    )
    fence_match = fence_pattern.search(cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    # 4. State-aware brace scanner
    in_string = False
    escape_next = False
    brace_depth = 0
    start_idx = -1

    for i, char in enumerate(cleaned):
        if escape_next:
            escape_next = False
            continue

        if char == '"':
            in_string = not in_string
        elif char == '\\' and in_string:
            escape_next = True
        elif not in_string:
            if char == '{':
                if brace_depth == 0:
                    start_idx = i
                brace_depth += 1
            elif char == '}':
                if brace_depth > 0:
                    brace_depth -= 1
                    if brace_depth == 0:
                        candidate = cleaned[start_idx:i + 1]
                        # 5. Try strict parsing of candidate
                        try:
                            parsed = json.loads(candidate)
                        except json.JSONDecodeError as e:
                            # 6. ONLY if parsing fails specifically with "Invalid control character"
                            if "Invalid control character" in str(e):
                                sanitized = _sanitize_control_characters(candidate)
                                # 7. Retry json.loads() once on sanitized candidate
                                try:
                                    parsed = json.loads(sanitized)
                                except json.JSONDecodeError as retry_err:
                                    # 8. Raise clear extraction error without structural guessing
                                    raise JsonExtractionError(
                                        f"Failed to parse extracted JSON: {retry_err}\n"
                                        f"Extracted substring: {candidate[:200]}"
                                    ) from retry_err
                            else:
                                raise JsonExtractionError(
                                    f"Failed to parse extracted JSON: {e}\n"
                                    f"Extracted substring: {candidate[:200]}"
                                ) from e

                        if not isinstance(parsed, dict):
                            raise JsonExtractionError(
                                f"Extracted JSON is not an object, "
                                f"got {type(parsed).__name__}"
                            )
                        return parsed

    raise JsonExtractionError("No balanced JSON object found in text.")
