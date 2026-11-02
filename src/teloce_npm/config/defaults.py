"""
Default configuration values for Teloce-NPM.
"""

from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    # List of explicitly added packages (populated by `teloce-npm add`
    # and `teloce-npm install <pkg>`). The install command scans .vel files
    # too, but explicit entries are always honored.
    "packages": [],

    # Approach A: Explicit Entry Point
    # The single HTML file that Teloce-NPM will inject <script> tags into.
    "entry_html": "templates/index.html",

    # Where wrapped packages and generated runtime files are written.
    # Aligned with Teloce-Py's `dist/` output.
    "output_dir": "dist/static/teloce-npm",

    # Where downloaded tarballs and extracted code are stored.
    "cache_dir": ".teloce-npm/cache",

    # The npm registry to fetch packages from.
    "registry": "https://registry.npmjs.org",

    # URL prefix under which output_dir is served.
    # If unset (None), the adapter derives it from output_dir
    # (e.g., "dist/static/teloce-npm" -> "/static/teloce-npm").
    "base_path": None,

    # Security policies
    "security": {
        "verify_integrity": True,       # Always verify SHA-512
        "scan_malware": True,           # AST-based scanning
        "block_install_scripts": True,  # Block preinstall/postinstall
        "check_vulnerabilities": True,  # Query OSV database
    },

    # Bundling configuration (MinifyJS / esbuild fallback)
    # Handles packages the static Tree-sitter wrapper cannot.
    "bundling": {
        "mode": "auto",         # "auto" | "always" | "never"
        "minify": True,         # compress + mangle
        "target": "es2020",     # JS target syntax level
        "format": "esm",        # "esm" | "cjs" | "iife"
        "sourcemap": None,      # None | "inline" | "external" | "both"
        "splitting": False,     # requires format="esm"
        "platform": "browser",  # "browser" | "node" | "neutral"
    },
}