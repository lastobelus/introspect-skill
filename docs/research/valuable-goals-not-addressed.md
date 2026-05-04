# Valuable Goals Not Currently Addressed

Research date: 2026-05-04.

This repo is intentionally focused on local session forensics. The goals below are valuable and adjacent, but are not currently first-class targets.

## 1. Usage, Cost, And Productivity Analytics

Other tools compute:

- token and cost totals by day, model, project, or session
- activity heatmaps
- tool-call frequency and failure rates
- context-window pressure
- productivity or standup summaries
- redundant file-read patterns

Why it matters: once users run many sessions across Claude, Codex, T3, and opencode, the next question after "what happened?" is "what patterns are costing me time or tokens?"

Possible scope for this repo: add metadata-only aggregate commands without turning the project into a dashboard.

## 2. Live Cross-Session Monitoring

Dashboards such as Claude-Code-Agent-Monitor, Claude Code Dashboard, and Claude Code Trace watch active sessions and show:

- active/idle status
- current tool call
- token/cost counters
- active branch and files
- subagent status
- recent events

Why it matters: forensic tooling is reactive. Live status helps avoid duplicated work, port conflicts, and lost agent sessions.

Possible scope for this repo: a read-only `watch` command that tails known local stores and prints normalized event summaries.

## 3. Shareable Redacted Session Artifacts

Replay tools convert logs into HTML, browser timelines, markdown, or videos. Their goal is review and communication, not just local lookup.

Why it matters: sessions often contain the rationale behind code changes. Reviewers need a safe artifact that preserves intent without dumping raw private logs.

Possible scope for this repo: `introspect-build-bundle --redact --format html|md|json`, with fixture-tested redaction.

## 4. Prompt And Workflow Improvement

Some session analyzers produce recommendations:

- prompt clarity issues
- wasted tool use
- missing tests or verification
- repeated context discovery
- risky approval patterns
- model/tool choice recommendations

Why it matters: users want the history to teach future agents how to operate better.

Possible scope for this repo: structured "retrospective facts" output, leaving opinionated coaching to another layer.

## 5. Evaluation And Regression Measurement

Evaluation tools target:

- parser correctness across fixture corpora
- summarizer fidelity
- redaction leakage tests
- query/result quality
- adapter drift detection

Why it matters: this repo parses unstable private formats. Confidence should come from fixture coverage and drift tests.

Possible scope for this repo: a fixture conformance suite that scores each adapter on identity resolution, metadata extraction, redaction, and dedupe.

## 6. OpenTelemetry / OpenInference Export

Observability platforms use standardized traces, spans, sessions, attributes, and evaluation scores.

Why it matters: normalized exports would let local forensic data flow into existing observability tools without forcing this repo to own a UI.

Possible scope for this repo: export normalized local sessions to JSONL using an OpenTelemetry-inspired schema, with optional OTLP export later.

## 7. Session Graphs And Relationships

Codex has subagent spawn edges, T3 has provider runtime/session linkage, and opencode has parent sessions. Current support is mostly lookup-oriented.

Why it matters: modern workflows split work across agents. Users need to know who spawned whom, which branch/worktree each agent touched, and which output was incorporated.

Possible scope for this repo: `introspect-session-graph <query>` that emits text, Graphviz DOT, Mermaid, or JSON.

## 8. Worktree And Environment Health

The recent `mise` trust issue is an example of session forensics crossing into environment reliability.

Why it matters: failed or misleading session conclusions often come from broken setup, wrong Python/Node versions, missing dependencies, or unselected Codex app environments.

Possible scope for this repo: surface environment metadata from session stores and link to a separate environment-healing skill instead of owning setup repair.

## 9. Cross-Harness Skill And Plugin Inventory

Local session capability depends on available skills, plugins, MCP servers, hooks, and commands.

Why it matters: when auditing why an agent behaved a certain way, "what tools and skills were available?" is often as important as the transcript.

Possible scope for this repo: inventory installed skills/plugins and attach them to session summaries when available in local metadata.

## 10. Privacy And Compliance Modes

The repo already warns against feeding sensitive raw artifacts to external reviewers. It does not yet provide a comprehensive privacy mode.

Why it matters: session logs can contain secrets, filenames, proprietary code snippets, screenshots, and personal prompts.

Possible scope for this repo:

- metadata-only mode
- path hashing
- prompt/body omission
- allowlist-based artifact inclusion
- redaction leakage tests

