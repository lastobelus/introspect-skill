# Introspect-Skill Review Lenses

Use these lenses for plan, implementation, and PR review in this repository.

## correctness

Check behavior against the requested scope, public CLI contracts, parser edge cases,
dedupe behavior, config precedence, timestamps, path expansion, and failure modes.
Prefer fixture-backed evidence over assumptions about a real local home directory.

## harness-store

Use when code or docs touch T3Code, Claude, Codex, or opencode session discovery,
SQLite/JSONL parsing, provider-log summaries, resolver matching, or canonicalization.
Check upstream-store version sensitivity, malformed or missing metadata, duplicate
records across roots, cwd/session-id matching, and bounded reads.

## privacy-safety

Use when work touches local session stores, logs, bundle creation, external reviewers,
or paths under real home directories. Check that raw auth stores, `.env` files, keys,
browser profiles, local tool state, and full unbounded logs are not exposed to external
reviewers or committed artifacts. Prefer sanitized excerpts and synthetic fixtures.

## package-install

Use when work touches `pyproject.toml`, console scripts, `.codex/environments`, install
docs, marketplace or skill-host wiring, or packaging behavior. Check entry point names,
editable install behavior, package data, Python version assumptions, and README/SKILL
alignment.

## docs-skill-workflow

Use when work changes `SKILL.md`, `.agents/skills/**`, `agents/openai.yaml`, docs that
teach agent behavior, plan files, installer guidance, or workflow scripts. Check trigger
precision, progressive disclosure, source-of-truth clarity, validation instructions,
and whether README, CONTRIBUTING, SKILL, references, and plans stay synchronized.

## cli-operator-ux

Use when work affects scripts or console entry points. Check argument names, error
messages, JSON output stability, stderr/stdout separation, nonzero exits, config flag
behavior, and whether commands in docs are copyable.

## KISS

Check whether the work adds avoidable compatibility layers, broad abstractions,
unbounded scans, brittle string parsing where structured parsing exists, duplicate
logic between scripts and package modules, or docs churn not needed for the change.
