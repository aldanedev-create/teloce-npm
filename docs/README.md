# Teloce-NPM documentation

The documentation is a [VitePress](https://vitepress.dev) site. These Markdown files are its source, and they read fine on GitHub too.

```bash
cd docs
npm install
npm run dev        # http://localhost:5173/
npm run build      # static site in .vitepress/dist
```

Node.js is needed only to build the documentation site. Teloce-NPM itself never needs it.

## Layout

| Folder | Contents |
| --- | --- |
| `guide/` | Introduction, installation, walkthroughs, `Use` declarations, security, how it works, FAQ |
| `reference/` | Commands, configuration, the browser runtime API |
| `api/` | The Python API |
| `teloce/` | Teloce-Py, HTML components, Flaxon, server-side rendering |
| `examples/` | Example walkthroughs |
| `.vitepress/` | Site configuration (`config.mts`), theme and styles |
| `public/` | Static assets such as the logo |

## Deploying to Vercel

1. Push the repository to GitHub.
2. In Vercel choose **Add New... > Project** and import the repository.
3. Set **Root Directory** to `docs`. Leave the framework as detected (VitePress); `docs/vercel.json` already sets the install command, build command (`npm run build`) and output directory (`.vitepress/dist`).
4. Deploy. The site is served from the root of its domain, and the base path is set automatically.

Every push to `main` redeploys, and every pull request gets a preview URL. To use a custom domain, add it under the project's Domains settings.

Hosting somewhere that serves the site from a sub-path (for example GitHub Pages project sites) needs `DOCS_BASE=/teloce-npm/` when building.

Start at the [Introduction](guide/introduction.md).
