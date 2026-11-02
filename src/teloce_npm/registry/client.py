"""
HTTP client for the npm registry.
"""

import urllib.parse
from typing import Any

import requests

from teloce_npm.utils.errors import PackageNotFoundError, RegistryError
from teloce_npm.utils.logging import logger
from teloce_npm.version import __version__


class RegistryClient:
    """Handles HTTP communication with the npm registry."""

    def __init__(self, registry_url: str):
        self.registry_url = registry_url.rstrip("/")
        self.session = requests.Session()
        # Set a User-Agent so the registry knows who we are
        self.session.headers.update(
            {"User-Agent": f"Teloce-NPM/{__version__}", "Accept": "application/json"}
        )

    def get_package_metadata(self, package_name: str) -> dict[str, Any]:
        """
        Fetch the full metadata for a package from the registry.

        Args:
            package_name: The name of the package (e.g., 'lodash', '@types/node').

        Returns:
            The raw JSON metadata as a dictionary.

        Raises:
            PackageNotFoundError: If the package does not exist (404).
            RegistryError: If there is a network or server error.
        """
        # npm requires scoped packages to be URL encoded (e.g., @types/node -> %40types%2Fnode)
        encoded_name = urllib.parse.quote(package_name, safe="")
        url = f"{self.registry_url}/{encoded_name}"

        logger.debug(f"Fetching metadata from {url}")

        try:
            response = self.session.get(url, timeout=15)

            if response.status_code == 404:
                raise PackageNotFoundError(f"Package '{package_name}' not found in the registry.")

            response.raise_for_status()
            return dict(response.json())

        except requests.exceptions.Timeout:
            raise RegistryError(f"Timeout while fetching metadata for '{package_name}'.") from None
        except requests.exceptions.RequestException as e:
            raise RegistryError(f"Network error while fetching '{package_name}': {e}") from e
