# Configuration

Teloce-NPM reads `teloce-npm.json` from the project folder (the folder you run the command in). The file is optional: without it every default below applies. `install <package>` creates it and keeps its `packages` list up to date.

```json
{
  "packages": ["lodash@4.17.21", "chart.js"],
  "entry_html": "templates/index.html",
  "security": {
    "allow": { "lodash": ["dynamic_function"] }
  },
  "bundling": { "mode": "auto" }
}
```

You only write the keys you want to change. `security` and `bundling` are merged key by key with their defaults. Every other key replaces its default. An invalid value stops the command with a message naming the key.

## Top-level options

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `packages` | list of strings | `[]` | Packages to install, as `name` or `name@version-or-range`. Combined with the packages found in `Use` lines; if a package is in both, this entry wins. |
| `entry_html` | string | `"templates/index.html"` | The one HTML file that gets the `<script>` tags. See [HTML injection](html-injection.md). |
| `output_dir` | string | `"dist/static/teloce-npm"` | Where `loader.js`, `use.js`, `manifest.json` and the packages are written. |
| `cache_dir` | string | `".teloce-npm/cache"` | Where downloads and extracted code are kept. See [Cache](cache.md). |
| `registry` | string | `"https://registry.npmjs.org"` | The npm registry. Must be `https://`; `http://` is accepted only for a local mirror on `localhost` or a loopback address. |
| `base_path` | string or `null` | `null` | The URL prefix the output folder is served under. When `null` it is derived from `output_dir`: `dist/static/teloce-npm` becomes `/static/teloce-npm`. |

Relative paths are relative to the project folder.

### Where files end up

With the default layout Teloce-NPM writes to `dist/static/teloce-npm/` and also mirrors the files to `static/teloce-npm/`, because Teloce-Py's `build.clean` deletes `dist/` before each build and copies `static/` back in. See the [Teloce-Py contract](teloce-py-contracts.md).

## `security`

The full explanation of each setting is in [Security](security.md).

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `scan_malware` | boolean | `true` | Scan package code for dangerous patterns |
| `block_install_scripts` | boolean | `true` | Block packages that declare `preinstall`/`postinstall` scripts (they are never run either way) |
| `check_vulnerabilities` | boolean | `true` | Look up packages in the OSV database |
| `fail_on_critical` | boolean | `true` | Block a package that has a CRITICAL advisory |
| `allow_vulnerabilities` | list of strings | `[]` | Advisory IDs you have reviewed, for example `["GHSA-xxxx-xxxx-xxxx"]` |
| `require_osv` | boolean | `false` | Fail the install when OSV cannot be reached (otherwise it only warns) |
| `require_lockfile_match` | boolean | `true` | Block when a locked version's integrity differs from the registry |
| `allowed_registries` | list of strings | `["https://registry.npmjs.org"]` | Hosts tarballs may be downloaded from. The configured `registry` is always allowed too |
| `block_unknown_domains` | boolean | `true` | Enforce `allowed_registries` |
| `max_tarball_mb` | integer | `100` | Largest download |
| `max_unpacked_mb` | integer | `500` | Largest unpacked size, for a whole tarball and for any single file |
| `max_files` | integer | `50000` | Most files in one tarball |
| `allow` | object | `{}` | Reviewed exceptions: `{"package": ["finding_type"]}` |
| `verify_integrity` | boolean | `true` | Reserved. Integrity is always verified; changing this has no effect |

## `bundling`

Bundling uses [MinifyJS](https://pypi.org/project/minifyjs/), which wraps esbuild. See [Wrapper formats](wrapper-formats.md) for when it is used.

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `mode` | `"auto"`, `"always"`, `"never"` | `"auto"` | `auto` tries the static wrapper first and falls back to the bundler. `always` bundles every package. `never` only uses the static wrapper. |
| `minify` | boolean | `true` | Compress and mangle the output |
| `target` | string | `"es2020"` | JavaScript syntax level of the output |
| `format` | `"esm"`, `"cjs"`, `"iife"` | `"esm"` | Output module format. The loader expects `esm` |
| `platform` | `"browser"`, `"node"`, `"neutral"` | `"browser"` | Target platform |
| `sourcemap` | `null`, `"inline"`, `"external"`, `"both"` | `null` | Source map output |
| `splitting` | boolean | `false` | Code splitting (needs `format: "esm"`) |
| `tree_shaking` | boolean | `true` | Remove unused code |
| `packages` | `"bundle"` or `"external"` | `"bundle"` | Bundle dependencies, or leave them as imports |
| `external` | list of strings | `[]` | Modules to leave out of the bundle |
| `define` | object | `{}` | Compile-time replacements, for example `{"process.env.NODE_ENV": "\"production\""}` |
| `drop` | list of strings | `[]` | Statements to remove (for example `"console"`) |
| `charset` | string | `"utf8"` | Output character set |
| `legal_comments` | string or `null` | `null` | How to keep license comments |
| `entry_names`, `chunk_names`, `asset_names` | string or `null` | `null` | Output file name patterns |
| `metafile` | string or `null` | `null` | Write build metadata |

Most projects never change these. The usual reason to touch `bundling` is `"mode": "always"` for a package that the static wrapper handles badly.

## Examples

A project that pins one package, allows one reviewed finding and bundles everything:

```json
{
  "packages": ["d3@^7"],
  "security": {
    "allow": { "d3": ["dynamic_function"], "d3-dsv": ["dynamic_function"] }
  },
  "bundling": { "mode": "always", "minify": true }
}
```

A project served from a sub-path:

```json
{
  "output_dir": "public/vendor/teloce-npm",
  "base_path": "/assets/vendor/teloce-npm"
}
```

A local mirror (for example Verdaccio) for offline or air-gapped use:

```json
{ "registry": "http://localhost:4873" }
```

## Environment

There are no Teloce-NPM environment variables. Network behaviour follows `requests`: `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY` and `REQUESTS_CA_BUNDLE` are honoured.
