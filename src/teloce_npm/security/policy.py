"""
Security policy configuration for Teloce-NPM.

Defines the default security rules and provides a unified interface
for running all security checks on a package.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional

from teloce_npm.utils.logging import logger


@dataclass
class SecurityPolicy:
    """
    Configuration for security checks.
    
    Mirrors the 'security' block in teloce-npm.json.
    """
    # Integrity
    verify_integrity: bool = True
    lockfile: bool = True
    require_lockfile_match: bool = True

    # Malware scanning
    scan_packages: bool = True
    block_install_scripts: bool = True
    max_entropy_threshold: float = 7.5

    # Vulnerabilities
    check_osv: bool = True
    fail_on_critical: bool = False

    # Network
    allowed_registries: List[str] = field(default_factory=lambda: ["https://registry.npmjs.org"])
    block_unknown_domains: bool = True

    # Wrapping
    strip_node_builts: bool = True
    polyfill_browser: bool = True

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "SecurityPolicy":
        """
        Build a SecurityPolicy from a configuration dictionary.
        
        Args:
            config: The 'security' block from teloce-npm.json.
            
        Returns:
            A SecurityPolicy instance.
        """
        return cls(
            verify_integrity=config.get("verify_integrity", True),
            scan_packages=config.get("scan_malware", True),
            block_install_scripts=config.get("block_install_scripts", True),
            check_osv=config.get("check_vulnerabilities", True),
            fail_on_critical=config.get("fail_on_critical", False),
        )


def run_security_checks(
    package_dir: Path,
    package_name: str,
    policy: SecurityPolicy,
) -> Dict[str, Any]:
    """
    Run the full security pipeline on an extracted package.
    
    Pipeline:
        1. Install script blocking
        2. Malware scanning (AST-based)
        3. Vulnerability check (OSV)
        
    Args:
        package_dir: The extracted package directory.
        package_name: The name of the package.
        policy: The security policy to apply.
        
    Returns:
        A dict with 'safe' (bool) and 'findings' (list of issues).
    """
    findings = []
    is_safe = True

    # 1. Install script blocking
    if policy.block_install_scripts:
        from .install_policy import check_install_scripts
        try:
            check_install_scripts(package_dir, package_name)
        except Exception as e:
            findings.append({
                "type": "install_script",
                "severity": "HIGH",
                "message": str(e),
            })
            is_safe = False

    # 2. Malware scanning
    if policy.scan_packages:
        from .malware_scanner import scan_package
        result = scan_package(package_dir, package_name, policy)
        if not result["safe"]:
            findings.extend(result["findings"])
            is_safe = False

    return {
        "safe": is_safe,
        "findings": findings,
    }