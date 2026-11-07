# Troubleshooting

First run `teloce-npm doctor`. It shows the paths in use, whether they exist, the lockfile status and the active settings. To see what is happening during an install, add `--verbose`.

## The app never mounts

Symptom: the page is blank and your code never runs.

1. Open the browser console. If the loader cannot load `manifest.json`, it logs `Could not load .../manifest.json. Have you run teloce-npm install?` and does **not** fire `teloce-npm-ready`, so an app that waits for the event never starts.
2. Check the Network tab. A 404 for `loader.js`, `use.js` or `manifest.json` means the files are not where the page expects them:
   - Is `build.hash_assets` set to `false` in `teloce.config.json`? Hashed file names break the fixed URLs. See the [contract](teloce-py-contracts.md).
   - Does `dist/static/teloce-npm/` exist after your build? With Teloce-Py's `build.clean`, the files are restored from `static/teloce-npm/`. Run `teloce-npm install` before the build.
   - Does `base_path` match the URL your server really uses?
3. If you changed Teloce-NPM or its templates, run `teloce-npm clean`, then `teloce-npm install`, then hard-refresh the browser (Ctrl+Shift+R) so it does not use a cached `loader.js`.

## `use()` returns `undefined`

The console says one of:

- **`registered but not loaded yet`**: you called `use()` before `teloce-npm-ready`. Wait for the event. See [`use()` at runtime](use-declarations.md#use-at-runtime).
- **`not found. Available packages: ...`**: the name is not installed. Check the `Use` line (it ignores typos without a message) and run `teloce-npm list`.
- **`Package "x" did not attach to window`**: an IIFE package did not set the global the wrapper expected. Try `"bundling": {"mode": "always"}`.

## The component mounts but the editor, chart or widget is empty

The package loaded but your code failed after `use()`. Look for a red error in the console. Common causes: the package exports an object and you treated it as a function, or the reverse. Print it with `console.log(use('name'))` to see its shape, and handle both: `const mod = use('x'); const Thing = mod.default || mod.Thing || mod;`.

## A package is blocked by the security scan

```
[BLOCKED] lodash: security checks failed
  - [HIGH] Package uses the Function() constructor, which can execute arbitrary code. (dynamic_function) in lodash.js
  - [HIGH] Package uses the Function() constructor, which can execute arbitrary code. (dynamic_function) in template.js
  If you have reviewed this package, allow exactly these findings with
  "security": {"allow": {"lodash": ["dynamic_function"]}} in teloce-npm.json
```

Decide whether the finding is acceptable for what the package does. If so, add the printed entry to `teloce-npm.json`. Avoid `--no-verify`. See [Security](security.md#allowing-reviewed-findings).

If the message names a **dependency** (`Dependency 'd3-dsv' failed security checks`), the package you asked for is fine but one it needs is not. Add an entry for that dependency name.

## `differs from the lockfile`

```
[BLOCKED] lodash@4.17.21: the registry's integrity hash differs from the lockfile.
```

The registry now serves different bytes for a version you locked. That can be a republished package or tampering. Investigate before continuing. If you trust the change, run `teloce-npm update` (or delete the entry from `teloce-npm.lock`) and review the new result. To turn the check off: `security.require_lockfile_match: false`.

## `not in the lockfile, and --frozen-lockfile forbids resolving new versions`

You ran `install --frozen-lockfile` for a package the lockfile does not list. Run `teloce-npm install` locally, commit the updated `teloce-npm.lock`, and try again.

## `Could not resolve "x"` while bundling

The bundler found an `import` it cannot follow.

- If `x` is an npm package, Teloce-NPM downloads it and retries automatically. You see `[DEPENDENCY] x@1.2.3`. If it still fails, that dependency may have been blocked by the scan (add a `security.allow` entry for it) or could not be downloaded (check the message above the error).
- If `x` is a Node.js built-in (`fs`, `path`, `child_process`, ...), the package expects Node.js and cannot run in the browser.

## `Tarball URL points at 'host', which is not an allowed registry host`

The registry told Teloce-NPM to download from a host you have not allowed. For a mirror or proxy that serves tarballs from a different host, add that host's URL to `security.allowed_registries`. Do this only for hosts you trust.

## `Registry URL must use https`

`registry` must be `https://`. `http://` is accepted only for `localhost` or a loopback address (a local mirror).

## `Integrity check failed`

The downloaded file does not match the hash the registry published. Teloce-NPM keeps nothing from a failed download. Retry once; if it persists, a proxy may be altering downloads, or the registry is serving a corrupt file. Do not work around it.

## `Tarball exceeds the ... byte limit` / `more than ... files`

A package is larger than the safety limits. If it is a legitimate large package, raise `security.max_tarball_mb`, `security.max_unpacked_mb` or `security.max_files`.

## `Could not query OSV ... Name or service not known`

The vulnerability database could not be reached (offline, firewall). By default this is a warning and the install continues. Set `security.require_osv: true` if you want it to fail instead, or `security.check_vulnerabilities: false` to skip the lookup.

## `[RESCAN]` on every install

A cached copy was not scanned by the current scanner (for example it was installed with `--no-verify`, or the scanner was upgraded). It is scanned once and cached again. If it repeats every time, the cache is being cleared: check that `.teloce-npm/` is not deleted between runs.

## The scan takes a long time

The first scan of a very large package (Monaco has about 1,600 JavaScript files, roughly 100 MB) takes tens of seconds on one core, less on several. The result is cached, so later installs are fast. To skip repeated work in CI, keep `.teloce-npm/` between runs.

## Styles in a `.vel` file are not applied

Teloce-Py passes CSS through unchanged and does not support `:global(...)`. A rule such as `:global(body) { ... }` is invalid CSS and the browser drops it. Write `body { ... }`. Component styles are not scoped, so they already apply globally.

## `ModuleNotFoundError: No module named 'teloce'`

The examples and your own `app.py` import Teloce-Py: `pip install teloce-py`.

## `OSError: [Errno 98] Address already in use`

The port your dev server wants is taken, usually by an earlier run that is still going. Stop it (`fuser -k 8000/tcp` on Linux) or pick another port.

## After upgrading Teloce-NPM nothing changed

`loader.js` and `use.js` are generated files. Run `teloce-npm clean` and `teloce-npm install` to regenerate them, then hard-refresh the browser.

## Still stuck?

Run with `--verbose` and look at the first error, not the last. Then open an issue with the command you ran, the output, `teloce-npm doctor`, and your `teloce-npm.json`.
