from pathlib import Path

from introspect_skill.config import SearchConfig
from introspect_skill.history import collect_introspection_requests
from tests.support import write_claude_session, write_codex_session, write_t3_state_db


def test_collect_introspection_requests_dedupes_t3_backed_codex_session(tmp_path: Path) -> None:
    t3_root = tmp_path / ".t3"
    codex_root = tmp_path / ".codex" / "sessions"
    message = "investigate session logs in ~/.t3 for times when I've done introspection"
    native_session_id = "codex-native-1"

    write_t3_state_db(t3_root, "thread-1", message, native_session_id, title="Intro")
    write_codex_session(codex_root, native_session_id, message, str(tmp_path / "repo"))

    config = SearchConfig(
        enabled_harnesses={"t3", "codex"},
        t3_roots=[t3_root],
        claude_project_roots=[],
        codex_session_indexes=[],
        codex_session_roots=[codex_root],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = collect_introspection_requests(config, [], limit=10)
    assert result["summary"]["t3_results"] == 1
    assert result["summary"]["deduped_native_results"] == 1
    assert result["results"][0]["canonical_source"] == "t3"
    assert result["deduped_native_results"][0]["deduped_to_thread_id"] == "thread-1"


def test_collect_introspection_requests_dedupes_t3_backed_claude_session(tmp_path: Path) -> None:
    t3_root = tmp_path / ".t3"
    claude_root = tmp_path / ".claude" / "projects"
    message = "investigate session logs in ~/.t3 for times when I've done introspection"
    native_session_id = "claude-native-1"

    write_t3_state_db(
        t3_root,
        "thread-1",
        message,
        native_session_id,
        title="Intro",
        provider_name="claudeAgent",
        resume_cursor_json='{"resume":"claude-native-1"}',
    )
    write_claude_session(claude_root, native_session_id, message, str(tmp_path / "repo"))

    config = SearchConfig(
        enabled_harnesses={"t3", "claude"},
        t3_roots=[t3_root],
        claude_project_roots=[claude_root],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = collect_introspection_requests(config, [], limit=10)
    assert result["summary"]["t3_results"] == 1
    assert result["summary"]["deduped_native_results"] == 1
    assert result["results"][0]["canonical_source"] == "t3"
    assert result["deduped_native_results"][0]["provider"] == "claude"


def test_collect_introspection_requests_dedupes_t3_backed_structured_claude_session(tmp_path: Path) -> None:
    t3_root = tmp_path / ".t3"
    claude_root = tmp_path / ".claude" / "projects"
    message = "investigate session logs in ~/.t3 for times when I've done introspection"
    native_session_id = "claude-native-2"

    write_t3_state_db(
        t3_root,
        "thread-2",
        message,
        native_session_id,
        title="Intro Structured",
        provider_name="claudeAgent",
        resume_cursor_json='{"resume":"claude-native-2"}',
    )
    session_path = write_claude_session(claude_root, native_session_id, message, str(tmp_path / "repo"))
    session_path.write_text(
        session_path.read_text().replace(
            f'"message": {{"content": "{message}"}}',
            f'"message": {{"content": [{{"type":"text","text":"{message}"}}]}}',
        )
    )

    config = SearchConfig(
        enabled_harnesses={"t3", "claude"},
        t3_roots=[t3_root],
        claude_project_roots=[claude_root],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = collect_introspection_requests(config, [], limit=10)
    assert result["summary"]["t3_results"] == 1
    assert result["summary"]["deduped_native_results"] == 1
    assert result["deduped_native_results"][0]["provider"] == "claude"


def test_collect_introspection_requests_dedupes_duplicate_t3_rows_across_roots(tmp_path: Path) -> None:
    message = "investigate session logs in ~/.t3 for times when I've done introspection"
    root_a = tmp_path / ".t3-a"
    root_b = tmp_path / ".t3-b"

    write_t3_state_db(root_a, "thread-1", message, "codex-native-1", title="Intro")
    write_t3_state_db(root_b, "thread-1", message, "codex-native-1", title="Intro")

    config = SearchConfig(
        enabled_harnesses={"t3"},
        t3_roots=[root_a, root_b],
        claude_project_roots=[],
        codex_session_indexes=[],
        codex_session_roots=[],
        opencode_databases=[],
        opencode_session_diff_roots=[],
        source_path=None,
    )

    result = collect_introspection_requests(config, [], limit=10)
    assert result["summary"]["t3_results"] == 1
    assert len(result["results"]) == 1


def test_collect_introspection_requests_uses_full_codex_filename_suffix_when_session_meta_missing(tmp_path: Path) -> None:
    codex_root = tmp_path / ".codex" / "sessions" / "2026" / "04" / "20"
    codex_root.mkdir(parents=True)
    path = codex_root / "rollout-2026-04-20T00-00-00-session-1.jsonl"
    path.write_text(
        '{"timestamp":"2026-04-20T00:00:01Z","type":"event_msg","payload":{"type":"user_message","message":"investigate session logs in ~/.t3 for times when I have done introspection"}}\n'
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

    result = collect_introspection_requests(config, [], limit=10)
    assert result["results"][0]["native_session_id"] == "session-1"
