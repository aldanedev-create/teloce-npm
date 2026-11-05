"""
MinifyJS-backed bundler for complex npm packages.

Uses MinifyJS's bundle() function (esbuild's api.Build under the hood)
to resolve import graphs, tree-shake, and produce browser-ready output
without Node.js.

Serves as the fallback engine when the Tree-sitter static wrapper
cannot handle a package (unresolved relative imports, worker graphs,
or explicit bundling mode).

Limitations (documented, not solved by this module):
    - Worker URL policies remain package-specific.
    - No plugin API: no virtual modules, no custom resolvers.
    - No tsconfig.json: TypeScript path aliases are not resolved.
    - No custom loaders: .json, .wasm, and .node imports are not handled.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from teloce_npm.bundler.asset_pipeline import copy_worker_assets, prepare_package
from teloce_npm.utils.errors import TeloceNpmError
from teloce_npm.utils.logging import logger


class MinifyJSNotAvailable(TeloceNpmError):  # noqa: N818
    """Raised when MinifyJS is not installed but bundling is required."""

    pass


def _import_minifyjs():
    """
    Lazy-import minifyjs so Teloce-NPM works without it installed.

    Returns the bundle() and BundleError symbols.
    """
    try:
        from minifyjs import BundleError, bundle

        return bundle, BundleError
    except ImportError as error:
        raise MinifyJSNotAvailable(
            "MinifyJS is not installed. Bundling complex packages requires it.\n"
            "Install with: pip install minifyjs"
        ) from error


class MinifyJSBundler:
    """
    Wraps MinifyJS's bundle() for Teloce-NPM's needs.

    One instance per install run. Reads bundling config from
    `teloce-npm.json` (see config/defaults.py for schema).
    """

    def __init__(self, config: Optional[dict] = None):
        config = config or {}
        self.minify = config.get("minify", True)
        self.target = config.get("target", "es2020")
        self.format = config.get("format", "esm")
        self.sourcemap = config.get("sourcemap", None)
        self.splitting = config.get("splitting", False)
        self.platform = config.get("platform", "browser")
        self.tree_shaking = config.get("tree_shaking", True)
        self.packages = config.get("packages", "bundle")
        self.external = config.get("external", [])
        self.define = config.get("define", {})
        self.drop = config.get("drop", [])
        self.charset = config.get("charset", "utf8")
        self.legal_comments = config.get("legal_comments", None)
        self.entry_names = config.get("entry_names", None)
        self.chunk_names = config.get("chunk_names", None)
        self.asset_names = config.get("asset_names", None)
        self.metafile = config.get("metafile", None)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def bundle_package(
        self,
        extracted_dir: Path,
        package_name: str,
        output_dir: Path,
        dependency_dirs: Optional[dict[str, Path]] = None,
    ) -> dict[str, object]:
        """
        Bundle an extracted npm package into a browser-ready file.

        Args:
            extracted_dir: The `package/` directory extracted from the tarball.
            package_name: The npm package name (e.g., "lodash").
            output_dir: Where to write the bundled output (typically the
                        adapter's output_dir).
            dependency_dirs: Optional {dependency name: extracted directory} map.
                        Each is placed under `node_modules/<name>` next to the
                        package so imports of its npm dependencies resolve.

        Returns:
            A dict with:
                - output_files: list of Path objects written
                - bundle_dir: Path to the directory containing the output
                - diagnostics: list of MinifyJS diagnostic dicts
                - bytes_saved: int (informational)

        Raises:
            MinifyJSNotAvailable: If minifyjs is not installed.
            TeloceNpmError: If bundling fails or the entry point is unresolved.
        """
        with tempfile.TemporaryDirectory(prefix="teloce-npm-assets-") as temp_dir:
            prepared_dir = prepare_package(extracted_dir, Path(temp_dir))
            for dep_name, dep_dir in (dependency_dirs or {}).items():
                shutil.copytree(dep_dir, prepared_dir / "node_modules" / dep_name, dirs_exist_ok=True)
            return self._bundle_prepared_package(prepared_dir, package_name, output_dir)

    def _bundle_prepared_package(
        self,
        extracted_dir: Path,
        package_name: str,
        output_dir: Path,
    ) -> dict[str, object]:
        bundle, bundle_error = _import_minifyjs()

        # 1. Resolve the entry point
        entry_file = self._resolve_entry(extracted_dir, package_name)

        # 2. Prepare output paths
        bundle_dir = output_dir / self._safe_name(package_name)
        bundle_dir.mkdir(parents=True, exist_ok=True)

        safe = self._safe_name(package_name)
        kwargs = {
            "entry_points": [str(entry_file)],
            "working_dir": str(extracted_dir),
            "platform": self.platform,
            "splitting": self.splitting,
            "compress": self.minify,
            "mangle": self.minify,
            "target": self.target,
            "format": self.format,
            "tree_shaking": self.tree_shaking,
            "packages": self.packages,
            "external": self.external,
            "define": self.define,
            "drop": self.drop,
            "charset": self.charset,
            "banner": (
                f"// Bundled by Teloce-NPM (MinifyJS / esbuild)\n" f"// Package: {package_name}"
            ),
        }

        if self.sourcemap:
            kwargs["sourcemap"] = self.sourcemap
        if self.legal_comments:
            kwargs["legal_comments"] = self.legal_comments
        if self.entry_names:
            kwargs["entry_names"] = self.entry_names
        if self.chunk_names:
            kwargs["chunk_names"] = self.chunk_names
        if self.asset_names:
            kwargs["asset_names"] = self.asset_names
        if self.metafile:
            kwargs["metafile"] = str(bundle_dir / self.metafile)

        if self.splitting:
            kwargs["outdir"] = str(bundle_dir)
        else:
            kwargs["outfile"] = str(bundle_dir / f"{safe}.js")

        # 3. Run bundle()
        logger.debug(f"MinifyJS bundling {package_name} from {entry_file}")
        try:
            result = bundle(**kwargs)
        except bundle_error as error:
            raise TeloceNpmError(f"MinifyJS failed to bundle '{package_name}': {error}") from error

        # 4. Handle errors surfaced via diagnostics
        diagnostics = getattr(result, "diagnostics", []) or []
        errors = [d for d in diagnostics if _diag_severity(d) == "error"]
        if errors:
            messages = "\n".join(f"  - {_diag_text(d)}" for d in errors)
            raise TeloceNpmError(f"Bundle errors for '{package_name}':\n{messages}")

        # 5. Collect written files
        written = sorted(bundle_dir.glob("*.js")) if self.splitting else [bundle_dir / f"{safe}.js"]

        written = [p for p in written if p.exists()]
        if not written:
            raise TeloceNpmError(f"MinifyJS produced no output files for '{package_name}'")

        copy_worker_assets(extracted_dir, bundle_dir)

        total_bytes = sum(p.stat().st_size for p in written)
        logger.debug(
            f"MinifyJS bundled {package_name}: " f"{len(written)} file(s), {total_bytes} bytes"
        )

        return {
            "output_files": [str(p) for p in written],
            "bundle_dir": bundle_dir,
            "diagnostics": diagnostics,
            "bytes_saved": getattr(result, "bytes_saved", 0),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_entry(self, package_dir: Path, package_name: str) -> Path:
        """
        Find the package entry point from package.json.

        Resolution order (matches npm/esbuild conventions):
            module → browser → main → index.{js,mjs,cjs}
        """
        pkg_json = package_dir / "package.json"
        if not pkg_json.exists():
            raise TeloceNpmError(f"No package.json found for '{package_name}' in {package_dir}")

        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise TeloceNpmError(f"Invalid package.json for '{package_name}': {e}") from e

        for field in ("module", "browser", "main"):
            value = data.get(field)
            if isinstance(value, str):
                candidate = package_dir / value.lstrip("./")
                if candidate.exists() and candidate.is_file():
                    return candidate

        # Fallback to conventional index files
        for candidate_name in ("index.js", "index.mjs", "index.cjs"):
            candidate = package_dir / candidate_name
            if candidate.exists():
                return candidate

        raise TeloceNpmError(
            f"Could not resolve entry point for '{package_name}'. "
            f"Checked package.json fields: module, browser, main; "
            f"and index.{{js,mjs,cjs}}."
        )

    @staticmethod
    def _safe_name(package_name: str) -> str:
        """Convert a package name into a filesystem-safe identifier."""
        return package_name.replace("@", "").replace("/", "_").replace("-", "_").replace(".", "_")


# ----------------------------------------------------------------------
# Diagnostics helpers — MinifyJS diagnostic objects vary by version,
# so these normalize them defensively.
# ----------------------------------------------------------------------
def _diag_severity(diagnostic) -> str:
    if hasattr(diagnostic, "severity"):
        return str(diagnostic.severity).lower()
    if isinstance(diagnostic, dict):
        return str(diagnostic.get("severity", "")).lower()
    return ""


def _diag_text(diagnostic) -> str:
    if hasattr(diagnostic, "text"):
        return str(diagnostic.text)
    if isinstance(diagnostic, dict):
        return str(diagnostic.get("text") or diagnostic.get("message") or diagnostic)
    return str(diagnostic)
