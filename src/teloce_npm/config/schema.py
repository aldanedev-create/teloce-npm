"""
Validate configuration against JSON schema rules.
"""

from typing import Any, Dict

from teloce_npm.utils.errors import ConfigError


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the merged configuration dictionary.

    Raises:
        ConfigError: If any validation rule fails.
    """
    # ------------------------------------------------------------------
    # Required top-level keys
    # ------------------------------------------------------------------
    required_keys = [
        "packages",
        "entry_html",
        "output_dir",
        "cache_dir",
        "registry",
        "security",
        "bundling",
    ]
    for key in required_keys:
        if key not in config:
            raise ConfigError(f"Missing required config key: '{key}'")

    # ------------------------------------------------------------------
    # packages
    # ------------------------------------------------------------------
    if not isinstance(config["packages"], list):
        raise ConfigError("Config key 'packages' must be a list.")
    for pkg in config["packages"]:
        if not isinstance(pkg, str):
            raise ConfigError("All items in 'packages' must be strings.")

    # ------------------------------------------------------------------
    # Paths (strings in config; loader converts to Path)
    # ------------------------------------------------------------------
    for key in ("entry_html", "output_dir", "cache_dir"):
        if not isinstance(config[key], str) or not config[key]:
            raise ConfigError(f"Config key '{key}' must be a non-empty string.")

    # ------------------------------------------------------------------
    # base_path (optional)
    # ------------------------------------------------------------------
    base_path = config.get("base_path")
    if base_path is not None:
        if not isinstance(base_path, str):
            raise ConfigError("Config key 'base_path' must be a string or None.")
        if base_path and not base_path.startswith("/"):
            raise ConfigError("Config key 'base_path' must start with '/' when set.")

    # ------------------------------------------------------------------
    # registry
    # ------------------------------------------------------------------
    if not isinstance(config["registry"], str):
        raise ConfigError("Config key 'registry' must be a string.")
    if not config["registry"].startswith(("http://", "https://")):
        raise ConfigError("Config key 'registry' must be a valid HTTP/HTTPS URL.")

    # ------------------------------------------------------------------
    # security block
    # ------------------------------------------------------------------
    if not isinstance(config["security"], dict):
        raise ConfigError("Config key 'security' must be a dictionary.")

    security_keys = [
        "verify_integrity",
        "scan_malware",
        "block_install_scripts",
        "check_vulnerabilities",
    ]
    for key in security_keys:
        if key not in config["security"]:
            raise ConfigError(f"Missing required security key: 'security.{key}'")
        if not isinstance(config["security"][key], bool):
            raise ConfigError(f"Security key 'security.{key}' must be a boolean.")

    # ------------------------------------------------------------------
    # bundling block
    # ------------------------------------------------------------------
    if not isinstance(config["bundling"], dict):
        raise ConfigError("Config key 'bundling' must be a dictionary.")

    bundling = config["bundling"]
    bundling_keys = [
        "mode",
        "minify",
        "target",
        "format",
        "sourcemap",
        "splitting",
        "platform",
    ]
    for key in bundling_keys:
        if key not in bundling:
            raise ConfigError(f"Missing required bundling key: 'bundling.{key}'")

    # mode
    if bundling["mode"] not in ("auto", "always", "never"):
        raise ConfigError(
            f"bundling.mode must be one of: auto, always, never. "
            f"Got: {bundling['mode']!r}"
        )

    # boolean keys
    for key in ("minify", "splitting"):
        if not isinstance(bundling[key], bool):
            raise ConfigError(f"bundling.{key} must be a boolean.")

    # target
    if not isinstance(bundling["target"], str) or not bundling["target"]:
        raise ConfigError("bundling.target must be a non-empty string (e.g., 'es2020').")

    # format
    if bundling["format"] not in ("esm", "cjs", "iife"):
        raise ConfigError(
            f"bundling.format must be one of: esm, cjs, iife. "
            f"Got: {bundling['format']!r}"
        )

    # platform
    if bundling["platform"] not in ("browser", "node", "neutral"):
        raise ConfigError(
            f"bundling.platform must be one of: browser, node, neutral. "
            f"Got: {bundling['platform']!r}"
        )

    # sourcemap (optional)
    sm = bundling.get("sourcemap")
    if sm is not None and sm not in ("inline", "external", "both"):
        raise ConfigError(
            f"bundling.sourcemap must be None, 'inline', 'external', or 'both'. "
            f"Got: {sm!r}"
        )

    # splitting requires ESM format
    if bundling["splitting"] and bundling["format"] != "esm":
        raise ConfigError(
            "bundling.splitting requires bundling.format to be 'esm'. "
            f"Got format={bundling['format']!r}, splitting={bundling['splitting']!r}."
        )