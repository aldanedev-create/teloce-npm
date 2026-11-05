# Examples

Each example is a small `.vel` app. Run one with:

```bash
cd examples/<name>
teloce-npm install
python app.py
```

| Example | Package(s) | Port | Shows |
| --- | --- | --- | --- |
| `monaco-example` | `monaco-editor` | 8767 | Editor, workers, fonts and CSS bundled from npm (uses `security.allow`) |
| `lodash-example` | `lodash` | 8765 | CommonJS package, reactive computed values (uses `security.allow`) |
| `chart-example` | `chart.js` | 8766 | Bundling with an npm dependency (`@kurkle/color`) |
| `dayjs-example` | `dayjs` | 8768 | UMD package |
| `markdown-example` | `marked`, `dompurify` | 8769 | Two packages in one component, sanitized HTML |
| `papaparse-example` | `papaparse` | 8770 | CSV to table (uses `security.allow`) |
| `fuse-example` | `fuse.js` | 8771 | ESM-only package, fuzzy search |
| `confetti-example` | `canvas-confetti` | 8772 | Function-style package with named exports |
| `sortable-example` | `sortablejs` | 8773 | DOM library, drag and drop |
| `d3-example` | `d3` | 8774 | Many transitive dependencies (uses `security.allow`) |
| `three-example` | `three` | 8775 | Large ESM build, WebGL (uses `security.allow`) |
| `highlight-example` | `highlight.js` | 8776 | Package with relative `require`s |

Examples that need `security.allow` (monaco, lodash, papaparse, d3, three) list the reviewed findings in their `teloce-npm.json`. See [docs/security.md](../docs/security.md).
`apple-example` is still an empty placeholder.
