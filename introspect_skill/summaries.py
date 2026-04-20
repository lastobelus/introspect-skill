from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


LINE_RE = re.compile(r"^\[(?P<ts>[^\]]+)\]\s+\w+:\s+(?P<body>\{.*\})$")


def content_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
        elif block.get("type") == "tool_use":
            parts.append(f"[tool_use:{block.get('name')}]")
    return " ".join(parts)


def summarize_claude_jsonl(path: str | Path) -> dict:
    file_path = Path(path).expanduser()
    session_id = None
    cwd = None
    git_branch = None
    user_prompts: list[dict[str, object]] = []
    assistant_texts: list[dict[str, object]] = []
    hook_feedback: list[dict[str, object]] = []
    tool_uses: Counter[str] = Counter()

    with file_path.open(errors="replace") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue

            session_id = session_id or row.get("sessionId")
            cwd = cwd or row.get("cwd")
            git_branch = git_branch or row.get("gitBranch")

            if row.get("type") == "user":
                message = row.get("message", {})
                text = content_text(message.get("content", ""))
                if text:
                    user_prompts.append({"timestamp": row.get("timestamp"), "text": text[:360]})

            if row.get("type") == "assistant":
                message = row.get("message", {})
                content = message.get("content", [])
                text = content_text(content)
                if text:
                    assistant_texts.append({"timestamp": row.get("timestamp"), "text": text[:360]})
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_uses[block.get("name", "unknown")] += 1

            if row.get("type") == "attachment" and row.get("attachment", {}).get("type") == "hook_success":
                attachment = row.get("attachment", {})
                hook_feedback.append(
                    {
                        "timestamp": row.get("timestamp"),
                        "hook_name": attachment.get("hookName"),
                        "hook_event": attachment.get("hookEvent"),
                        "command": attachment.get("command"),
                        "duration_ms": attachment.get("durationMs"),
                    }
                )

    return {
        "path": str(file_path),
        "session_id": session_id,
        "cwd": cwd,
        "git_branch": git_branch,
        "first_user_prompts": user_prompts[:5],
        "final_assistant_messages": assistant_texts[-5:],
        "tool_use_counts": tool_uses.most_common(),
        "hook_feedback": hook_feedback[-5:],
    }


def parse_provider_log_line(raw: str) -> dict | None:
    match = LINE_RE.match(raw)
    if not match:
        return None
    try:
        body = json.loads(match.group("body"))
    except json.JSONDecodeError:
        return None
    body["_observed_at"] = match.group("ts")
    return body


def summarize_provider_log(path: str | Path) -> dict:
    file_path = Path(path).expanduser()
    methods: Counter[str] = Counter()
    init = None
    hooks: list[dict[str, object]] = []
    assistants: list[dict[str, object]] = []
    notable: list[dict[str, object]] = []
    first_ts = None
    last_ts = None

    with file_path.open(errors="replace") as fh:
        for raw in fh:
            parsed = parse_provider_log_line(raw.rstrip("\n"))
            if not parsed:
                continue
            event = parsed.get("event", {})
            method = event.get("method", "")
            payload = event.get("payload", {})
            methods[method] += 1
            first_ts = first_ts or parsed["_observed_at"]
            last_ts = parsed["_observed_at"]

            if method.endswith("/system/init") and init is None:
                init = {
                    "observed_at": parsed["_observed_at"],
                    "provider": event.get("provider"),
                    "provider_thread_id": event.get("providerThreadId"),
                    "cwd": payload.get("cwd"),
                    "model": payload.get("model"),
                    "permission_mode": payload.get("permissionMode"),
                    "session_id": payload.get("session_id"),
                }

            if "hook" in method:
                hooks.append(
                    {
                        "observed_at": parsed["_observed_at"],
                        "method": method,
                        "hook_name": payload.get("hook_name"),
                        "hook_event": payload.get("hook_event"),
                        "outcome": payload.get("outcome"),
                        "exit_code": payload.get("exit_code"),
                    }
                )

            if method.endswith("/assistant"):
                message = payload.get("message", {})
                text_blocks = []
                for block in message.get("content", []):
                    if block.get("type") == "text":
                        text_blocks.append(block.get("text", ""))
                if text_blocks:
                    assistants.append({"observed_at": parsed["_observed_at"], "text": " ".join(text_blocks)[:320]})

            if "error" in method.lower() or payload.get("status") in {"errored", "failed"}:
                notable.append(
                    {
                        "observed_at": parsed["_observed_at"],
                        "method": method,
                        "payload": json.dumps(payload)[:320],
                    }
                )

    return {
        "path": str(file_path),
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "init": init,
        "top_methods": methods.most_common(20),
        "hooks": hooks[-20:],
        "assistant_text_samples": assistants[-10:],
        "notable": notable[-20:],
    }
