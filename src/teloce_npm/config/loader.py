"""
Load, merge, and validate teloce-npm.json configuration.
"""

import json
from pathlib import Path
from typing import Dict, Any

from teloce_npm.utils.errors import ConfigError
from teloce_npm.utils.logging import logger
from .defaults import DEFAULT_CONFIG
from .schema import validate_config

def load_config(project_root: Path = Path(".")) -> Dict[str, Any]:
    """
    Load the configuration for a Teloce-NPM project.
    
    1. Looks for 'teloce-npm.json' in the project root.
    2. If missing, uses DEFAULT_CONFIG.
    3. Deep-merges user config with defaults.
    4. Validates the result.
    5. Converts string paths to Path objects.
    
    Args:
        project_root: The root directory of the Teloce project.
        
    Returns:
        A validated, merged configuration dictionary.
    """
    config_path = project_root / "teloce-npm.json"
    
    user_config = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            logger.debug(f"Loaded configuration from {config_path}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {config_path}: {e}")
    else:
        logger.debug(f"No {config_path} found, using default configuration.")

    # 1. Create a deep copy of the defaults
    config = {
        "packages": list(DEFAULT_CONFIG["packages"]),
        "entry_html": DEFAULT_CONFIG["entry_html"],
        "output_dir": DEFAULT_CONFIG["output_dir"],
        "cache_dir": DEFAULT_CONFIG["cache_dir"],
        "registry": DEFAULT_CONFIG["registry"],
        "security": dict(DEFAULT_CONFIG["security"])
    }

    # 2. Merge user config (shallow for top level, deep for security)
    for key, value in user_config.items():
        if key == "security" and isinstance(value, dict):
            # Deep merge the security settings
            config["security"].update(value)
        else:
            config[key] = value

    # 3. Validate the merged configuration
    validate_config(config)

    # 4. Convert path strings to Path objects for internal use
    config["entry_html"] = (project_root / config["entry_html"]).resolve()
    config["output_dir"] = (project_root / config["output_dir"]).resolve()
    config["cache_dir"] = (project_root / config["cache_dir"]).resolve()

    return config