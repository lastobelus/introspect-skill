# Configuration

`introspect-skill` searches a set of known session stores. The public repo version keeps those locations configurable because local layouts vary and T3Code users may run multiple forks with different data roots.

## Config File

Default config path:

- `~/.config/introspect-skill/config.toml`

Override with:

- `INTROSPECT_SKILL_CONFIG=/path/to/config.toml`

## Supported Keys

Top-level keys:

- `enabled_harnesses`
- `t3_roots`
- `claude_project_roots`
- `codex_session_indexes`
- `codex_session_roots`
- `opencode_databases`
- `opencode_session_diff_roots`

All path values may use `~`.

## Example

```toml
enabled_harnesses = ["t3", "claude", "codex", "opencode"]

t3_roots = [
  "~/.t3",
  "~/.t3-dev",
  "~/Library/Application Support/t3code-fork",
]

claude_project_roots = ["~/.claude/projects"]
codex_session_indexes = ["~/.codex/session_index.jsonl"]
codex_session_roots = ["~/.codex/sessions"]
opencode_databases = ["~/.local/share/opencode/opencode.db"]
opencode_session_diff_roots = ["~/.local/share/opencode/storage/session_diff"]
```

## Environment Variables

The config loader also reads:

- `INTROSPECT_T3_ROOTS`
- `INTROSPECT_ENABLED_HARNESSES`

These accept a path-separated list using the local platform separator, for example `:` on macOS and Linux.

If `enabled_harnesses` is omitted or empty, all supported harnesses are enabled.

## Auto-Discovery

When no explicit config is provided, the loader:

- searches `~/.t3` and sibling directories matching `~/.t3*` for `userdata/state.sqlite`
- checks `~/.claude/projects`
- checks `~/.codex/session_index.jsonl` and `~/.codex/sessions`
- checks `~/.local/share/opencode/opencode.db` and the session-diff directory

When a store-family key is present in `config.toml`, it replaces that family's default roots. Environment-variable path lists remain additive and extend the configured roots. This keeps the zero-config path useful while still letting users pin a deterministic store set for an installed skill.
