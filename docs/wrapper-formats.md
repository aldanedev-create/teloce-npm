# Wrapper formats and bundling

npm packages come in several module formats, and browsers cannot run most of them directly. Teloce-NPM turns each package into one file that the loader can `import()`, either by **wrapping** it or by **bundling** it.

## The two strategies

**Wrapping** is the lightweight route. The package source is parsed (with Tree-sitter), and wrapped in a small function that gives it a private scope and puts its exports on `window`. The code itself is not rewritten beyond what is needed. It works for self-contained packages: Day.js, Lodash, PapaParse, SortableJS and similar.

**Bundling** uses MinifyJS (esbuild). It follows `import`s, joins the package and its dependencies into one file, and can inline CSS and fonts. It is needed when a package imports other files or other npm packages, such as Chart.js, D3, Three.js, Monaco, marked and highlight.js.

## `bundling.mode`

| Mode | Behaviour |
| --- | --- |
| `auto` (default) | Try the wrapper. If the package cannot be wrapped, fall back to the bundler. |
| `always` | Bundle every package. Slower, but the most robust. |
| `never` | Wrapper only. A package that needs bundling fails with a clear error. |

If a package misbehaves in `auto` mode, try `"mode": "always"` first.

## Module formats the wrapper understands

The format is detected from the package's `package.json`, not by reading its code:

| `package.json` | Format |
| --- | --- |
| `"type": "module"`, or a `module` field | ES module |
| a `browser` field that is a string | UMD |
| `main` contains `umd` | UMD |
| `main` contains `iife` or `browser` | IIFE |
| anything else | CommonJS |

What the wrapper does for each:

| Format | What the wrapper does |
| --- | --- |
| **IIFE / browser global** | Runs the script in a closure. It expects the script to attach itself to `window`, and logs a warning if nothing appears under the package's safe name. |
| **UMD** | Gives the script a fake `module` and `exports`, which makes it take its CommonJS branch, then exposes `module.exports`. A UMD that sets a global instead keeps that global. |
| **CommonJS** | Gives the script a private `module` and `exports` and exposes `module.exports`. A `require('some-package')` is replaced by a lookup of that package's global, so the other package must be installed too (the loader loads dependencies first). |
| **ES module** | Rewrites each `export`. The default export becomes the package; named exports are attached to it as properties (or form the namespace object when there is no default). |

A single wrapped file cannot contain other files. These cases are therefore **not wrappable** and need the bundler:

- a CommonJS package that does `require('./other-file')`;
- an ES module that re-exports (`export * from`, `export { x } from`).

In `auto` mode the install falls back to the bundler for them automatically (you will see `[auto] Tree-sitter wrapper failed ... falling back to MinifyJS` in verbose output). In `never` mode the install fails with a message saying the package needs bundling.

## Which file is used

The entry point is the first of these that exists: `module`, `browser`, `main`, then `index.js`.

## What `use()` returns

The wrapped or bundled package ends up on `window` under a safe name (`chart.js` becomes `chart_js`), and `use('chart.js')` returns it. For bundled ES modules that is the **namespace object** (all exports), except when the module has only a default export, in which case it is that default. See [`use()` at runtime](use-declarations.md#use-at-runtime).

## Output files

Each package becomes one file in the output folder, named after the package (`dayjs.js`), or a folder of the same name when it is bundled with extra files (`chart_js/chart_js.js`). `manifest.json` records the exact path in `file`, and the [lockfile](lockfile.md) records it in `wrapped`.

`manifest.json` looks like this:

```json
{
  "manifest_version": "1.0.0",
  "generated_at": "2026-11-06T22:26:13+00:00",
  "base_path": "/static/teloce-npm",
  "total_size": 215001,
  "packages": {
    "chart.js": {
      "version": "4.6.1",
      "file": "chart_js.js",
      "size": 207347,
      "integrity": "sha512-...",
      "dependencies": { "@kurkle/color": "^0.3.0" },
      "workers": {}
    }
  }
}
```

## Dependencies when bundling

When a package imports another npm package, the bundler cannot resolve it from the single package folder. Teloce-NPM reads the "Could not resolve" messages, downloads exactly those packages (with the same integrity checks and [security scan](security.md) as top-level packages) and tries again, repeating for their own dependencies. Node built-ins such as `fs` are never fetched.

A dependency that trips the scanner needs its own `security.allow` entry. For D3 that is `d3-dsv`.

## Assets: CSS, fonts and workers

- **CSS.** `import "x.css"` in a package is turned into code that adds a `<style>` element when the package loads. `import styles from "x.css"` gives you the CSS text.
- **Fonts and images in CSS.** Local `url(...)` references are inlined as `data:` URLs, so nothing extra is requested.
- **Web workers.** Worker bundles shipped by a package (files with `worker` in the name under an `assets` folder) are copied to `workers/` next to the package and listed under `workers` in the manifest, by label (`editor`, `typescript`, `json`, `css`, `html`).
- **Monaco.** When `monaco-editor` is loaded, the loader sets `MonacoEnvironment.getWorkerUrl` for you. A language label that has no worker of its own maps to the one that serves it: `javascript` uses the `typescript` worker, `less` and `scss` use `css`, `handlebars` and `razor` use `html`.

Remote URLs in CSS are left alone.

## Packages that cannot be used

- Packages that need Node.js built-ins at runtime (`fs`, `child_process`, `net`, ...). The bundler reports the unresolved import.
- Packages whose entry point is TypeScript source or needs a build step that is not in the published tarball.
- Native add-ons (`.node` files).

For anything else, `bundling.mode: "always"` is worth a try. The [`examples/`](../examples/README.md) folder shows twelve packages that work.
