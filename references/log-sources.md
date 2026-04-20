# Introspection Log Sources

Start with the durable stores, then move outward.

The public repo version lets users replace default roots per store family via `config.toml`
and add extra roots via environment variables. The list below documents the default store
families, not a requirement that every installation use the same locations.

## Primary stores

### `~/.t3/userdata/state.sqlite`

Main tables:

- `projection_threads`
- `projection_thread_messages`
- `projection_thread_activities`
- `projection_thread_sessions`
- `provider_session_runtime`
- `projection_turns`

Use this first for:

- thread title / branch / worktree path
- recent messages
- T3 thread status
- provider/runtime status

### `~/.t3/userdata/logs/provider/*.log`

Harness/provider event stream. Useful for:

- provider init metadata
- provider thread/session ids
- hooks
- tool-call chronology
- approvals / auth / crash signals

### `~/.claude/projects/**/*.jsonl`

Claude-native session files. Useful for:

- exact prompt text
- tool use
- hook feedback
- final assistant answer
- Claude `sessionId`

## Secondary stores

### `~/.codex/session_index.jsonl`

Codex session ids and thread names. Use this for quick ID/title lookup.

Related stores:

- `~/.codex/sessions/**/*.jsonl`
- `~/.codex/archived_sessions/*.jsonl`
- `~/.codex/history.jsonl`

### `~/.local/share/opencode/opencode.db`

Opencode-native session metadata and message parts. Use this for:

- session id / title / cwd lookup
- targeted prompt-text mining across opencode history
- session-level timelines without exporting every session

Related stores:

- `opencode session list`
- `~/.local/share/opencode/storage/session_diff/*.json`
- `opencode export <sessionID>`

### `~/.t3/userdata/logs/terminals/*.log`

Only use this when the higher-level stores are insufficient. These logs are noisy and are
better for confirming cwd / shell commands / foreground process behavior than for primary
thread reconstruction.

## Dedupe policy

- When a T3 thread is backed by a native Claude or Codex session, the same user ask can
  appear in both places.
- For history collection, prefer the T3 message as canonical and suppress the matching
  native duplicate when the provider session alias and normalized prompt text line up.
- Native hits that do not map back to a T3 thread stay as standalone results.
- With multiple configured T3 roots, treat all configured state databases as one logical
  T3 search surface.

## Protected / high-risk artifacts

Do not feed these raw into external reviewers:

- `.env` files
- auth stores / credentials
- browser profiles
- local tool-state blobs
- anything containing copied secrets

Translate the needed contract into a sanitized summary instead.
