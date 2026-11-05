# Changelog

## Unreleased

### Security
- Lockfile integrity is enforced: a locked version whose integrity changed on the registry is blocked (`security.require_lockfile_match`).
- `install --frozen-lockfile` for CI: installs only what the lockfile pins.
- Downloads: https-only, host allowlist (re-checked on redirects), size cap, verified in a temp file and moved into place atomically, retries with backoff.
- Extraction: per-member extraction; rejects links, device files and FIFOs; file-count and size limits; strips setuid and world-writable bits.
- Package names and versions are validated before they reach paths, URLs or generated JavaScript; generated JS and HTML escape configured paths.
- The registry response must be for the requested package.
- The cache is only reused if the package was scanned by the current scanner; `--no-verify` installs are never trusted later.
- Scanner: no more silent skips (large files, `.cjs`, BOM or invalid UTF-8, parse errors now block); detects `Function()` without `new`, indirect eval, string timers, ESM and dynamic imports of Node built-ins; ignores CLI-only (`bin/`) files; single query pass and parallel scanning.
- OSV: real severities (GHSA label or CVSS v3 score), `fail_on_critical` now works, `allow_vulnerabilities`, `require_osv`, withdrawn advisories ignored.
- `security.allow`: reviewed, per-package exceptions to blocking findings.

### Fixed
- `install` exits non-zero when any package is blocked or fails.
- `update` actually updates (it was pinned to the locked version).
- npm range matching: partial versions (`3`, `3.x`), hyphen ranges, `||`, comparators, and custom dist-tags.
- ESM wrapper: `export` rewriting is node-local; named exports are kept.
- CJS wrapper no longer rewrites `Function('return this')()` into a `require`.
- Bundler fetches only the dependencies esbuild reports as unresolved.
- Loader exposes ESM bundles on `window`; Monaco worker labels map to the right worker.
- Empty lockfile no longer crashes install.

### Added
- Examples: lodash, chart.js, dayjs, markdown (marked + dompurify), papaparse, fuse.js, canvas-confetti, sortablejs, d3, three, highlight.js.
