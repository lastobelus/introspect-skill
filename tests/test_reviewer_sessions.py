from datetime import datetime, timezone
from pathlib import Path

from introspect_skill.config import SearchConfig
from introspect_skill.reviewer_sessions import find_reviewer_session
from tests.support import write_claude_session, write_codex_session, write_opencode_db


def test_find_reviewer_session_matches_codex_subdirectory_cwd(tmp_path: Path) -> None:
    root = tmp_path / ".codex" / "sessions" / "2026" / "04" / "20"
    root.mkdir(parents=True)
    path = root / "rollout-2026-04-20T00-00-00-session-1.jsonl"
    path.write_text(
        '{"timestamp":"2026-04-20T00:00:00Z","type":"session_meta","payload":{"id":"session-1","cwd":"' + str(tmp_path / "repo" / "nested") + '"}}\n'
    )

    config = SearchConfig(
        enabled_harnesses={"codex"},
        t3_roots=[],
        claude_project_roots=[],
        codex_session_indexes=[],
        codex_session_roots=[tmp_path / ".codex" / "sessions"],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = find_reviewer_session(config, "codex", None, str(tmp_path / "repo"), None)
    assert result["matches"][0]["session_id"] == "session-1"


def test_find_reviewer_session_matches_codex_query_from_first_user_message(tmp_path: Path) -> None:
    codex_root = tmp_path / ".codex" / "sessions"
    write_codex_session(
        codex_root,
        "session-1",
        "Please inspect the other thread session log.",
        str(tmp_path / "repo"),
    )

    config = SearchConfig(
        enabled_harnesses={"codex"},
        t3_roots=[],
        claude_project_roots=[],
        codex_session_indexes=[],
        codex_session_roots=[codex_root],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = find_reviewer_session(config, "codex", None, str(tmp_path / "repo"), "other thread")
    assert result["matches"][0]["session_id"] == "session-1"


def test_find_reviewer_session_matches_claude_query(tmp_path: Path) -> None:
    claude_root = tmp_path / ".claude" / "projects"
    write_claude_session(
        claude_root,
        "claude-session-1",
        "Please inspect the other thread session log.",
        str(tmp_path / "repo" / "nested"),
    )

    config = SearchConfig(
        enabled_harnesses={"claude"},
        t3_roots=[],
        claude_project_roots=[claude_root],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = find_reviewer_session(config, "claude", None, str(tmp_path / "repo"), "other thread")
    assert result["matches"][0]["session_id"] == "claude-session-1"


def test_find_reviewer_session_matches_claude_structured_query(tmp_path: Path) -> None:
    claude_root = tmp_path / ".claude" / "projects"
    session_path = write_claude_session(
        claude_root,
        "claude-session-2",
        "Please inspect the other thread session log.",
        str(tmp_path / "repo" / "nested"),
    )
    session_path.write_text(
        session_path.read_text().replace(
            '"message": {"content": "Please inspect the other thread session log."}',
            '"message": {"content": [{"type":"text","text":"Please inspect the other thread session log."}]}',
        )
    )

    config = SearchConfig(
        enabled_harnesses={"claude"},
        t3_roots=[],
        claude_project_roots=[claude_root],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = find_reviewer_session(config, "claude", None, str(tmp_path / "repo"), "other thread")
    assert result["matches"][0]["session_id"] == "claude-session-2"


def test_find_reviewer_session_cwd_filter_rejects_missing_metadata(tmp_path: Path) -> None:
    claude_root = tmp_path / ".claude" / "projects"
    session_path = claude_root / "project-a" / "claude-session-3.jsonl"
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(
        '{"sessionId":"claude-session-3","type":"user","timestamp":"2026-04-20T00:00:00Z","message":{"content":"Please inspect the other thread session log."}}\n'
    )

    config = SearchConfig(
        enabled_harnesses={"claude"},
        t3_roots=[],
        claude_project_roots=[claude_root],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = find_reviewer_session(config, "claude", None, str(tmp_path / "repo"), "other thread")
    assert result["matches"] == []


def test_find_reviewer_session_matches_opencode_query(tmp_path: Path) -> None:
    opencode_db = write_opencode_db(
        tmp_path / ".local" / "share" / "opencode" / "opencode.db",
        "opencode-session-1",
        "Investigate the other thread session log.",
        str(tmp_path / "repo"),
    )

    config = SearchConfig(
        enabled_harnesses={"opencode"},
        t3_roots=[],
        claude_project_roots=[],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[opencode_db],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = find_reviewer_session(config, "opencode", None, str(tmp_path / "repo"), "opencode-session-1")
    assert result["matches"][0]["session_id"] == "opencode-session-1"


def test_find_reviewer_session_rejects_unknown_provider(tmp_path: Path) -> None:
    config = SearchConfig(
        enabled_harnesses=set(),
        t3_roots=[],
        claude_project_roots=[],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    try:
        find_reviewer_session(config, "unknown", None, str(tmp_path), None)
    except ValueError as exc:
        assert "Unsupported provider" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError for unsupported provider")


def test_find_reviewer_session_filters_opencode_by_since(tmp_path: Path) -> None:
    db_path = tmp_path / ".local" / "share" / "opencode" / "opencode.db"
    write_opencode_db(
        db_path,
        "old-session",
        "Investigate the other thread session log.",
        str(tmp_path / "repo"),
        time_created=1000,
        time_updated=2000,
    )
    write_opencode_db(
        db_path,
        "new-session",
        "Investigate the other thread session log.",
        str(tmp_path / "repo"),
        time_created=4000,
        time_updated=5000,
    )

    config = SearchConfig(
        enabled_harnesses={"opencode"},
        t3_roots=[],
        claude_project_roots=[],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[db_path],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = find_reviewer_session(config, "opencode", datetime.fromtimestamp(3, tz=timezone.utc), str(tmp_path / "repo"), None)
    assert [match["session_id"] for match in result["matches"]] == ["new-session"]


def test_find_reviewer_session_uses_full_codex_filename_suffix_when_session_meta_missing(tmp_path: Path) -> None:
    codex_root = tmp_path / ".codex" / "sessions" / "2026" / "04" / "20"
    codex_root.mkdir(parents=True)
    path = codex_root / "rollout-2026-04-20T00-00-00-session-1.jsonl"
    path.write_text(
        '{"timestamp":"2026-04-20T00:00:01Z","type":"event_msg","payload":{"type":"user_message","message":"Please inspect the other thread session log."}}\n'
    )

    config = SearchConfig(
        enabled_harnesses={"codex"},
        t3_roots=[],
        claude_project_roots=[],
        codex_session_indexes=[],
        codex_session_roots=[tmp_path / ".codex" / "sessions"],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = find_reviewer_session(config, "codex", None, None, "other thread")
    assert result["matches"][0]["session_id"] == "session-1"
