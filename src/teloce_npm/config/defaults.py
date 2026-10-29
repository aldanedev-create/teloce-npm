"""
Default configuration values for Teloce-NPM.
"""

from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    # List of explicitly added packages (usually populated by `teloce-npm add`)
    "packages": [],
    
    # Approach A: Explicit Entry Point
    # The single HTML file that Teloce-NPM will inject <script> tags into.
    "entry_html": "templates/index.html",
    
    # The directory where wrapped packages and generated JS files are written.
    # Aligned with Teloce-Py's `dist` output.
    "output_dir": "dist/static/teloce-npm",
    
    # Where downloaded tarballs are stored locally.
    "cache_dir": ".teloce-npm/cache",
    
    # The npm registry to fetch packages from.
    "registry": "https://registry.npmjs.org",
    
    # Security policies
    "security": {
        "verify_integrity": True,      # Always verify SHA-512
        "scan_malware": True,          # Scan for dangerous patterns
        "block_install_scripts": True, # Block preinstall/postinstall
        "check_vulnerabilities": True, # Query OSV database
    }
}