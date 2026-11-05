"""security.allow: reviewed, per-package exceptions to blocking findings."""

from teloce_npm.security import SecurityPolicy, run_security_checks


def _package(tmp_path, source):
    (tmp_path / "package.json").write_text('{"name": "pkg", "version": "1.0.0"}', encoding="utf-8")
    (tmp_path / "index.js").write_text(source, encoding="utf-8")
    return tmp_path


def test_finding_blocks_by_default(tmp_path):
    pkg = _package(tmp_path, "var f = new Function('a', 'return a');")
    result = run_security_checks(pkg, "pkg", SecurityPolicy())
    assert result["safe"] is False
    assert result["findings"][0]["type"] == "dynamic_function"


def test_allowed_type_is_reported_not_blocking(tmp_path):
    pkg = _package(tmp_path, "var f = new Function('a', 'return a');")
    policy = SecurityPolicy.from_config({"allow": {"pkg": ["dynamic_function"]}})
    result = run_security_checks(pkg, "pkg", policy)
    assert result["safe"] is True
    assert [f["type"] for f in result["allowed"]] == ["dynamic_function"]


def test_allow_is_scoped_to_the_named_package_and_type(tmp_path):
    pkg = _package(tmp_path, "var f = new Function('a', 'return a'); eval('1');")
    other_pkg = SecurityPolicy.from_config({"allow": {"someone-else": ["dynamic_function"]}})
    assert run_security_checks(pkg, "pkg", other_pkg)["safe"] is False
    only_function = SecurityPolicy.from_config({"allow": {"pkg": ["dynamic_function"]}})
    assert run_security_checks(pkg, "pkg", only_function)["safe"] is False  # eval still blocks
