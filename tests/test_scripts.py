from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tests.support import write_claude_session, write_provider_log, write_t3_state_db


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str, env: dict[str, str] | None = None) -> dict:
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return json.loads(proc.stdout)


def test_claude_jsonl_summary_script(tmp_path: Path) -> None:
    session = write_claude_session(
        tmp_path / ".claude" / "projects",
        "claude-session-1",
        "Please inspect the other thread session log.",
        str(tmp_path / "repo"),
    )

    result = run_script(str(REPO_ROOT / "scripts" / "claude_jsonl_summary.py"), str(session))
    assert result["session_id"] == "claude-session-1"
    assert result["cwd"] == str(tmp_path / "repo")
    assert result["tool_use_counts"] == [["Read", 1]]
    assert result["hook_feedback"][0]["hook_name"] == "pre-tool"


def test_provider_log_summary_script(tmp_path: Path) -> None:
    log_path = write_provider_log(
        tmp_path / "userdata" / "logs" / "provider" / "thread-1.log",
        str(tmp_path / "repo"),
        "provider-session-1",
    )

    result = run_script(str(REPO_ROOT / "scripts" / "provider_log_summary.py"), str(log_path))
    assert result["init"]["session_id"] == "provider-session-1"
    assert result["init"]["cwd"] == str(tmp_path / "repo")
    assert result["hooks"][0]["hook_name"] == "pre-tool"
    assert result["assistant_text_samples"][0]["text"] == "Found the session."


def test_build_bundle_script(tmp_path: Path) -> None:
    t3_root = tmp_path / ".t3"
    config_dir = tmp_path / ".config" / "introspect-skill"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.toml"
    config_path.write_text(f'enabled_harnesses = ["t3"]\nt3_roots = ["{t3_root}"]\n')

    write_t3_state_db(
        t3_root,
        "thread-1",
        "inspect the other thread session log",
        "native-session-1",
        title="Bundle test",
    )

    bundle = run_script(
        str(REPO_ROOT / "scripts" / "build_bundle.py"),
        "--config",
        str(config_path),
        "--query",
        "thread-1",
        "--thread-id",
        "thread-1",
        "--output-dir",
        str(tmp_path / "bundle"),
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )

    file_names = {Path(path).name for path in bundle["files"]}
    assert bundle["bundle_dir"] == str(tmp_path / "bundle")
    assert {"README.txt", "resolved_target.json", "thread_context.json"} <= file_names


def test_find_reviewer_session_script_rejects_invalid_since(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "find_reviewer_session.py"),
            "codex",
            "--since",
            "not-a-timestamp",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    assert proc.returncode != 0
    assert "invalid --since value" in proc.stderr


def test_thread_sqlite_script_rejects_missing_explicit_state_db(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "thread_sqlite.py"),
            "--state-db",
            str(tmp_path / "missing.sqlite"),
            "thread-1",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    assert proc.returncode != 0
    assert "State database not found" in proc.stderr
