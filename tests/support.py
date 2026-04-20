from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def write_t3_state_db(
    root: Path,
    thread_id: str,
    message_text: str,
    native_session_id: str,
    title: str = "Thread",
    provider_name: str = "codex",
    resume_cursor_json: str | None = None,
) -> Path:
    db_path = root / "userdata" / "state.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS projection_threads (
              thread_id TEXT PRIMARY KEY,
              project_id TEXT,
              title TEXT,
              branch TEXT,
              worktree_path TEXT,
              runtime_mode TEXT,
              interaction_mode TEXT,
              latest_turn_id TEXT,
              created_at TEXT,
              updated_at TEXT,
              archived_at TEXT
            );
            CREATE TABLE IF NOT EXISTS projection_thread_messages (
              message_id TEXT PRIMARY KEY,
              thread_id TEXT,
              turn_id TEXT,
              role TEXT,
              text TEXT,
              is_streaming INTEGER,
              created_at TEXT,
              updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS projection_thread_sessions (
              thread_id TEXT,
              status TEXT,
              provider_name TEXT,
              provider_session_id TEXT,
              provider_thread_id TEXT,
              active_turn_id TEXT,
              last_error TEXT,
              updated_at TEXT,
              runtime_mode TEXT
            );
            CREATE TABLE IF NOT EXISTS provider_session_runtime (
              thread_id TEXT,
              provider_name TEXT,
              adapter_key TEXT,
              runtime_mode TEXT,
              status TEXT,
              last_seen_at TEXT,
              resume_cursor_json TEXT,
              runtime_payload_json TEXT
            );
            CREATE TABLE IF NOT EXISTS projection_thread_activities (
              activity_id TEXT,
              thread_id TEXT,
              turn_id TEXT,
              tone TEXT,
              kind TEXT,
              summary TEXT,
              payload_json TEXT,
              sequence INTEGER,
              created_at TEXT
            );
            """
        )
        cur.execute(
            """
            INSERT INTO projection_threads
              (thread_id, project_id, title, branch, worktree_path, runtime_mode, interaction_mode, latest_turn_id, created_at, updated_at, archived_at)
            VALUES
              (?, 'p1', ?, 'main', ?, 'full-access', 'default', 'turn-1', '2026-04-20T00:00:00Z', '2026-04-20T00:00:00Z', NULL)
            """,
            (thread_id, title, str(root / "worktree")),
        )
        cur.execute(
            """
            INSERT INTO projection_thread_messages
              (message_id, thread_id, turn_id, role, text, is_streaming, created_at, updated_at)
            VALUES
              (?, ?, 'turn-1', 'user', ?, 0, '2026-04-20T00:00:00Z', '2026-04-20T00:00:00Z')
            """,
            (f"msg-{thread_id}", thread_id, message_text),
        )
        cur.execute(
            """
            INSERT INTO projection_thread_sessions
              (thread_id, status, provider_name, provider_session_id, provider_thread_id, active_turn_id, last_error, updated_at, runtime_mode)
            VALUES
              (?, 'running', ?, ?, ?, 'turn-1', NULL, '2026-04-20T00:00:00Z', 'full-access')
            """,
            (thread_id, provider_name, native_session_id, native_session_id),
        )
        resume_cursor = resume_cursor_json or json.dumps({"threadId": native_session_id})
        cur.execute(
            """
            INSERT INTO provider_session_runtime
              (thread_id, provider_name, adapter_key, runtime_mode, status, last_seen_at, resume_cursor_json, runtime_payload_json)
            VALUES
              (?, ?, ?, 'full-access', 'running', '2026-04-20T00:00:00Z', ?, '{}')
            """,
            (thread_id, provider_name, provider_name, resume_cursor),
        )
    return db_path


def write_codex_session(root: Path, session_id: str, message_text: str, cwd: str) -> Path:
    path = root / "2026" / "04" / "20" / f"rollout-2026-04-20T00-00-00-{session_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-04-20T00:00:00Z",
                        "type": "session_meta",
                        "payload": {"id": session_id, "cwd": cwd, "source": "cli"},
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-04-20T00:00:01Z",
                        "type": "event_msg",
                        "payload": {"type": "user_message", "message": message_text},
                    }
                ),
            ]
        )
        + "\n"
    )
    return path


def write_opencode_db(
    path: Path,
    session_id: str,
    message_text: str,
    directory: str,
    *,
    title: str = "opencode session",
    time_created: int = 1000,
    time_updated: int = 2000,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS session (
              id TEXT PRIMARY KEY,
              project_id TEXT,
              parent_id TEXT,
              slug TEXT,
              directory TEXT,
              title TEXT,
              version TEXT,
              share_url TEXT,
              summary_additions INTEGER,
              summary_deletions INTEGER,
              summary_files INTEGER,
              summary_diffs TEXT,
              revert TEXT,
              permission TEXT,
              time_created INTEGER,
              time_updated INTEGER,
              time_compacting INTEGER,
              time_archived INTEGER,
              workspace_id TEXT
            );
            CREATE TABLE IF NOT EXISTS message (
              id TEXT PRIMARY KEY,
              session_id TEXT,
              time_created INTEGER,
              time_updated INTEGER,
              data TEXT
            );
            CREATE TABLE IF NOT EXISTS part (
              id TEXT PRIMARY KEY,
              message_id TEXT,
              session_id TEXT,
              time_created INTEGER,
              time_updated INTEGER,
              data TEXT
            );
            """
        )
        cur.execute(
            """
            INSERT INTO session
              (id, project_id, parent_id, slug, directory, title, version, share_url, summary_additions, summary_deletions, summary_files, summary_diffs, revert, permission, time_created, time_updated, time_compacting, time_archived, workspace_id)
            VALUES
              (?, 'p1', NULL, 'slug', ?, ?, '1', NULL, 0, 0, 0, NULL, NULL, NULL, ?, ?, NULL, NULL, NULL)
            """,
            (session_id, directory, title, time_created, time_updated),
        )
        message_id = f"msg-{session_id}"
        part_id = f"part-{session_id}"
        cur.execute(
            "INSERT INTO message (id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?)",
            (message_id, session_id, time_created, time_updated, json.dumps({"role": "user"})),
        )
        cur.execute(
            "INSERT INTO part (id, message_id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?, ?)",
            (part_id, message_id, session_id, time_created, time_updated, json.dumps({"text": message_text})),
        )
    return path


