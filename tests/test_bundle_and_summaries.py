from __future__ import annotations

from introspect_skill.bundle import build_bundle
from introspect_skill.config import SearchConfig
from introspect_skill.summaries import summarize_provider_log


def test_build_bundle_expands_user_output_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
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

    result = build_bundle(config, output_dir="~/bundle-target")
    assert result["bundle_dir"] == str(tmp_path / "bundle-target")


def test_summarize_provider_log_keeps_latest_hooks_and_notables(tmp_path) -> None:
    log_path = tmp_path / "provider.log"
    lines = []
    for idx in range(25):
        lines.append(
            f'[2026-04-20T00:00:{idx:02d}Z] INFO: {{"event":{{"method":"provider/hook/success","payload":{{"hook_name":"hook-{idx}","hook_event":"event-{idx}","outcome":"ok","exit_code":0}}}}}}'
        )
    for idx in range(25):
        lines.append(
            f'[2026-04-20T00:01:{idx:02d}Z] INFO: {{"event":{{"method":"provider/error","payload":{{"status":"failed","message":"error-{idx}"}}}}}}'
        )
    log_path.write_text("\n".join(lines) + "\n")

    result = summarize_provider_log(log_path)
    assert len(result["hooks"]) == 20
    assert result["hooks"][0]["hook_name"] == "hook-5"
    assert result["hooks"][-1]["hook_name"] == "hook-24"
    assert len(result["notable"]) == 20
    assert '"message": "error-5"' in result["notable"][0]["payload"]
    assert '"message": "error-24"' in result["notable"][-1]["payload"]
