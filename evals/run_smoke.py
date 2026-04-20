#!/usr/bin/env python3

from pathlib import Path
import json
import os
import subprocess
import sys
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from introspect_skill.config import SearchConfig, load_config
from introspect_skill.history import collect_introspection_requests
from introspect_skill import resolve as resolve_module
from introspect_skill.resolve import resolve_target
from tests.support import write_claude_session, write_codex_session, write_opencode_db, write_provider_log, write_t3_state_db


def main() -> None:
    scenarios: list[tuple[str, bool]] = []
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}

    with TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        home = tmp / "home"

        write_t3_state_db(home / ".t3", "thread-1", "inspect this session in ~/.t3", "native-1", title="T3 One")
        write_t3_state_db(home / ".t3-alt", "thread-2", "inspect the other thread in ~/.t3", "native-2", title="T3 Two")
        config_dir = home / ".config" / "introspect-skill"
        config_dir.mkdir(parents=True)
        (config_dir / "config.toml").write_text('t3_roots = ["~/.t3-alt"]\n')
        config = load_config(home=home)
        scenarios.append(("multi_t3_root_discovery", config.t3_roots == [home / ".t3-alt"]))

        codex_root = home / ".codex" / "sessions"
        message = "investigate session logs in ~/.t3 for times when I've done introspection"
        write_t3_state_db(home / ".t3-eval", "thread-3", message, "codex-native-3", title="Eval Thread")
        write_codex_session(codex_root, "codex-native-3", message, str(home / "repo"))
        history_config = SearchConfig(
            enabled_harnesses={"t3", "codex"},
            t3_roots=[home / ".t3-eval"],
            claude_project_roots=[],
            codex_session_indexes=[],
            codex_session_roots=[codex_root],
            opencode_databases=[],
            opencode_session_diff_roots=[],
            source_path=None,
        )
        history_result = collect_introspection_requests(history_config, [], limit=10)
        scenarios.append(("t3_codex_dedupe", history_result["summary"]["deduped_native_results"] == 1))

        claude_root = home / ".claude" / "projects"
        write_t3_state_db(
            home / ".t3-claude",
            "thread-4",
            message,
            "claude-native-4",
            title="Claude Eval Thread",
            provider_name="claudeAgent",
            resume_cursor_json='{"resume":"claude-native-4"}',
        )
        write_claude_session(claude_root, "claude-native-4", message, str(home / "repo"))
        claude_history_config = SearchConfig(
            enabled_harnesses={"t3", "claude"},
            t3_roots=[home / ".t3-claude"],
            claude_project_roots=[claude_root],
            codex_session_indexes=[],
            codex_session_roots=[],
            opencode_databases=[],
            opencode_session_diff_roots=[],
            source_path=None,
        )
        claude_history_result = collect_introspection_requests(claude_history_config, [], limit=10)
        scenarios.append(("t3_claude_dedupe", claude_history_result["summary"]["deduped_native_results"] == 1))

        opencode_db = home / ".local" / "share" / "opencode" / "opencode.db"
        write_opencode_db(opencode_db, "ses_eval", "inspect this thread", str(home / "repo"))
        resolve_config = SearchConfig(
            enabled_harnesses={"opencode"},
            t3_roots=[],
            claude_project_roots=[],
            codex_session_indexes=[],
            codex_session_roots=[],
            opencode_databases=[opencode_db],
            opencode_session_diff_roots=[],
            source_path=None,
        )
        resolve_result = resolve_target("ses_eval", resolve_config)
        scenarios.append(("opencode_db_resolution", any(item["kind"] == "opencode-session" for item in resolve_result["matches"])))

        codex_index = home / ".codex" / "session_index.jsonl"
        codex_index.parent.mkdir(parents=True, exist_ok=True)
        codex_index.write_text('{"id":"codex-session-9","thread_name":"Inspect other thread","updated_at":"2026-04-20T00:00:00Z"}\n')
        index_config = SearchConfig(
            enabled_harnesses={"codex"},
            t3_roots=[],
            claude_project_roots=[],
            codex_session_indexes=[codex_index],
            codex_session_roots=[],
            opencode_databases=[],
            opencode_session_diff_roots=[],
            source_path=None,
        )
        index_result = resolve_target("Inspect other thread", index_config)
        scenarios.append(("codex_index_resolution", any(item["kind"] == "codex-session" for item in index_result["matches"])))

        diff_root = home / ".local" / "share" / "opencode" / "storage" / "session_diff"
        diff_root.mkdir(parents=True, exist_ok=True)
        (diff_root / "ses_diff_1.json").write_text("{}\n")
        diff_config = SearchConfig(
            enabled_harnesses={"opencode"},
            t3_roots=[],
            claude_project_roots=[],
            codex_session_indexes=[],
            codex_session_roots=[],
            opencode_databases=[],
            opencode_session_diff_roots=[diff_root],
            source_path=None,
        )
        diff_result = resolve_target("ses_diff_1", diff_config)
        scenarios.append(("opencode_session_diff_resolution", any(item["session_id"] == "ses_diff_1" for item in diff_result["matches"])))

        original_run = resolve_module.subprocess.run

        def fake_run(*args, **kwargs):
            if args and args[0] == ["opencode", "session", "list"]:
                return subprocess.CompletedProcess(
                    args=args[0],
                    returncode=0,
                    stdout="ses_list_1  Session list hit  2026-04-20T00:00:00Z\n",
                    stderr="",
                )
            return original_run(*args, **kwargs)

        resolve_module.subprocess.run = fake_run
        try:
            session_list_result = resolve_target("Session list hit", diff_config)
        finally:
            resolve_module.subprocess.run = original_run
        scenarios.append(("opencode_session_list_resolution", any(item["session_id"] == "ses_list_1" for item in session_list_result["matches"])))

        cli_proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "resolve_target.py"), "--config", str(config_dir / "config.toml"), "thread-2"],
            capture_output=True,
            text=True,
            check=True,
            cwd=REPO_ROOT,
            env={**env, "HOME": str(home)},
        )
        cli_payload = json.loads(cli_proc.stdout)
        scenarios.append(("resolve_target_cli_json", cli_payload["matches"][0]["kind"] == "t3-thread"))

        claude_jsonl = write_claude_session(
            home / ".claude" / "projects",
            "claude-eval",
            "Inspect the other thread session log.",
            str(home / "repo"),
        )
        claude_summary = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "claude_jsonl_summary.py"), str(claude_jsonl)],
            capture_output=True,
            text=True,
            check=True,
            cwd=REPO_ROOT,
            env=env,
        )
        scenarios.append(("claude_jsonl_summary_cli_json", json.loads(claude_summary.stdout)["session_id"] == "claude-eval"))

        provider_log = write_provider_log(
            home / ".t3" / "userdata" / "logs" / "provider" / "provider.log",
            str(home / "repo"),
            "provider-session-1",
        )
        provider_summary = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "provider_log_summary.py"), str(provider_log)],
            capture_output=True,
            text=True,
            check=True,
            cwd=REPO_ROOT,
            env=env,
        )
        scenarios.append(("provider_log_summary_cli_json", json.loads(provider_summary.stdout)["init"]["session_id"] == "provider-session-1"))

    failed = [name for name, passed in scenarios if not passed]
    for name, passed in scenarios:
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    if failed:
        raise SystemExit(f"Smoke eval failures: {', '.join(failed)}")


if __name__ == "__main__":
    main()
