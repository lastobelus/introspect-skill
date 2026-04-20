# Evals

These are lightweight repo-local smoke evals that exercise the public skill against synthetic session stores.

Current scenarios:

- T3-backed Codex history dedupe
- T3-backed Claude history dedupe
- multi-root T3 discovery
- opencode session resolution
- Codex session-index resolution
- opencode session-diff resolution
- `opencode session list` resolution
- `resolve_target.py` CLI JSON output
- `claude_jsonl_summary.py` CLI JSON output
- `provider_log_summary.py` CLI JSON output

Run:

```bash
python3 evals/run_smoke.py
```
