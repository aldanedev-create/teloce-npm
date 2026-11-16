# Introduction

Teloce-NPM lets a web page use **npm packages without Node.js and without a `node_modules` folder**. You name the packages you need, run one command, and call `use('name')`.

It is a small Python tool. It downloads each package from the npm registry, verifies and scans it, turns it into one browser-ready file, and wires it into your page. There is nothing to bundle by hand and no build server to run.

::: tip Two ways to use it
Teloce-NPM works with **plain HTML, CSS and JavaScript**, and with **Teloce components** (`.vel` or `.html`). The package manager is the same in both. Pick whichever fits your project.
:::

## Pick your style

::: code-group

```html [Plain HTML]
<!doctype html>
<html>
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
</html>
```

```vel [Teloce component]
Use dayjs from teloce-npm

<script>
export default {
  data() { return { today: "" }; },
  async mounted() {
    await use.ready;
    this.today = use('dayjs')().format('dddd, MMMM D');
  }
};
</script>

<template>
  <h1>{{ today }}</h1>
</template>
```

:::

Then, for either:

```bash
pip install teloce-npm
teloce-npm install
```

`teloce-npm install` finds the `Use` line, downloads and checks `dayjs`, writes the files your page needs and adds two `<script>` tags to it.

## How it works

1. **Scan.** `install` reads your `.html` and `.vel` files for `Use <package> from teloce-npm` lines, and the `packages` list in `teloce-npm.json`.
2. **Download.** Each package comes from the npm registry as a tarball and is checked against its SHA-512 integrity hash.
3. **Check.** The package is scanned for dangerous code and looked up in the OSV vulnerability database. See [Security](./security).
4. **Wrap or bundle.** Plain scripts are wrapped so they expose a browser global. Packages that need it (ES modules, CSS, fonts, workers, npm dependencies) are bundled with an esbuild-based bundler for Python. See [Wrapper formats](./wrapper-formats).
5. **Generate.** `loader.js`, `use.js` and `manifest.json` are written next to your static files, and two script tags are added to your page.
6. **Run.** In the browser the loader loads every package. `await use.ready` waits for it, and `use('name')` returns the package.

## Why use it

- **No Node.js.** It is pure Python and works in a plain Python container or CI job.
- **Reproducible.** `teloce-npm.lock` pins every version and integrity hash. `install --frozen-lockfile` is made for CI.
- **Secure by default.** Integrity checks, a code scanner, vulnerability lookups, download and extraction limits, and a registry host allowlist.
- **Real libraries.** Monaco, Chart.js, D3, Three.js, Lodash, Day.js, marked and DOMPurify, PapaParse, Fuse.js, canvas-confetti, SortableJS, highlight.js and Supabase are all tested. See the [examples](/examples/).
- **Small runtime.** The browser side is two small generated files.

## What it is not

Teloce-NPM is not a replacement for npm. It has no scripts, no dev dependencies and no workspaces, and it does not compile TypeScript or JSX. It installs browser libraries so a page can use them.

## Requirements

Python 3.9 or newer, and internet access to the npm registry when you install. Teloce components need [Teloce-Py](/teloce/). See [Installation](./installation).

## Next steps

- [Installation](./installation)
- [Plain HTML, CSS and JavaScript](./plain-html), a complete walkthrough
- [Teloce project](./getting-started), a complete walkthrough with Teloce components
- [Teloce, Flaxon and SSR](/teloce/)
