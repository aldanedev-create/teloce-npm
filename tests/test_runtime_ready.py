"""use.ready and the loader's ready/error signalling, run as real JavaScript in Node."""

import shutil
import subprocess

import pytest

from teloce_npm.generator import generate_loader_js, generate_use_js

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

PACKAGES = [
    {"name": "dayjs", "version": "1.0.0", "file": "dayjs.js", "size": 1, "integrity": "sha512-x"}
]
PRELUDE = """
globalThis.window = new EventTarget();
const log = [];
console.error = (...a) => log.push(a.join(' '));
console.log = () => {};
console.warn = () => {};
"""


def _run(tmp_path, body, *, loader=False, fetch=None):
    parts = [PRELUDE]
    if fetch:
        parts.append(f"globalThis.fetch = {fetch};")
    if loader:
        parts.append(generate_loader_js("/static/teloce-npm"))
    parts.append(generate_use_js(PACKAGES))
    parts.append(
        f"(async () => {{ {body} }})().then(r => process.stdout.write(JSON.stringify(r)));"
    )
    script = tmp_path / "t.js"
    script.write_text("\n".join(parts), encoding="utf-8")
    done = subprocess.run(["node", str(script)], capture_output=True, text=True, timeout=20)
    assert done.returncode == 0, done.stderr
    return done.stdout


def test_ready_resolves_when_the_ready_event_fires_later(tmp_path):
    out = _run(
        tmp_path,
        "setTimeout(() => window.dispatchEvent(new Event('teloce-npm-ready')), 5);"
        "await window.use.ready; return 'resolved';",
    )
    assert out == '"resolved"'


def test_ready_resolves_immediately_when_loading_already_finished(tmp_path):
    """The loader may finish before use.js runs; the stored state still settles use.ready."""
    path = tmp_path / "late.js"
    path.write_text(
        PRELUDE
        + "window.__teloceNpmState = { status: 'ready' };"
        + generate_use_js(PACKAGES)
        + "window.use.ready.then(() => process.stdout.write('ok'));",
        encoding="utf-8",
    )
    done = subprocess.run(["node", str(path)], capture_output=True, text=True, timeout=20)
    assert done.stdout == "ok"


def test_ready_rejects_on_error_event_without_unhandled_rejection(tmp_path):
    out = _run(
        tmp_path,
        "setTimeout(() => window.dispatchEvent(new CustomEvent('teloce-npm-error', {detail: 'boom'})), 5);"
        "try { await window.use.ready; return 'resolved'; } catch (e) { return 'rejected:' + e; }",
    )
    assert out == '"rejected:boom"'


def test_a_rejected_ready_nobody_awaits_does_not_crash_node(tmp_path):
    # Node exits non-zero on an unhandled rejection; _run asserts a zero exit.
    _run(
        tmp_path,
        "window.dispatchEvent(new CustomEvent('teloce-npm-error', {detail: 'boom'}));"
        "await new Promise(r => setTimeout(r, 20)); return 'alive';",
    )


def test_loader_with_no_packages_sets_state_and_fires_ready(tmp_path):
    out = _run(
        tmp_path,
        "await window.use.ready; return window.__teloceNpmState.status;",
        loader=True,
        fetch="async () => ({ ok: true, json: async () => ({ packages: {} }) })",
    )
    assert out == '"ready"'


def test_loader_reports_an_unreachable_manifest_as_an_error_event(tmp_path):
    out = _run(
        tmp_path,
        "try { await window.use.ready; return 'resolved'; }"
        " catch (e) { return [window.__teloceNpmState.status, String(e.message)]; }",
        loader=True,
        fetch="async () => ({ ok: false, status: 404, statusText: 'Not Found' })",
    )
    assert out == '["error","Could not load /static/teloce-npm/manifest.json"]'
