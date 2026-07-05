---
name: review-plan
description: |
  Review an introspect-skill plan file with bounded real external reviewers and
  repo-specific lenses before implementation. Use when the user says "review plan",
  "review-plan", "review the plan at a path", or invokes this skill on a plan file.
  The primary input is ${PLAN_FILE}.
---

# Review Plan Skill

Review `${PLAN_FILE}` with real reviewers. Update the plan until it is coherent,
implementable, and validated for this repository.

## Stop Only For Real Blockers

- No eligible external reviewer can run after diagnosis and one retry.
- The configured review depth is exhausted while material plan changes are still being
  made.
- A source-of-truth conflict requires user judgement.
- Protected local context is required but cannot be safely summarized.

Do not stop between rounds just because one reviewer completed.

## Review Depth

- `light review-plan`, `single round`, or `one round`: run one full cycle.
- `heavy review-plan`: use the default budget and stronger available reviewers for
  later cycles.
- `N rounds` or `max N`: run at most that many full cycles.
- Default: up to 3 cycles, stopping earlier when all applicable lenses are quiet.

## Pre-Round Preparation

1. Read the plan fully.
2. Run `references/context-hygiene.md` when exploratory docs, prior plans, research
   notes, or old explanations may be nearby.
3. Build a focused context file list. Include the plan, directly relevant code/tests,
   `CONTRIBUTING.md`, root `SKILL.md`, and specific docs the plan changes or depends
   on.
4. Exclude raw local session stores, provider logs, native session logs, `.env`, auth,
   key, or browser-profile files. Use sanitized excerpts or synthetic fixtures.
5. Read `../_references/repo-lenses.md` and
   `../_references/external-review-mechanics.md`.

## Lens Applicability

Always run:

- `correctness`
- `KISS`

Run conditionally:

- `harness-store`: session-store discovery, parser, resolver, history, bundle, summary,
  or `references/log-sources.md` changes
- `privacy-safety`: real local logs/stores, protected context, bundle output, external
  reviewer context, or home-directory path behavior
- `package-install`: packaging, entry points, environment setup, install docs,
  marketplace metadata, or skill-host wiring
- `docs-skill-workflow`: root `SKILL.md`, `.agents/skills/**`, agent metadata, workflow
  docs, or plan/review process changes
- `cli-operator-ux`: scripts, console commands, JSON output, error messages, or command
  examples

## Cycle Order

1. `correctness`
2. `harness-store` when applicable
3. `privacy-safety` when applicable
4. `package-install` when applicable
5. `docs-skill-workflow` when applicable
6. `cli-operator-ux` when applicable
7. `KISS`

Cycle 1 covers every applicable lens. Later cycles skip quiet lenses unless a material
plan change reopens them.

## Per-Review Rules

- Invoke the reviewer on the current plan from scratch.
- Do not ask reviewers to compare previous rounds.
- Ask for findings first, ordered by severity.
- For cycle 1, cap each lens at 10 findings, except `correctness` at 12.
- For later cycles, cap each lens at 8 findings, except `correctness` at 10.
- Normalize every finding in the main session with one disposition: `applied`,
  `defended`, `rejected`, or `deferred`.
- Apply useful findings to the plan. If rejecting or defending a finding, make the
  plan's rationale concrete enough that future implementers do not re-litigate it.
- Mark a lens quiet when it has no real findings or only trivial wording changes.
- Reopen quiet lenses when another lens causes a material plan change.

## Plan Quality Bar

A reviewed plan should specify:

- source of truth and relevant context
- exact touched areas or discovery strategy
- expected behavior and non-goals
- validation commands, including targeted tests, compile check, pytest, and smoke eval
- fixture strategy for parser/session-store changes
- protected-context handling when real logs or stores are involved
- docs that must be kept aligned
- acceptance checklist

## Final Handoff

Report what changed, cycles completed, lenses run/skipped, disposition totals, final
quiet/open state, residual risks, and whether the plan is ready for `implement-plan`.
Do not end with a magic-phrase prompt.
