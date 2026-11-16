# Teloce-NPM

Use npm packages in **plain HTML, CSS and JavaScript** or in [Teloce](https://pypi.org/project/teloce-py/) components, **without Node.js and without `node_modules`**.


```html
<!-- index.html -->
<head>
  <!--
  Use dayjs from teloce-npm
  -->
</head>
<body>
  <p id="today"></p>
  <script type="module">
    await use.ready;
    document.getElementById("today").textContent = use("dayjs")().format("dddd, MMMM D");
  </script>
</body>
```

```bash
pip install teloce-npm
teloce-npm install     # finds the Use line, downloads dayjs, wraps it, wires up your HTML
```

That is the whole workflow: declare what you need, run one command, call `use('name')`. The same works in Teloce components (`.vel` and `.html`), in [Flaxon](docs/teloce/flaxon.md) apps and with [server-side rendering](docs/teloce/ssr.md).

## How it works

1. **Scan.** `teloce-npm install` reads your `.html` and `.vel` files for `Use <package> from teloce-npm` lines.
2. **Download.** Each package is fetched from the npm registry and verified against its SHA-512 integrity hash.
3. **Check.** The package is scanned for dangerous code and looked up in the OSV vulnerability database.
4. **Wrap or bundle.** Plain scripts are wrapped so they expose a browser global. Packages that need it (ES modules with imports, CSS, fonts, workers, npm dependencies) are bundled with [MinifyJS](https://pypi.org/project/minifyjs/), an esbuild-based bundler for Python.
5. **Generate.** `loader.js`, `use.js` and `manifest.json` are written next to your static files, and two `<script>` tags are added to your page.
6. **Run.** In the browser the loader loads every package. `await use.ready` waits for it, and `use('name')` returns the package.

Everything is plain Python plus a bundled esbuild. Nothing needs Node.js at build time or at runtime.

## Quick start

```bash
pip install teloce-npm
```

- **Plain HTML, CSS and JavaScript:** follow [the guide](docs/guide/plain-html.md). Three files and any static server.
- **Teloce project:** follow [the walkthrough](docs/guide/getting-started.md) (also `pip install teloce-py`).
- **Flaxon:** [Using Teloce-NPM with Flaxon](docs/teloce/flaxon.md).

Add or remove packages at any time:

```bash
teloce-npm install lodash@4.17.21     # install and record in teloce-npm.json
teloce-npm remove lodash
teloce-npm list
teloce-npm doctor
```

## What you get

- **No Node.js.** Pure Python. Works in a plain Python container or CI job.
- **Plain HTML or Teloce.** No framework required.
- **Reproducible.** `teloce-npm.lock` pins every version and integrity hash. `install --frozen-lockfile` is built for CI.
- **Secure by default.** Integrity checks, a code scanner, vulnerability lookups, download and extraction limits, and a registry host allowlist. See [Security](docs/guide/security.md).
- **Works with real libraries.** Tested with Monaco, Chart.js, D3, Three.js, Lodash, Day.js, marked + DOMPurify, PapaParse, Fuse.js, canvas-confetti, SortableJS, highlight.js and Supabase. See [`examples/`](examples/).
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

Full reference: [Commands](docs/reference/commands.md).

## Documentation

The docs are a [VitePress](https://vitepress.dev) site in [`docs/`](docs/). The Markdown reads fine on GitHub too.

| Guide | |
| --- | --- |
| [Introduction](docs/guide/introduction.md) | What it is and how it works |
| [Installation](docs/guide/installation.md) | Requirements and setup |
| [Plain HTML, CSS and JavaScript](docs/guide/plain-html.md) | No framework needed |
| [A Teloce project](docs/guide/getting-started.md) | A complete walkthrough |
| [`Use` declarations](docs/guide/use-declarations.md) | The syntax |
| [Runtime API](docs/reference/runtime.md) | `use()`, `use.ready` and events |
| [Configuration](docs/reference/configuration.md) | Every `teloce-npm.json` option |
| [Security](docs/guide/security.md) | What is checked and how to configure it |
| [Teloce, Flaxon and SSR](docs/teloce/index.md) | Using it with the Teloce ecosystem |
| [FAQ](docs/guide/faq.md) and [Troubleshooting](docs/guide/troubleshooting.md) | Help |
| [Examples](examples/README.md) | Fourteen runnable apps |

## Status

Version 0.1.0. The command line and the file formats may still change before 1.0.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues: see the section there.

## License

MIT. See [LICENSE](LICENSE).
