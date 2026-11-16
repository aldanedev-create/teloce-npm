# Installation

## Requirements

- **Python 3.9 or newer.**
- Internet access to the npm registry (`registry.npmjs.org`) when you install packages. After that the build works offline from the cache.
- **Teloce-Py** (`teloce-py` on PyPI) only if you use Teloce components. Teloce-NPM itself does not need it; a plain HTML page does not.

You do **not** need Node.js or npm. The bundler is a Python package that ships its own esbuild.

## Install Teloce-NPM

```bash
pip install teloce-npm
```

Use a virtual environment so the dependencies stay out of your system Python:

::: code-group

```bash [Linux and macOS]
python -m venv .venv
source .venv/bin/activate
pip install teloce-npm
```

```bash [Windows]
python -m venv .venv
.venv\Scripts\activate
pip install teloce-npm
```

:::

To work on Teloce-NPM itself, install from a clone instead:

```bash
git clone https://github.com/aldanedev-create/teloce-npm.git
cd teloce-npm
pip install -e ".[dev]"
```

## Install what you use it with

Teloce-NPM works on its own, with plain HTML, CSS and JavaScript. Add the others only if you use them:

```bash
pip install teloce-py               # Teloce components (.vel and .html)
pip install "flaxon[standard]"      # the Flaxon framework (Python 3.11+)
```

## Check it worked

```bash
teloce-npm --version
teloce-npm doctor
```

`doctor` prints the paths it will use, the packages it finds, and the active security settings. Run it from your project folder.

## Dependencies

Installed automatically:

| Package | Used for |
| --- | --- |
| `requests` | Talking to the npm registry and OSV |
| `semver` | Version parsing |
| `tqdm` | Progress bars |
| `tree-sitter`, `tree-sitter-javascript` | Reading JavaScript to wrap and scan it |
| `minifyjs` | Bundling (esbuild) |
| `tomli` | Only on Python older than 3.11 |

## Corporate networks

Teloce-NPM uses `requests`, which honours the standard `HTTPS_PROXY`, `HTTP_PROXY` and `NO_PROXY` environment variables, and `REQUESTS_CA_BUNDLE` for a custom certificate authority. Registry authentication is **not** supported, so private registries that need a token do not work yet. See the [FAQ](faq.md).

## Updating

```bash
pip install --upgrade teloce-npm
teloce-npm clean
teloce-npm install
```

Cleaning and reinstalling regenerates `loader.js` and `use.js` from the newer templates.
