# Approach Matrix

Research date: 2026-05-04. Adoption metrics are GitHub snapshots collected from the public GitHub API unless marked otherwise.

## Summary Matrix

| Approach                              | Representative tools                                                                                                                     | How it works                                                                                                                                                                  | Adoption/activity signal                                                                                                                                                                                                  | Fit for this repo                                                                                                                                                                                              |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Local cross-harness session resolver  | `introspect-skill`, Vibe Log, Aivo stats/logs, SessionPilot                                                                              | Reads local session stores from multiple agent CLIs and maps sessions by path, id, title, provider metadata, and timestamps.                                                  | Vibe Log: 321 stars, 21 forks, pushed 2026-04-19. Aivo and SessionPilot are visible product sites but GitHub metrics were not confirmed.                                                                                  | Direct fit. This repo already does the forensic resolver slice; opportunity is deeper metadata indexes and safer redacted summaries.                                                                           |
| Claude Code session viewers           | claude-code-log, Poirot, cc9s, Claude Code Trace, clog, Claude Code Dashboard                                                            | Parses `~/.claude/projects/**/*.jsonl`, then renders sessions in HTML, TUI, desktop, or dashboard form. Often focuses on tool calls, tokens, costs, resume links, and search. | claude-code-log: 988 stars, 79 forks, pushed 2026-04-29. claude-replay: 667/41, pushed 2026-05-03. Claude Code Trace: 261/6, pushed 2026-05-03. Poirot: 174/11, pushed 2026-03-30. cc9s: 65/5, pushed 2026-04-27.         | Good feature inspiration, but most are Claude-first and do not solve T3/native dedupe or cross-provider identity.                                                                                              |
| Shareable replay/export               | claude-replay, Capsule, ccreplay, claude-code-log                                                                                        | Converts session logs into self-contained HTML, browser timeline, or video. Some support Claude, Codex, Cursor, Gemini, and OpenCode formats.                                 | claude-replay: 667 stars, 41 forks, active 2026-05-03. Capsule: 10/1, pushed 2026-03-13. ccreplay: 7/0, pushed 2026-03-14.                                                                                                | Strong candidate for a redacted export/bundle feature. Less useful for identity resolution by itself.                                                                                                          |
| Live monitoring dashboards            | Claude-Code-Agent-Monitor, Claude Code Dashboard, Claude Code Trace, SessionPilot                                                        | Watches local logs or hooks, aggregates active sessions, tool use, token/cost data, and status across terminals.                                                              | Claude-Code-Agent-Monitor: 299/61, pushed 2026-05-04. Claude Code Dashboard: 9/2, pushed 2026-03-09. Claude Code Trace: 261/6, pushed 2026-05-03.                                                                         | Adjacent. This repo currently inspects after the fact; live monitoring could be a separate mode if kept read-only.                                                                                             |
| LLM observability platforms           | Langfuse, LangSmith, Phoenix, Helicone, AgentOps, OpenLLMetry, Opik, MLflow tracing, LangWatch, Weave                                    | Instrument application code or gateways to emit traces, spans, metrics, prompts, sessions, eval scores, and costs to a local or hosted backend.                               | Langfuse: 26,545 stars, 2,687 forks, pushed 2026-05-04. MLflow: 25,716/5,685, pushed 2026-05-04. Opik: 19,197/1,465, pushed 2026-05-04. Phoenix: 9,517/850, pushed 2026-05-04. OpenLLMetry: 7,068/951, pushed 2026-04-30. | Conceptually important but a different layer. They need instrumentation; this repo reverse-engineers local harness artifacts after the fact. OpenTelemetry/OpenInference schemas are useful design references. |
| Evaluation and red-team tools         | promptfoo, DeepEval, Braintrust, LangSmith evals, Langfuse evals, Phoenix experiments                                                    | Define datasets, assertions, LLM-as-judge checks, regression tests, red-team probes, and CI gates for prompts/agents.                                                         | promptfoo: 20,838 stars, 1,804 forks, pushed 2026-05-04. DeepEval: 15,137/1,407, pushed 2026-05-04.                                                                                                                       | Useful for testing parser quality and summarization quality. Not a replacement for local session discovery.                                                                                                    |
| Agent frameworks and coding harnesses | Codex CLI, opencode, OpenHands, Aider, LangGraph, AutoGen, CrewAI, OpenAI Agents SDK                                                     | Own execution, tools, workspace state, and sometimes tracing. Store logs in their own formats or expose traces through SDK/platform integrations.                             | opencode: 154,522 stars, 17,892 forks, pushed 2026-05-04. Codex: 79,928/11,498, pushed 2026-05-04. OpenHands: 72,613/9,180, pushed 2026-05-04. Aider: 44,316/4,352, pushed 2026-04-25.                                    | These are sources to inspect, not competitors. The repo should add adapters only when stores are local and stable enough to parse.                                                                             |
| Skills and workflow plugins           | Claude session-report plugin, session-inspector skill, 0xDarkMatter introspect/log-ops, Codex skills, local `codex-worktree-environment` | Package procedures and scripts as agent-loadable capabilities. Some summarize sessions; others manage skill/plugin/hook development or workflow state.                        | Session-inspector and 0xDarkMatter introspect are discoverable skill pages; GitHub metrics were not fully verified. Local Claude plugin marketplace contains a `session-report` skill.                                    | Very relevant packaging model. This repo's `SKILL.md` should stay concise and route heavy work to scripts.                                                                                                     |

