"""
Tests for teloce_npm.utils.errors.
"""

import pytest

from teloce_npm.utils.errors import (
    TeloceNpmError,
    ConfigError,
    RegistryError,
    SecurityError,
    LockfileMismatch,
    PackageNotFoundError,
)


def test_base_error_inherits_exception():
    assert issubclass(TeloceNpmError, Exception)


@pytest.mark.parametrize(
    "subclass",
    [
        ConfigError,
        RegistryError,
        SecurityError,
        LockfileMismatch,
        PackageNotFoundError,
    ],
)
def test_subclasses_inherit_base(subclass):
    assert issubclass(subclass, TeloceNpmError)


@pytest.mark.parametrize(
    "error_class",
    [
        TeloceNpmError,
        ConfigError,
        RegistryError,
        SecurityError,
        LockfileMismatch,
        PackageNotFoundError,
    ],
)
def test_errors_can_be_raised_and_caught(error_class):
    with pytest.raises(error_class, match="test message"):
        raise error_class("test message")


def test_specific_error_can_be_caught_as_base():
    with pytest.raises(TeloceNpmError):
        raise ConfigError("config problem")


def test_catching_config_error_does_not_catch_security_error():
    """Ensure error classes are distinct and not interchangeable."""
    try:
        raise SecurityError("security issue")
    except ConfigError:
        pytest.fail("SecurityError was incorrectly caught as ConfigError")
    except SecurityError:
        pass  # expected