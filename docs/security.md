# Security

Teloce-NPM downloads code from npm and runs it in your users' browsers, so every
step between the registry and your page is checked. This page describes what is
enforced and how to configure it (`security` block of `teloce-npm.json`).

## What is checked

| Stage | Protection |
| --- | --- |
| Names and versions | Package names and versions are validated before they reach file paths, URLs or generated JavaScript. Names found by the bundler (from package code) are validated too. |
| Registry | https only (http only for a loopback mirror), retries with backoff, and the response must be for the package that was requested. |
| Download | Tarball URL must be https on an allowed host, re-checked on every redirect. Size is capped. The file is verified (SHA-512) in a temporary file and moved into place only if it matches. |
| Extraction | Members are extracted one by one. Links, device files and FIFOs are rejected, paths cannot leave the target, setuid/world-writable bits are dropped, and file count and size are limited (decompression bombs). |
| Lockfile | A locked version must still have the recorded integrity. If the registry now serves different bytes, the install is blocked. |
| Code scan | Tree-sitter scan of every `.js`/`.mjs`/`.cjs` file, in one pass, in parallel for large packages. See below. |
| Vulnerabilities | OSV lookup. A **CRITICAL** advisory blocks the install. |
| Cache | A cached package is reused only if it was scanned by the current scanner. An install made with `--no-verify` is never trusted by a later normal install. |
| Exit code | If any package is blocked or fails, `install` exits non-zero. |
| Updates | `update` stays inside the range in `teloce-npm.json`, runs the same checks, and keeps the old locked version if the new one is blocked. |
| Audit trail | `teloce-npm.lock` records `"scan_result": "clean"` or `"skipped"` (for `--no-verify`) for every package. `teloce-npm doctor` shows the active settings. |

### What the code scan looks for

`eval` (direct, indirect, `window.eval`), `Function(...)` with or without `new`,
`setTimeout`/`setInterval` with a string, Node built-ins (`fs`, `child_process`,
`net`, ...) via `require`, `import`, `export ... from` and `import()`,
`process.env`, install scripts, and high-entropy (obfuscated) code.

- `Function("return this")()` (the global-object idiom) is not reported.
- Node built-ins are not reported in CLI-only files: those under `bin/` and those
  named in package.json's `bin` field.
- A file the scanner cannot inspect (over 32 MB, or a scanner error) **blocks**
  the install. It never passes silently.

The scan is static analysis. It raises the cost of an attack but does not prove a
package is safe: review what you depend on, and keep the lockfile in version control.

## Allowing reviewed findings

Real libraries trip the scanner: lodash's `_.template` compiles code with
`Function`, `d3-dsv` builds parsers with `new Function`, and `monaco-editor`
ships an AMD loader and the TypeScript compiler. Instead of disabling every
check with `--no-verify`, allow specific finding types for that one package:

```json
{
  "packages": ["d3"],
  "security": {
    "allow": {
      "d3": ["dynamic_function"],
      "d3-dsv": ["dynamic_function"]
    }
  }
}
```

- Finding types: `dynamic_function`, `eval_usage`, `dangerous_module`,
  `process_env_access`, `high_entropy`, `install_script`, `unscanned_file`, `scan_error`.
- An entry applies only to the named package and only to the listed types.
- Allowed findings are printed during install (`[ALLOWED] ...`).
- A blocked install prints each finding with the file it was found in (`... (dynamic_function) in lib/template.js`) and the exact entry to add once you have reviewed the package.
- Dependencies pulled in for bundling need their own entry (for example `d3-dsv`).

## Vulnerabilities

```json
{ "security": { "allow_vulnerabilities": ["GHSA-xxxx-xxxx-xxxx"] } }
```

`allow_vulnerabilities` lists advisory IDs you have reviewed. Set
`"fail_on_critical": false` to only warn, `"check_vulnerabilities": false` to skip
the lookup, or `"require_osv": true` to fail when OSV cannot be reached
(the default is to warn and continue).

## Reproducible, locked installs (CI)

```bash
teloce-npm install --frozen-lockfile
```

Installs only what the lockfile pins. It fails if a package is missing from the
lockfile or its integrity changed, and never resolves a new version. Use
`teloce-npm update` to deliberately move to a new version.

## Limits and registries

| Setting | Default | Meaning |
| --- | --- | --- |
| `max_tarball_mb` | 100 | Largest download |
| `max_unpacked_mb` | 500 | Largest unpacked size, per tarball and per file |
| `max_files` | 50000 | Most files in one tarball |
| `allowed_registries` | `["https://registry.npmjs.org"]` | Hosts tarballs may come from (the configured `registry` is always allowed) |
| `block_unknown_domains` | `true` | Enforce the host list |
| `require_lockfile_match` | `true` | Block when a locked version's integrity changed |
