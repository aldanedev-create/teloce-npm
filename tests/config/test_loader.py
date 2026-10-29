"""
Tests for teloce_npm.config.loader.load_config.

Verifies:
- Missing config file -> defaults are used
- Config file -> user values override defaults
- Paths are converted to absolute Path objects
- Security block is deep-merged
- Invalid JSON raises ConfigError
- Invalid schema raises ConfigError
"""

import json
import pytest
from pathlib import Path

from teloce_npm.config import load_config
from teloce_npm.utils.errors import ConfigError


def test_load_config_without_file_returns_defaults(tmp_project):
    """No teloce-npm.json -> defaults, but paths are still absolute Paths."""
    config = load_config(tmp_project)

    assert config["packages"] == []
    assert config["registry"] == "https://registry.npmjs.org"

    # Paths must be absolute Path objects
    assert isinstance(config["entry_html"], Path)
    assert isinstance(config["output_dir"], Path)
    assert isinstance(config["cache_dir"], Path)

    assert config["entry_html"].is_absolute()
    assert config["entry_html"].name == "index.html"
    assert config["entry_html"].parent.name == "templates"


def test_load_config_with_user_overrides(tmp_project):
    """User config overrides defaults, but defaults remain for unspecified keys."""
    config_data = {
        "packages": ["lodash"],
        "entry_html": "templates/custom.html",
    }
    (tmp_project / "teloce-npm.json").write_text(
        json.dumps(config_data), encoding="utf-8"
    )

    config = load_config(tmp_project)

    assert config["packages"] == ["lodash"]
    assert config["entry_html"].name == "custom.html"
    # Non-overridden defaults survive
    assert config["registry"] == "https://registry.npmjs.org"
    assert config["output_dir"].name == "teloce-npm"


def test_load_config_resolves_paths(tmp_project):
    """entry_html / output_dir / cache_dir must be absolute Paths."""
    config = load_config(tmp_project)

    for key in ("entry_html", "output_dir", "cache_dir"):
        assert isinstance(config[key], Path)
        assert config[key].is_absolute()


def test_load_config_output_dir_default_path(tmp_project):
    """Default output_dir must resolve to <project>/dist/static/teloce-npm."""
    config = load_config(tmp_project)

    expected = (tmp_project / "dist/static/teloce-npm").resolve()
    assert config["output_dir"] == expected


def test_load_config_cache_dir_default_path(tmp_project):
    """Default cache_dir must resolve to <project>/.teloce-npm/cache."""
    config = load_config(tmp_project)

    expected = (tmp_project / ".teloce-npm/cache").resolve()
    assert config["cache_dir"] == expected


def test_load_config_deep_merges_security(tmp_project):
    """User overriding one security flag keeps the others from defaults."""
    config_data = {"security": {"scan_malware": False}}
    (tmp_project / "teloce-npm.json").write_text(
        json.dumps(config_data), encoding="utf-8"
    )

    config = load_config(tmp_project)

    assert config["security"]["scan_malware"] is False          # overridden
    assert config["security"]["verify_integrity"] is True       # from default
    assert config["security"]["block_install_scripts"] is True  # from default
    assert config["security"]["check_vulnerabilities"] is True  # from default


def test_load_config_invalid_json_raises(tmp_project):
    (tmp_project / "teloce-npm.json").write_text("{ not json", encoding="utf-8")

    with pytest.raises(ConfigError, match="Invalid JSON"):
        load_config(tmp_project)


def test_load_config_invalid_schema_raises(tmp_project):
    """A user config that violates the schema must raise ConfigError."""
    (tmp_project / "teloce-npm.json").write_text(
        json.dumps({"packages": "not-a-list"}), encoding="utf-8"
    )

    with pytest.raises(ConfigError, match="packages"):
        load_config(tmp_project)


def test_load_config_does_not_mutate_defaults(tmp_project):
    """Loading a config must not corrupt DEFAULT_CONFIG for future calls."""
    from teloce_npm.config.defaults import DEFAULT_CONFIG

    original_packages = list(DEFAULT_CONFIG["packages"])

    config_data = {"packages": ["lodash"]}
    (tmp_project / "teloce-npm.json").write_text(
        json.dumps(config_data), encoding="utf-8"
    )
    load_config(tmp_project)

    # DEFAULT_CONFIG must still have the original (empty) packages
    assert DEFAULT_CONFIG["packages"] == original_packages