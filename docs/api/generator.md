# Python API: generator

`teloce_npm.generator` creates the three files the browser needs. `install` calls it for you; use it directly to build your own tooling.

```python
from pathlib import Path
from teloce_npm.generator import generate_all

packages = [
    {
        "name": "dayjs",
        "version": "1.11.23",
        "file": "dayjs.js",                 # relative to the output folder
        "size": 7700,
        "integrity": "sha512-...",
        "dependencies": {},
        "workers": {},
    }
]

paths = generate_all(packages, Path("dist/static/teloce-npm"), base_path="/static/teloce-npm")
# {"loader": Path(".../loader.js"), "use": Path(".../use.js"), "manifest": Path(".../manifest.json")}
```

## Functions

| Function | Returns |
| --- | --- |
| `generate_all(packages, output_dir, base_path="/static/teloce-npm")` | Writes all three files; returns a dict of their paths |
| `generate_loader_js(base_path="/static/teloce-npm", manifest_url=None)` | The text of `loader.js` |
| `generate_use_js(packages)` | The text of `use.js` |
| `generate_manifest(packages, base_path="/static/teloce-npm")` | The text of `manifest.json` |
| `write_loader_js(output_dir, base_path=..., manifest_url=None)` | Writes `loader.js`; returns its path |
| `write_use_js(packages, output_dir)` | Writes `use.js`; returns its path |
| `write_manifest(packages, output_dir, base_path=...)` | Writes `manifest.json`; returns its path |

`manifest_url` defaults to `<base_path>/manifest.json`.

## Package dictionaries

Each entry in `packages` has: `name`, `version`, `file`, `size`, `integrity`, and optionally `dependencies` (name to range) and `workers` (label to relative path).

## Safe by construction

The generator writes configured values into JavaScript as JSON string literals, so a quote, backslash or line break in `base_path`, a package name or a version cannot break out of the string.

## The templates

The browser code is generated from `src/teloce_npm/generator/templates/loader.js.tmpl` and `use.js.tmpl`, which use `string.Template` placeholders (`${manifest_url}`, `${base_path}`, `${available_packages}`). Both are typed with JSDoc and can be checked with `tsc --allowJs --checkJs` (see [CONTRIBUTING](../../CONTRIBUTING.md)).

## Runtime behaviour

`loader.js` loads the packages in the manifest in dependency order, detects dependency cycles, and logs a clear message for a package that fails to load. When a package is an ES module bundle it assigns the module's exports to a global named after the package (`chart.js` becomes `window.chart_js`). It configures Monaco's worker URLs when `monaco-editor` is present. At the end it dispatches `teloce-npm-ready`. If the loader itself throws, it dispatches `teloce-npm-error` with the error in `event.detail`.

`use.js` defines `window.use(name)`. See [`use()` at runtime](../use-declarations.md#use-at-runtime).
