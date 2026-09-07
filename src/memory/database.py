import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "orchestrator.db"


def get_connection():
    """Create and return a connection to the SQLite database."""
    return sqlite3.connect(DATABASE_PATH)


def initialize_database():
    """Create required database tables if they do not exist."""

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
    connection.close()

    print(f"Database initialized: {DATABASE_PATH}")