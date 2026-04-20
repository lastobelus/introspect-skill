---
name: introspect
description: |
  Inspect T3/agent session state for the current thread or another thread. Use whenever
  the user asks to look in `~/.t3`, inspect a session log, map a thread/provider/session
  ID to the thread it came from, continue another thread's work, explain what another
  thread did, audit review-agent behavior, or diagnose cross-thread/session conflicts.

  This skill is for thread/session forensics, continuity, and log-based debugging. It is
  not a general code-debugging skill.
---

# Introspect Skill

Use this skill to inspect the harness and provider artifacts around a T3Code thread.

## What this skill is for

Common requests that should trigger this skill:

- "look in `~/.t3`"
- "inspect the session log"
- "what happened in the other thread?"
- "continue Claude's work from this session/log"
- "map this id/log path to the thread it came from"
- "did the review agent actually do the review?"
- "which session clobbered this shared resource?"

In practice, most introspection requests fall into one of these buckets:

1. identity lookup
2. continuity / handoff
3. review-agent forensics
4. cross-session resource conflict
5. provider-log / hook / approval failure debug

## Rules

- Prefer durable state first. Start with `~/.t3/userdata/state.sqlite` before scraping raw
  terminal noise.
- Keep the search targeted. Do not grep all of `~` or dump giant logs into the thread.
- Report exact ids, timestamps, worktree paths, branch names, provider names, and source
  files when you have them.
- When collecting history across stores, prefer T3 as the canonical record for a request
  that also appears in the backing Claude/Codex session log. Do not double-count the
  native session copy of the same ask.
- Use the repo config layer when the user has multiple T3 roots or non-default session
  store locations. The public repo supports multiple T3 roots explicitly.
- Treat raw protected files as off-limits for sidecar analysis. Do not feed auth stores,
  `.env`, browser profiles, or local tool-state blobs to an external reviewer.
- When you need cheap high-context clustering or summarization, extract a small local
  bundle first, then use `opencode` on that bundle instead of pointing it at the full
  home directory.

## Start Here

Run commands from the skill root directory. If the skill is bundled into another harness,
that means the directory containing this `SKILL.md`.

If the skill has also been installed as a Python package, prefer the installed
`introspect-*` entry points. The `python3 scripts/...` form below is the repo-local
checkout workflow.

OpenAI-compatible skill hosts may expose this skill as `$introspect`. That alias maps to
this `SKILL.md`, not to a separate executable.

### 1. Resolve the target

The input may be a T3 thread id, a provider session id, a provider log path, a Claude
JSONL path, a Codex session id, an opencode session id, a worktree path, or a fuzzy
title/query.

If the installed entrypoints are available, start with:

```bash
introspect-resolve-target "<query-or-id>"
```

Otherwise fall back to:

```bash
python3 scripts/resolve_target.py "<query-or-id>"
```

If you keep custom session-store locations:

```bash
python3 scripts/resolve_target.py \
  --config ~/.config/introspect-skill/config.toml \
  "<query-or-id>"
```

This intentionally does "dumb but broad" resolution across the harness stores first:

- `~/.t3/userdata/state.sqlite`
- `~/.t3/userdata/logs/provider/`
- `~/.claude/projects/`
- `~/.codex/session_index.jsonl`
- `~/.codex/sessions/`
- `~/.local/share/opencode/opencode.db`
- `opencode session list`

The point is to answer: "what source knows about this id, and what thread/worktree was it
associated with?"

### 2. Collect prior introspection asks

When the request is "find earlier times I asked for thread/session introspection," use
the installed entrypoint when available:

```bash
introspect-collect-history
```

Otherwise use:

```bash
python3 scripts/collect_introspection_requests.py
```

Add `--term` when the user supplied extra clues:

```bash
python3 scripts/collect_introspection_requests.py \
  --term "~/.t3" \
  --term "session" \
  --term "thread"
```

