# Example: Chart.js

[`examples/chart-example`](../../examples/chart-example) draws a bar chart with [Chart.js](https://www.chartjs.org/) and a button that randomises the data.

It shows:

- an **ES module package with an npm dependency**: Chart.js imports `@kurkle/color`, which Teloce-NPM downloads and bundles automatically;
- using a library from `mounted()`, after the DOM exists;
- keeping a non-reactive object (the chart) out of component state;
- cleaning up in `beforeUnmount()`.

## Run it

```bash
cd examples/chart-example
teloce-npm install
python app.py
```

Open <http://127.0.0.1:8766>.

## Install output

```
[DOWNLOADING] chart.js@4.6.1...
[DEPENDENCY] @kurkle/color@0.3.4
[INSTALLED] chart.js@4.6.1
```

The `[DEPENDENCY]` line is the bundler asking for a package that Chart.js imports. See [Wrapper formats](../wrapper-formats.md#dependencies-when-bundling).

## Configuration

```json
{
  "packages": ["chart.js"],
  "bundling": {
    "mode": "always",
    "minify": true,
    "format": "esm",
    "target": "es2020"
  }
}
```

`"mode": "always"` bundles Chart.js directly. Without it, `auto` mode tries the lighter wrapper first and falls back to the bundler, with the same result.

## The component

```vel
<script>
// Kept outside component state so the reactivity layer never wraps the chart.
let chart = null;

const LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];

function randomData() {
  return LABELS.map(() => Math.round(20 + Math.random() * 80));
}

export default {
  mounted() {
    const mod = use('chart.js');
    const Chart = mod.Chart || mod;
    if (mod.registerables) {
      Chart.register(...mod.registerables);
    }
    chart = new Chart(document.getElementById('chart'), {
      type: 'bar',
      data: {
        labels: LABELS,
        datasets: [{
          label: 'Signups',
          data: [42, 58, 35, 77, 64, 90],
          backgroundColor: '#72d6c9',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#e7edf7' } } },
        scales: {
          x: { ticks: { color: '#9da9ba' }, grid: { color: '#2d3848' } },
          y: { ticks: { color: '#9da9ba' }, grid: { color: '#2d3848' }, beginAtZero: true }
        }
      }
    });
  },
  methods: {
    randomize() {
      chart.data.datasets[0].data = randomData();
      chart.update();
    }
  },
  beforeUnmount() {
    chart?.destroy();
    chart = null;
  }
};
</script>
```

Points worth noticing:

- `use('chart.js')` returns the module's exports. `Chart` is one of them, and `registerables` lists the chart types, which Chart.js needs registered before use.
- `chart` lives in a plain variable outside the component, so the reactivity layer never wraps or proxies it.
- `beforeUnmount()` destroys the chart so its canvas and listeners are released.

## Files

| File | Purpose |
| --- | --- |
| `static/js/App.vel` | The component |
| `templates/index.html` | The page; the script block is injected by `install` |
| `teloce-npm.json` | Package list and bundling mode |
| `teloce-npm.lock` | Pinned version and integrity hash |
| `app.py` | Builds and serves the page on port 8766 |
