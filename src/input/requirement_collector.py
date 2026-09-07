import re
from typing import Callable


BANNER_TEXT = """
================================
AI DEVELOPMENT ORCHESTRATOR
PROJECT REQUIREMENTS
================================

Describe the project you want to build.

Enter your requirements below.
When finished, type a special terminator such as:

END
""".strip()


def normalize_requirements(text: str) -> str:
    """
    Normalize requirement text by stripping leading/trailing whitespace,
    removing trailing spaces on each line, and collapsing excessive consecutive blank lines.

    Preserves the user's actual requirement text and structure without altering meaning.
    """
    if not text:
        return ""

    # Normalize carriage returns to standard newlines
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip trailing whitespace on each line while preserving line indentation
    lines = [line.rstrip() for line in normalized.split("\n")]
    normalized = "\n".join(lines)

    # Collapse 3 or more consecutive newlines down to at most 2 newlines (1 blank line)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    # Strip overall leading and trailing whitespace
    return normalized.strip()


def collect_requirements(
    terminator: str = "END",
    input_func: Callable[[], str] = input,
    output_func: Callable[[str], None] = print,
) -> str:
    """
    Collect multi-line project requirements from the user via CLI.

    Continuously prompts until valid, non-empty requirements are provided.
    The user can enter multiple lines of text and finish by entering the terminator.

    Args:
        terminator: The keyword that signals the end of input (default: "END").
        input_func: Callable to read input lines (defaults to built-in input).
        output_func: Callable to display output messages (defaults to built-in print).

    Returns:
        str: Normalized non-empty project requirements.
    """
    while True:
        output_func("\n" + BANNER_TEXT + "\n")

        lines = []

        while True:
            try:
                line = input_func()
            except EOFError:
                break

            if line.strip().upper() == terminator.upper():
                break

            lines.append(line)

        raw_text = "\n".join(lines)
        normalized = normalize_requirements(raw_text)

        if normalized:
            return normalized

        output_func(
            "\n[ERROR] Requirements cannot be empty. "
            "Please provide a meaningful description of the project you want to build."
        )


def get_project_requirements(
    source: str = "cli",
    **kwargs,
) -> str:
    """
    Unified entry point for retrieving project requirements.

    Currently supports 'cli'. Designed for future extensions (such as 'gui',
    programmatic API, or configuration files).

    Args:
        source: Input source identifier (default: "cli").
        **kwargs: Additional parameters passed to the underlying collector.

    Returns:
        str: Normalized non-empty project requirements.
    """
    if source.lower() == "cli":
        return collect_requirements(**kwargs)

    raise ValueError(
        f"Unsupported requirement source: '{source}'. Supported sources: ['cli']"
    )
