"""
Validate configuration against JSON schema rules.
"""

from typing import Dict, Any
from teloce_npm.utils.errors import ConfigError

def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the configuration dictionary.
    
    Args:
        config: The merged configuration dictionary.
        
    Raises:
        ConfigError: If any validation rule fails.
    """
    # Check required keys
    required_keys = ["packages", "entry_html", "output_dir", "registry", "security"]
    for key in required_keys:
        if key not in config:
            raise ConfigError(f"Missing required config key: '{key}'")

    # Validate types
    if not isinstance(config["packages"], list):
        raise ConfigError("Config key 'packages' must be a list.")
    for pkg in config["packages"]:
        if not isinstance(pkg, str):
            raise ConfigError("All items in 'packages' must be strings.")

    if not isinstance(config["entry_html"], str):
        raise ConfigError("Config key 'entry_html' must be a string.")

    if not isinstance(config["output_dir"], str):
        raise ConfigError("Config key 'output_dir' must be a string.")
        
    if not isinstance(config["registry"], str):
        raise ConfigError("Config key 'registry' must be a string.")
        
    if not config["registry"].startswith(("http://", "https://")):
        raise ConfigError("Config key 'registry' must be a valid HTTP/HTTPS URL.")

    # Validate security block
    if not isinstance(config["security"], dict):
        raise ConfigError("Config key 'security' must be a dictionary.")
        
    security_keys = [
        "verify_integrity", 
        "scan_malware", 
        "block_install_scripts", 
        "check_vulnerabilities"
    ]
    
    for key in security_keys:
        if key not in config["security"]:
            raise ConfigError(f"Missing required security key: 'security.{key}'")
        if not isinstance(config["security"][key], bool):
            raise ConfigError(f"Security key 'security.{key}' must be a boolean.")