# Recommendations And Experiments

Research date: 2026-05-04.

## Near-Term Recommendations

### 1. Add Metadata-Only Mode

Add a privacy-preserving mode across T3, Claude, Codex, and opencode commands.

Output should include:

- ids
- paths
- timestamps
- branch/worktree/git metadata
- event counts
- tool names and statuses
- token/cost counters when available
- source files

Output should omit:

- prompt text
- assistant body text
- tool result bodies
- file contents
- screenshots or attachment contents

This directly supports safe research, review handoffs, and external sidecar analysis.

### 2. Make Codex SQLite A First-Class Source

Current defaults emphasize `session_index.jsonl` and session JSONL. Local findings show `~/.codex/state_5.sqlite` is a much richer thread index.

Experiment:

- add optional config keys for `codex_state_databases` and `codex_log_databases`
- query `threads` first for cwd/git/session lookup
- use `thread_spawn_edges` for subagent graphs
- use `logs_2.sqlite` for diagnostics and lifecycle timing

Success criteria:

- faster Codex lookup by cwd, branch, and session id
- resolver can identify parent/subagent relationships
- no raw message content needed for basic diagnostics

### 3. Add Archived Codex Sessions

Add `~/.codex/archived_sessions` to default discovery.

Success criteria:

- `resolve_target` can find archived sessions by id/title/path
- history collection does not double-count active and archived copies

### 4. Normalize Project Identity Across Worktrees

Build a path identity layer that maps:

- canonical checkout path
- T3 worktree path
- Codex app worktree path
- git common dir
- branch
- commit
- origin URL

Success criteria:

- Claude/opencode sessions under `/Users/lasto/projects/introspect-skill` can be related to T3/Codex worktree sessions under `/Users/lasto/.t3/worktrees/introspect-skill/...`
- lookup by any path returns grouped related sessions, not isolated hits

### 5. Treat Claude Queue And Last-Prompt Rows Explicitly

Claude local logs include `queue-operation` and `last-prompt` rows. They should be parsed as event types rather than incidental JSONL rows.

Success criteria:

- summaries show queue enqueue/dequeue counts
- prompt-history rows can be included or excluded by mode
- metadata-only mode can summarize queue behavior without prompt text

### 6. Prefer Structured opencode JSON Extraction

The opencode store has structured `message.data` and `part.data` JSON. Avoid broad text searches where structured queries are available.

Success criteria:

- session summaries include model/provider/tokens/cost/finish/time
- part summaries include tool, call id, state, and step boundaries
- account/auth tables are never touched by default

## Medium-Term Experiments

### 7. Session Graph Command

Prototype:

```bash
introspect-session-graph "<query-or-id>" --format text
introspect-session-graph "<query-or-id>" --format mermaid
introspect-session-graph "<query-or-id>" --format json
```

Nodes:

- T3 thread
- provider runtime session
- Codex session
- Claude session
- opencode session
- subagent session
- worktree
- branch/commit
- provider log

Edges:

- backed_by
- spawned
- same_worktree
- same_git_origin
- same_branch
- same_prompt_hash
- wrote_artifact

### 8. Redacted Portable Bundle

Extend `introspect-build-bundle` with a redacted mode:

```bash
introspect-build-bundle --query "<query>" --redact metadata --format json
introspect-build-bundle --query "<query>" --redact standard --format markdown
```

Redaction levels:

- `metadata`: no message bodies
- `standard`: short excerpts with path and secret redaction
- `full-local`: current behavior for trusted local use only

### 9. Adapter Drift Check

Add a command that checks whether current local store schemas still match expected fixtures:

```bash
introspect-check-stores
```

It should report:

- found/missing stores
- table/schema shape changes
- unknown JSONL event types
- adapter warnings
- suggested fixture updates

### 10. Lightweight Analytics Without Dashboard Ownership

Add a report command that emits markdown or JSON:

```bash
introspect-usage-summary --since 7d --metadata-only
```

Metrics:

- sessions by harness
- turns/messages/tool calls
- models used
- token/cost counters when exposed by stores
- failure/approval counts
- top projects and worktrees

Keep this as a CLI report, not a web dashboard.

### 11. OpenTelemetry-Inspired Export

Define an internal normalized event schema and optionally export it:

```bash
introspect-export "<query>" --format normalized-jsonl
```

Do not start with live OTLP export. First prove a stable local JSONL model.

## Lower-Priority Ideas

### 12. Viewer Integration Instead Of Viewer Ownership

Rather than building a full UI, generate files compatible with existing viewers:

- self-contained HTML via `claude-replay`-style timeline
- markdown reports for PRs
- JSON graph for custom viewers
- links/commands to open native tools when installed

### 13. Skill/Plugin Inventory

Add an optional command:

```bash
introspect-capabilities --session "<id>"
```

Report available skills, plugins, MCP servers, hooks, and app tools when they are discoverable from local metadata.

### 14. Session-Derived Lessons

Generate structured lessons from prior sessions:

- repeated failed commands
- repeated file rediscovery
- missing environment setup
- recurring approval blocks
- high-cost session shapes

Keep this behind an explicit command because it is more interpretive than forensic.

## Suggested Iteration Order

1. Metadata-only summaries.
2. Codex SQLite adapter.
3. Path identity normalization.
4. Archived Codex sessions.
5. Claude queue/last-prompt parsing.
6. opencode structured extraction cleanup.
7. Session graph.
8. Redacted bundle.
9. Store drift checker.
10. Lightweight usage summary.

This sequence strengthens the core forensic resolver before expanding into analytics or export features.

