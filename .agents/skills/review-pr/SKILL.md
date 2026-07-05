---
name: review-pr
description: |
  Review an existing GitHub pull request for the introspect-skill repo, or the current
  branch's PR when the user says "review this PR". Run bounded real reviews with
  repo-specific lenses, apply safe fixes to the PR branch, rerun validation, push, and
  provide a concise handoff. Use when the user says "review PR", "review-pr", "review
  pull request #N", or invokes this skill with a PR number. The primary input is
  ${PR_NUMBER} when provided.
---

# Review PR Skill

Review `${PR_NUMBER}` or the current branch's PR against its base branch. Improve the
PR when fixes are local, safe, and within scope.

## Operating Rules

- Resolve PR metadata first: URL, title/body, base, head, head SHA, changed files, and
  current check status when available.
- Work in the PR head branch or a safe temporary worktree for that branch.
- Review the whole PR diff against a freshly fetched base ref, not only local edits.
- Apply safe fixes, commit, and push to the PR head branch.
- Ask the user only when a finding changes user-visible behavior beyond PR intent,
  materially expands scope, requires protected context, or has multiple plausible
  fixes with different outcomes.
- Stop if the PR cannot be resolved, branch/worktree safety is ambiguous, validation
  fails and cannot be fixed, or no eligible reviewer can run after diagnosis and retry.

## Branch Safety

Before edits or pushes:

```bash
git status --short --branch
git branch -vv
```

Do not push from a non-main branch tracking `origin/main`. If a PR work branch is
tracking `origin/main`, unset the upstream and push with an explicit destination:

```bash
git branch --unset-upstream
git push -u origin HEAD:refs/heads/PR_HEAD_BRANCH
```

## Review Depth

- `light review-pr`, `single round`, or `one round`: run one full round.
- `heavy review-pr`: use the default budget and stronger available reviewers for later
  rounds.
- `N rounds` or `max N`: run at most that many rounds.
- Default: up to 3 rounds, stopping earlier when all applicable lenses are quiet.

## Build Review Context

Define:

- `BASE_REF`: freshly fetched remote base ref or exact base SHA
- `HEAD_REF`: PR head SHA at review start, refreshed after fixes
- `PR_DESCRIPTION`: title and body
- `PR_DIFF_SUMMARY`: bounded `git diff --stat`, `git diff --name-status`, and focused
  hunks for relevant files
- `TOUCHED_FILE_LIST`: PR changed files
- `CONTEXT_FILE_LIST`: touched files plus relevant docs, tests, plans, fixtures, and
  root guidance

Exclude raw protected local logs/stores, `.env`, keys, auth stores, and browser
profiles from reviewer context.

## Lens Schedule

Read `../_references/repo-lenses.md` and
`../_references/external-review-mechanics.md`.

Run review rounds in this order:

1. `correctness`
2. `harness-store` when touched paths or PR text affect session-store discovery,
   parsing, resolver/history behavior, summaries, bundles, or `references/log-sources.md`
3. `privacy-safety` when touched paths or PR text affect local stores/logs, protected
   context, bundle output, or external-review exposure
4. `package-install` when the PR affects packaging, entry points, environment setup,
   install docs, marketplace metadata, or skill-host wiring
5. `docs-skill-workflow` when the PR affects root `SKILL.md`, `.agents/skills/**`,
   agent metadata, docs that teach agent workflows, or plan/review process
6. `cli-operator-ux` when scripts, console commands, JSON output, errors, or command
   examples change
7. `KISS`

Round 1 runs every applicable lens. Later rounds rerun only active or reopened lenses.

## Synthesis And Action

For each finding, record one disposition:

- `applied`: changed code, tests, docs, or plan
- `defended`: clarified the rationale in the right place
- `rejected`: wrong, duplicate, already covered, or outside PR scope
- `deferred`: blocked by tooling, quota, validation, protected context, or human
  judgement

After applying fixes, rerun focused validation plus relevant standard checks:

```bash
mise exec -- python -m py_compile introspect_skill/*.py scripts/*.py tests/*.py evals/*.py
PYTHONPATH=$PWD mise exec -- python -m pytest
PYTHONPATH=$PWD mise exec -- python evals/run_smoke.py
```

Commit accepted fixes with concise messages and push them to the PR branch.

## PR Comment And Handoff

When the review is complete, add or prepare a concise PR comment with lenses run,
key findings, dispositions, commits, validation, and remaining risks.

Final handoff should link the PR, list review depth and rounds completed, commits
pushed, validation results, disposition totals by lens, deferred decisions, and whether
another round looks worth the cost.
