from __future__ import annotations

import sqlite3
from pathlib import Path

from introspect_skill.config import SearchConfig


def rows(cur: sqlite3.Cursor, query: str, params: tuple = ()) -> list[dict]:
    return [dict(row) for row in cur.execute(query, params)]


def find_state_db_for_thread(thread_id: str, config: SearchConfig) -> Path | None:
    for state_db in config.state_databases:
        if not state_db.exists():
            continue
        with sqlite3.connect(state_db) as conn:
            cur = conn.cursor()
            match = cur.execute(
                "SELECT 1 FROM projection_threads WHERE thread_id = ? LIMIT 1",
                (thread_id,),
            ).fetchone()
        if match:
            return state_db
    return None


def thread_context(thread_id: str, config: SearchConfig, state_db: Path | None = None) -> dict:
    state_db = Path(state_db) if state_db else find_state_db_for_thread(thread_id, config)
    if state_db is None:
        raise ValueError(f"Could not find thread {thread_id!r} in any configured T3 state database.")
    if not state_db.exists():
        raise ValueError(f"State database not found: {state_db}")

    with sqlite3.connect(state_db) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        return {
            "state_db": str(state_db),
            "thread": rows(
                cur,
                """
                SELECT thread_id, project_id, title, branch, worktree_path, runtime_mode,
                       interaction_mode, latest_turn_id, created_at, updated_at, archived_at
                FROM projection_threads
                WHERE thread_id = ?
                """,
                (thread_id,),
            ),
            "thread_session": rows(
                cur,
                """
                SELECT thread_id, status, provider_name, provider_session_id, provider_thread_id,
                       active_turn_id, last_error, updated_at, runtime_mode
                FROM projection_thread_sessions
                WHERE thread_id = ?
                """,
                (thread_id,),
            ),
            "provider_runtime": rows(
                cur,
                """
                SELECT thread_id, provider_name, adapter_key, runtime_mode, status, last_seen_at,
                       resume_cursor_json, runtime_payload_json
                FROM provider_session_runtime
                WHERE thread_id = ?
                """,
                (thread_id,),
            ),
            "recent_messages": rows(
                cur,
                """
                SELECT message_id, turn_id, role, substr(text, 1, 320) AS text,
                       is_streaming, created_at, updated_at
                FROM projection_thread_messages
                WHERE thread_id = ?
                ORDER BY created_at DESC
                LIMIT 12
                """,
                (thread_id,),
            ),
            "recent_activities": rows(
                cur,
                """
                SELECT activity_id, turn_id, tone, kind, summary, substr(payload_json, 1, 240) AS payload_json,
                       sequence, created_at
                FROM projection_thread_activities
                WHERE thread_id = ?
                ORDER BY COALESCE(sequence, 0) DESC, created_at DESC
                LIMIT 12
                """,
                (thread_id,),
            ),
        }
