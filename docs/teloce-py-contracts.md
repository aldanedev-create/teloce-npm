# Teloce-Py Integration Contracts

Verified against the indexed Teloce-Py reference repository with Xerj.

## Public APIs

- `compile(source: str, filename: str = "<input>") -> dict` compiles in-memory `.vel` source.
- `compile_file(filepath: str | Path, **options) -> dict` compiles a file from disk.
- `build_project(root_dir, out_dir=None, options=None) -> dict` builds a project and raises `RuntimeError` when the result contains failed components.

## Build and runtime layout

- Authored components live under `static/` and are emitted under `dist/static/`.
- The standard shared runtime is emitted as `dist/static/teloce-runtime.js` (hashed in production builds).
- Generated component modules import the shared runtime.
- The HTML shell mounts a generated module with `mount("#app")`.
- `teloce.config.json` uses `build.out_dir`, `build.static_dir`, and `build.shared_runtime`; `build.clean` may remove the entire `dist/` tree before rebuilding.

## Teloce-NPM bridge

- Teloce-NPM keeps its public default output at `dist/static/teloce-npm` and derives `/static/teloce-npm` as its URL path.
- For the standard layout, installation also mirrors generated npm assets to `static/teloce-npm`. Teloce-Py then copies them into the cleaned `dist/static/teloce-npm` directory.
- Set Teloce-Py's `build.hash_assets` to `false` for projects using the injected npm runtime. The generated loader intentionally requests stable `loader.js`, `use.js`, and `manifest.json` URLs; hashing those files would make the injected URLs return 404.
- Runtime injection remains framework-agnostic and adds `loader.js` and `use.js` under the derived static URL. The entry HTML must still mount the Teloce-Py component at `#app`.
- `Use <package> from teloce-npm` declarations are discovered by Teloce-NPM's scanner; Teloce-Py can compile the component source independently.
- MinifyJS is a core Teloce-NPM dependency. `bundling.mode` defaults to `auto`: Tree-sitter is attempted first and the esbuild-backed MinifyJS backend is used when the static wrapper cannot process a package. Set `mode` to `always` for libraries with complex JavaScript module graphs.
- Lockfiles record the actual relative output path, including nested MinifyJS bundle paths.

Teloce-NPM preprocesses CSS imports in Python, inlines local font assets as data
URLs, copies worker bundles, and records worker URLs in the package manifest before
invoking MinifyJS. The generated loader exposes generic worker metadata and
automatically configures `MonacoEnvironment.getWorkerUrl` when `monaco-editor` is
loaded. `pdfjs-dist` and `monaco-editor` both install and build with their emitted
runtime assets available under the package output directory.

## Fixes applied

- Corrected SemVer 3.x validation and added npm-style `*`, `^`, and `~` range matching.
- Implemented the missing `teloce-npm clean` command.
- Preserved bundled output paths across lockfile writes and cache restores.
- Mirrored standard npm assets into Teloce-Py's source static tree so `build.clean` does not delete the integration.
