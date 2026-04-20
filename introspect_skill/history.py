from __future__ import annotations

import json
import sqlite3
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from introspect_skill.codex import codex_session_id_from_path
from introspect_skill.config import SearchConfig
from introspect_skill.summaries import content_text
from introspect_skill.sql import like_pattern
from introspect_skill.timestamps import iso_from_ms, parse_iso


DEFAULT_TERMS = [
    "~/.t3",
    "session",
    "thread",
    "session log",
    "other thread",
    "another thread",
    "another session",
    "provider log",
    "thread id",
    "session id",
    "continue claude",
    "continue codex",
    "continue opencode",
    "introspect",
    "introspection",
]

ACTION_TERMS = [
    "collect",
    "continue",
    "diagnose",
    "explain",
    "find",
    "inspect",
    "investigate",
    "look at",
    "look in",
    "map",
    "mine",
    "review",
    "search",
    "show me",
    "what happened",
    "why",
]


def normalize_text(text: str) -> str:
    return " ".join(text.split()).strip().lower()


def normalize_provider_name(name: str) -> str:
    return "claude" if name == "claudeAgent" else name


def strip_wrapping_quotes(text: str) -> str:
    cleaned = text.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] == '"':
        return cleaned[1:-1]
    return cleaned


def excerpt(text: str, limit: int = 240) -> str:
    compact = " ".join(text.split()).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def trim_harness_preamble(text: str) -> str:
    trimmed = text
    for marker in ("</environment_context>", "</INSTRUCTIONS>"):
        if marker in trimmed:
            trimmed = trimmed.rsplit(marker, 1)[-1]
    return trimmed.strip() or text


def matched_terms(text: str, extra_terms: list[str]) -> list[str]:
    lowered = text.lower()
    matched: list[str] = []
    for term in DEFAULT_TERMS + extra_terms:
        if term.lower() in lowered and term not in matched:
            matched.append(term)

    core_hits = sum(1 for term in ("~/.t3", "session", "thread") if term in lowered)
    strong_phrase = any(
        phrase in lowered
        for phrase in (
            "introspect",
            "introspection",
            "session log",
            "other thread",
            "another thread",
            "another session",
            "provider log",
            "continue claude",
            "continue codex",
            "continue opencode",
        )
    )
    action_hit = any(term in lowered for term in ACTION_TERMS)
    if strong_phrase or (core_hits >= 2 and action_hit):
        return matched
    return []


def rg_candidate_files(root: Path, terms: list[str]) -> list[Path]:
    if not root.exists():
        return []
    cmd = ["rg", "-l", "-i"]
    for term in terms:
        cmd.extend(["-e", term])
    cmd.append(str(root))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return sorted(root.rglob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)
    files: list[Path] = []
    for line in proc.stdout.splitlines():
        path = Path(line.strip())
        if path.exists():
            files.append(path)
    return files


def t3_alias_map(state_db: Path, thread_ids: set[str]) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = defaultdict(set)
    if not thread_ids or not state_db.exists():
        return aliases

    placeholders = ",".join("?" for _ in thread_ids)
    with sqlite3.connect(state_db) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        for row in cur.execute(
            f"""
            SELECT thread_id, provider_name, resume_cursor_json
            FROM provider_session_runtime
            WHERE thread_id IN ({placeholders})
            """,
            tuple(thread_ids),
        ):
            raw = row["resume_cursor_json"] or ""
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {}
            provider = row["provider_name"] or ""
            if provider == "codex" and payload.get("threadId"):
                aliases[row["thread_id"]].add(f"codex:{payload['threadId']}")
            if provider == "claudeAgent":
                if payload.get("resume"):
                    aliases[row["thread_id"]].add(f"claude:{payload['resume']}")
                if payload.get("resumeSessionAt"):
                    aliases[row["thread_id"]].add(f"claude:{payload['resumeSessionAt']}")

        for row in cur.execute(
            f"""
            SELECT thread_id, provider_name, provider_session_id, provider_thread_id
            FROM projection_thread_sessions
            WHERE thread_id IN ({placeholders})
            """,
            tuple(thread_ids),
        ):
            provider = normalize_provider_name(row["provider_name"] or "")
            if row["provider_session_id"]:
                aliases[row["thread_id"]].add(f"{provider}:{row['provider_session_id']}")
            if row["provider_thread_id"]:
                aliases[row["thread_id"]].add(f"{provider}:{row['provider_thread_id']}")
    return aliases


