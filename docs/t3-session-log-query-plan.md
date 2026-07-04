# T3 Session Log Query Plan

## Summary

Update the `introspect` skill and package so agents can efficiently answer requests like:

```text
investigate t3 session 94676c03-5cdc-4a39-92e4-aa8d497d3a76 for churn around flightdeck
```

The implementation will treat T3 provider logs with `CANON` and `NTIVE` records as the
primary transcript source, use `state.sqlite` for resolution and metadata, and use native
Codex JSONL only as fallback or enrichment. Add deterministic slicing tools plus an
opencode/GLM sidecar summarizer.

## Implementation Prep

1. Rebase this worktree before editing:
   - `git fetch origin main`
   - `git rebase origin/main`
   - Confirm `docs/research` is present from main.
2. Use the research docs as context, but do not add extra research-doc churn beyond what
   arrives from main.
3. Keep the implementation branch focused on the skill/tooling work.

## Public Commands

Add two new entry points in `pyproject.toml`:

- `introspect-t3-session-query = "introspect_skill.cli:t3_session_query_main"`
- `introspect-t3-session-summarize = "introspect_skill.cli:t3_session_summarize_main"`

Add matching repo-local scripts:

- `scripts/t3_session_query.py`
- `scripts/t3_session_summarize.py`

Update `SKILL.md` examples to prefer installed entry points, and use
`uv run python scripts/...` for repo-local fallbacks because the project requires
Python 3.11+ and local `python3` may be 3.9.

## New Package Modules

Add `introspect_skill/t3_session.py` for deterministic parsing, normalization,
resolution, slicing, redaction, and text rendering.

Add `introspect_skill/t3_session_summarize.py` for sidecar bundle creation, opencode
invocation, JSONL validation, size checking, and retry.

Keep existing commands working; do not remove current summary/bundle APIs.

## Session Resolution

For a query/id:

1. Call existing `resolve_target(query, config)`.
2. Prefer a `t3-thread` match.
3. Locate provider logs at:
   - `~/.t3/userdata/logs/provider/<thread-id>.log`
   - any rotated siblings matching `<thread-id>.log.*`
4. Read `provider_session_runtime.resume_cursor_json` for the provider thread id, for
   example `{"threadId":"019f0ff4..."}`.
5. Enrich with `projection_threads`, `projection_thread_sessions`, and
   `provider_session_runtime`.
6. If multiple T3 thread matches are plausible, return a clear nonzero ambiguity error
   listing candidates.

Read rotated provider logs and merge records by timestamp/line metadata so long sessions
spanning rotations stay chronological.

## Provider Log Parsing

Support the new line format:

```text
[ISO_TIMESTAMP] CANON: {json}
[ISO_TIMESTAMP] NTIVE: {json}
```

Primary parsing uses `CANON` records. Use `NTIVE` only for metadata or fallback fields not
present in `CANON`.

Normalize records into turns:

- `turn.started`
- `turn.completed`
- `item.started`
- `item.updated`
- `item.completed`
- `content.delta`
- `thread.token-usage.updated`
- `turn.diff.updated`
- `request.opened`
- `request.resolved`
- `runtime.warning`
- `runtime.error`
- `account.rate-limits.updated`

Group by `turnId`, then `itemId`. Reconstruct assistant/user text and command output by
accumulating `content.delta` by `itemId` and `streamKind`.

## Query CLI

Command shape:

```bash
introspect-t3-session-query <query-or-thread-id> \
  [--phrase TEXT ...] \
  [--tool TEXT ...] \
  [--turn-id TURN_ID ...] \
  [--between START_ANCHOR END_ANCHOR] \
  [--before-turns N] \
  [--after-turns N] \
  [--format json|text|jsonl] \
  [--max-output-chars N] \
  [--max-item-chars N] \
  [--include-raw] \
  [--case-sensitive] \
  [--limit N] \
  [--config PATH]
```

Defaults:

- `--format json`
- `--before-turns 1`
- `--after-turns 1`
- tool-output bloat threshold: 3,000 chars or 50 lines
- include capped excerpts and metrics, not full raw output
- redaction enabled

Selectors:

- `--phrase`: match user prompts, assistant text, reasoning summaries, tool arguments,
  commands, and output excerpts.
