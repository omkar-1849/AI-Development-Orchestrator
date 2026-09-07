from src.memory.database import get_connection


def save_interaction(
    agent: str,
    model: str,
    prompt: str,
    response: str,
    status: str = "completed"
):
    """Save an AI interaction to the SQLite database."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO interactions (
            agent,
            model,
            prompt,
            response,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            agent,
            model,
            prompt,
            response,
            status
        )
    )

    interaction_id = cursor.lastrowid

    connection.commit()
    connection.close()

    print(f"Interaction saved with ID: {interaction_id}")

    return interaction_id


def get_interaction(interaction_id: int):
    """Retrieve one interaction by its ID."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            agent,
            model,
            prompt,
            response,
            status,
            created_at
        FROM interactions
        WHERE id = ?
        """,
        (interaction_id,)
    )

    interaction = cursor.fetchone()

    connection.close()

    return interaction


def get_latest_interaction():
    """Retrieve the most recent interaction."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            agent,
            model,
            prompt,
            response,
            status,
            created_at
        FROM interactions
        ORDER BY id DESC
        LIMIT 1
        """
    )

    interaction = cursor.fetchone()

    connection.close()

    return interaction


def save_project_execution(
    project_name: str,
    project_path: str,
    final_status: str,
    phases_completed: int,
    total_attempts: int,
    started_at: str,
    completed_at: str,
    summary_report: str,
) -> int:
    """Save project execution summary to the SQLite database."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO project_executions (
            project_name,
            project_path,
            final_status,
            phases_completed,
            total_attempts,
            started_at,
            completed_at,
            summary_report
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_name,
            project_path,
            final_status,
            phases_completed,
            total_attempts,
            started_at,
            completed_at,
            summary_report,
        ),
    )

    execution_id = cursor.lastrowid
    connection.commit()
    connection.close()

    return execution_id