def collect_t3(config: SearchConfig, extra_terms: list[str]) -> tuple[list[dict], dict[tuple[str, str], dict]]:
    results: list[dict] = []
    seen_t3: set[tuple[str, str, str]] = set()

    for state_db in config.state_databases:
        if not state_db.exists():
            continue
        with sqlite3.connect(state_db) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            like_terms = DEFAULT_TERMS + list(extra_terms)
            where = " OR ".join("lower(m.text) LIKE ? ESCAPE '!'" for _ in like_terms)
            params = [like_pattern(term.lower()) for term in like_terms]
            rows = cur.execute(
                f"""
                SELECT m.thread_id, m.turn_id, m.message_id, m.text, m.created_at,
                       t.title, t.branch, t.worktree_path
                FROM projection_thread_messages AS m
                JOIN projection_threads AS t ON t.thread_id = m.thread_id
                WHERE m.role = 'user'
                  AND ({where})
                ORDER BY m.created_at DESC
                """,
                params,
            ).fetchall()

            thread_ids = {row["thread_id"] for row in rows}
            alias_map = t3_alias_map(state_db, thread_ids)
            for row in rows:
                terms = matched_terms(row["text"] or "", extra_terms)
                if not terms:
                    continue
                normalized = normalize_text(trim_harness_preamble(row["text"] or ""))
                t3_key = (row["thread_id"], row["message_id"], normalized)
                if t3_key in seen_t3:
                    continue
                seen_t3.add(t3_key)
                results.append(
                    {
                        "canonical_source": "t3",
                        "provider": "t3",
                        "thread_id": row["thread_id"],
                        "turn_id": row["turn_id"],
                        "message_id": row["message_id"],
                        "title": row["title"],
                        "branch": row["branch"],
                        "worktree_path": row["worktree_path"],
                        "state_db": str(state_db),
                        "created_at": row["created_at"],
                        "matched_terms": terms,
                        "excerpt": excerpt(row["text"] or ""),
                        "normalized_text": normalized,
                        "native_aliases": sorted(alias_map.get(row["thread_id"], set())),
                    }
                )

    dedupe: dict[tuple[str, str], dict] = {}
    for item in results:
        for alias in item["native_aliases"]:
            dedupe[(alias, item["normalized_text"])] = {
                "thread_id": item["thread_id"],
                "message_id": item["message_id"],
                "title": item["title"],
            }
    return results, dedupe


def maybe_add_native(
    seen: set[tuple[str, str, str]],
    results: list[dict],
    deduped: list[dict],
    t3_index: dict[tuple[str, str], dict],
    item: dict,
) -> None:
    key = (item["provider"], item["native_session_id"], item["normalized_text"])
    if key in seen:
        return
    seen.add(key)

    t3_match = t3_index.get((f"{item['provider']}:{item['native_session_id']}", item["normalized_text"]))
    if t3_match:
        deduped.append(
            {
                "provider": item["provider"],
                "native_session_id": item["native_session_id"],
                "created_at": item["created_at"],
                "excerpt": item["excerpt"],
                "deduped_to_thread_id": t3_match["thread_id"],
                "deduped_to_message_id": t3_match["message_id"],
                "deduped_to_title": t3_match["title"],
            }
        )
        return

    results.append(item)


def parse_claude_file(path: Path, extra_terms: list[str]) -> list[dict]:
    session_id = path.stem
    cwd = None
    results: list[dict] = []
    with path.open(errors="replace") as handle:
        for raw in handle:
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue

            texts: list[str] = []
            timestamp = row.get("timestamp")
            cwd = cwd or row.get("cwd")

            if row.get("type") == "queue-operation" and row.get("operation") == "enqueue":
                if isinstance(row.get("content"), str):
                    texts.append(row["content"])
                session_id = row.get("sessionId") or session_id

            if row.get("type") == "user":
                message = row.get("message", {})
                text = content_text(message.get("content"))
                if text:
                    texts.append(text)
                session_id = row.get("sessionId") or session_id
                cwd = cwd or row.get("cwd") or message.get("cwd")

            for text in texts:
                candidate = trim_harness_preamble(text)
                terms = matched_terms(candidate, extra_terms)
                if not terms:
                    continue
                results.append(
                    {
                        "canonical_source": "native",
                        "provider": "claude",
                        "native_session_id": session_id,
                        "path": str(path),
                        "cwd": cwd,
                        "created_at": timestamp or datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
                        "matched_terms": terms,
                        "excerpt": excerpt(candidate),
                        "normalized_text": normalize_text(candidate),
                    }
                )
    return results


def parse_codex_file(path: Path, extra_terms: list[str]) -> list[dict]:
    session_id = codex_session_id_from_path(path)
    cwd = None
    results: list[dict] = []
    with path.open(errors="replace") as handle:
        for raw in handle:
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue

            timestamp = row.get("timestamp")
            texts: list[str] = []
            if row.get("type") == "session_meta":
                payload = row.get("payload", {})
                session_id = payload.get("id") or session_id
                cwd = cwd or payload.get("cwd")
                continue

            if row.get("type") == "event_msg":
                payload = row.get("payload", {})
                if payload.get("type") == "user_message" and isinstance(payload.get("message"), str):
                    texts.append(payload["message"])

            for text in texts:
                candidate = trim_harness_preamble(text)
                terms = matched_terms(candidate, extra_terms)
                if not terms:
                    continue
                results.append(
                    {
                        "canonical_source": "native",
                        "provider": "codex",
                        "native_session_id": session_id,
                        "path": str(path),
                        "cwd": cwd,
                        "created_at": timestamp or datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
                        "matched_terms": terms,
                        "excerpt": excerpt(candidate),
                        "normalized_text": normalize_text(candidate),
                    }
                )
    return results


