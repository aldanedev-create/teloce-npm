# Teloce, Flaxon and SSR

Teloce-NPM is a package manager. It does not render pages itself, so it is easiest to understand next to the projects that do. This section explains how it works with them.

<Badge type="tip" text="Teloce-Py 0.3+" /> <Badge type="tip" text="Flaxon 0.3+" /> <Badge type="info" text="Teloce-NPM 0.1+" />

## The pieces

| Project | What it is | Install |
| --- | --- | --- |
| **Teloce** | A component format: single files with `<template>`, `<script>` and `<style>` sections, written as `.vel` or (in HTML mode) `.html` files. | |
| **Teloce-Py** | A Python-native compiler and runtime for Teloce components, with a server-side renderer for SSR and hydration. | `pip install teloce-py` |
| **Flaxon** | An async-first Python full-stack framework with integrated Teloce interfaces: Flaxon serves your API and uses Teloce as the UI layer. | `pip install "flaxon[standard]"` |
| **Teloce-NPM** | This tool: it lets any of the above, or a plain HTML page, use npm packages. | `pip install teloce-npm` |

::: info Not to be confused with "Teloce on npm"
Some Teloce-Py pages use "Teloce npm" to mean the original JavaScript implementation of Teloce that is published on npm. **Teloce-NPM** here is a different thing: a Python tool that lets pages use npm packages. They do not depend on each other.
:::

## Choose your setup

| You have | Use | Read |
| --- | --- | --- |
| Static HTML, CSS and JavaScript | Teloce-NPM on its own | [Plain HTML, CSS and JavaScript](/guide/plain-html) |
| A Teloce-Py project built with `teloce build` or `build_project` | `.vel` or `.html` components | [Teloce project](/guide/getting-started), [HTML components](./html-components) |
| A Flaxon app | `app.use_teloce(...)` | [Flaxon](./flaxon) |
| Server-rendered Teloce pages with hydration | Teloce-Py's `Renderer` | [Server-side rendering](./ssr) |

The package manager is identical in all four. What changes is how the page that loads the packages is produced.

## Three things to know first

**1. Packages run in the browser.** Teloce-NPM delivers JavaScript to the page. Server-side code does not execute it. In SSR, use packages from browser-only hooks such as `mounted()`.

**2. Packages load after the page starts.** If something else mounts your component, as Flaxon does, `await use.ready` before calling `use()`. See [Runtime API](/reference/runtime#use-ready).

**3. Tell Teloce where your components are.** Teloce-Py scans the project folder for components unless you narrow it, and that includes Teloce-NPM's `.teloce-npm/` cache. Flaxon and SSR setups already do this (`source_roots`). If you call `build_project` yourself, pass `static_dir`. See [HTML components](./html-components#do-not-let-the-build-scan-the-cache).

## Version support

| | Supported |
| --- | --- |
| Teloce-NPM | 0.1+ |
| Teloce-Py | 0.3+ |
| Flaxon | 0.3+ (needs Python 3.11+) |
| Python (Teloce-NPM itself) | 3.9+ |

## Upstream documentation

- [Teloce-Py documentation](https://github.com/aldanedev-create/teloce-py/tree/main/docs): the compiler, the component format, SSR and hydration, and a lesson series.
- [Flaxon documentation](https://github.com/aldanedev-create/flaxon/tree/main/docs), and its [Teloce integration reference](https://github.com/aldanedev-create/flaxon/blob/main/docs/api/teloce.md).
