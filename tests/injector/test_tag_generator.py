"""
Tests for teloce_npm.injector.tag_generator.generate_script_tags.

Scope: only tag string construction.
"""

from teloce_npm.injector.tag_generator import generate_script_tags


# ---------------------------------------------------------------------------
# Default base path
# ---------------------------------------------------------------------------
def test_default_base_path_produces_two_tags():
    tags = generate_script_tags()
    assert tags.count("<script") == 2
    assert tags.count("</script>") == 2


def test_default_base_path_contains_loader():
    tags = generate_script_tags()
    assert "/static/teloce-npm/loader.js" in tags


def test_default_base_path_contains_use():
    tags = generate_script_tags()
    assert "/static/teloce-npm/use.js" in tags


def test_uses_defer_attribute():
    tags = generate_script_tags()
    assert tags.count("defer") == 2


# ---------------------------------------------------------------------------
# Custom base path
# ---------------------------------------------------------------------------
def test_custom_base_path():
    tags = generate_script_tags(base_path="/my/assets/teloce")
    assert "/my/assets/teloce/loader.js" in tags
    assert "/my/assets/teloce/use.js" in tags


def test_trailing_slash_stripped():
    tags = generate_script_tags(base_path="/my/path/")
    # Must not produce /my/path//loader.js
    assert "//loader.js" not in tags
    assert "/my/path/loader.js" in tags


# ---------------------------------------------------------------------------
# Output format
# ---------------------------------------------------------------------------
def test_contains_newline_between_tags():
    tags = generate_script_tags()
    assert 'loader.js"' in tags
    # The use tag must be on a separate line
    lines = tags.strip().split("\n")
    assert len(lines) == 2


def test_no_template_markers_remain():
    tags = generate_script_tags()
    assert "$" not in tags