def write_claude_session(root: Path, session_id: str, message_text: str, cwd: str) -> Path:
    path = root / "project-a" / f"{session_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "sessionId": session_id,
                        "cwd": cwd,
                        "gitBranch": "main",
                        "type": "user",
                        "timestamp": "2026-04-20T00:00:00Z",
                        "message": {"content": message_text},
                    }
                ),
                json.dumps(
                    {
                        "sessionId": session_id,
                        "cwd": cwd,
                        "type": "assistant",
                        "timestamp": "2026-04-20T00:00:01Z",
                        "message": {
                            "content": [
                                {"type": "text", "text": "I inspected the other thread."},
                                {"type": "tool_use", "name": "Read"},
                            ]
                        },
                    }
                ),
                json.dumps(
                    {
                        "sessionId": session_id,
                        "cwd": cwd,
                        "type": "attachment",
                        "timestamp": "2026-04-20T00:00:02Z",
                        "attachment": {
                            "type": "hook_success",
                            "hookName": "pre-tool",
                            "hookEvent": "before_read",
                            "command": "echo ok",
                            "durationMs": 12,
                        },
                    }
                ),
            ]
        )
        + "\n"
    )
    return path


def write_provider_log(path: Path, cwd: str, session_id: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                '[2026-04-20T00:00:00Z] INFO: {"event":{"method":"provider/system/init","provider":"codex","providerThreadId":"thread-1","payload":{"cwd":"'
                + cwd
                + '","model":"gpt-5.4","permissionMode":"full-access","session_id":"'
                + session_id
                + '"}}}',
                '[2026-04-20T00:00:01Z] INFO: {"event":{"method":"provider/hook/success","payload":{"hook_name":"pre-tool","hook_event":"before_read","outcome":"ok","exit_code":0}}}',
                '[2026-04-20T00:00:02Z] INFO: {"event":{"method":"provider/assistant","payload":{"message":{"content":[{"type":"text","text":"Found the session."}]}}}}',
            ]
        )
        + "\n"
    )
    return path


__all__ = [
    "write_t3_state_db",
    "write_codex_session",
    "write_opencode_db",
    "write_claude_session",
    "write_provider_log",
]
