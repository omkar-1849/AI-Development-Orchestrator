import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.memory.database import initialize_database, run_migrations
from src.memory.conversation_store import (
    save_interaction,
    get_interaction,
    get_project_interactions,
)


class TestDatabaseMigrationAndScoping(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_orchestrator.db")
        self.patcher_db = patch("src.memory.database.DATABASE_PATH", Path(self.db_path))
        self.patcher_db.start()

    def tearDown(self):
        self.patcher_db.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def test_fresh_database_initialization(self):
        """Fresh database should have interactions and project_executions tables with new columns."""
        with patch("src.memory.database.get_connection", side_effect=self._get_connection):
            initialize_database()

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(interactions)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        expected_columns = {
            "id",
            "agent",
            "model",
            "prompt",
            "response",
            "status",
            "created_at",
            "project_name",
            "phase",
            "attempt",
        }
        self.assertTrue(expected_columns.issubset(columns))

    def test_migration_on_legacy_database(self):
        """Pre-existing database without project_name/phase/attempt should be migrated cleanly."""
        # Create legacy schema without new columns
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT NOT NULL,
                model TEXT,
                prompt TEXT NOT NULL,
                response TEXT,
                status TEXT NOT NULL DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Insert legacy row
        cursor.execute("""
            INSERT INTO interactions (agent, model, prompt, response, status)
            VALUES ('planner', 'claude', 'old prompt', 'old response', 'completed')
        """)
        conn.commit()
        conn.close()

        # Run initialize_database which invokes run_migrations
        with patch("src.memory.database.get_connection", side_effect=self._get_connection):
            initialize_database()

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(interactions)")
        columns = {row[1] for row in cursor.fetchall()}

        self.assertIn("project_name", columns)
        self.assertIn("phase", columns)
        self.assertIn("attempt", columns)

        # Ensure legacy row survived with NULL for new columns
        cursor.execute("SELECT id, agent, prompt, project_name, phase, attempt FROM interactions WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(row[1], "planner")
        self.assertEqual(row[2], "old prompt")
        self.assertIsNone(row[3])  # project_name is None
        self.assertIsNone(row[4])  # phase is None
        self.assertIsNone(row[5])  # attempt is None

    def test_save_interaction_with_project_scoping(self):
        """Saving interactions with project metadata and retrieving them."""
        with patch("src.memory.database.get_connection", side_effect=self._get_connection), \
             patch("src.memory.conversation_store.get_connection", side_effect=self._get_connection):
            initialize_database()

            id_1 = save_interaction(
                agent="implementer",
                model="Antigravity",
                prompt="Task 1 prompt",
                response="Task 1 response",
                status="dispatched",
                project_name="ProjectAlpha",
                phase=1,
                attempt=1,
            )

            id_2 = save_interaction(
                agent="implementer",
                model="Antigravity",
                prompt="Task 2 prompt",
                response="Task 2 response",
                status="dispatched",
                project_name="ProjectBeta",
                phase=1,
                attempt=1,
            )

            record = get_interaction(id_1)
            self.assertEqual(record[7], "ProjectAlpha")
            self.assertEqual(record[8], 1)
            self.assertEqual(record[9], 1)

            alpha_interactions = get_project_interactions("ProjectAlpha")
            beta_interactions = get_project_interactions("ProjectBeta")

            self.assertEqual(len(alpha_interactions), 1)
            self.assertEqual(alpha_interactions[0][0], id_1)
            self.assertEqual(alpha_interactions[0][7], "ProjectAlpha")

            self.assertEqual(len(beta_interactions), 1)
            self.assertEqual(beta_interactions[0][0], id_2)
            self.assertEqual(beta_interactions[0][7], "ProjectBeta")


if __name__ == "__main__":
    unittest.main()
