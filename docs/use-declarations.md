# `Use` declarations

A `Use` line tells Teloce-NPM which npm package a file needs. `use('name')` then gives you the package at runtime.

## Syntax

```
Use <package> from teloce-npm
```

```vel
Use lodash from teloce-npm
Use chart.js from teloce-npm
Use @popperjs/core from teloce-npm
```

Rules:

- The declaration must be the **only thing on its line**. Leading and trailing spaces are fine, trailing text such as a comment is not.
- `Use` and `from teloce-npm` are matched without regard to case.
- The package name is a normal npm name: letters, digits, `-`, `_`, `.`, and an optional `@scope/` prefix.
- One package per line. Put several `Use` lines at the top of the file.

### Versions

A `Use` line **cannot** contain a version or range. `Use lodash@4.17.21 from teloce-npm` is read as a package named `lodash@4.17.21`, which is blocked as an invalid name. Pin versions in one of these places instead:

```bash
teloce-npm install lodash@4.17.21        # records "lodash@4.17.21" in teloce-npm.json
```

```json
{ "packages": ["lodash@^4.17.0", "chart.js@4"] }
```

If a package appears both in a `Use` line and in `teloce-npm.json`, the version from `teloce-npm.json` wins. A package with no version resolves to the latest stable release, and the lockfile pins it from then on.

### Where files are scanned

`install` looks at every `.vel` and `.html` file in the project. These folders are skipped: `.git`, `.github`, `node_modules`, `dist`, `build`, `.venv`, `venv`, `__pycache__`, `.teloce-npm`, `.pytest_cache`, `.idea` and `.vscode`.

A line that does not match the syntax is ignored without a message, so a typo such as `Use lodash form teloce-npm` simply declares nothing. If `use('lodash')` returns `undefined`, check the declaration. A line that matches but names an invalid package is blocked when you run `install`.

## `use()` at runtime

`use(name)` is a global function that returns a loaded package.

```js
const _ = use('lodash');
const Chart = use('chart.js');
```

### Wait for `teloce-npm-ready`

Packages load asynchronously after the page starts. Until the loader finishes, `use()` cannot find them. It logs an error and returns `undefined`. The loader fires one event on `window` when it is done:

```js
window.addEventListener('teloce-npm-ready', () => {
  const dayjs = use('dayjs');
  // mount your app here
}, { once: true });
```

The example apps mount their `.vel` component from this event.

| Event | When |
| --- | --- |
| `teloce-npm-ready` | Every package has finished loading (or failed; failures are logged) |
| `teloce-npm-error` | The loader itself crashed. `event.detail` is the error |

If `manifest.json` cannot be loaded (for example a 404), the loader logs the problem and **no event fires**, so an app that waits for `teloce-npm-ready` never starts. See [Troubleshooting](troubleshooting.md#the-app-never-mounts).

### What `use()` returns

`use()` returns whatever the package exports:

| Package style | Example | `use()` gives you |
| --- | --- | --- |
| Single function or object | `dayjs`, `lodash`, `canvas-confetti` | That function or object |
| ES module with several exports | `marked`, `chart.js`, `d3`, `three` | An object of exports (`use('chart.js').Chart`) |
| ES module with only a default export | `fuse.js`, `sortablejs` | The default export itself |

When unsure, handle both shapes:

```js
const mod = use('fuse.js');
const Fuse = mod.default || mod.Fuse || mod;
```

### How names map to globals

Packages are stored on `window` under a safe name, and `use()` tries these in order:

1. The exact name: `window['lodash']`
2. The name with `@`, `/`, `-` and `.` replaced by `_`: `chart.js` becomes `chart_js`, `@scope/pkg` becomes `_scope_pkg`
3. The same without the leading `@`: `@scope/pkg` becomes `scope_pkg`

You normally never touch the globals directly. Use `use()`.

### Errors

`use()` logs a clear message and returns `undefined` when:

- the name is not a non-empty string;
- the package is declared but has not finished loading ("registered but not loaded yet");
- the package is unknown ("not found. Available packages: ...").

## Packages with CSS, fonts or workers

Bundled packages can bring CSS, fonts and web workers with them, and you do not need extra `<link>` tags. CSS and fonts are inlined into the package's JavaScript; workers are copied next to it. See [Wrapper formats](wrapper-formats.md#assets-css-fonts-and-workers).
