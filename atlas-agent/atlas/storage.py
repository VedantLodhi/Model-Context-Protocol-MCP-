import json
import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "atlas_memory.db"
)


class AtlasStorage:
    """
    SQLite persistence layer for Atlas.

    Stores:
    - conversation history
    - execution history
    """

    def __init__(
        self,
        db_path: Path = DB_PATH,
    ):
        self.db_path = db_path
        self._initialize()

    def _connect(self):
        return sqlite3.connect(
            self.db_path
        )

    def _initialize(self) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS
                conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_query TEXT NOT NULL,
                    atlas_response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS
                execution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    tool_name TEXT,
                    result TEXT,
                    status TEXT NOT NULL,
                    follow_up INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            connection.commit()

    def save_turn(
        self,
        user_query: str,
        atlas_response: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_history
                (user_query, atlas_response)
                VALUES (?, ?)
                """,
                (
                    user_query,
                    atlas_response,
                ),
            )

            connection.commit()

    def save_execution(
        self,
        query: str,
        intent: str,
        tool_name: str | None,
        result: Any,
        status: str,
        follow_up: bool,
    ) -> None:

        serialized_result = json.dumps(
            self._serialize(result)
        )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO execution_history
                (
                    query,
                    intent,
                    tool_name,
                    result,
                    status,
                    follow_up
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    query,
                    intent,
                    tool_name,
                    serialized_result,
                    status,
                    int(follow_up),
                ),
            )

            connection.commit()

    def load_history(
        self,
    ) -> list[dict[str, str]]:

        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT user_query, atlas_response
                FROM conversation_history
                ORDER BY id ASC
                """
            )

            rows = cursor.fetchall()

        return [
            {
                "user": row[0],
                "atlas": row[1],
            }
            for row in rows
        ]

    def load_executions(
        self,
    ) -> list[dict[str, Any]]:

        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT
                    query,
                    intent,
                    tool_name,
                    result,
                    status,
                    follow_up
                FROM execution_history
                ORDER BY id ASC
                """
            )

            rows = cursor.fetchall()

        executions = []

        for row in rows:
            try:
                result = json.loads(row[3])
            except (
                json.JSONDecodeError,
                TypeError,
            ):
                result = None

            executions.append(
                {
                    "query": row[0],
                    "intent": row[1],
                    "tool_name": row[2],
                    "result": result,
                    "status": row[4],
                    "follow_up": bool(row[5]),
                }
            )

        return executions

    def clear(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM conversation_history"
            )

            connection.execute(
                "DELETE FROM execution_history"
            )

            connection.commit()

    @staticmethod
    def _serialize(value: Any) -> Any:
        """
        Convert Atlas/MCP/workflow objects into
        JSON-compatible structures.
        """

        if value is None:
            return None

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):
            return value

        if isinstance(value, list):
            return [
                AtlasStorage._serialize(item)
                for item in value
            ]

        if isinstance(value, dict):
            return {
                str(key): AtlasStorage._serialize(
                    item
                )
                for key, item in value.items()
            }

        structured_content = getattr(
            value,
            "structured_content",
            None,
        )

        if structured_content is not None:
            return AtlasStorage._serialize(
                structured_content
            )

        if hasattr(value, "__dataclass_fields__"):
            return {
                field_name: AtlasStorage._serialize(
                    getattr(value, field_name)
                )
                for field_name in (
                    value.__dataclass_fields__
                )
            }

        return str(value)