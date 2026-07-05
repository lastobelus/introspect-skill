---
name: implement-plan
description: |
  Implement a reviewed plan file end-to-end for the introspect-skill repo: code the
  plan, validate Python package/script behavior, run bounded real implementation
  reviews with repo-specific lenses, update docs and plan state, and prepare a concise
  handoff. Use when the user says "implement plan", "implement-plan", "ship the plan
  at a path", "build the plan", or invokes this skill on a plan file. The primary
  input is ${PLAN_FILE}.
---

# Implement Plan Skill

Implement `${PLAN_FILE}` with minimal user interaction. Continue through
implementation, validation, review, cleanup, and handoff unless a real blocker appears.

## Stop Only For Real Blockers

- The active branch or PR worktree is ambiguous.
- Rebase or checkout conflicts cannot be resolved safely.
- Validation fails and you cannot fix it.
- No eligible external reviewer can run after diagnosis and one retry.
- A finding requires product/user judgement or would materially expand plan scope.
- Protected local context is required but cannot be safely summarized.

Dirty unrelated files are reportable, not blocking.

## Review Depth

- `light implement-plan`, `single round`, or `one round`: run exactly one review round.
- `heavy implement-plan`: use the default round budget and stronger available reviewers
  for later rounds.
- `N rounds` or `max N`: run at most that many rounds.
- Default: up to 3 rounds, stopping earlier when all lenses are quiet.

Never silently exceed the configured depth.

## Start Conditions

1. Resolve the plan path and read it fully.
2. Read repo guidance: `CONTRIBUTING.md`, root `SKILL.md`, and any docs named by the
   plan.
3. Use `references/source-of-truth-guard.md` when prior plans, research notes, or
   exploratory docs exist near the plan.
4. Resolve current branch/PR when applicable. Fetch the base before substantial work.
5. Before any push, verify branch safety with `git status --short --branch` and
   `git branch -vv`. Do not push from a non-main branch tracking `origin/main`.

## Implementation Rules

- Keep scope anchored to the plan.
- Do not add compatibility layers during pre-MVP work unless the plan or user requires
  them.
- Keep shared logic in `introspect_skill/`; keep `scripts/` as thin entry points.
- Prefer structured parsing for SQLite, JSONL, TOML, timestamps, and paths.
- Keep searches bounded. Do not make repo code scan all of `~` by default.
- Use synthetic fixtures in tests instead of reading real user session stores.
- Update `README.md`, `SKILL.md`, `CONTRIBUTING.md`, `references/log-sources.md`, and
  `docs/install-script-plan.md` together when the change affects their shared contract.

## Validation

Run focused tests as you work, then the standard checks before review and handoff:

```bash
mise exec -- python -m py_compile introspect_skill/*.py scripts/*.py tests/*.py evals/*.py
PYTHONPATH=$PWD mise exec -- python -m pytest
PYTHONPATH=$PWD mise exec -- python evals/run_smoke.py
```

If setup is missing, run:

```bash
mise install
mise exec -- python -m pip install -e '.[test]'
```

If `mise` is unavailable, use the equivalent active Python environment and record that
substitution.

## Review Orchestration

Before review:

- push the branch if a PR exists or the user expects PR review
- build a focused context list from the plan, touched files, relevant docs, tests, and
  validation summary
- exclude raw protected local logs and stores; provide sanitized summaries only

Use `references/review-orchestration.md` for lens applicability, order, quiet/reopen
rules, and validation after fixes. Use real external reviews through
`../_references/external-review-mechanics.md`.

## Cleanup

After review fixes, do one explicit cleanup pass for duplication, names, error
handling, docs drift, and unnecessary abstractions. Record meaningful follow-ups in the
plan rather than expanding the implementation.

## Done Means

- plan scope is implemented or the plan is updated for an explicit scope correction
- tests, compile check, and smoke eval are clean or documented with a real blocker
- applicable real review rounds completed or a reviewer blocker is reported
- review findings are applied, defended, rejected, or deferred with reasons
- docs and plan state match the implementation
- branch/PR is pushed when applicable
- final handoff follows `references/handoff.md`
