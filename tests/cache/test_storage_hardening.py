"""Cache paths can never escape the cache directory."""

import pytest

from teloce_npm.cache.storage import CacheStorage
from teloce_npm.utils.errors import SecurityError


@pytest.mark.parametrize("name,version", [("../../x", "1.0.0"), ("lodash", "../../../etc"), ("lodash", "1.0.0/../.."), ("a/b", "1.0.0")])
def test_hostile_names_and_versions_are_rejected(tmp_path, name, version):
    storage = CacheStorage(tmp_path / "cache")
    with pytest.raises(SecurityError):
        storage.package_dir(name, version)


def test_scoped_package_stays_inside_cache(tmp_path):
    storage = CacheStorage(tmp_path / "cache")
    path = storage.package_dir("@kurkle/color", "0.3.4")
    assert path.resolve().is_relative_to((tmp_path / "cache").resolve())
