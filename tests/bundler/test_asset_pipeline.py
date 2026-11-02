import base64
from pathlib import Path

from teloce_npm.bundler.asset_pipeline import prepare_package
from teloce_npm.bundler.minifyjs_bundler import MinifyJSBundler


def test_prepare_package_inlines_css_and_font_assets(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "index.js").write_text('import "./theme.css";', encoding="utf-8")
    (package / "theme.css").write_text("@font-face { src: url('./font.woff2'); }", encoding="utf-8")
    font = b"font-data"
    (package / "font.woff2").write_bytes(font)

    prepared = prepare_package(package, tmp_path / "work")
    output = (prepared / "index.js").read_text(encoding="utf-8")

    assert "document.createElement('style')" in output
    assert "data:font/woff2;base64," in output
    assert base64.b64encode(font).decode("ascii") in output


def test_prepare_package_rewrites_css_require(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "index.js").write_text('require("./theme.css");', encoding="utf-8")
    (package / "theme.css").write_text(".editor { color: red; }", encoding="utf-8")

    prepared = prepare_package(package, tmp_path / "work")
    output = (prepared / "index.js").read_text(encoding="utf-8")

    assert "document.createElement('style')" in output
    assert "color: red" in output


def test_minifyjs_bundle_accepts_css_and_font_assets(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "package.json").write_text('{"name":"assets","main":"index.js"}')
    (package / "index.js").write_text('import "./theme.css"; export default 1;')
    (package / "theme.css").write_text("@font-face { src: url('./font.woff2'); }")
    (package / "font.woff2").write_bytes(b"font-data")

    result = MinifyJSBundler().bundle_package(package, "assets", tmp_path / "out")
    output = Path(result["output_files"][0]).read_text(encoding="utf-8")

    assert 'document.createElement("style")' in output
    assert "data:font/woff2;base64," in output
