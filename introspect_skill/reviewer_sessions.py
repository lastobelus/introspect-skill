from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from introspect_skill.codex import codex_session_id_from_path
from introspect_skill.config import SearchConfig
from introspect_skill.summaries import content_text
from introspect_skill.timestamps import parse_iso


def _within_cwd(candidate: str | None, cwd: str | None) -> bool:
    if not cwd:
        return True
    if not candidate:
        return False
    candidate_real = os.path.realpath(candidate)
    cwd_real = os.path.realpath(cwd)
    return candidate_real == cwd_real or candidate_real.startswith(cwd_real + os.sep)


def find_claude(config: SearchConfig, since: datetime | None, cwd: str | None, query: str | None) -> list[dict]:
    matches: list[dict] = []
    for root in config.claude_project_roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True):
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if since and mtime < since:
                continue
            session_id = None
            seen_cwd = None
            text = ""
            with path.open(errors="replace") as handle:
                for _ in range(12):
                    line = handle.readline()
                    if not line:
                        break
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(row, dict):
                        continue
                    session_id = session_id or row.get("sessionId")
                    seen_cwd = seen_cwd or row.get("cwd")
                    message = row.get("message", {})
                    content = content_text(message.get("content", ""))
                    if content:
                        text += " " + content
            if not _within_cwd(seen_cwd, cwd):
                continue
            if query and query.lower() not in (text + str(path)).lower():
                continue
            matches.append(
                {
                    "provider": "claude",
                    "session_id": session_id,
                    "path": str(path),
                    "cwd": seen_cwd,
                    "updated_at": mtime.isoformat(),
                    "source": str(root),
                }
            )
    return matches[:10]


def find_codex(config: SearchConfig, since: datetime | None, cwd: str | None, query: str | None) -> list[dict]:
    matches: list[dict] = []
    for root in config.codex_session_roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True):
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if since and mtime < since:
                continue
            session_id = codex_session_id_from_path(path)
            seen_cwd = None
            metadata_terms: list[str] = []
            with path.open(errors="replace") as handle:
                for _ in range(20):
                    line = handle.readline()
                    if not line:
                        break
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if row.get("type") == "session_meta":
                        payload = row.get("payload", {})
                        session_id = payload.get("id") or session_id
                        seen_cwd = payload.get("cwd") or seen_cwd
                        metadata_terms.extend(
                            str(payload.get(field, ""))
                            for field in ("source", "originator", "cwd")
                            if payload.get(field)
                        )
                        continue
                    if row.get("type") == "event_msg":
                        payload = row.get("payload", {})
                        if payload.get("type") == "user_message" and isinstance(payload.get("message"), str):
                            metadata_terms.append(payload["message"])
                            break
            haystack = " ".join(part for part in [*metadata_terms, str(path)] if part)
            if not _within_cwd(seen_cwd, cwd):
                continue
            if query and query.lower() not in haystack.lower():
                continue
            matches.append(
                {
                    "provider": "codex",
                    "session_id": session_id,
                    "path": str(path),
                    "cwd": seen_cwd,
                    "updated_at": mtime.isoformat(),
                    "source": str(root),
                }
            )
    return matches[:10]


def find_opencode(config: SearchConfig, since: datetime | None, cwd: str | None, query: str | None) -> list[dict]:
    matches: list[dict] = []
    for db_path in config.opencode_databases:
        if not db_path.exists():
            continue
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            params: list[object] = []
            where = ""
            if since:
                where = "WHERE time_updated >= ?"
                params.append(int(since.timestamp() * 1000))
            for row in cur.execute(
                f"""
                SELECT id, title, directory, time_updated
                FROM session
                {where}
                ORDER BY time_updated DESC
                LIMIT 50
                """,
                params,
            ):
                updated = datetime.fromtimestamp(row["time_updated"] / 1000, tz=timezone.utc)
                haystack = " ".join([row["id"], row["title"] or "", row["directory"] or ""])
                if not _within_cwd(row["directory"], cwd):
                    continue
                if query and query.lower() not in haystack.lower():
                    continue
                matches.append(
                    {
                        "provider": "opencode",
                        "session_id": row["id"],
                        "title": row["title"],
                        "path": str(db_path),
                        "cwd": row["directory"],
                        "updated_at": updated.isoformat(),
                        "source": str(db_path),
                    }
                )
    return matches[:10]


def find_reviewer_session(
    config: SearchConfig,
    provider: str,
    since: datetime | None,
    cwd: str | None,
    query: str | None,
) -> dict:
    if provider == "claude":
        matches = find_claude(config, since, cwd, query)
    elif provider == "codex":
        matches = find_codex(config, since, cwd, query)
    elif provider == "opencode":
        matches = find_opencode(config, since, cwd, query)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    return {"provider": provider, "matches": matches}