def collect_claude(config: SearchConfig, extra_terms: list[str], t3_index: dict[tuple[str, str], dict]) -> tuple[list[dict], list[dict]]:
    seen: set[tuple[str, str, str]] = set()
    results: list[dict] = []
    deduped: list[dict] = []
    for root in config.claude_project_roots:
        for path in rg_candidate_files(root, DEFAULT_TERMS + list(extra_terms)):
            for item in parse_claude_file(path, extra_terms):
                maybe_add_native(seen, results, deduped, t3_index, item)
    return results, deduped


def collect_codex(config: SearchConfig, extra_terms: list[str], t3_index: dict[tuple[str, str], dict]) -> tuple[list[dict], list[dict]]:
    seen: set[tuple[str, str, str]] = set()
    results: list[dict] = []
    deduped: list[dict] = []
    for root in config.codex_session_roots:
        for path in rg_candidate_files(root, DEFAULT_TERMS + list(extra_terms)):
            for item in parse_codex_file(path, extra_terms):
                maybe_add_native(seen, results, deduped, t3_index, item)
    return results, deduped


def collect_opencode(config: SearchConfig, extra_terms: list[str], t3_index: dict[tuple[str, str], dict]) -> tuple[list[dict], list[dict]]:
    seen: set[tuple[str, str, str]] = set()
    results: list[dict] = []
    deduped: list[dict] = []

    like_terms = ["~/.t3", "session", "thread", "introspect", "introspection"] + list(extra_terms)
    where = " OR ".join("lower(p.data) LIKE ? ESCAPE '!'" for _ in like_terms)
    params = [like_pattern(term.lower()) for term in like_terms]

    for db_path in config.opencode_databases:
        if not db_path.exists():
            continue
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            session_rows = cur.execute(
                f"""
                SELECT DISTINCT s.id, s.title, s.directory, s.time_updated
                FROM session AS s
                JOIN part AS p ON p.session_id = s.id
                WHERE {where}
                ORDER BY s.time_updated DESC
                """,
                params,
            ).fetchall()

            for session in session_rows:
                part_rows = cur.execute(
                    """
                    SELECT m.data AS message_data, p.data AS part_data, p.time_created
                    FROM part AS p
                    JOIN message AS m ON m.id = p.message_id
                    WHERE p.session_id = ?
                    ORDER BY p.time_created ASC
                    """,
                    (session["id"],),
                ).fetchall()

                for row in part_rows:
                    try:
                        message_data = json.loads(row["message_data"])
                        part_data = json.loads(row["part_data"])
                    except json.JSONDecodeError:
                        continue
                    if message_data.get("role") != "user":
                        continue
                    text = part_data.get("text")
                    if not isinstance(text, str):
                        continue
                    candidate = trim_harness_preamble(strip_wrapping_quotes(text))
                    terms = matched_terms(candidate, extra_terms)
                    if not terms:
                        continue
                    maybe_add_native(
                        seen,
                        results,
                        deduped,
                        t3_index,
                        {
                            "canonical_source": "native",
                            "provider": "opencode",
                            "native_session_id": session["id"],
                            "title": session["title"],
                            "cwd": session["directory"],
                            "db_path": str(db_path),
                            "created_at": iso_from_ms(row["time_created"]) or iso_from_ms(session["time_updated"]),
                            "matched_terms": terms,
                            "excerpt": excerpt(candidate),
                            "normalized_text": normalize_text(candidate),
                        },
                    )
    return results, deduped


def _sort_key(item: dict) -> datetime:
    return parse_iso(item["created_at"]) or datetime.fromtimestamp(0, tz=timezone.utc)


def collect_introspection_requests(config: SearchConfig, extra_terms: list[str], limit: int = 50) -> dict:
    t3_results, t3_index = collect_t3(config, extra_terms) if "t3" in config.enabled_harnesses else ([], {})
    claude_results, claude_deduped = collect_claude(config, extra_terms, t3_index) if "claude" in config.enabled_harnesses else ([], [])
    codex_results, codex_deduped = collect_codex(config, extra_terms, t3_index) if "codex" in config.enabled_harnesses else ([], [])
    opencode_results, opencode_deduped = collect_opencode(config, extra_terms, t3_index) if "opencode" in config.enabled_harnesses else ([], [])

    results = sorted(
        t3_results + claude_results + codex_results + opencode_results,
        key=_sort_key,
        reverse=True,
    )
    deduped = sorted(
        claude_deduped + codex_deduped + opencode_deduped,
        key=_sort_key,
        reverse=True,
    )
    return {
        "terms": DEFAULT_TERMS + extra_terms,
        "summary": {
            "t3_results": len(t3_results),
            "claude_native_results": len(claude_results),
            "codex_native_results": len(codex_results),
            "opencode_native_results": len(opencode_results),
            "deduped_native_results": len(deduped),
        },
        "results": results[:limit],
        "deduped_native_results": deduped[:limit],
    }