- `--tool`: match tool item type, tool/function name, command text, MCP tool name, or
  command detail.
- `--turn-id`: return exact turn windows.
- `--between`: accept phrase text or turn id anchors; include both anchors and turns
  between them.

Default JSON output:

```json
{
  "schema": "introspect.t3_session.query.v1",
  "thread": {
    "thread_id": "...",
    "title": "...",
    "branch": "...",
    "worktree_path": "...",
    "provider": "codex",
    "provider_thread_id": "..."
  },
  "sources": {
    "state_db": "...",
    "provider_logs": ["..."]
  },
  "selectors": [],
  "match_stats": {},
  "matches": [],
  "slices": [
    {
      "slice_id": "slice-1",
      "anchor": {},
      "turns": []
    }
  ],
  "warnings": []
}
```

Normalized turn shape:

```json
{
  "idx": 3,
  "turn": "019f...",
  "started": "2026-...",
  "completed": "2026-...",
  "user": "short prompt text",
  "assistant": "short assistant text",
  "reasoning": "short reasoning summary if present",
  "tools": [
    {
      "id": "call_...",
      "kind": "command_execution",
      "name": "exec_command",
      "cmd": "moon run ...",
      "status": "completed",
      "exit": 0,
      "out": {
        "chars": 1234,
        "lines": 20,
        "head": "...",
        "tail": "...",
        "truncated": false,
        "bloat": false
      }
    }
  ],
  "friction": [],
  "bloat": []
}
```

Text output is for humans and should render turn boundaries, prompts, assistant messages,
tool calls, exit/status, capped output, and churn/bloat warnings.

JSONL output emits normalized turn records for sidecar or pipeline use.

## Redaction

Apply conservative obvious-secret redaction before stdout and before opencode:

- bearer/API tokens
- `*_TOKEN=...`, `*_SECRET=...`, `*_KEY=...`, `PASSWORD=...`
- long high-entropy credential-like strings
- protected-store paths called out by the existing skill rules

Keep ordinary prompts, tool names, file paths, commands, and non-secret output.

## Sidecar Summarizer CLI

Command shape:

```bash
introspect-t3-session-summarize <query-or-thread-id> \
  [--focus TEXT ...] \
  [--diagnose-churn] \
  [--diagnostic-mode evidence|broad] \
  [--layout turn|phase] \
  [--model MODEL] \
  [--output PATH] \
  [--prepare-only] \
  [--config PATH]
```

Defaults:

- model: `zai-coding-plan/glm-5.2`
- layout: `turn`
- diagnostic mode: `evidence`
- auto-run opencode
- stdout: JSONL only
- status/progress: stderr
- soft size cap: summary should be no larger than 1/5 estimated tokens of normalized
  session input
- one compression retry if summary exceeds cap

If opencode or `zai-coding-plan/glm-5.2` is unavailable, fail clearly and suggest
`--model`; do not silently fall back.

## Summarizer Data Flow

1. Resolve the T3 session.
2. Build normalized turn JSONL from `CANON` provider-log records.
3. Create a temporary bundle containing:
   - `normalized_turns.jsonl`
   - `session_meta.json`
   - `summary_glossary.md` or `.json`
   - `prompt.md`
   - optional capped raw excerpts for clarification
4. Invoke:

```bash
opencode run -m zai-coding-plan/glm-5.2 --dir <bundle-dir> --file normalized_turns.jsonl --file session_meta.json --file summary_glossary.md "<prompt>"
```

5. Validate returned JSONL.
6. If over the 1/5 size cap, retry once with a compression prompt.
7. Print final JSONL to stdout and optionally write to `--output`.

For large sessions, automatically chunk normalized turns by estimated token budget,
summarize each chunk, then consolidate. `--layout phase` can emit chunk/phase rows for
first-pass inspection of very large sessions.

## Summary JSONL Layout

Default layout emits:

- one `meta` row
- one `turn` row per user/assistant turn
- optional `finding` rows for cross-turn churn, missing-tool expectations, retries, or
  bloat opportunities

Example:

```jsonl
{"kind":"meta","thread":"94676c03...","title":"PR-118: Launch Flightdeck QA","focus":["flightdeck"],"ratio":0.16,"cap_met":true}
{"kind":"turn","idx":3,"turn":"019f...","user":"continue","act":"fd prepare/browser handoff","tools":["exec:fd-plan","exec:fd-prepare"],"friction":[],"bloat":[]}
{"kind":"finding","cat":"tool-friction","sev":"med","turns":[7,8],"evidence":"agent expected node_repl js execution but available surface differed; switched to local node one-shot"}
```

