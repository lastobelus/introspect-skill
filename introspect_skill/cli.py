from __future__ import annotations

import argparse
import json

from introspect_skill.bundle import build_bundle
from introspect_skill.config import load_config
from introspect_skill.history import collect_introspection_requests
from introspect_skill.resolve import resolve_target
from introspect_skill.reviewer_sessions import find_reviewer_session
from introspect_skill.summaries import summarize_claude_jsonl, summarize_provider_log
from introspect_skill.timestamps import parse_iso
from introspect_skill.threads import thread_context


def _load_config_or_exit(config_path: str | None):
    try:
        return load_config(config_path)
    except ValueError as exc:
        raise SystemExit(str(exc))


def _parse_since_arg(parser: argparse.ArgumentParser, raw: str | None):
    if raw is None:
        return None
    try:
        return parse_iso(raw)
    except ValueError:
        parser.error(f"invalid --since value {raw!r}; expected ISO-8601 like 2026-04-20T18:00:00Z")


def resolve_target_main() -> None:
    parser = argparse.ArgumentParser(description="Resolve a thread, provider session, log path, or fuzzy query across configured session stores.")
    parser.add_argument("--config", help="Optional path to a config.toml file.")
    parser.add_argument("query", help="Thread ID, session ID, log path, worktree path, or fuzzy query.")
    args = parser.parse_args()
    config = _load_config_or_exit(args.config)
    print(json.dumps(resolve_target(args.query, config), indent=2))


def collect_introspection_requests_main() -> None:
    parser = argparse.ArgumentParser(description="Collect prior introspection-style requests from configured T3, Claude, Codex, and opencode stores.")
    parser.add_argument("--config", help="Optional path to a config.toml file.")
    parser.add_argument("--term", action="append", default=[], help="Extra search term")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of results to include in the output.")
    args = parser.parse_args()
    config = _load_config_or_exit(args.config)
    print(json.dumps(collect_introspection_requests(config, args.term, limit=args.limit), indent=2))


def thread_sqlite_main() -> None:
    parser = argparse.ArgumentParser(description="Load thread context for a T3 thread from a configured or explicitly supplied state.sqlite database.")
    parser.add_argument("--config", help="Optional path to a config.toml file.")
    parser.add_argument("--state-db", help="Optional explicit state.sqlite path to query instead of searching configured T3 roots.")
    parser.add_argument("thread_id", help="T3 thread ID to inspect.")
    args = parser.parse_args()
    config = _load_config_or_exit(args.config)
    try:
        out = thread_context(args.thread_id, config, state_db=args.state_db)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps(out, indent=2))


def find_reviewer_session_main() -> None:
    parser = argparse.ArgumentParser(description="Find recent persisted reviewer sessions for Claude, Codex, or opencode.")
    parser.add_argument("--config", help="Optional path to a config.toml file.")
    parser.add_argument("provider", choices=["claude", "codex", "opencode"], help="Reviewer provider to inspect.")
    parser.add_argument("--since", help="Optional ISO timestamp lower bound, such as 2026-04-20T18:00:00Z.")
    parser.add_argument("--cwd", help="Optional working-directory prefix to filter matching sessions.")
    parser.add_argument("--query", help="Optional title or metadata query to narrow matches.")
    args = parser.parse_args()
    config = _load_config_or_exit(args.config)
    print(json.dumps(find_reviewer_session(config, args.provider, _parse_since_arg(parser, args.since), args.cwd, args.query), indent=2))


def provider_log_summary_main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a T3 provider log into init metadata, hook events, assistant samples, and notable errors.")
    parser.add_argument("path", help="Path to a provider log file under userdata/logs/provider.")
    args = parser.parse_args()
    print(json.dumps(summarize_provider_log(args.path), indent=2))


def claude_jsonl_summary_main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a Claude JSONL session file into prompts, assistant messages, tool uses, and hook feedback.")
    parser.add_argument("path", help="Path to a Claude JSONL session file.")
    args = parser.parse_args()
    print(json.dumps(summarize_claude_jsonl(args.path), indent=2))


def build_bundle_main() -> None:
    parser = argparse.ArgumentParser(description="Create a small local bundle of thread/session artifacts for sidecar analysis.")
    parser.add_argument("--config", help="Optional path to a config.toml file.")
    parser.add_argument("--query", help="Optional thread ID, session ID, or fuzzy query to resolve.")
    parser.add_argument("--thread-id", help="Optional T3 thread ID to expand into thread context.")
    parser.add_argument("--provider-log", help="Optional provider log path to summarize into the bundle.")
    parser.add_argument("--claude-jsonl", help="Optional Claude JSONL path to summarize into the bundle.")
    parser.add_argument("--opencode-session", help="Optional opencode session ID to export into the bundle.")
    parser.add_argument("--output-dir", help="Optional output directory. Defaults to a temporary bundle directory.")
    args = parser.parse_args()
    config = _load_config_or_exit(args.config)
    print(
        json.dumps(
            build_bundle(
                config,
                query=args.query,
                thread_id=args.thread_id,
                provider_log=args.provider_log,
                claude_jsonl=args.claude_jsonl,
                opencode_session=args.opencode_session,
                output_dir=args.output_dir,
            ),
            indent=2,
        )
    )
