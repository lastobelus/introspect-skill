# Local Session Store Findings

Research date: 2026-05-04.

These findings came from read-only background agents inspecting local T3, Codex, Claude, and opencode stores. Private message content was intentionally excluded; findings focus on structure, counts, metadata fields, and opportunities.

## T3

One T3 root was found:

- `~/.t3`

Main stores:

- `~/.t3/userdata/state.sqlite`
- `~/.t3/userdata/logs/provider/*.log`
- `~/.t3/userdata/logs/terminals/*.log`
- `~/.t3/userdata/logs/server.trace.ndjson*`
- `~/.t3/userdata/attachments/*.png`
- `~/.t3/worktrees/<project>/<worktree>`

Observed volumes:

- `~/.t3`: 14G
- `~/.t3/worktrees`: 12G
- `~/.t3/userdata`: 2.4G
- `state.sqlite`: 464M
- provider logs: 1.8G across 250 files
- terminal logs: 25 files
- worktree dirs: 42

Relevant `introspect-skill` thread:

- project title: `introspect-skill`
- workspace root: `/Users/lasto/projects/introspect-skill`
- thread: `21b3e169-c598-4b60-8aa6-508f2e9eb791`
- branch: `t3code/project-status`
- worktree: `/Users/lasto/.t3/worktrees/introspect-skill/t3code-952db7f5`
- runtime/provider: Codex
- provider log: `~/.t3/userdata/logs/provider/21b3e169-c598-4b60-8aa6-508f2e9eb791.log`

Important T3 tables:

- `orchestration_events`
- `orchestration_command_receipts`
- `projection_projects`
- `projection_threads`
- `projection_thread_sessions`
- `provider_session_runtime`
- `projection_turns`
- `projection_thread_activities`
- `projection_thread_messages`
- `projection_thread_proposed_plans`
- `projection_pending_approvals`

Global row counts:

- `orchestration_events`: 69,005
- `orchestration_command_receipts`: 68,077
- `projection_thread_activities`: 49,867
- `projection_thread_messages`: 7,380
- `projection_turns`: 851
- `projection_threads`: 95
- `projection_thread_sessions`: 95
- `provider_session_runtime`: 64
- `projection_projects`: 12

T3 opportunities:

- Add a metadata-only thread summary mode that avoids message text.
- Use the event store for chronology and projections for current state.
- Add a structured provider-log parser that extracts event kinds, ids, levels, and timestamps without raw message bodies.
- Include attachment linkage metadata without inspecting image contents.

## Codex

Main stores:

- `~/.codex/sessions/**/*.jsonl`
- `~/.codex/archived_sessions/*.jsonl`
- `~/.codex/session_index.jsonl`
- `~/.codex/history.jsonl`
- `~/.codex/state_5.sqlite`
- `~/.codex/logs_2.sqlite`
- `~/.codex/sqlite/codex-dev.db`
- `~/.codex/plugins/cache`
- `~/.codex/skills`
- `~/.codex/worktrees`

Observed volumes:

- `~/.codex`: 4.0G
- worktrees: 3.2G
- sessions: 307M
- archived sessions: 27M
- plugin cache: 31M
- shell snapshots: 9.8M

Session counts:

- active session JSONL files: 303
- active JSONL records: 140,185
- `session_index.jsonl`: 105 entries
- `history.jsonl`: 24 entries

Relevant current-worktree sessions:

- 4 Codex session JSONL files referenced `/Users/lasto/.t3/worktrees/introspect-skill/t3code-952db7f5`
- event envelope: `type`, `timestamp`, `payload`
- event types in those files: `response_item`, `event_msg`, `turn_context`, `session_meta`

Useful Codex metadata fields:

- `cwd`
- session id and turn id
- git commit, branch, and repository URL
- model and reasoning effort
- sandbox and approval policy
- token usage and context window
- CLI version and model provider

Important Codex SQLite stores:

- `state_5.sqlite`
  - tables include `threads`, `thread_dynamic_tools`, `thread_spawn_edges`, `thread_goals`, `jobs`, `agent_jobs`, `agent_job_items`
  - `threads`: 270 rows
  - `thread_spawn_edges`: 18 rows
- `logs_2.sqlite`
  - `logs`: 140,545 rows
  - logs with `thread_id`: 80,190
  - distinct logged thread ids: 107

Codex opportunities:

- Add `state_5.sqlite` as a primary Codex lookup index.
- Add `logs_2.sqlite` as a thread-scoped diagnostics source.
- Include `archived_sessions` in default discovery.
- Use `thread_spawn_edges` to expose subagent relationships.
- Inventory plugin/skill availability from Codex metadata when relevant.

## Claude

Relevant durable store:

- `~/.claude/projects/-Users-lasto-projects-introspect-skill`

Observed volumes:

- `~/.claude`: 156M
- `~/.claude/projects`: 123M
- relevant project dir: 2.9M
- relevant JSONL files: 8
- relevant JSONL rows: 659

Observed Claude row types:

- `user`
- `assistant`
- `last-prompt`
- `queue-operation`

Relevant counts:

- user rows: 281
- assistant rows: 305
- last-prompt rows: 57
- queue-operation rows: 16

Useful Claude metadata fields:

- `sessionId`
- `cwd`
- `gitBranch`
- `permissionMode`
- `entrypoint`
- `version`
- `requestId`
- model, usage, stop reason
- content block types such as text, thinking, tool use, and tool result

Claude opportunities:

- Treat `queue-operation` and `last-prompt` rows as first-class event types.
- Add metadata-only Claude summaries.
- Normalize canonical repo paths and T3 worktree paths. Claude entries pointed at `/Users/lasto/projects/introspect-skill`, not the T3 worktree path.

## opencode

Primary store:

- `~/.local/share/opencode/opencode.db`

Related paths:

- `~/.local/share/opencode/storage/session_diff`
- `~/.local/share/opencode/snapshot`
- `~/.local/share/opencode/log`
- `~/.local/share/opencode/tool-output`

Observed volumes:

- `~/.local/share/opencode`: 127M
- `opencode.db`: 80M
- snapshot: 19M
- storage/session_diff: 10M

Important tables:

- `project`
- `session`
- `message`
- `part`
- `todo`
- `event`
- `session_entry`

Sensitive tables to avoid raw export:

- `account`
- `account_state`
- `control_account`
- `session_share`

Global counts:

- `project`: 10
- `session`: 235
- `message`: 2,608
- `part`: 11,629
- `todo`: 97
- `event`: 0
- `session_entry`: 0

Relevant `introspect-skill` opencode project:

- project id: `913143b6d79d4777fbb00b036e723a32915b1892`
- directory: `/Users/lasto/projects/introspect-skill`
- relevant sessions: 8
- relevant messages: 50
- relevant parts: 404
- relevant session diffs: 8 empty arrays

Observed part types:

- `tool`
- `text`
- `reasoning`
- `step-start`
- `step-finish`

opencode opportunities:

- Prefer structured JSON extraction from `message.data` and `part.data`.
- Tolerate empty `event` and `session_entry` tables.
- Add macOS Application Support and XDG fallback path discovery.
- Normalize canonical repo paths and T3 worktree paths.

## Cross-Store Observation

The biggest practical gap is path identity. T3 and Codex can point at ephemeral T3 worktrees, while Claude and opencode often point at the canonical project checkout. A robust resolver should treat these as related when git metadata, worktree metadata, branch names, and commit ancestry line up.

