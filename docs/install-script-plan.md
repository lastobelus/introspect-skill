# Global Install Script Plan

This repo is not shipping the global installer yet, but this is the concrete plan for it.

## Goal

Install `introspect-skill` into one or more harnesses from a single command, while letting the user choose which session stores the installed skill should search.

## Target Entry Point

Proposed command:

```bash
python3 install.py
```

## Installer Responsibilities

1. Detect candidate harness installs already present on the machine.
2. Show a small TUI to select which harnesses should receive the skill.
3. Show a second TUI for which session-store families should be enabled in the installed config.
4. Generate or merge a config file with the selected roots.
5. Copy or symlink the skill bundle into each harness-specific skill location.

## Autodiscovery Rules

Initial detection targets:

- T3Code roots: existing directories matching `~/.t3*` with `userdata/state.sqlite`
- Claude: `~/.claude/projects`
- Codex: `~/.codex/session_index.jsonl` and `~/.codex/sessions`
- opencode: `~/.local/share/opencode/opencode.db`

The installer should also inspect any user-provided extra roots before rendering the final selection list.

## TUI Flow

Screen 1:

- detected harness installs
- checkboxes for `Codex`, `Claude`, `opencode`
- optional `just generate config` mode

Screen 2:

- detected session-store groups
- per-store enable/disable toggles
- editable list for extra T3 roots so multiple forks can be added before writing config

Screen 3:

- preview of files to write
- preview of the generated `config.toml`
- confirmation

## File Outputs

The installer should write:

- the skill bundle into the selected harness skill directories
- `~/.config/introspect-skill/config.toml`

It should avoid destructive overwrites and prefer:

- merging known config keys
- timestamped backups when a target file already exists

## Implementation Constraints

- stdlib-first if practical
- text UI should work in a normal terminal
- path resolution must be deterministic and testable
- installation logic should be dry-run capable

## Verification

When the installer lands, it should ship with:

- unit tests for autodiscovery and config generation
- fixture-based install tests in temp directories
- a smoke test that installs into synthetic Codex and Claude skill roots

