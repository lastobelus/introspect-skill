# Contributing

`introspect-skill` is currently T3Code-first on purpose. Contributions are most useful when they either improve the existing T3/Codex/Claude/opencode workflows or make that bias easier to relax without breaking the current discovery model.

## Priorities

- add new harness or session-store adapters behind the existing config layer
- improve matching and dedupe without regressing T3-backed canonicalization
- strengthen tests and evals with synthetic fixture stores
- improve installability for Codex, Claude, opencode, and future marketplaces

## Development workflow

1. Keep user-configurable paths in config, not hard-coded in scripts.
2. Prefer synthetic fixture stores in `tests/` over tests that read your real home directory.
3. If a change affects session-source discovery or dedupe, update both tests and `references/log-sources.md`.
4. If a change affects packaging or install flow, update `README.md`, `SKILL.md`, and `docs/install-script-plan.md` together.

## Local checks

```bash
mise install
mise exec -- python -m pip install '.[test]'
mise exec -- python -m py_compile introspect_skill/*.py scripts/*.py tests/*.py evals/*.py
PYTHONPATH=$PWD mise exec -- python -m pytest
PYTHONPATH=$PWD mise exec -- python evals/run_smoke.py
```

## Adding a new harness

When adding a new harness or session store:

1. Extend `introspect_skill/config.py` so roots are configurable.
2. Add the resolver/history logic in the shared package first, not only in a script.
3. Document the store format in `references/log-sources.md`.
4. Add at least one unit test and one smoke-style eval or subprocess test that exercises the new path.
