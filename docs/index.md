---
layout: home
title: Teloce-NPM, npm packages without Node.js
titleTemplate: false

hero:
  name: Teloce-NPM
  text: npm packages, no Node.js
  tagline: Use Day.js, Chart.js, D3, Monaco, Supabase and more in plain HTML, CSS and JavaScript, or in Teloce components. One Python command, no node_modules.
  image:
    src: /logo.svg
    alt: Teloce-NPM
  actions:
    - theme: brand
      text: Get Started
      link: /guide/introduction
    - theme: alt
      text: Plain HTML
      link: /guide/plain-html
    - theme: alt
      text: View on GitHub
      link: https://github.com/aldanedev-create/teloce-npm

features:
  - icon: 🧩
    title: HTML, CSS and JavaScript
    details: No framework needed. Declare a package in a comment, run one command, and call use('name') from any script.
    link: /guide/plain-html
    linkText: Plain HTML guide
  - icon: 🐍
    title: No Node.js
    details: Pure Python. Packages are downloaded, wrapped and bundled by Python, so it runs in a plain Python container or CI job.
    link: /guide/introduction#how-it-works
    linkText: How it works
  - icon: ⚡
    title: Teloce, Flaxon and SSR
    details: Works in .vel and .html components, in Flaxon apps, and with server-side rendering and hydration.
    link: /teloce/
    linkText: Teloce guides
  - icon: 🔒
    title: Secure by default
    details: SHA-512 integrity, a code scanner, vulnerability lookups, download and extraction limits, and a registry allowlist.
    link: /guide/security
    linkText: Security
  - icon: 📌
    title: Reproducible
    details: A lockfile pins every version and hash. install --frozen-lockfile is built for CI, and a changed package is blocked.
    link: /guide/lockfile
    linkText: Lockfile
  - icon: 📦
    title: Real libraries
    details: Monaco, Chart.js, D3, Three.js, Lodash, Supabase and more are tested, with runnable examples for each.
    link: /examples/
    linkText: Examples
---

<div class="home-section">

## Start in two minutes

::: code-group

```bash [Plain HTML]
pip install teloce-npm

# index.html declares:  <!--  Use dayjs from teloce-npm  -->
teloce-npm install
python -m http.server 8000
```

```bash [Teloce]
pip install teloce-npm teloce-py

# App.vel starts with:  Use dayjs from teloce-npm
teloce-npm install
python app.py
```

```bash [Flaxon]
pip install teloce-npm "flaxon[standard]" teloce-py

# teloce-npm.json: { "entry_html": null, "output_dir": "public/teloce-npm" }
teloce-npm install
flaxon run app:app
```

:::

Then, in your page or component:

```js
await use.ready;                    // packages load after the page starts
const dayjs = use('dayjs');
console.log(dayjs().format('dddd, MMMM D'));
```

## Where to go next

| I want to | Read |
| --- | --- |
| Understand what it does | [Introduction](/guide/introduction) |
| Use it in a plain HTML page | [Plain HTML, CSS and JavaScript](/guide/plain-html) |
| Use it in a Teloce project | [A Teloce project](/guide/getting-started) |
| Use it with Flaxon | [Flaxon](/teloce/flaxon) |
| Use it with server-side rendering | [Server-side rendering](/teloce/ssr) |
| Look up a command or option | [Commands](/reference/commands), [Configuration](/reference/configuration) |
| Fix a problem | [Troubleshooting](/guide/troubleshooting) |

</div>
