import subprocess
from pathlib import Path

from introspect_skill.config import SearchConfig
from introspect_skill.resolve import resolve_target
from tests.support import write_opencode_db, write_t3_state_db


def test_resolve_target_finds_opencode_session_in_db(tmp_path: Path) -> None:
    opencode_db = tmp_path / ".local" / "share" / "opencode" / "opencode.db"
    write_opencode_db(opencode_db, "ses_abc123", "inspect this thread", str(tmp_path / "repo"))

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

    result = resolve_target("ses_abc123", config)
    assert any(match["kind"] == "opencode-session" for match in result["matches"])


def test_resolve_target_searches_second_t3_root(tmp_path: Path) -> None:
    t3_root = tmp_path / ".t3-fork"
    write_t3_state_db(t3_root, "thread-2", "inspect the other thread", "codex-thread-2", title="Fork Thread")

    config = SearchConfig(
        enabled_harnesses={"t3"},
        t3_roots=[t3_root],
        claude_project_roots=[],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = resolve_target("thread-2", config)
    assert result["matches"][0]["kind"] == "t3-thread"
    assert result["matches"][0]["title"] == "Fork Thread"


def test_resolve_target_treats_like_wildcards_as_literals(tmp_path: Path) -> None:
    t3_root = tmp_path / ".t3"
    write_t3_state_db(t3_root, "thread-percent", "inspect this session", "codex-thread-1", title="100% Thread")
    write_t3_state_db(t3_root, "thread-plain", "inspect this session", "codex-thread-2", title="Plain Thread")

    config = SearchConfig(
        enabled_harnesses={"t3"},
        t3_roots=[t3_root],
        claude_project_roots=[],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = resolve_target("%", config)
    thread_matches = [match for match in result["matches"] if match["kind"] == "t3-thread"]
    assert [match["thread_id"] for match in thread_matches] == ["thread-percent"]


def test_resolve_target_finds_codex_session_in_index(tmp_path: Path) -> None:
    index_path = tmp_path / ".codex" / "session_index.jsonl"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text('{"id":"session-9","thread_name":"Inspect other thread","updated_at":"2026-04-20T00:00:00Z"}\n')

    config = SearchConfig(
        enabled_harnesses={"codex"},
        t3_roots=[],
        claude_project_roots=[],
        codex_session_indexes=[index_path],
        codex_session_roots=[],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = resolve_target("Inspect other thread", config)
    assert any(match["kind"] == "codex-session" and match["session_id"] == "session-9" for match in result["matches"])


def test_resolve_target_finds_opencode_session_in_diff_dir(tmp_path: Path) -> None:
    diff_root = tmp_path / ".local" / "share" / "opencode" / "storage" / "session_diff"
    diff_root.mkdir(parents=True)
    (diff_root / "ses_diff_1.json").write_text("{}\n")

    config = SearchConfig(
        enabled_harnesses={"opencode"},
        t3_roots=[],
        claude_project_roots=[],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[],
        opencode_session_diff_roots=[diff_root],
        source_path=None,
    )

    result = resolve_target("ses_diff_1", config)
    assert any(match["kind"] == "opencode-session" and match["session_id"] == "ses_diff_1" for match in result["matches"])


def test_resolve_target_finds_opencode_session_from_session_list(tmp_path: Path, monkeypatch) -> None:
    config = SearchConfig(
        enabled_harnesses={"opencode"},
        t3_roots=[],
        claude_project_roots=[],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="ses_list_1  Session list hit  2026-04-20T00:00:00Z\n",
            stderr="",
        )

    monkeypatch.setattr("introspect_skill.resolve.subprocess.run", fake_run)
    result = resolve_target("Session list hit", config)
    assert any(match["kind"] == "opencode-session" and match["session_id"] == "ses_list_1" for match in result["matches"])
