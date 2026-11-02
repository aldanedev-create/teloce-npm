"""
Security layer for Teloce-NPM.

Provides integrity verification, malware scanning, install script
blocking, and vulnerability checks.
"""

from .install_policy import check_install_scripts
from .integrity import IntegrityVerifier
from .malware_scanner import scan_package
from .policy import SecurityPolicy, run_security_checks
from .vulnerability import check_vulnerabilities

__all__ = [
    "IntegrityVerifier",
    "SecurityPolicy",
    "check_install_scripts",
    "check_vulnerabilities",
    "run_security_checks",
    "scan_package",
]
