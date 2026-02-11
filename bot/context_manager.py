from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class FSMState(str, Enum):
    IDLE = "IDLE"
    WAIT_FILE = "WAIT_FILE"
    FILE_UPLOADED = "FILE_UPLOADED"
    ANALYZED = "ANALYZED"
    FILTERING = "FILTERING"
    READY_EXPORT = "READY_EXPORT"
    DONE = "DONE"


@dataclass
class UserContext:
    user_id: int
    state: FSMState = FSMState.IDLE
    active_file_id: str | None = None
    active_operation: str | None = None


class ContextManager:
    def __init__(self, db_path: str = "storage/context.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        self.pattern_counter: defaultdict[int, Counter] = defaultdict(Counter)

    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_context (
                user_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL,
                active_file_id TEXT,
                active_operation TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS file_registry (
                file_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                original_name TEXT NOT NULL,
                original_path TEXT NOT NULL,
                working_path TEXT NOT NULL,
                analyzed INTEGER NOT NULL DEFAULT 0,
                analysis_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS operation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_id TEXT,
                operation TEXT NOT NULL,
                phase TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def get_user_context(self, user_id: int) -> UserContext:
        cur = self.conn.cursor()
        row = cur.execute("SELECT * FROM user_context WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            ctx = UserContext(user_id=user_id)
            self.upsert_user_context(ctx)
            return ctx
        return UserContext(
            user_id=user_id,
            state=FSMState(row["state"]),
            active_file_id=row["active_file_id"],
            active_operation=row["active_operation"],
        )

    def upsert_user_context(self, ctx: UserContext):
        self.conn.execute(
            """
            INSERT INTO user_context (user_id, state, active_file_id, active_operation)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              state=excluded.state,
              active_file_id=excluded.active_file_id,
              active_operation=excluded.active_operation
            """,
            (ctx.user_id, ctx.state.value, ctx.active_file_id, ctx.active_operation),
        )
        self.conn.commit()

    def register_file(self, user_id: int, file_id: str, original_name: str, original_path: str, working_path: str):
        self.conn.execute(
            """
            INSERT OR REPLACE INTO file_registry
            (file_id, user_id, original_name, original_path, working_path, analyzed)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (file_id, user_id, original_name, original_path, working_path),
        )
        self.conn.commit()

    def mark_analyzed(self, file_id: str, analysis: dict):
        self.conn.execute(
            "UPDATE file_registry SET analyzed = 1, analysis_json = ? WHERE file_id = ?",
            (json.dumps(analysis, ensure_ascii=False), file_id),
        )
        self.conn.commit()

    def get_file_record(self, file_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM file_registry WHERE file_id = ?", (file_id,)).fetchone()

    def log_operation(self, user_id: int, file_id: str | None, operation: str, phase: str):
        self.conn.execute(
            "INSERT INTO operation_history (user_id, file_id, operation, phase) VALUES (?, ?, ?, ?)",
            (user_id, file_id, operation, phase),
        )
        self.conn.commit()
        if phase == "exit":
            self.pattern_counter[user_id][operation] += 1

    def last_operations(self, user_id: int, limit: int = 10) -> list[str]:
        rows = self.conn.execute(
            "SELECT operation FROM operation_history WHERE user_id = ? AND phase = 'exit' ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [r["operation"] for r in rows]

    def should_suggest_export(self, user_id: int) -> bool:
        ops = list(reversed(self.last_operations(user_id, 12)))
        if len(ops) < 2:
            return False
        # deterministic pattern learning: analyze -> filter frequently
        transitions = 0
        for i in range(len(ops) - 1):
            if ops[i] == "analyze" and ops[i + 1] == "filter":
                transitions += 1
        return transitions >= 2

    def reset_user(self, user_id: int):
        ctx = self.get_user_context(user_id)
        ctx.state = FSMState.IDLE
        ctx.active_file_id = None
        ctx.active_operation = None
        self.upsert_user_context(ctx)
