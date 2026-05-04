# Research Index

Research date: 2026-05-04.

This directory surveys adjacent tools, skills, session-store realities, and iteration ideas for `introspect-skill`.

## Reports

- [Approach Matrix](approach-matrix.md): comparison of local session viewers, agent observability platforms, evaluation tools, coding-agent harnesses, and skills.
- [Valuable Goals Not Currently Addressed](valuable-goals-not-addressed.md): related goals other tools cover that `introspect-skill` does not yet target.
- [Local Session Store Findings](local-session-store-findings.md): read-only findings from local T3, Codex, Claude, and opencode stores, with private message content intentionally excluded.
- [Recommendations And Experiments](recommendations-and-experiments.md): prioritized experiments and project improvements to consider.
- [Adoption Snapshot](adoption-snapshot.md): GitHub adoption metrics and source-method notes used by the matrix.

## Current Repo Positioning

`introspect-skill` is best described as a local-first forensic resolver for agent sessions:

- identify a T3 thread, native provider session, log path, or fuzzy title
- reconstruct enough context to continue or audit prior work
- map T3 canonical records to backing Claude, Codex, and opencode artifacts
- dedupe repeated native/T3 copies of the same ask
- stay lightweight, read-only, and installable as both a skill and script bundle

Most adjacent projects optimize for one of three different centers of gravity:

- observability platforms for instrumented LLM apps
- visual replay or productivity analytics for a single coding agent's logs
- agent harnesses that own the execution environment

The opportunity for this repo is to remain narrower than those platforms while becoming much stronger at cross-harness local identity resolution, redacted structural audits, and portable session bundles.

