"""
Load, merge, and validate teloce-npm.json configuration.
"""

import json
from pathlib import Path
from typing import Any

from teloce_npm.utils.errors import ConfigError
from teloce_npm.utils.logging import logger

from .defaults import DEFAULT_CONFIG
from .schema import validate_config


def load_config(project_root: Path = Path(".")) -> dict[str, Any]:
    """
    Load the configuration for a Teloce-NPM project.

    Workflow:
        1. Look for 'teloce-npm.json' in the project root.
        2. If missing, use DEFAULT_CONFIG.
        3. Deep-merge user config with defaults:
             - Top-level scalars/lists: replaced by user value
             - Nested dicts ('security', 'bundling'): merged key-by-key
        4. Validate the merged result against the schema.
        5. Convert path strings into absolute Path objects.
        6. Normalize base_path (None if unset).

    Args:
        project_root: The root directory of the Teloce project.

    Returns:
        A validated, merged configuration dictionary where:
            - 'entry_html', 'output_dir', 'cache_dir' are absolute Paths
            - 'base_path' is either None or a leading-slash string
            - 'security' and 'bundling' are fully populated dicts
    """
    project_root = project_root.resolve()
    config_path = project_root / "teloce-npm.json"

    # ------------------------------------------------------------------
    # 1. Read user config (or start with empty dict)
    # ------------------------------------------------------------------
    user_config: dict[str, Any] = {}
    if config_path.exists():
        try:
            raw = config_path.read_text(encoding="utf-8")
            user_config = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {config_path}: {e}") from e
        except OSError as e:
            raise ConfigError(f"Could not read {config_path}: {e}") from e

        if not isinstance(user_config, dict):
            raise ConfigError(
                f"Config file must be a JSON object. " f"Got: {type(user_config).__name__}"
            )

        logger.debug(f"Loaded configuration from {config_path}")
    else:
        logger.debug(f"No {config_path} found, using default configuration.")

    # ------------------------------------------------------------------
    # 2. Build merged config (deep copy of defaults)
    # ------------------------------------------------------------------
    config: dict[str, Any] = {
        "packages": list(DEFAULT_CONFIG["packages"]),
        "entry_html": DEFAULT_CONFIG["entry_html"],
        "output_dir": DEFAULT_CONFIG["output_dir"],
        "cache_dir": DEFAULT_CONFIG["cache_dir"],
        "registry": DEFAULT_CONFIG["registry"],
        "base_path": DEFAULT_CONFIG["base_path"],  # None by default
        "security": dict(DEFAULT_CONFIG["security"]),
        "bundling": dict(DEFAULT_CONFIG["bundling"]),
    }

    # ------------------------------------------------------------------
    # 3. Merge user config
    # ------------------------------------------------------------------
    nested_keys = {"security", "bundling"}

    for key, value in user_config.items():
        if key in nested_keys:
            if not isinstance(value, dict):
                raise ConfigError(
                    f"Config key '{key}' must be a dictionary. " f"Got: {type(value).__name__}"
                )
            # Deep merge: only override keys the user provided
            config[key].update(value)
        else:
            config[key] = value

    # ------------------------------------------------------------------
    # 4. Validate the merged result
    # ------------------------------------------------------------------
    validate_config(config)

    # ------------------------------------------------------------------
    # 5. Convert path strings to absolute Path objects
    # ------------------------------------------------------------------
    config["entry_html"] = (project_root / config["entry_html"]).resolve()
    config["output_dir"] = (project_root / config["output_dir"]).resolve()
    config["cache_dir"] = (project_root / config["cache_dir"]).resolve()

    # ------------------------------------------------------------------
    # 6. Normalize base_path
    # ------------------------------------------------------------------
    # After validation: base_path is None or a leading-slash string.
    # No transformation needed beyond trailing-slash stripping, which
    # the adapter does. We leave it as-is so the adapter can decide
    # whether to auto-derive or use the explicit value.
    base_path = config.get("base_path")
    if base_path == "":
        # Treat empty string as "not set"
        config["base_path"] = None

    # ------------------------------------------------------------------
    # 7. Attach the project root (useful for downstream modules)
    # ------------------------------------------------------------------
    config["_project_root"] = project_root

    logger.debug(
        f"Configuration loaded: "
        f"entry_html={config['entry_html']}, "
        f"output_dir={config['output_dir']}, "
        f"bundling.mode={config['bundling']['mode']}"
    )

    return config
