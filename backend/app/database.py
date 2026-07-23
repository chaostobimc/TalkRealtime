from __future__ import annotations

import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class Database:
    """Small SQLite repository.

    Messages retain their source text permanently; generated variants live in a
    separate cache table keyed by (message, target language).
    """

    def __init__(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True) if Path(path).parent != Path(".") else None
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                room_id TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                author_id TEXT NOT NULL,
                author_name TEXT NOT NULL,
                original_content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_room_created
                ON messages(room_id, created_at);

            CREATE TABLE IF NOT EXISTS translations (
                message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
                language TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('complete', 'unavailable')),
                updated_at TEXT NOT NULL,
                PRIMARY KEY (message_id, language)
            );
            """
        )
        self.connection.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def create_room(self, name: str) -> dict[str, str]:
        # Six unambiguous characters make a link pleasant to dictate while the
        # 32-symbol alphabet leaves a large enough space for this demo.
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        for _ in range(10):
            room_id = "".join(secrets.choice(alphabet) for _ in range(6))
            room = {"id": room_id, "name": name, "created_at": self._now()}
            try:
                self.connection.execute(
                    "INSERT INTO rooms (id, name, created_at) VALUES (:id, :name, :created_at)", room
                )
                self.connection.commit()
                return room
            except sqlite3.IntegrityError:
                continue
        raise RuntimeError("Could not allocate a room code")

    def room(self, room_id: str) -> dict[str, str] | None:
        row = self.connection.execute(
            "SELECT id, name, created_at FROM rooms WHERE id = ?", (room_id.upper(),)
        ).fetchone()
        return dict(row) if row else None

    def add_message(
        self, room_id: str, author_id: str, author_name: str, original_content: str
    ) -> dict[str, str]:
        message = {
            "id": secrets.token_urlsafe(12),
            "room_id": room_id,
            "author_id": author_id,
            "author_name": author_name,
            "original_content": original_content,
            "created_at": self._now(),
        }
        self.connection.execute(
            """INSERT INTO messages
               (id, room_id, author_id, author_name, original_content, created_at)
               VALUES (:id, :room_id, :author_id, :author_name, :original_content, :created_at)""",
            message,
        )
        self.connection.commit()
        return message

    def messages(self, room_id: str, limit: int) -> list[dict[str, str]]:
        rows = self.connection.execute(
            """SELECT id, room_id, author_id, author_name, original_content, created_at
               FROM messages WHERE room_id = ? ORDER BY created_at DESC LIMIT ?""",
            (room_id, limit),
        ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def translation(self, message_id: str, language: str) -> dict[str, str] | None:
        row = self.connection.execute(
            """SELECT content, status FROM translations
               WHERE message_id = ? AND language = ?""",
            (message_id, language),
        ).fetchone()
        return dict(row) if row else None

    def put_translation(self, message_id: str, language: str, content: str, status: str) -> None:
        self.connection.execute(
            """INSERT INTO translations (message_id, language, content, status, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(message_id, language) DO UPDATE SET
                 content=excluded.content, status=excluded.status, updated_at=excluded.updated_at""",
            (message_id, language, content, status, self._now()),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
