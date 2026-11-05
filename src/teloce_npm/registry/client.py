"""
HTTP client for the npm registry.
"""

import urllib.parse
from typing import Any

import requests

from teloce_npm.security.validation import validate_package_name, validate_url
from teloce_npm.utils import retry
from teloce_npm.utils.errors import PackageNotFoundError, RegistryError, SecurityError
from teloce_npm.utils.logging import logger
from teloce_npm.version import __version__


class RegistryClient:
    """Handles HTTP communication with the npm registry."""

    def __init__(self, registry_url: str):
        # https only (http is accepted for a loopback mirror such as Verdaccio).
        self.registry_url = validate_url(registry_url.rstrip("/"), what="Registry URL")
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
        validate_package_name(package_name)

        # npm requires scoped packages to be URL encoded (e.g., @types/node -> %40types%2Fnode)
        encoded_name = urllib.parse.quote(package_name, safe="")
        url = f"{self.registry_url}/{encoded_name}"
        logger.debug(f"Fetching metadata from {url}")

        last_error: Exception | None = None
        for attempt in range(retry.DEFAULT_ATTEMPTS):
            if attempt:
                retry.sleep(retry.backoff_delay(attempt - 1))
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 404:
                    raise PackageNotFoundError(f"Package '{package_name}' not found in the registry.")
                if response.status_code in retry.RETRYABLE_STATUS:
                    last_error = RegistryError(f"HTTP {response.status_code}")
                    continue
                response.raise_for_status()
                metadata = dict(response.json())
            except requests.exceptions.Timeout as error:
                last_error = error
                continue
            except requests.exceptions.ConnectionError as error:
                last_error = error
                continue
            except requests.exceptions.RequestException as e:
                raise RegistryError(f"Network error while fetching '{package_name}': {e}") from e

            # A registry must answer with the package that was asked for.
            returned = metadata.get("name")
            if returned is not None and str(returned).lower() != package_name.lower():
                raise SecurityError(
                    f"Registry returned metadata for '{returned}' when '{package_name}' was requested."
                )
            return metadata

        if isinstance(last_error, requests.exceptions.Timeout):
            raise RegistryError(f"Timeout while fetching metadata for '{package_name}'.") from None
        raise RegistryError(f"Network error while fetching '{package_name}': {last_error}") from last_error
