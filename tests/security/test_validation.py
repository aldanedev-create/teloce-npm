"""Validation of names, versions and URLs that reach paths, URLs and JavaScript."""

import pytest

from teloce_npm.security.validation import validate_package_name, validate_url, validate_version
from teloce_npm.utils.errors import SecurityError


@pytest.mark.parametrize(
    "name", ["lodash", "chart.js", "@types/node", "@kurkle/color", "JSONStream", "d3-array", "a", "x_y~z"]
)
def test_valid_names(name):
    assert validate_package_name(name) == name


@pytest.mark.parametrize(
    "name",
    [
        "", "..", ".", "../x", "a/b", "@scope", "@scope/", "@a/b/c", "@/x", "node_modules",
        "@x/node_modules", "-leading", ".hidden", "_private", "has space", "semi;colon", "lodash\n", "lodash ",
        'quo"te', "back\\slash", "new\nline", "a" * 215, None, 5,
    ],
)
def test_invalid_names(name):
    with pytest.raises(SecurityError):
        validate_package_name(name)


@pytest.mark.parametrize("version", ["1.0.0", "0.0.1", "10.20.30", "1.2.3-beta.1", "1.2.3+build.5", "2.0.0-rc.1+sha"])
def test_valid_versions(version):
    assert validate_version(version) == version


@pytest.mark.parametrize("version", ["", "1", "1.2", "^1.0.0", "../../x", "1.0.0/../..", "1.0.0 ", "latest", None, "1.0.0\n"])
def test_invalid_versions(version):
    with pytest.raises(SecurityError):
        validate_version(version)


def test_https_url_is_accepted():
    assert validate_url("https://registry.npmjs.org/x.tgz", ["registry.npmjs.org"])


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "[::1]"])
def test_http_is_only_accepted_for_loopback(host):
    assert validate_url(f"http://{host}:4873/x.tgz")


@pytest.mark.parametrize("url", ["http://registry.npmjs.org/x", "ftp://registry.npmjs.org/x", "file:///etc/passwd", "//registry.npmjs.org/x", "https:///x", ""])
def test_other_schemes_and_missing_hosts_are_rejected(url):
    with pytest.raises(SecurityError):
        validate_url(url)


def test_host_match_is_exact_not_suffix():
    with pytest.raises(SecurityError):
        validate_url("https://registry.npmjs.org.evil.com/x", ["registry.npmjs.org"])
    with pytest.raises(SecurityError):
        validate_url("https://evilregistry.npmjs.org/x", ["registry.npmjs.org"])


def test_host_match_is_case_insensitive():
    assert validate_url("https://Registry.NPMJS.org/x", ["registry.npmjs.org"])
