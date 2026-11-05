"""
Default configuration values for Teloce-NPM.
"""

from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
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
        "verify_integrity": True,  # Always verify SHA-512
        "scan_malware": True,  # AST-based scanning
        "block_install_scripts": True,  # Block preinstall/postinstall
        "check_vulnerabilities": True,  # Query OSV database
        "fail_on_critical": True,  # Block packages with a CRITICAL OSV advisory
        "allow_vulnerabilities": [],  # Advisory IDs you have reviewed, e.g. ["GHSA-xxxx"]
        "require_osv": False,  # Fail the install if OSV cannot be reached
        "require_lockfile_match": True,  # Locked integrity must match the registry
        # Hosts tarballs may be downloaded from (the configured registry is always allowed).
        "allowed_registries": ["https://registry.npmjs.org"],
        "block_unknown_domains": True,
        # Download/extraction limits (decompression-bomb protection).
        "max_tarball_mb": 100,
        "max_unpacked_mb": 500,
        "max_files": 50000,
        # Reviewed exceptions: {"package": ["finding_type", ...]} (see docs/security.md).
        "allow": {},
    },
    # Bundling configuration (MinifyJS / esbuild backend)
    # MinifyJS is installed as a core dependency and handles packages the
    # static Tree-sitter wrapper cannot.
    "bundling": {
        "mode": "auto",  # "auto" | "always" | "never"
        "minify": True,  # compress + mangle
        "target": "es2020",  # JS target syntax level
        "format": "esm",  # "esm" | "cjs" | "iife"
        "sourcemap": None,  # None | "inline" | "external" | "both"
        "splitting": False,  # requires format="esm"
        "platform": "browser",  # "browser" | "node" | "neutral"
        "tree_shaking": True,
        "packages": "bundle",  # "bundle" | "external"
        "external": [],
        "define": {},
        "drop": [],
        "charset": "utf8",
        "legal_comments": None,
        "entry_names": None,
        "chunk_names": None,
        "asset_names": None,
        "metafile": None,
    },
}