## Glossary

Create a short readable glossary for JSONL keys and common enum values. Use compact but
human-readable keys, not single-letter codes.

Suggested keys:

- `kind`: `meta`, `turn`, `finding`
- `idx`: numeric turn index
- `turn`: turn id
- `user`: terse user ask
- `act`: terse assistant action summary
- `tools`: terse tool list, e.g. `exec:mix precommit`, `mcp:preview_snapshot`
- `friction`: retry/missing-tool/failed-result notes
- `bloat`: verbose output/context growth notes
- `cat`: finding category
- `sev`: `low`, `med`, `high`
- `evidence`: short pointer to turn/tool/result
- `ratio`: estimated summary/input token ratio
- `cap_met`: boolean

Common `cat` values:

- `retry`
- `tool-friction`
- `missing-tool`
- `bad-assumption`
- `verbose-output`
- `context-growth`
- `env-confusion`
- `workflow-churn`

## Churn Definition

Default `--diagnose-churn` flags:

- failed or unsatisfactory tool results followed by alternate attempts
- missing-tool or tool-discovery friction
- repeated exploratory reads/searches that indicate the agent could not find what it
  needed
- verbose outputs that inflated context
- environment or state confusion that caused retries

Evidence-tied inference is the default. `--diagnostic-mode broad` permits more
interpretive summaries for comparison.

## Skill Updates

Update `SKILL.md` to add a new "T3 Session Log Querying" workflow:

1. Resolve target with `introspect-resolve-target`.
2. For narrow inspection, run `introspect-t3-session-query`.
3. For requests like "investigate session X for churn around Y", run:

```bash
introspect-t3-session-summarize "<id>" --focus "Y" --diagnose-churn
```

4. Use query follow-ups for exact slices:

```bash
introspect-t3-session-query "<id>" --phrase "Flightdeck.Repo" --format text
```

Update repo-local fallback examples to use `uv run python`.

Update `agents/openai.yaml` only if the skill metadata becomes stale after `SKILL.md`
edits.

## Tests

Add synthetic tests covering:

- parsing `CANON` and `NTIVE` lines
- rotated log ordering
- turn reconstruction from `content.delta`
- user/assistant/tool item extraction
- command output capping
- aggressive bloat thresholds: over 3k chars or 50 lines
- phrase matching
- tool matching
- `--between` anchors
- JSON output schema
- text output mode
- JSONL normalized turn output
- redaction of obvious secrets
- ambiguous resolution errors
- missing opencode/model errors

Add a tiny redacted real-shape fixture derived from the example T3 session to catch drift
in `CANON` and `NTIVE` structure without private content.

Add summarizer tests with `subprocess.run` monkeypatch/fake opencode:

- prints valid JSONL to stdout
- writes `--output`
- fails clearly when opencode is unavailable
- retries once when summary exceeds size cap
- chunks large normalized input
- validates/salvages JSONL lines and fails if no valid rows remain

Run:

```bash
uv run pytest
```

Optionally run a live smoke after implementation:

```bash
uv run python scripts/t3_session_query.py 94676c03-5cdc-4a39-92e4-aa8d497d3a76 --phrase flightdeck --format json
uv run python scripts/t3_session_summarize.py 94676c03-5cdc-4a39-92e4-aa8d497d3a76 --focus flightdeck --diagnose-churn
```

## Acceptance Criteria

- The example T3 thread resolves through `provider_session_runtime.resume_cursor_json`
  even when `projection_thread_sessions.provider_session_id` is null.
- Agents can query by phrase/tool/turn/range without loading the full provider log into
  context.
- Human-readable text mode is available.
- The summarizer uses opencode with `zai-coding-plan/glm-5.2` by default and returns
  JSONL.
- Summary JSONL includes turn summaries, tool calls, churn/friction, missing-tool
  expectations, and bloat opportunities.
- Summary size is checked against the 1/5 rule and retried once if too large.
- The skill instructions guide agents to use summarization first for broad focus/churn
  investigations and query slices for follow-up.
