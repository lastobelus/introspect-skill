from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

from introspect_skill.config import SearchConfig
from introspect_skill.sql import like_pattern


def add_match(matches: list[dict], **kwargs: object) -> None:
    if kwargs not in matches:
        matches.append(kwargs)


def sqlite_matches(state_db: Path, query: str, matches: list[dict]) -> None:
    if not state_db.exists():
        return
    like = like_pattern(query)
    with sqlite3.connect(state_db) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        for row in cur.execute(
            """
            SELECT thread_id, title, branch, worktree_path, updated_at
            FROM projection_threads
            WHERE thread_id = ?
               OR title LIKE ? ESCAPE '!'
               OR branch LIKE ? ESCAPE '!'
               OR worktree_path LIKE ? ESCAPE '!'
            ORDER BY updated_at DESC
            LIMIT 20
            """,
            (query, like, like, like),
        ):
            add_match(
                matches,
                source=str(state_db),
                kind="t3-thread",
                thread_id=row["thread_id"],
                title=row["title"],
                branch=row["branch"],
                worktree_path=row["worktree_path"],
                updated_at=row["updated_at"],
            )

        for row in cur.execute(
            """
            SELECT thread_id, status, provider_name, provider_session_id, provider_thread_id, updated_at
            FROM projection_thread_sessions
            WHERE thread_id = ?
               OR provider_session_id = ?
               OR provider_thread_id = ?
            ORDER BY updated_at DESC
            LIMIT 20
            """,
            (query, query, query),
        ):
            add_match(
                matches,
                source=str(state_db),
                kind="thread-session",
                thread_id=row["thread_id"],
                provider=row["provider_name"],
                provider_session_id=row["provider_session_id"],
                provider_thread_id=row["provider_thread_id"],
                status=row["status"],
                updated_at=row["updated_at"],
            )

        for row in cur.execute(
            """
            SELECT thread_id, provider_name, adapter_key, runtime_mode, status, last_seen_at, resume_cursor_json
            FROM provider_session_runtime
            WHERE thread_id = ?
               OR resume_cursor_json LIKE ? ESCAPE '!'
               OR runtime_payload_json LIKE ? ESCAPE '!'
            ORDER BY last_seen_at DESC
            LIMIT 20
            """,
            (query, like, like),
        ):
            add_match(
                matches,
                source=str(state_db),
                kind="provider-runtime",
                thread_id=row["thread_id"],
                provider=row["provider_name"],
                adapter_key=row["adapter_key"],
                runtime_mode=row["runtime_mode"],
                status=row["status"],
                last_seen_at=row["last_seen_at"],
                resume_cursor_json=row["resume_cursor_json"],
            )


