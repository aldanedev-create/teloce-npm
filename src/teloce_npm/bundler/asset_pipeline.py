"""Prepare npm assets that MinifyJS does not expose loaders for."""

import base64
import mimetypes
import re
import shutil
from pathlib import Path
from typing import Optional

from teloce_npm.utils.errors import TeloceNpmError

_CSS_IMPORT_RE = re.compile(
    r"(?P<full>import\s+(?:(?P<binding>[\w$]+)\s+from\s+)?(?P<quote>['\"])(?P<path>[^'\"]+\.css)(?P=quote)\s*;?)"
)
_CSS_REQUIRE_RE = re.compile(r"require\(\s*(?P<quote>['\"])(?P<path>[^'\"]+\.css)(?P=quote)\s*\)")
_CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(?P<path>[^)'\"]+)\1\s*\)")


def prepare_package(package_dir: Path, work_dir: Path) -> Path:
    """Copy a package and inline CSS/font imports for JavaScript bundling."""
    prepared = work_dir / "package"
    shutil.copytree(package_dir, prepared)

    for source in prepared.rglob("*"):
        if source.is_file() and source.suffix.lower() in {".js", ".mjs", ".cjs"}:
            _rewrite_javascript(source)

    return prepared


def copy_worker_assets(package_dir: Path, bundle_dir: Path) -> dict[str, str]:
    """Copy self-contained worker bundles and return label-to-file mappings."""
    candidates = [
        path
        for path in package_dir.rglob("*.js")
        if "worker" in path.name.lower()
        and "assets" in path.parts
        and "node_modules" not in path.parts
    ]
    if not candidates:
        return {}

    selected: dict[str, Path] = {}
    for source in candidates:
        label = _worker_label(source.name)
        if label not in selected or source.stat().st_size > selected[label].stat().st_size:
            selected[label] = source

    worker_dir = bundle_dir / "workers"
    worker_dir.mkdir(parents=True, exist_ok=True)
    workers: dict[str, str] = {}
    for label, source in selected.items():
        target_name = source.name
        target = worker_dir / target_name
        shutil.copy2(source, target)
        workers[label] = f"workers/{target_name}"
    return workers


def discover_worker_assets(bundle_dir: Path) -> dict[str, str]:
    """Read worker mappings from an already generated bundle directory."""
    worker_dir = bundle_dir / "workers"
    if not worker_dir.exists():
        return {}
    return {_worker_label(path.name): f"workers/{path.name}" for path in worker_dir.glob("*.js")}


def _worker_label(filename: str) -> str:
    lower_name = filename.lower()
    if "typescript" in lower_name or "ts.worker" in lower_name:
        return "typescript"
    if "javascript" in lower_name or "js.worker" in lower_name:
        return "javascript"
    if "json.worker" in lower_name:
        return "json"
    if "css.worker" in lower_name:
        return "css"
    if "html.worker" in lower_name:
        return "html"
    return "editor"


def _rewrite_javascript(path: Path) -> None:
    source = path.read_text(encoding="utf-8")

    def replace_import(match: re.Match[str]) -> str:
        css_path = _resolve_asset(path, match.group("path"))
        css = _load_css(css_path, set()) if css_path is not None else ""
        binding = match.group("binding")
        if binding:
            return f"const {binding} = {css!r};"
        return _style_injection(css)

    def replace_require(match: re.Match[str]) -> str:
        css_path = _resolve_asset(path, match.group("path"))
        css = _load_css(css_path, set()) if css_path is not None else ""
        return _style_injection(css)

    source = _CSS_IMPORT_RE.sub(replace_import, source)
    source = _CSS_REQUIRE_RE.sub(replace_require, source)
    path.write_text(source, encoding="utf-8")


def _resolve_asset(source: Path, relative: str) -> Optional[Path]:
    asset = (source.parent / relative).resolve()
    if not asset.exists() or not asset.is_file():
        if not relative.startswith((".", "/")):
            return None
        raise TeloceNpmError(f"CSS asset not found: {relative} imported by {source.name}")
    return asset


def _load_css(path: Path, seen: set[Path]) -> str:
    path = path.resolve()
    if path in seen:
        return ""
    seen.add(path)
    css = path.read_text(encoding="utf-8")

    def replace_url(match: re.Match[str]) -> str:
        raw_path = match.group("path").strip()
        if raw_path.startswith(("data:", "http:", "https:", "#")):
            return match.group(0)
        asset = (path.parent / raw_path).resolve()
        if not asset.exists() or not asset.is_file():
            return match.group(0)
        mime = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(asset.read_bytes()).decode("ascii")
        return f"url(data:{mime};base64,{encoded})"

    return _CSS_URL_RE.sub(replace_url, css)


def _style_injection(css: str) -> str:
    return (
        "(() => { const style = document.createElement('style'); "
        f"style.textContent = {css!r}; document.head.appendChild(style); }})();"
    )
