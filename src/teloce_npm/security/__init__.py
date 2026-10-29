"""
Security layer for Teloce-NPM.

Provides integrity verification, malware scanning, install script
blocking, and vulnerability checks.
"""

from .integrity import IntegrityVerifier
from .malware_scanner import scan_package
from .install_policy import check_install_scripts
from .vulnerability import check_vulnerabilities
from .policy import SecurityPolicy, run_security_checks

__all__ = [
    "IntegrityVerifier",
    "scan_package",
    "check_install_scripts",
    "check_vulnerabilities",
    "SecurityPolicy",
    "run_security_checks",
]