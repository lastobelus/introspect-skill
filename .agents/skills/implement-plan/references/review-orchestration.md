# Implement-Plan Review Orchestration

Use real reviews only. Do not simulate reviewer output. Read
`../../_references/external-review-mechanics.md` and
`../../_references/repo-lenses.md` before starting external review rounds.

## Applicability

Always run `correctness` and `KISS`.

Run `harness-store` when touched files or plan scope affect `introspect_skill/`
resolver/history/config/sql/parser modules, provider-log or native-session summary
logic, scripts that read session stores, `references/log-sources.md`, or fixture data.

Run `privacy-safety` when work touches local path discovery, session/log reading,
bundle creation, external review context, config paths, or docs that instruct users to
inspect real home-directory stores.

Run `package-install` when work touches `pyproject.toml`, `.codex/environments`,
console scripts, packaging, install docs, marketplace metadata, or the root `SKILL.md`
install instructions.

Run `docs-skill-workflow` when work touches `SKILL.md`, `.agents/skills/**`,
`agents/openai.yaml`, docs that teach agents how to use the repo, or plan/review
workflow behavior.

Run `cli-operator-ux` when work touches `scripts/**`, console entry points, JSON CLI
output, error messages, usage docs, or evals that exercise operator workflows.

## Round Order

For each configured review round, use this order and skip inapplicable or quiet lenses:

1. `correctness`
2. `harness-store`
3. `privacy-safety`
4. `package-install`
5. `docs-skill-workflow`
6. `cli-operator-ux`
7. `KISS`

Round 1 runs every applicable lens. Later rounds rerun only lenses that remain active
or were reopened by material fixes.

## Quiet And Reopen Rules

A lens becomes quiet when it has no real findings or only trivial edits that do not
change behavior, validation, docs contracts, or scope. Reopen a quiet lens only when a
later fix materially affects that concern area.

Record one disposition per finding: `applied`, `defended`, `rejected`, or `deferred`.
Use `deferred` only for tooling, quota, protected context, validation blockers, or
required human judgement.

## Validation After Review Fixes

After material edits from review findings, rerun focused tests plus the relevant
standard checks:

```bash
mise exec -- python -m py_compile introspect_skill/*.py scripts/*.py tests/*.py evals/*.py
PYTHONPATH=$PWD mise exec -- python -m pytest
PYTHONPATH=$PWD mise exec -- python evals/run_smoke.py
```

If `mise` is unavailable, use the same Python commands directly after installing
`.[test]`. Document any skipped command and why.
