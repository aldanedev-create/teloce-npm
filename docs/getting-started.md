# Getting started

This walkthrough builds a page that shows today's date using [Day.js](https://day.js.org/), from an empty folder to a running app. Every command below was run as written.

## 1. Create the project

```
my-app/
  app.py
  teloce.config.json
  templates/
    index.html
  static/
    js/
      App.vel
```

### `static/js/App.vel`

The first line declares the package. `use('dayjs')` returns it at runtime.

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

<style>
body { font-family: system-ui, sans-serif; margin: 3rem; }
</style>
```

### `templates/index.html`

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>My app</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module">
      const start = async () => {
        const { mount } = await import("/static/js/App.js");
        mount("#app");
      };
      window.addEventListener("teloce-npm-ready", start, { once: true });
    </script>
  </body>
</html>
```

Packages load asynchronously, so the app waits for the `teloce-npm-ready` event before mounting. If you mount immediately, `use('dayjs')` returns `undefined`. See [`use()` at runtime](use-declarations.md#use-at-runtime).

### `teloce.config.json`

```json
{
  "build": {
    "out_dir": "dist",
    "static_dir": "static",
    "clean": true,
    "shared_runtime": true,
    "hash_assets": false
  }
}
```

`hash_assets` must be `false`. Hashed file names would break the fixed `loader.js` and `use.js` URLs that Teloce-NPM injects. See the [Teloce-Py contract](teloce-py-contracts.md).

### `app.py`

A small server that builds the project and serves it:

```python
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from teloce.build import build_project

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def do_GET(self):
        if self.path == "/":
            body = (ROOT / "templates" / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


if __name__ == "__main__":
    build_project(ROOT, out_dir=DIST, options={"clean": True, "shared_runtime": True})
    print("Running at http://127.0.0.1:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
```

## 2. Install the package

From the project folder:

```bash
teloce-npm install
```

```
[1/6] Scanning for packages...
  Found 1 package(s):
    - dayjs

[2/6] Installing packages...
    [DOWNLOADING] dayjs@1.11.23...
    [INSTALLED] dayjs@1.11.23

[3/6] Generating runtime files...

[4/6] Injecting scripts...

[5/6] Saving lockfile...

[6/6] Installation complete!
  1 package(s) installed
  Output: /path/to/my-app/dist/static/teloce-npm
```

What changed on disk:

| Path | What it is |
| --- | --- |
| `static/teloce-npm/` and `dist/static/teloce-npm/` | `loader.js`, `use.js`, `manifest.json` and the wrapped `dayjs.js` |
| `templates/index.html` | Two `<script>` tags added between `TELOCE-NPM-START` and `TELOCE-NPM-END` comments |
| `teloce-npm.lock` | The exact version and integrity hash. **Commit this file.** |
| `.teloce-npm/` | The download cache. Do not commit it. |

## 3. Run it

```bash
python app.py
```

Open <http://127.0.0.1:8000>. You should see the current date as a heading.

## 4. Add another package

```bash
teloce-npm install lodash@4.17.21
```

Lodash is blocked at first:

```
[BLOCKED] lodash: security checks failed
  - [HIGH] Package uses the Function() constructor, which can execute arbitrary code. (dynamic_function) in lodash.js
  - [HIGH] Package uses the Function() constructor, which can execute arbitrary code. (dynamic_function) in template.js
  If you have reviewed this package, allow exactly these findings with
  "security": {"allow": {"lodash": ["dynamic_function"]}} in teloce-npm.json
```

This is the security scanner doing its job. Lodash's `_.template` really does build code with `Function`. If you accept that, put the printed entry in `teloce-npm.json` and run the install again:

```json
{
  "packages": ["lodash@4.17.21"],
  "security": { "allow": { "lodash": ["dynamic_function"] } }
}
```

See [Security](security.md) for what the scanner looks for and how to review a finding.

## 5. Commit the right files

Commit: `teloce-npm.json`, `teloce-npm.lock`, your sources.

Ignore: `.teloce-npm/`, `dist/`, `static/teloce-npm/`.

```gitignore
.teloce-npm/
dist/
static/teloce-npm/
```

On a fresh checkout or in CI, run `teloce-npm install --frozen-lockfile` to get exactly the locked versions.

## Next steps

- [`Use` declarations](use-declarations.md): version pinning and runtime behaviour.
- [Configuration](configuration.md): bundling and security options.
- [Examples](../examples/README.md): Monaco, Chart.js, D3, Three.js and more.
