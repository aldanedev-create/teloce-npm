# Teloce-NPM

Use npm packages in [Teloce](https://pypi.org/project/teloce-py/) `.vel` files **without Node.js and without `node_modules`**.

```vel
Use dayjs from teloce-npm

<script>
export default {
  data() { return { today: use('dayjs')().format('dddd, MMMM D') }; }
};
</script>

<template>
  <h1>{{ today }}</h1>
</template>
```

```bash
teloce-npm install     # finds the Use line, downloads dayjs, wraps it, wires up your HTML
```

That is the whole workflow: declare what you need, run one command, call `use('name')`.

## How it works

1. **Scan.** `teloce-npm install` reads your `.vel` and `.html` files for `Use <package> from teloce-npm` lines.
2. **Download.** Each package is fetched from the npm registry as a tarball and verified against its SHA-512 integrity hash.
3. **Check.** The package is scanned for dangerous code and looked up in the OSV vulnerability database.
4. **Wrap or bundle.** Plain scripts are wrapped so they expose a browser global. Packages that need it (ES modules with imports, CSS, fonts, workers, npm dependencies) are bundled with [MinifyJS](https://pypi.org/project/minifyjs/), an esbuild-based bundler for Python.
5. **Generate.** `loader.js`, `use.js` and `manifest.json` are written next to your static files, and two `<script>` tags are injected into your HTML.
6. **Run.** In the browser the loader loads every package and fires a `teloce-npm-ready` event. After that, `use('name')` returns the package.

Everything is plain Python plus a bundled esbuild. Nothing needs Node.js at build time or at runtime.

## Quick start

```bash
pip install "teloce-npm @ git+https://github.com/aldanedev-create/teloce-npm.git"
pip install teloce-py            # compiles .vel files (see docs/installation.md)
```

Create `templates/index.html` and `static/js/App.vel` as shown in the [Getting started](docs/getting-started.md) guide, then:

```bash
teloce-npm install
```

Add or remove packages at any time:

```bash
teloce-npm install lodash@4.17.21     # install and record in teloce-npm.json
teloce-npm remove lodash
teloce-npm list
teloce-npm doctor
```

## What you get

- **No Node.js.** Pure Python. Works in a plain Python container or CI job.
- **Reproducible.** `teloce-npm.lock` pins every version and integrity hash. `install --frozen-lockfile` is built for CI.
- **Secure by default.** Integrity checks, a code scanner, vulnerability lookups, download and extraction limits, and a registry host allowlist. See [Security](docs/security.md).
- **Works with real libraries.** Tested with Monaco, Chart.js, D3, Three.js, Lodash, Day.js, marked + DOMPurify, PapaParse, Fuse.js, canvas-confetti, SortableJS and highlight.js. See [`examples/`](examples/).
- **Small runtime.** The browser side is two small generated files.

## Commands

| Command | What it does |
| --- | --- |
| `teloce-npm install [pkg ...]` | Install everything declared in your files, or specific packages |
| `teloce-npm add <pkg>` | Alias for `install <pkg>` |
| `teloce-npm remove <pkg>` | Remove a package and its generated files |
| `teloce-npm update [pkg]` | Move to newer versions within your configured ranges |
| `teloce-npm list` | Show installed packages |
| `teloce-npm info <pkg>` | Show registry information about a package |
| `teloce-npm search <term>` | Search the registry |
| `teloce-npm doctor` | Check your setup |
| `teloce-npm clean` | Remove the cache, generated files and lockfile |

Full reference: [Commands](docs/commands.md).

## Documentation

| Guide | |
| --- | --- |
| [Installation](docs/installation.md) | Requirements and setup |
| [Getting started](docs/getting-started.md) | A complete walkthrough |
| [`Use` declarations](docs/use-declarations.md) | The syntax and `use()` at runtime |
| [Configuration](docs/configuration.md) | Every `teloce-npm.json` option |
| [Commands](docs/commands.md) | CLI reference |
| [Security](docs/security.md) | What is checked and how to configure it |
| [Wrapper formats](docs/wrapper-formats.md) | How packages are wrapped or bundled |
| [Lockfile](docs/lockfile.md) | `teloce-npm.lock` |
| [Cache](docs/cache.md) | `.teloce-npm/` |
| [HTML injection](docs/html-injection.md) | How the script tags are added |
| [FAQ](docs/faq.md) | Common questions |
| [Troubleshooting](docs/troubleshooting.md) | Fixing problems |
| [Python API](docs/api/commands.md) | Using Teloce-NPM from Python |
| [Teloce-Py contract](docs/teloce-py-contracts.md) | How it fits with the Teloce build |
| [Examples](examples/README.md) | Twelve runnable apps |

## Status

Version 0.1.0. The command line and the file formats may still change before 1.0. Not yet published to PyPI; install from GitHub.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues: see the section there.

## License

MIT. See [LICENSE](LICENSE).
