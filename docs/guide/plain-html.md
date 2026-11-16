# Plain HTML, CSS and JavaScript

You do not need Teloce, a framework or a build step to use Teloce-NPM. This page builds a small page with three files, [Day.js](https://day.js.org/) and [Chart.js](https://www.chartjs.org/). The finished version is in [`examples/plain-html-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/plain-html-example).

## 1. Write the page

Declare the packages in an HTML comment, each on its own line:

```html [index.html]
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Plain HTML, CSS and JavaScript</title>
  <link rel="stylesheet" href="styles.css">
  <!--
  Use dayjs from teloce-npm
  Use chart.js from teloce-npm
  -->
</head>
<body>
  <p id="today"></p>
  <div class="chart-box"><canvas id="chart"></canvas></div>
  <script type="module" src="app.js"></script>
</body>
</html>
```

::: warning The declaration must be alone on its line
A one-line comment such as `<!-- Use dayjs from teloce-npm -->` is ignored without a message. Put the `Use` line between `<!--` and `-->` on separate lines. You can also list packages in `teloce-npm.json` instead (see below).
:::

## 2. Write your JavaScript

`styles.css` is ordinary CSS. In `app.js`, wait for the packages, then use them:

```js [app.js]
await use.ready;

const dayjs = use("dayjs");
const { Chart, registerables } = use("chart.js");
Chart.register(...registerables);

document.getElementById("today").textContent = dayjs().format("dddd, MMMM D, YYYY");

new Chart(document.getElementById("chart"), {
  type: "bar",
  data: {
    labels: ["Jan", "Feb", "Mar"],
    datasets: [{ label: "Signups", data: [42, 58, 35] }],
  },
});
```

Packages load after the page starts, so `use()` is not ready on the very first line of your script. `await use.ready` waits until it is. A module script can use top-level `await`, as above. Without a module, use `use.ready.then(...)` or listen for the `teloce-npm-ready` event. See [Runtime API](/reference/runtime).

## 3. Configure

A plain site has no `templates/` folder, so tell Teloce-NPM which file is your page and where to put the generated files. Create `teloce-npm.json`:

```json [teloce-npm.json]
{
  "entry_html": "index.html",
  "output_dir": "static/teloce-npm"
}
```

The script URLs are derived from `output_dir`: this one gives `/static/teloce-npm/loader.js`.

To skip the comment and list the packages here instead:

```json
{
  "packages": ["dayjs", "chart.js@4"],
  "entry_html": "index.html",
  "output_dir": "static/teloce-npm"
}
```

## 4. Install

```bash
pip install teloce-npm
teloce-npm install
```

```
[2/6] Installing packages...
    [INSTALLED] chart.js@4.6.1
    [INSTALLED] dayjs@1.11.23
```

Two script tags are now in your `<head>`, between `TELOCE-NPM-START` and `TELOCE-NPM-END` comments, and the generated files are in `static/teloce-npm/`.

## 5. Serve it

Any static file server works:

```bash
python -m http.server 8000
```

Open <http://127.0.0.1:8000/index.html>. Serve the page over `http`, not by opening the file directly: browsers generally block module loading from `file://`.

## Deploying

Upload the folder to any static host. Commit `index.html`, `teloce-npm.json` and `teloce-npm.lock`. Do not commit `.teloce-npm/` or `static/teloce-npm/`; run `teloce-npm install --frozen-lockfile` in your build step to recreate them.

::: tip Hosting under a sub-path
The script URLs start at `/`. If your site lives under a sub-path, for example `https://example.com/docs-site/`, set `base_path`:

```json
{ "entry_html": "index.html", "output_dir": "static/teloce-npm", "base_path": "/docs-site/static/teloce-npm" }
```
:::

## More than one page

Only the file named by `entry_html` gets the script tags. For other pages, copy the block from your entry page into their `<head>`:

```html
<script src="/static/teloce-npm/loader.js" defer></script>
<script src="/static/teloce-npm/use.js" defer></script>
```

Declare packages once, in any one scanned `.html` file or in `teloce-npm.json`; every page then shares the same generated files.

## Next

- [`Use` declarations](./use-declarations)
- [Runtime API](/reference/runtime)
- [Security](./security) explains the checks that ran during `install`.
- [Supabase example](/examples/supabase) uses the same approach with a hosted database.
