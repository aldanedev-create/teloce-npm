# Examples

Each example is a small app you can run. They install with the security scan **on**; the ones that need `security.allow` say so.

```bash
cd examples/<name>
teloce-npm install
python app.py          # or: python -m http.server for the plain HTML example
```

## Plain HTML, CSS and JavaScript

| Example | Packages | Shows |
| --- | --- | --- |
| [`plain-html-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/plain-html-example) | `dayjs`, `chart.js` | Three files and a static server, no Teloce. See the [guide](/guide/plain-html). |

## Teloce components

| Example | Packages | Port | Shows |
| --- | --- | --- | --- |
| [`dayjs-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/dayjs-example) | `dayjs` | 8768 | A UMD package |
| [`lodash-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/lodash-example) | `lodash` | 8765 | A CommonJS package, computed values. [Walkthrough](./lodash) |
| [`chart-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/chart-example) | `chart.js` | 8766 | Bundling with an npm dependency. [Walkthrough](./chartjs) |
| [`monaco-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/monaco-example) | `monaco-editor` | 8767 | An editor with workers, fonts and CSS |
| [`markdown-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/markdown-example) | `marked`, `dompurify` | 8769 | Two packages in one component, sanitized HTML |
| [`papaparse-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/papaparse-example) | `papaparse` | 8770 | CSV to a table |
| [`fuse-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/fuse-example) | `fuse.js` | 8771 | An ES-module-only package, fuzzy search |
| [`confetti-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/confetti-example) | `canvas-confetti` | 8772 | A function-style package |
| [`sortable-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/sortable-example) | `sortablejs` | 8773 | Drag and drop |
| [`d3-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/d3-example) | `d3` | 8774 | Dozens of transitive dependencies |
| [`three-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/three-example) | `three` | 8775 | A WebGL scene |
| [`highlight-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/highlight-example) | `highlight.js` | 8776 | A package with relative `require`s |
| [`supabase-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/supabase-example) | `@supabase/supabase-js` | 8777 | An `.html` component and a hosted database. [Walkthrough](./supabase) |

## With Flaxon and SSR

The [Flaxon](/teloce/flaxon) and [SSR](/teloce/ssr) pages are complete, tested walkthroughs. They build on Teloce-Py's and Flaxon's own examples.
