from pathlib import Path

from introspect_skill.config import load_config, parse_toml
from tests.support import write_t3_state_db


def test_load_config_discovers_multiple_t3_roots(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    default_root = home / ".t3"
    second_root = home / ".t3-experimental"
    write_t3_state_db(default_root, "thread-1", "inspect this session", "codex-thread-1")
    write_t3_state_db(second_root, "thread-2", "inspect the other thread", "codex-thread-2")

    config_dir = home / ".config" / "introspect-skill"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(f't3_roots = ["{second_root}"]\n')

    monkeypatch.setenv("HOME", str(home))
    config = load_config(home=home)
    assert second_root in config.t3_roots
    assert default_root not in config.t3_roots


def test_load_config_t3_env_roots_extend_configured_roots(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    configured_root = home / ".t3-configured"
    env_root = home / ".t3-env"
    write_t3_state_db(configured_root, "thread-1", "inspect this session", "codex-thread-1")
    write_t3_state_db(env_root, "thread-2", "inspect the other thread", "codex-thread-2")

    config_dir = home / ".config" / "introspect-skill"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(f't3_roots = ["{configured_root}"]\n')

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("INTROSPECT_T3_ROOTS", str(env_root))
    config = load_config(home=home)
    assert configured_root in config.t3_roots
    assert env_root in config.t3_roots


def test_parse_toml_supports_basic_repo_config_shape() -> None:
    parsed = parse_toml('enabled_harnesses = ["t3", "codex"]\nt3_roots = ["~/.t3"]\n')
    assert parsed["enabled_harnesses"] == ["t3", "codex"]
    assert parsed["t3_roots"] == ["~/.t3"]


def test_load_config_rejects_missing_explicit_config_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing.toml"
    try:
        load_config(config_path=missing, home=tmp_path)
    except ValueError as exc:
        assert str(missing) in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError for missing explicit config path")
