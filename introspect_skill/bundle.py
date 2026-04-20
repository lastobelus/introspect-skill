from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from introspect_skill.config import SearchConfig
from introspect_skill.resolve import resolve_target
from introspect_skill.summaries import summarize_claude_jsonl, summarize_provider_log
from introspect_skill.threads import thread_context


def build_bundle(
    config: SearchConfig,
    *,
    query: str | None = None,
    thread_id: str | None = None,
    provider_log: str | None = None,
    claude_jsonl: str | None = None,
    opencode_session: str | None = None,
    output_dir: str | None = None,
) -> dict:
    bundle_dir = Path(output_dir).expanduser() if output_dir else Path(tempfile.mkdtemp(prefix="introspect-bundle-"))
    bundle_dir.mkdir(parents=True, exist_ok=True)

    created: list[str] = []

    if query:
        path = bundle_dir / "resolved_target.json"
        path.write_text(json.dumps(resolve_target(query, config), indent=2))
        created.append(str(path))

    if thread_id:
        path = bundle_dir / "thread_context.json"
        path.write_text(json.dumps(thread_context(thread_id, config), indent=2))
        created.append(str(path))

    if provider_log:
        path = bundle_dir / "provider_log_summary.json"
        path.write_text(json.dumps(summarize_provider_log(provider_log), indent=2))
        created.append(str(path))

    if claude_jsonl:
        path = bundle_dir / "claude_jsonl_summary.json"
        path.write_text(json.dumps(summarize_claude_jsonl(claude_jsonl), indent=2))
        created.append(str(path))

    if opencode_session:
        try:
            proc = subprocess.run(
                ["opencode", "export", opencode_session],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("opencode is not installed or not on PATH") from exc
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"opencode export failed for {opencode_session}")
        safe_name = Path(opencode_session).name
        path = bundle_dir / f"{safe_name}.export.json"
        path.write_text(proc.stdout)
        created.append(str(path))

    readme = bundle_dir / "README.txt"
    readme.write_text(
        "This bundle is for targeted session introspection.\n"
        "Prefer asking for one JSON object with summary, timeline, findings, unknowns, and next_reads.\n"
        "Do not feed protected raw files or credentials to an external reviewer.\n"
        "If you did not supply --output-dir, clean up this temporary directory when you are done.\n"
    )
    created.append(str(readme))

    return {"bundle_dir": str(bundle_dir), "files": created}
