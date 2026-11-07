# Changelog

All notable changes are listed here. The project follows [Semantic Versioning](https://semver.org/); while the version is 0.x, minor versions may change the command line or file formats.

## [0.1.0] - Unreleased

First release.

### Added
- Commands: `install`, `add`, `remove`, `update`, `list`, `info`, `search`, `doctor`, `clean`, and a Python API for each.
- `Use <package> from teloce-npm` declarations in `.vel` and `.html` files, and a `use()` function in the browser.
- Wrapping of IIFE, UMD, CommonJS and ES-module packages (Tree-sitter), and bundling through MinifyJS (esbuild), with CSS and font inlining and worker support (including Monaco).
- `teloce-npm.lock` with integrity hashes, and `install --frozen-lockfile` for CI.
- Security checks: SHA-512 integrity, install-script blocking, a code scanner, OSV vulnerability lookups, and a registry host allowlist.
- `security.allow`: reviewed, per-package exceptions to blocking findings. `security.allow_vulnerabilities` for reviewed advisory IDs.
- Download and extraction limits: `max_tarball_mb`, `max_unpacked_mb`, `max_files`.
- Twelve runnable examples (Monaco, Lodash, Chart.js, Day.js, marked + DOMPurify, PapaParse, Fuse.js, canvas-confetti, SortableJS, D3, Three.js, highlight.js) and full documentation.

### Security
- The lockfile is enforced: a locked version whose integrity changed on the registry is blocked (`security.require_lockfile_match`).
- Downloads: https-only, host allowlist (re-checked on every redirect), size cap, verified in a temporary file and moved into place atomically, retries with backoff.
- Extraction: per-member extraction; links, device files and FIFOs are rejected; file-count and size limits; setuid and world-writable bits are dropped.
- Package names and versions are validated before they reach paths, URLs or generated JavaScript; generated JS and HTML escape configured values.
- The registry's response must be for the package that was requested.
- The cache is only reused if the package was scanned by the current scanner; `--no-verify` installs are never trusted later, and the lockfile records `"scan_result": "skipped"` for them.
- Scanner: nothing is silently skipped (large files, `.cjs`, BOM or invalid UTF-8 and parse errors are covered or block); detects `Function()` with or without `new`, indirect `eval`, string timers, and ES and dynamic imports of Node built-ins; ignores CLI-only (`bin/`) files; scans in one pass and in parallel for large packages. Blocked-package messages name the file.
- OSV: real severities (advisory label or CVSS v3 score), a working `fail_on_critical`, `require_osv`, and withdrawn advisories are ignored.
- Bundler dependencies get the same checks as top-level packages and only packages esbuild reports as missing are fetched.

### Fixed
- `install` exits non-zero when any package is blocked or fails.
- `update` actually updates (it was pinned to the locked version), stays inside the range in `teloce-npm.json`, and reports blocked updates instead of counting them.
- `remove` removes config entries that carry a version (`lodash@^4`); `install` replaces an entry instead of adding a duplicate.
- npm range matching: partial versions (`3`, `3.x`), comparators, hyphen ranges, `||` and custom dist-tags.
- The ES-module wrapper rewrites only the `export` it is processing and keeps named exports.
- The CommonJS wrapper no longer turns `Function('return this')()` into a `require`, and a relative `require` now makes `auto` mode fall back to the bundler instead of producing code that receives `undefined`.
- The loader exposes ES bundles on `window`, and maps Monaco worker labels (`javascript`, `scss`, ...) to the right worker.
- `use()` finds scoped packages under both naming conventions (`_scope_pkg` and `scope_pkg`).
- HTML injection finds `</HEAD>` and `</body >` regardless of case.
- An empty `teloce-npm.lock` no longer crashes `install`.
- `teloce_npm.add(..., no_verify=True)` no longer raises; the Python helpers accept `project_root` and return the exit code.
- `doctor` shows non-boolean security settings as values instead of `[ON]`/`[OFF]`.
- A `Path | None` annotation that failed to import on Python 3.9.
