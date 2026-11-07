# Commands

```
teloce-npm [-h] [-v] <command> ...
```

Run commands from your project folder. `-v` / `--version` prints the version.

**Exit codes.** `0` success. `1` failure: an error, a blocked or failed package, or nothing to do for a command that needs input. `130` interrupted with Ctrl+C.

## `install`

```
teloce-npm install [--verbose] [--no-verify] [--frozen-lockfile] [packages ...]
```

**With no arguments** it scans your `.vel` and `.html` files for [`Use` declarations](use-declarations.md), adds the packages listed in `teloce-npm.json`, installs everything, regenerates the runtime files, injects the script tags and saves the lockfile. This is the command to run in a build.

**With package arguments** it installs those packages and records them in `teloce-npm.json`:

```bash
teloce-npm install lodash                # latest
teloce-npm install lodash@4.17.21        # exact version
teloce-npm install "lodash@^4.17.0"      # range
teloce-npm install dayjs chart.js        # several
```

Installing a package that is already listed replaces its entry, so there is never more than one entry per package.

| Option | Meaning |
| --- | --- |
| `--verbose` | Show detailed output |
| `--no-verify` | Skip the code scan and the vulnerability lookup. **Dangerous.** Integrity is still verified. The lockfile records `"scan_result": "skipped"` and the cache will not be trusted by a later normal install. Prefer [`security.allow`](security.md#allowing-reviewed-findings). |
| `--frozen-lockfile` | CI mode: install only what the lockfile pins. Fails if a package is missing from the lockfile or its integrity changed. Never resolves new versions. |
| `--production` | Accepted for compatibility. It currently has no effect. |

If any package is blocked or fails, the others are still installed but the command exits with `1` and lists what failed.

Typical output:

```
[1/6] Scanning for packages...
  Found 1 package(s):
    - dayjs

[2/6] Installing packages...
    [DOWNLOADING] dayjs@1.11.23...
    [INSTALLED] dayjs@1.11.23
...
[6/6] Installation complete!
  1 package(s) installed
```

Status tags you may see: `[DOWNLOADING]`, `[INSTALLED]`, `[CACHED]` (reused from the cache), `[RESCAN]` (a cached copy was not scanned by the current scanner), `[DEPENDENCY]` (an npm dependency fetched for bundling), `[ALLOWED]` (findings permitted by `security.allow`), `[VULN]`, `[VULN-ALLOWED]`, `[BLOCKED]`, `[ERROR]`.

## `add`

```
teloce-npm add [--no-verify] [--verbose] <package>
```

An alias for `install <package>`.

## `remove`

```
teloce-npm remove <package>
```

Removes the package from the cache, the output folder, the lockfile, the manifest and `teloce-npm.json` (whatever version or range is written there). When the last package is removed, the script tags are taken out of your HTML.

## `update`

```
teloce-npm update [package]
```

Looks for a newer version of every installed package (or just the one named), downloads it, runs the security checks and updates the outputs and the lockfile.

- A package written with a range in `teloce-npm.json` stays inside that range: `d3@^7` moves to the newest 7.x and never to 8.
- A package with no range moves to the registry's latest version.
- An exact pin (`lodash@4.17.21`) never moves.
- If the newer version is blocked or fails, the old version stays locked, the command prints `[FAILED]` and exits with `1`.

## `list`

```
teloce-npm list
```

```
Installed packages:

  chart.js@4.6.1  (202.5 KB, chart_js.js)
  dayjs@1.11.23  (7.5 KB, dayjs.js)

Total: 2 package(s), 210.0 KB
```

## `info`

```
teloce-npm info <package>
```

Shows the registry's latest version, description, tarball URL, integrity hash, dependencies and any install scripts:

```
dayjs@1.11.23
  Description: 2KB immutable date time library alternative to Moment.js with the same modern API
  Tarball:     https://registry.npmjs.org/dayjs/-/dayjs-1.11.23.tgz
  Integrity:   sha512-QDTCU0M0MxR3hQfnlDJfwekQiaanm1ubO...
  Dependencies: none
  Install scripts: none
```

## `search`

```
teloce-npm search <query>
```

Searches the registry and prints name, version and description of the matches.

## `doctor`

```
teloce-npm doctor
```

Prints the Python and Teloce-NPM versions, the registry, the resolved paths (entry HTML, output folder, cache, base path) and whether they exist, a lockfile verification report, the cached packages and the active security settings. Settings that are on or off show as `[ON ]` / `[OFF]`; the others show their value. Run it first when something does not work.

## `clean`

```
teloce-npm clean
```

Removes the cache, the output folder, the manifest, the lockfile and the injected script tags. It keeps `teloce-npm.json` and your sources. Run `install` afterwards to rebuild. Use it after upgrading Teloce-NPM so the runtime files are regenerated.
