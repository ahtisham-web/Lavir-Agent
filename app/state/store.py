"""
Lightweight SQLite-backed session store so conversation context survives
process restarts (the spec calls for "a database or state-storage
solution"). Swap this out for Postgres/Redis later without touching the
agents, since MasterAgent only depends on ConversationState.
"""
import json
import sqlite3
from contextlib import contextmanager

from app.config import settings
from app.state.conversation import ConversationState


class SessionStore:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.LARVI_DB_PATH
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    messages TEXT NOT NULL,
                    pending_confirmation TEXT
                )"""
            )
            conn.commit()

    def load(self, session_id: str) -> ConversationState:
        state = ConversationState(session_id)
        with self._conn() as conn:
            row = conn.execute(
                "SELECT messages, pending_confirmation FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row:
            state.messages = json.loads(row[0])
            state.pending_confirmation = json.loads(row[1]) if row[1] else None
        return state

    def save(self, state: ConversationState) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO sessions (session_id, messages, pending_confirmation)
                   VALUES (?, ?, ?)
                   ON CONFLICT(session_id) DO UPDATE SET
                       messages = excluded.messages,
                       pending_confirmation = excluded.pending_confirmation""",
                (
                    state.session_id,
                    json.dumps(state.messages),
                    json.dumps(state.pending_confirmation) if state.pending_confirmation else None,
                ),
            )
            conn.commit()