## Detailed Notes

### Local Session Analytics

Vibe Log is closest in spirit to a user-facing productivity-report layer over local coding-agent sessions. Its README describes local analysis of Claude Code and Codex sessions and report generation. Aivo's public site describes local SQLite logging and stats across Claude Code, Codex, Gemini, OpenCode, and other tools, including token/model breakdowns.

Difference from `introspect-skill`: those tools are analytics/productivity oriented. This repo is forensic and identity oriented. A useful split is:

- `introspect-skill`: "which session/thread/log is this, what happened, and how do I continue safely?"
- analytics tools: "how much did I use, what did it cost, and what patterns are emerging?"

### Claude Session Viewers

The Claude session-viewer ecosystem is crowded and fast-moving because Claude Code JSONL files are visible, rich, and painful to inspect manually. Common features:

- chronological rendering of messages and tool calls
- token and cost calculations
- full-text search
- session grouping by project
- resume links or command generation
- file diff/history viewers
- plugin/hook/config inspection

This repo should not try to become another Claude-only viewer. The useful ideas are metadata-only summaries, cost/token aggregation, resume affordances, and redacted exports.

### Observability Platforms

Langfuse, Phoenix, LangSmith, AgentOps, OpenLLMetry, Opik, Helicone, and MLflow all assume an instrumented app, gateway, or SDK. They model traces, spans, sessions, evals, costs, prompt versions, and sometimes datasets/experiments.

The design lesson is schema discipline. `introspect-skill` currently reads local artifacts whose schemas are not stable public APIs. A normalized internal event model inspired by OpenTelemetry/OpenInference would make downstream commands easier:

- `session`
- `turn`
- `message`
- `tool_call`
- `tool_result`
- `approval`
- `checkpoint`
- `cost_usage`
- `artifact`
- `relationship`

### Evaluation Tools

promptfoo and DeepEval point to a missing maturity layer: regression tests for parsers and summarizers against fixture session stores. The repo already has unit tests and smoke evals, but not much measurement of extraction quality, redaction quality, or adapter drift.

### Agent Harnesses

Codex, opencode, Claude Code, Aider, and OpenHands each represent a different harness ownership model. The repo should prefer:

- durable local stores first
- structured SQLite/JSON fields before log text
- adapters that can degrade gracefully when a store is absent
- explicit version-sensitive fixture updates

## Sources

- LangSmith docs: https://docs.langchain.com/langsmith/home
- Langfuse docs: https://langfuse.com/docs
- Phoenix docs: https://arize.com/docs/phoenix
- AgentOps docs: https://docs.agentops.ai/v2/introduction
- OpenLLMetry docs: https://www.traceloop.com/docs/openllmetry
- promptfoo docs: https://www.promptfoo.dev/docs/intro/
- Claude Code monitoring docs: https://code.claude.com/docs/en/monitoring-usage
- claude-code-log: https://github.com/daaain/claude-code-log
- claude-replay: https://github.com/es617/claude-replay
- cc9s: https://github.com/kincoy/cc9s
- Poirot: https://poirot.fyi/
- Capsule: https://capsule.endor.dev/

