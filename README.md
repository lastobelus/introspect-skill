# introspect-skill

`introspect-skill` is a publishable skill and script bundle for investigating agent-session state across T3Code and adjacent harnesses.

Today it is intentionally **T3Code-first**, not fully harness agnostic. The primary target user is someone whose main harness is T3Code, but who also sometimes uses Codex, Claude, or opencode directly. The repository includes:

- a skill entrypoint in [SKILL.md](SKILL.md)
- helper scripts under [scripts/](scripts/)
- shared Python logic under [introspect_skill/](introspect_skill/)
- tests under [tests/](tests/)
- fixture-style smoke evals under [evals/](evals/)
- installable console entry points for the main read-only workflows

Pull requests are welcome for:

- additional harness and session-store backends
- making the core discovery flow less T3Code-specific
- better installers for Codex, Claude, opencode, and other marketplaces

See [CONTRIBUTING.md](CONTRIBUTING.md) for the preferred workflow when adding a new harness backend, session-store mapping, or installer behavior.

## What It Does

The skill is meant for thread and session forensics, not general code debugging.

Typical uses:

- inspect the current thread's session state
- map a thread ID, provider session ID, or log path back to the originating thread
- explain what another thread did
- continue another thread's work from its logs
- audit review-agent behavior
- mine prior introspection requests and dedupe T3-backed native session duplicates

## Current Harness Support

Supported today:

- T3Code durable state via `state.sqlite` and provider logs
- Claude native session JSONL files
- Codex session indexes and native session logs
- opencode session metadata via `opencode.db`, session-diff files, and `opencode session list`

Important limitation:

- the current matching and dedupe logic assumes T3Code is the canonical harness when the same ask appears in both T3Code and the backing Codex or Claude session logs

## Format Compatibility

This repo parses upstream session stores that are not fully stable public APIs. It is
tested against the current on-disk shapes used by T3Code, Codex, Claude, and opencode,
but those harnesses can change their SQLite schemas, JSONL event shapes, or CLI output
formats over time.

Practical implications:

- treat the current source-path and parser behavior as version-sensitive
- prefer opening an issue or PR when an upstream format change breaks a parser
- add or update a fixture before changing parser logic so the new shape is captured in-repo
- do not assume support for every forked harness layout just because the upstream tool has a similar name

## Configuration

The public version adds a real config layer so users can search more than one T3Code session root.

Default behavior:

- auto-discovers `~/.t3` and sibling roots matching `~/.t3*` when they contain `userdata/state.sqlite`
- auto-discovers standard Claude, Codex, and opencode session stores
- lets `config.toml` replace the default roots for a store family
- lets environment variables add extra roots on top of that config

Default config path:

- `~/.config/introspect-skill/config.toml`

Optional override:

- `INTROSPECT_SKILL_CONFIG=/path/to/config.toml`
- `INTROSPECT_T3_ROOTS=/extra/t3/root:/another/t3/root`
- `INTROSPECT_ENABLED_HARNESSES=t3:claude:codex:opencode`

If `enabled_harnesses` is omitted or empty, all supported harnesses are enabled.

Example:

```toml
enabled_harnesses = ["t3", "claude", "codex", "opencode"]

t3_roots = [
  "~/.t3",
  "~/.t3-experimental",
  "~/Library/Application Support/my-t3-fork",
]

claude_project_roots = ["~/.claude/projects"]
codex_session_indexes = ["~/.codex/session_index.jsonl"]
codex_session_roots = ["~/.codex/sessions"]
opencode_databases = ["~/.local/share/opencode/opencode.db"]
opencode_session_diff_roots = ["~/.local/share/opencode/storage/session_diff"]
```

More detail is in [docs/configuration.md](docs/configuration.md).

## Usage

Install the repo's pinned Python first:

```bash
mise install
```

### Repo-local checkout

Use this when you cloned the repo and want to run the bundled scripts directly:

```bash
python3 scripts/resolve_target.py "<query-or-id>"
python3 scripts/thread_sqlite.py "<thread-id>"
python3 scripts/collect_introspection_requests.py
```

### Installed Python entrypoints

Use this when you want the `introspect-*` commands on your shell path:

```bash
python3 -m pip install '.[test]'
introspect-resolve-target "<query-or-id>"
introspect-thread-context "<thread-id>"
introspect-collect-history
introspect-provider-log-summary ~/.t3/userdata/logs/provider/<id>.log
introspect-claude-jsonl-summary ~/.claude/projects/.../<session>.jsonl
introspect-build-bundle --query "<query-or-id>"
```

`pip install` gives you the `introspect-*` commands. It does not install the root
`SKILL.md`, `references/`, or marketplace metadata into a harness-specific skill
directory. Skill hosts should point at the repo checkout until a dedicated installer lands.

If you use a non-default config:

```bash
python3 "$SKILL_ROOT/scripts/collect_introspection_requests.py" \
  --config ~/.config/introspect-skill/config.toml \
  --term "~/.t3" \
  --term "session" \
  --term "thread"
```

## Repo Layout

- [SKILL.md](SKILL.md): marketplace-facing skill instructions
- [references/log-sources.md](references/log-sources.md): store map and dedupe policy
- [scripts/](scripts/): CLI entrypoints
- [introspect_skill/](introspect_skill/): shared logic and config loading
- [tests/](tests/): unit tests with synthetic fixture stores
- [evals/](evals/): smoke-eval runner and scenarios
- [docs/install-script-plan.md](docs/install-script-plan.md): plan for the global installer TUI

## Tests And Evals

Run the unit tests:

```bash
mise install
mise exec -- python -m pip install '.[test]'
PYTHONPATH=$PWD mise exec -- python -m pytest
```

Run the fixture smoke eval:

```bash
mise install
mise exec -- python -m pip install '.[test]'
PYTHONPATH=$PWD mise exec -- python evals/run_smoke.py
```

## Installation

The portable global installer is planned but not implemented yet. The current install plan is documented in [docs/install-script-plan.md](docs/install-script-plan.md).

For now, there are two separate install surfaces:

- Python/CLI install: `python3 -m pip install '.[test]'` for the `introspect-*` entrypoints
- Skill-host install: keep the repo checkout available and point the host at the root `SKILL.md`

The repo is designed so a future installer can copy the repository root as a skill bundle and wire `SKILL.md`, `scripts/`, and `references/` into Codex, Claude, or opencode-specific skill locations.

Minimal manual install today:

- Codex/OpenAI-style skills: keep the repo checkout available and point your harness at the root `SKILL.md`.
- Claude-style skills: copy or symlink the repo checkout into your Claude skills location, then invoke the root `SKILL.md`.
- opencode-style skills: install the repo as a local skill bundle and call the root `SKILL.md` plus the installed `introspect-*` commands.

The exact target directory varies by harness fork, which is why this repo does not hard-code a single global path yet. The planned installer exists to automate that wiring, verify the result, and let the user choose which detected session stores to include.

## Marketplace Readiness

This repo is intended to become publishable to skill marketplaces later, so it already includes:

- a root `SKILL.md`
- public OSS docs
- a permissive license
- tests and evals
- configurable search roots instead of hard-coded personal paths

What still needs follow-up:

- a polished global installer
- any marketplace-specific metadata beyond `agents/openai.yaml`
- support for non-T3-first harness combinations