This collector does two passes:

- T3 thread/message history first
- native Claude/Codex/opencode stores second

It then dedupes native hits that map back to the same T3 ask via provider-runtime session
aliases, so you keep one canonical result instead of counting both the T3 message and the
backing native session log.

### 3. Pull thread context from SQLite

If you have a T3 thread id, prefer:

```bash
introspect-thread-context "<thread-id>"
```

Fallback:

```bash
python3 scripts/thread_sqlite.py "<thread-id>"
```

This is the fastest way to get:

- title
- branch
- worktree path
- provider/runtime state
- recent user/assistant messages
- recent thread activities

### 4. Summarize the provider-native artifact

For provider logs under `~/.t3/userdata/logs/provider/`, prefer:

```bash
introspect-provider-log-summary ~/.t3/userdata/logs/provider/<id>.log
```

Fallback:

```bash
python3 scripts/provider_log_summary.py ~/.t3/userdata/logs/provider/<id>.log
```

For Claude JSONL session files, prefer:

```bash
introspect-claude-jsonl-summary ~/.claude/projects/.../<session>.jsonl
```

Fallback:

```bash
python3 scripts/claude_jsonl_summary.py ~/.claude/projects/.../<session>.jsonl
```

These helpers are meant to pull out init metadata, key prompts, hooks, tool calls,
errors, and the final assistant answer without making you read the full artifact first.

### 5. Build a small bundle for sidecar analysis when needed

If the request is mostly log mining, chronology comparison, or cross-session clustering,
build a temp bundle first. Prefer:

```bash
introspect-build-bundle \
  --query "<query-or-id>" \
  --thread-id "<thread-id>" \
  --provider-log ~/.t3/userdata/logs/provider/<id>.log
```

Fallback:

```bash
python3 scripts/build_bundle.py \
  --query "<query-or-id>" \
  --thread-id "<thread-id>" \
  --provider-log ~/.t3/userdata/logs/provider/<id>.log
```

Then run `opencode` against the bundle directory, not the whole repo/home tree:

```bash
cd "<bundle-dir>"
opencode run -m <zai-model> "$PROMPT"
```

Ask `opencode` for exactly one JSON object with fields such as:

- `summary`
- `timeline`
- `findings`
- `unknowns`
- `next_reads`

Treat transcript leakage the same way `review-plan` does: salvage one unambiguous valid
JSON object if present instead of wasting quota on formatting retries.

If the bundle command created a temporary directory because no output dir was supplied,
clean it up after the sidecar analysis is done.

## Review-Agent Session IDs

Use this skill proactively when a workflow launches external reviewers and the user would
benefit from a persisted session id or log path in the main thread.

If you just launched an external reviewer, resolve the persisted session id with:

```bash
introspect-find-reviewer-session <provider> --since "<iso-timestamp>" --cwd "$PWD"
```

Fallback:

```bash
python3 scripts/find_reviewer_session.py <provider> --since "<iso-timestamp>" --cwd "$PWD"
```

If you prefer environment-based overrides instead of `--config`, use:

- `INTROSPECT_SKILL_CONFIG`
- `INTROSPECT_T3_ROOTS`
- `INTROSPECT_ENABLED_HARNESSES`

Supported providers:

- `claude`
- `codex`
- `opencode`

Echo the resolved id/path back into the thread in a compact line, for example:

```text
Reviewer session: provider=opencode session=ses_25938c8c7ffetz34BHVqpZcTp3 source=.local/share/opencode/storage/session_diff/ses_25938c8c7ffetz34BHVqpZcTp3.json
```

If immediate resolution fails, say so briefly and try again after the initial wait window
before calling the review "stuck".

## Output Shape

When reporting introspection findings, prefer this structure:

1. Resolved target
2. Where the session ran
3. Short timeline
4. Findings
5. Unknowns / next reads

Keep raw log excerpts short and evidence-oriented.
