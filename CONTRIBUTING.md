# Contributing

Thanks for helping. This guide covers setting up, running the checks, and where things live.

## Development setup

```bash
git clone https://github.com/aldanedev-create/teloce-npm.git
cd teloce-npm
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Python 3.9 or newer is required. Do not use syntax that needs a newer version in code that runs at import time (for example `X | None` in a function signature; use `Optional[X]`).

## Running the checks

```bash
pytest                               # the full test suite
pytest tests/security -q             # one area
ruff check src tests                 # lint
black --check src tests              # formatting (line length 100)
mypy src                             # types
```

Run all of them before opening a pull request. `python scripts/preflight.py --fast` runs the release checks without the slow steps.

The test suite is offline: network calls are mocked. Tests that run generated JavaScript use Node.js and are skipped if `node` is not installed.

## Project layout

```
src/teloce_npm/
  __main__.py        CLI entry point (argparse)
  commands/          one class per command (install, add, remove, update, ...)
  config/            defaults, loading, validation
  scanner/           finds `Use ... from teloce-npm` declarations
  registry/          npm registry client, version ranges, metadata
  downloader/        tarball download and safe extraction
  security/          integrity, install scripts, code scanner, OSV, name/URL validation
  wrapper/           wraps plain scripts (IIFE, UMD, CommonJS, ES modules)
  bundler/           MinifyJS bundling for packages that need it
  cache/             .teloce-npm cache storage and manager
  lockfile/          teloce-npm.lock reading, writing, verifying
  generator/         loader.js, use.js and manifest.json (templates in generator/templates)
  injector/          adds and removes the <script> tags in HTML
  adapters/          where output files go for a given project layout
tests/               mirrors src/; tests/integration runs whole flows offline
examples/            twelve runnable apps
docs/                documentation
```

## Making a change

1. Write a failing test first when fixing a bug. Put it next to the existing tests for that area.
2. Keep changes small and focused. Update the docs and `CHANGELOG.md` when behaviour changes.
3. Make sure `pytest`, `ruff`, `black` and `mypy` pass.

### Adding a command

Create a class in `src/teloce_npm/commands/` that extends `BaseCommand` and implements `execute(...)` returning an `int` exit code (0 means success). Register it in `__main__.py`, add a helper in `__init__.py` if it should be part of the Python API, and add tests under `tests/commands/`.

### Adding a scanner rule

Rules live in `security/malware_scanner.py`. Patterns are part of one Tree-sitter query (`_SCAN_QUERY`) so the code is parsed and walked once. Add the pattern, report it with a finding `type`, add that type to the list in `docs/security.md`, and bump `SCANNER_VERSION` so cached packages are scanned again. Add both a "flagged" and a "not flagged" test in `tests/security/test_scanner_hardening.py`.

### Changing the generated runtime

`loader.js` and `use.js` are generated from `src/teloce_npm/generator/templates/`. Both templates are typed with JSDoc. After editing, check them with TypeScript:

```bash
# render the templates, then:
npx tsc --allowJs --checkJs --noEmit --target es2020 --lib es2020,dom loader.js use.js
```

Placeholders such as `${manifest_url}` use `string.Template`, so avoid a stray `$` in the templates.

### Adding an example

Copy an existing folder in `examples/`, change `teloce-npm.json`, `static/js/App.vel` and the port in `app.py`, run `teloce-npm install` and load it in a browser. Examples must install with the security scan **on**; if a package needs `security.allow`, review why and say so in the example's README.

## Releasing

```bash
python scripts/preflight.py          # checks the repo is releasable
python scripts/publish.py            # build, check, upload, tag
```

Preflight needs a `## [x.y.z]` entry in `CHANGELOG.md` for the version in `pyproject.toml` and `src/teloce_npm/version.py`.

## Reporting security issues

Please do not open a public issue for a vulnerability. Use GitHub's private vulnerability reporting on the repository (Security tab), or contact the maintainers directly. Include what you found, how to reproduce it, and the version.
