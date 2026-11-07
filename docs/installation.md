# Installation

## Requirements

- **Python 3.9 or newer.**
- Internet access to the npm registry (`registry.npmjs.org`) when you install packages. After that the build works offline from the cache.
- **Teloce-Py** (`teloce-py` on PyPI) to compile `.vel` files. Teloce-NPM itself does not need it, but the examples and a normal project do.

You do **not** need Node.js or npm. The bundler is a Python package that ships its own esbuild.

## Install Teloce-NPM

Teloce-NPM is not on PyPI yet. Install it from GitHub:

```bash
pip install "teloce-npm @ git+https://github.com/aldanedev-create/teloce-npm.git"
```

Or from a local clone, which is what you want if you plan to change the code:

```bash
git clone https://github.com/aldanedev-create/teloce-npm.git
cd teloce-npm
pip install -e ".[dev]"
```

Use a virtual environment so the dependencies stay out of your system Python:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

## Install Teloce-Py

```bash
pip install teloce-py
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
pip install --upgrade "teloce-npm @ git+https://github.com/aldanedev-create/teloce-npm.git"
teloce-npm clean
teloce-npm install
```

Cleaning and reinstalling regenerates `loader.js` and `use.js` from the newer templates.
