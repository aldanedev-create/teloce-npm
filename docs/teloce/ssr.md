# Server-side rendering and hydration

<Badge type="tip" text="Teloce-Py 0.3+" />

Teloce-Py can render a component to HTML on the server and then **hydrate** it in the browser. This page shows how npm packages fit in.

## The rule

Server-side rendering never runs your component's JavaScript. It does not call `data()`, methods or lifecycle hooks. It renders the template from the values you pass in. So:

- **Packages are browser-only.** Use them in `mounted()`, which runs in the browser during hydration.
- **Do not call `use()` in `data()`, in computed values or in templates** of an SSR component. There is no `use()` on the server.
- **Pass every field the template needs** as server data. A package can then add to the page after it loads.

## How the pieces fit

1. The server renders HTML from your component and sends it, with the Teloce-NPM script tags in `<head>`.
2. The browser shows the HTML immediately.
3. The loader fetches the packages. Hydration attaches your component to the existing HTML.
4. `mounted()` runs, waits for `use.ready`, and then uses the package.

## The component

```html [ui/App.html]
Use dayjs from teloce-npm

<template>
  <main class="page">
    <h1>{{ title }}</h1>
    <p v-if="renderedAt" id="rendered-at">Hydrated in your browser at {{ renderedAt }}</p>
    <ul>
      <li v-for="(item, index) in items" :key="item.id">{{ index + 1 }}. {{ item.label }}</li>
    </ul>
  </main>
</template>

<script>
export default {
  data() {
    return { title: "Server-rendered Python UI", items: [], renderedAt: "" };
  },
  async mounted() {
    await use.ready;                 // browser only, after hydration
    this.renderedAt = use("dayjs")().format("HH:mm:ss");
  }
};
</script>
```

`renderedAt` starts empty, so the server renders without the line. The browser fills it in.

## Configure Teloce-NPM

A server that builds its own page has no HTML file to inject into:

```json [teloce-npm.json]
{
  "entry_html": null,
  "output_dir": "public/teloce-npm",
  "base_path": "/teloce-npm"
}
```

```bash
teloce-npm install
```

## The host

This is the part of Teloce-Py's `ssr-python` example that changes. Teloce-NPM provides `generate_script_tags` for hosts that build the page in Python:

```python [app.py]
from teloce.build import build_project
from teloce.server import Renderer, SSRRequest
from teloce_npm.injector import generate_script_tags

NPM_DIR = ROOT / "public" / "teloce-npm"      # written by `teloce-npm install`


def build() -> Renderer:
    build_project(
        ROOT,
        DIST,
        options={
            "html_mode": True,
            "source_roots": ["ui"],           # scan only your components
            "ssr": True,
            "ssr_entries": ["ui/App.html"],
            "clean": True,
            # ... your other options
        },
    )
    return Renderer(DIST, cache_size=32)


def page(renderer: Renderer, request_path: str) -> bytes:
    result = renderer.render(
        "ui/App.html",
        {"title": "Server-rendered Python UI", "renderedAt": "",
         "items": [{"id": "python", "label": "No Node.js required"}]},
        request=SSRRequest(path=request_path),
    )
    document = (
        '<!doctype html><html><head><meta charset="utf-8">'
        + generate_script_tags("/teloce-npm")      # <- the Teloce-NPM tags
        + "".join(result.head)
        + '</head><body><div id="app" data-teloce-ssr="1">'
        + result.html
        + '</div><script type="module">import { hydrate } from ...; hydrate("#app", '
        + result.props_json
        + ");</script></body></html>"
    )
    return document.encode("utf-8")
```

Your server must also serve `public/teloce-npm/` at `/teloce-npm/`. With Flask, FastAPI, Flaxon or any static handler that is one mount. Take care that the path cannot escape the folder.

## What I checked

I ran this on Teloce-Py's `ssr-python` example, with a package added:

| Check | Result |
| --- | --- |
| Raw server HTML (fetched without running JavaScript) | Contains the rendered content and the `data-teloce-ssr` marker |
| Teloce-NPM tags in the raw HTML | Present in `<head>` |
| The package-powered line in the raw HTML | Absent, as expected |
| After hydration in a browser | The line appears (`Hydrated in your browser at 15:23:52`), `v-model` still works, no console errors |

## Troubleshooting

- **`use is not defined` or `use(...) is not a function` in `mounted()`.** The hook ran before the packages loaded. Add `await use.ready`, and check that the two script tags are in the server's HTML.
- **A render error about an unsupported expression.** You called `use()` (or another function) in the template or in data. Move it to `mounted()`.
- **The build tries to compile files in `.teloce-npm/`.** Set `source_roots` so only your components are scanned.

## See also

- [Teloce-Py: SSR and hydration](https://github.com/aldanedev-create/teloce-py/blob/main/docs/ssr-and-hydration.md)
- [Using Teloce-NPM with Flaxon](./flaxon)
- [Runtime API](/reference/runtime)
