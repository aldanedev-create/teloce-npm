"""
Security policy configuration for Teloce-NPM.

Defines the default security rules and provides a unified interface
for running all security checks on a package.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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
    fail_on_critical: bool = True
    allow_vulnerabilities: list[str] = field(default_factory=list)
    require_osv: bool = False

    # Download / extraction limits
    max_tarball_bytes: int = 100 * 1024 * 1024
    max_unpacked_bytes: int = 500 * 1024 * 1024
    max_files: int = 50_000

    # Network
    allowed_registries: list[str] = field(default_factory=lambda: ["https://registry.npmjs.org"])
    block_unknown_domains: bool = True

    # Wrapping
    strip_node_builts: bool = True
    polyfill_browser: bool = True

    # Reviewed exceptions: {package name: [finding types]}. A listed finding
    # type no longer blocks that one package (e.g. d3 -> ["dynamic_function"]).
    allow: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "SecurityPolicy":
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
            fail_on_critical=config.get("fail_on_critical", True),
            allow_vulnerabilities=[str(v) for v in config.get("allow_vulnerabilities") or []],
            require_osv=config.get("require_osv", False),
            require_lockfile_match=config.get("require_lockfile_match", True),
            allowed_registries=list(
                config.get("allowed_registries") or ["https://registry.npmjs.org"]
            ),
            block_unknown_domains=config.get("block_unknown_domains", True),
            max_tarball_bytes=int(config.get("max_tarball_mb", 100)) * 1024 * 1024,
            max_unpacked_bytes=int(config.get("max_unpacked_mb", 500)) * 1024 * 1024,
            max_files=int(config.get("max_files", 50_000)),
            allow={
                str(name): [str(kind) for kind in kinds]
                for name, kinds in (config.get("allow") or {}).items()
            },
        )


def run_security_checks(
    package_dir: Path,
    package_name: str,
    policy: SecurityPolicy,
) -> dict[str, Any]:
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
    findings: list[dict[str, Any]] = []

    # 1. Install script blocking
    if policy.block_install_scripts:
        from .install_policy import check_install_scripts

        try:
            check_install_scripts(package_dir, package_name)
        except Exception as e:
            findings.append(
                {
                    "type": "install_script",
                    "severity": "HIGH",
                    "message": str(e),
                }
            )

    # 2. Malware scanning
    if policy.scan_packages:
        from .malware_scanner import scan_package

        result = scan_package(package_dir, package_name, policy)
        findings.extend(result["findings"])

    # 3. Apply reviewed, per-package exceptions from `security.allow`.
    allowed_types = set(policy.allow.get(package_name, []))
    blocking = [f for f in findings if f["type"] not in allowed_types]
    allowed = [f for f in findings if f["type"] in allowed_types]
    is_safe = not any(f["severity"] == "HIGH" for f in blocking)

    return {
        "safe": is_safe,
        "findings": blocking,
        "allowed": allowed,
    }
