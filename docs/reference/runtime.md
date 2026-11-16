# Runtime API

`teloce-npm install` generates two browser files, `loader.js` and `use.js`. Together they give your page one global function, `use()`, a promise, `use.ready`, and two events.

## `use(name)`

Returns a loaded package.

```js
const _ = use('lodash');
const { Chart } = use('chart.js');
```

| Parameter | Type | Description |
| --- | --- | --- |
| `name` | `string` | The npm package name, for example `lodash`, `chart.js` or `@supabase/supabase-js` |

**Returns** whatever the package exports, or `undefined` if the package is unknown or not loaded yet. In that case `use()` logs a clear message to the console.

What you get depends on the package:

| Package style | Examples | `use()` returns |
| --- | --- | --- |
| A function or an object | `dayjs`, `lodash`, `canvas-confetti` | That function or object |
| An ES module with several exports | `marked`, `chart.js`, `d3`, `three`, `@supabase/supabase-js` | An object of exports (`use('chart.js').Chart`) |
| An ES module with only a default export | `fuse.js`, `sortablejs` | The default export itself |

When unsure, handle both shapes:

```js
const mod = use('fuse.js');
const Fuse = mod.default || mod.Fuse || mod;
```

## `use.ready` <Badge type="tip" text="new in 0.1" />

A promise that settles when the loader has finished.

```js
await use.ready;
const dayjs = use('dayjs');
```

- It **resolves** when every package has loaded.
- It **rejects** when loading failed, for example when `manifest.json` could not be fetched. The rejection value is the error.
- It is safe to use at any time: if loading already finished, it is already settled.
- If nothing awaits a rejected `use.ready`, no "unhandled rejection" is reported.

Use it wherever you cannot listen for an event yourself. It matters most when something else mounts your code, such as a framework that generates the page shell: your component's `mounted()` may run before the packages have finished loading.

```js
async mounted() {
  await use.ready;
  this.today = use('dayjs')().format('dddd');
}
```

::: warning It is a race, not a guaranteed failure
On a fast local server a package often loads before your code runs, so a component that calls `use()` directly seems to work. On a slower connection it fails with `use(...) is not a function`. `await use.ready` removes the race.
:::

## Events

Both are dispatched on `window`.

| Event | When | `event.detail` |
| --- | --- | --- |
| `teloce-npm-ready` | Every package has finished loading (a package that fails to load is logged and skipped) | none |
| `teloce-npm-error` | The loader could not load `manifest.json`, or crashed | The error |

```js
window.addEventListener('teloce-npm-ready', () => {
  // use() is ready
}, { once: true });

window.addEventListener('teloce-npm-error', (event) => {
  console.error('Packages unavailable:', event.detail);
});
```

An event fires once, so attach the listener before the loader finishes. `use.ready` has no such timing problem.

## Loader state

The loader records its final state on `window.__teloceNpmState`: `{ status: "ready" }` or `{ status: "error", error }`. It is what `use.ready` reads, and it is there if you need to check synchronously. Treat it as read-only.

## How names map to globals

Each package is stored on `window` under a safe name. `use()` tries these in order:

1. The exact name: `window['lodash']`
2. The name with `@`, `/`, `-` and `.` replaced by `_`: `chart.js` becomes `chart_js`, `@scope/pkg` becomes `_scope_pkg`
3. The same without the leading `@`: `@scope/pkg` becomes `scope_pkg`

You normally never touch the globals. Use `use()`.

## Errors you may see

| Console message | Meaning |
| --- | --- |
| `registered but not loaded yet` | You called `use()` before loading finished. `await use.ready`. |
| `not found. Available packages: ...` | The package is not installed. Check the `Use` line and run `teloce-npm list`. |
| `Could not load .../manifest.json` | The manifest URL is wrong or the files are not served. See [Troubleshooting](/guide/troubleshooting#the-app-never-mounts). |
| `did not attach to window` | An IIFE package did not set the global the wrapper expected. Try `"bundling": {"mode": "always"}`. |

## Files and sizes

`loader.js` and `use.js` are small and generated; they are not meant to be edited. `teloce-npm clean` followed by `teloce-npm install` regenerates them, which is how you pick up a newer Teloce-NPM.
