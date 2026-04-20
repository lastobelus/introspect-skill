from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import tomllib


VALID_HARNESSES = {"t3", "claude", "codex", "opencode"}


def parse_toml(text: str) -> dict[str, object]:
    return tomllib.loads(text)


def _split_env_paths(value: str | None) -> list[str]:
    if not value:
        return []
    return [entry for entry in value.split(os.pathsep) if entry]


def _expand_path(value: str | Path, home: Path | None = None) -> Path:
    value = Path(value)
    if str(value).startswith("~"):
        if home is not None:
            text = str(value)
            if text == "~":
                return home
            if text.startswith("~/"):
                return home / text[2:]
        return value.expanduser()
    return value


def _expand_paths(values: list[str | Path] | None, home: Path | None = None) -> list[Path]:
    if not values:
        return []
    seen: set[Path] = set()
    expanded: list[Path] = []
    for value in values:
        path = _expand_path(value, home=home)
        if path in seen:
            continue
        seen.add(path)
        expanded.append(path)
    return expanded


def _defaults_or_configured(
    config_data: dict[str, object],
    key: str,
    defaults: list[str | Path],
    *,
    home: Path | None = None,
) -> list[Path]:
    if key in config_data:
        return _expand_paths(config_data.get(key), home=home)
    return _expand_paths(defaults, home=home)


def _discover_t3_roots(home: Path) -> list[Path]:
    roots: list[Path] = []
    for path in [home / ".t3", *sorted(home.glob(".t3*"))]:
        if not path.is_dir():
            continue
        if (path / "userdata" / "state.sqlite").exists() and path not in roots:
            roots.append(path)
    return roots


@dataclass
class SearchConfig:
    enabled_harnesses: set[str]
    t3_roots: list[Path]
    claude_project_roots: list[Path]
    codex_session_indexes: list[Path]
    codex_session_roots: list[Path]
    opencode_databases: list[Path]
    opencode_session_diff_roots: list[Path]
    source_path: Path | None = None

    @property
    def state_databases(self) -> list[Path]:
        return [root / "userdata" / "state.sqlite" for root in self.t3_roots]

    @property
    def provider_log_dirs(self) -> list[Path]:
        return [root / "userdata" / "logs" / "provider" for root in self.t3_roots]


def default_config_locations(home: Path) -> list[Path]:
    return [home / ".config" / "introspect-skill" / "config.toml"]


def load_config(config_path: str | Path | None = None, home: Path | None = None) -> SearchConfig:
    home = home or Path.home()
    explicit_path_requested = config_path is not None
    chosen_path = Path(config_path).expanduser() if config_path else None

    if chosen_path is None:
        env_override = os.environ.get("INTROSPECT_SKILL_CONFIG")
        if env_override:
            chosen_path = Path(env_override).expanduser()
            explicit_path_requested = True

    config_data: dict[str, object] = {}
    source_path = None
    if chosen_path is None:
        for candidate in default_config_locations(home):
            if candidate.exists():
                chosen_path = candidate
                break

    if chosen_path and explicit_path_requested and not chosen_path.exists():
        raise ValueError(f"Config file not found: {chosen_path}")

    if chosen_path and chosen_path.exists():
        config_data = parse_toml(chosen_path.read_text())
        source_path = chosen_path

    enabled = set(config_data.get("enabled_harnesses", []))
    enabled.update(entry.strip() for entry in _split_env_paths(os.environ.get("INTROSPECT_ENABLED_HARNESSES")))
    enabled = {entry for entry in enabled if entry in VALID_HARNESSES}
    if not enabled:
        enabled = set(VALID_HARNESSES)

    t3_roots = _defaults_or_configured(config_data, "t3_roots", _discover_t3_roots(home), home=home)
    t3_roots.extend(_expand_paths(_split_env_paths(os.environ.get("INTROSPECT_T3_ROOTS")), home=home))

    claude_roots = _defaults_or_configured(config_data, "claude_project_roots", [home / ".claude" / "projects"], home=home)

    codex_indexes = _defaults_or_configured(config_data, "codex_session_indexes", [home / ".codex" / "session_index.jsonl"], home=home)

    codex_roots = _defaults_or_configured(config_data, "codex_session_roots", [home / ".codex" / "sessions"], home=home)

    opencode_dbs = _defaults_or_configured(config_data, "opencode_databases", [home / ".local" / "share" / "opencode" / "opencode.db"], home=home)

    opencode_diffs = _defaults_or_configured(
        config_data,
        "opencode_session_diff_roots",
        [home / ".local" / "share" / "opencode" / "storage" / "session_diff"],
        home=home,
    )

    return SearchConfig(
        enabled_harnesses=enabled,
        t3_roots=t3_roots,
        claude_project_roots=claude_roots,
        codex_session_indexes=codex_indexes,
        codex_session_roots=codex_roots,
        opencode_databases=opencode_dbs,
        opencode_session_diff_roots=opencode_diffs,
        source_path=source_path,
    )
