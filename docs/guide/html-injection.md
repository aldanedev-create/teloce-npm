# HTML injection

For packages to be available in the browser, your page must load two generated files. `install` adds them for you.

## What is injected

Into the file named by `entry_html` (default `templates/index.html`), just before `</head>`:

```html
<!-- TELOCE-NPM-START -->
<script src="/static/teloce-npm/loader.js" defer></script>
<script src="/static/teloce-npm/use.js" defer></script>
<!-- TELOCE-NPM-END -->
</head>
```

The URL prefix is `base_path`, derived from `output_dir` unless you set it. The prefix is HTML-escaped.

- `loader.js` fetches `manifest.json`, loads every package in dependency order, then fires `teloce-npm-ready`.
- `use.js` defines the global `use()` function.

## Rules

- **Idempotent.** Running `install` again updates the block between the two marker comments instead of adding another one.
- **Only your entry HTML** is changed. Other files are never touched.
- **Removable.** `remove` (when the last package goes) and `clean` take the block out again.
- **Do not edit between the markers.** Your changes will be overwritten.
- **Placement.** The block goes just before `</head>`. If there is no `</head>` it goes before `</body>`, and if there is neither it is appended to the end of the file. Tag matching ignores case. A proper `<head>` is still the right place for it.

## Pages your server generates

Some servers build the page themselves, so there is no HTML file to edit: [Flaxon](../teloce/flaxon.md), [SSR hosts](../teloce/ssr.md), or any framework that renders its own shell. Set `entry_html` to `null`:

```json
{ "entry_html": null, "output_dir": "public/teloce-npm", "base_path": "/teloce-npm" }
```

`install` then changes no HTML. It prints the two tags, and you add them to the page your server generates:

```
  entry_html is null: no HTML file was changed. Load these tags in the page your server generates:
    <script src="/teloce-npm/loader.js" defer></script>
    <script src="/teloce-npm/use.js" defer></script>
```

From Python, `teloce_npm.injector.generate_script_tags("/teloce-npm")` returns the same two tags as a string. Your server must also serve the output folder at `base_path`.

## Mounting your app

The loader is asynchronous. Start your app after the ready event, or `await use.ready`:

```html
<script type="module">
  window.addEventListener("teloce-npm-ready", async () => {
    const { mount } = await import("/static/js/App.js");
    mount("#app");
  }, { once: true });
</script>
```

See [`use()` at runtime](use-declarations.md#use-at-runtime).

## Content-Security-Policy

The runtime uses `import()` to load package files from your own origin, and no inline scripts of its own. A strict policy needs `script-src 'self'` (plus whatever your own inline mount script needs). Wrapped packages that contain `eval` or `Function` will need `'unsafe-eval'`, and you should question whether you want them (the scanner flags those).
