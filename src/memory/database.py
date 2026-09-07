import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "orchestrator.db"


def get_connection():
    """Create and return a connection to the SQLite database."""
    return sqlite3.connect(DATABASE_PATH)


def run_migrations(connection):
    """
    Apply lightweight schema migrations.

    Safely adds missing columns to existing tables using ALTER TABLE.
    Existing rows and data are preserved.
    """
    cursor = connection.cursor()

    # Check existing columns in interactions table
    cursor.execute("PRAGMA table_info(interactions)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Add project context columns if missing
    migration_columns = {
        "project_name": "TEXT",
        "phase": "INTEGER",
        "attempt": "INTEGER",
    }

    for column_name, column_type in migration_columns.items():
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE interactions "
                f"ADD COLUMN {column_name} {column_type}"
            )
            print(f"Migration: Added column '{column_name}' to interactions table")

    connection.commit()


def initialize_database():
    """Create required database tables if they do not exist."""

    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            model TEXT,
            prompt TEXT NOT NULL,
            response TEXT,
            status TEXT NOT NULL DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            project_path TEXT NOT NULL,
            final_status TEXT NOT NULL,
            phases_completed INTEGER DEFAULT 0,
            total_attempts INTEGER DEFAULT 0,
            started_at TEXT,
            completed_at TEXT,
            summary_report TEXT
        )
    """)

    connection.commit()

    # Run schema migrations for existing databases
    run_migrations(connection)

    connection.close()

    print(f"Database initialized: {DATABASE_PATH}")