def file_name_matches(root: Path, query: str, matches: list[dict], kind: str) -> None:
    if not root.exists():
        return
    query_lower = query.lower()
    for path in sorted(root.rglob("*"), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_file():
            continue
        if query_lower in path.name.lower() or query_lower in str(path).lower():
            add_match(
                matches,
                source="filesystem",
                kind=kind,
                path=str(path),
                updated_at=int(path.stat().st_mtime),
            )


def rg_content_matches(root: Path, query: str, matches: list[dict], kind: str) -> None:
    if not root.exists():
        return
    try:
        proc = subprocess.run(["rg", "--json", "-m", "1", "-S", query, str(root)], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        proc = None

    if proc is None or proc.returncode not in {0, 1}:
        query_lower = query.lower()
        found = 0
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            try:
                handle = path.open(errors="replace")
            except OSError:
                continue
            with handle:
                for lineno, line in enumerate(handle, start=1):
                    if query_lower in line.lower():
                        add_match(
                            matches,
                            source="python-fallback",
                            kind=kind,
                            path=str(path),
                            line=lineno,
                            excerpt=line[:220],
                        )
                        found += 1
                        break
            if found >= 20:
                break
        return

    count = 0
    for line in proc.stdout.splitlines():
        if count >= 20:
            break
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("type") != "match":
            continue
        data = row.get("data", {})
        path = data.get("path", {}).get("text")
        lineno = data.get("line_number")
        excerpt = data.get("lines", {}).get("text", "")
        if not path or lineno is None:
            continue
        add_match(
            matches,
            source="ripgrep",
            kind=kind,
            path=path,
            line=int(lineno),
            excerpt=excerpt[:220],
        )
        count += 1


def codex_index_matches(index_path: Path, query: str, matches: list[dict]) -> None:
    if not index_path.exists():
        return
    query_lower = query.lower()
    for raw in reversed(index_path.read_text().splitlines()):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if row.get("id") == query or query_lower in row.get("thread_name", "").lower():
            add_match(
                matches,
                source=str(index_path),
                kind="codex-session",
                session_id=row.get("id"),
                title=row.get("thread_name"),
                updated_at=row.get("updated_at"),
            )


def opencode_db_matches(db_path: Path, query: str, matches: list[dict]) -> None:
    if not db_path.exists():
        return
    like = like_pattern(query)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        for row in cur.execute(
            """
            SELECT s.id, s.title, s.directory, s.time_updated
            FROM session AS s
            WHERE s.id = ?
               OR s.title LIKE ? ESCAPE '!'
               OR s.directory LIKE ? ESCAPE '!'
            ORDER BY s.time_updated DESC
            LIMIT 20
            """,
            (query, like, like),
        ):
            add_match(
                matches,
                source=str(db_path),
                kind="opencode-session",
                session_id=row["id"],
                title=row["title"],
                directory=row["directory"],
                updated_at=row["time_updated"],
            )

        for row in cur.execute(
            """
            SELECT s.id, s.title, s.directory, s.time_updated
            FROM session AS s
            JOIN part AS p ON p.session_id = s.id
            WHERE p.data LIKE ? ESCAPE '!'
            GROUP BY s.id, s.title, s.directory, s.time_updated
            ORDER BY s.time_updated DESC
            LIMIT 20
            """,
            (like,),
        ):
            add_match(
                matches,
                source=str(db_path),
                kind="opencode-session-content",
                session_id=row["id"],
                title=row["title"],
                directory=row["directory"],
                updated_at=row["time_updated"],
            )


def opencode_session_diff_matches(root: Path, query: str, matches: list[dict]) -> None:
    if not root.exists():
        return
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        if query == path.stem or query.lower() in path.name.lower():
            add_match(
                matches,
                source=str(root),
                kind="opencode-session",
                session_id=path.stem,
                path=str(path),
                updated_at=int(path.stat().st_mtime),
            )


def opencode_session_list_matches(query: str, matches: list[dict]) -> None:
    try:
        proc = subprocess.run(
            ["opencode", "session", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return

    for line in proc.stdout.splitlines():
        if not line.startswith("ses_"):
            continue
        columns = [column.strip() for column in line.split("  ") if column.strip()]
        if not columns:
            continue
        session_id = columns[0]
        title = columns[1] if len(columns) > 1 else ""
        updated = columns[2] if len(columns) > 2 else ""
        if session_id == query or query.lower() in title.lower():
            add_match(
                matches,
                source="opencode session list",
                kind="opencode-session",
                session_id=session_id,
                title=title,
                updated_at=updated,
            )


def resolve_target(query: str, config: SearchConfig) -> dict:
    matches: list[dict] = []

    if "t3" in config.enabled_harnesses:
        for state_db in config.state_databases:
            sqlite_matches(state_db, query, matches)
        for log_dir in config.provider_log_dirs:
            file_name_matches(log_dir, query, matches, "provider-log")
            if len(query) >= 4:
                rg_content_matches(log_dir, query, matches, "provider-log-content")

    if "claude" in config.enabled_harnesses:
        for root in config.claude_project_roots:
            file_name_matches(root, query, matches, "claude-jsonl")
            if len(query) >= 4:
                rg_content_matches(root, query, matches, "claude-jsonl-content")

    if "codex" in config.enabled_harnesses:
        for index_path in config.codex_session_indexes:
            codex_index_matches(index_path, query, matches)
        for root in config.codex_session_roots:
            file_name_matches(root, query, matches, "codex-session-jsonl")
            if len(query) >= 4:
                rg_content_matches(root, query, matches, "codex-session-content")

    if "opencode" in config.enabled_harnesses:
        for db_path in config.opencode_databases:
            opencode_db_matches(db_path, query, matches)
        for diff_root in config.opencode_session_diff_roots:
            opencode_session_diff_matches(diff_root, query, matches)
        opencode_session_list_matches(query, matches)

    return {"query": query, "matches": matches[:50]}
