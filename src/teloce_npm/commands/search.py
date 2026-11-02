"""
`teloce-npm search <query>` — search the npm registry.
"""

import requests

from teloce_npm.commands import BaseCommand


class SearchCommand(BaseCommand):

    def execute(self, query: str) -> int:
        self._setup()

        url = f"{self.config['registry']}/-/v1/search"
        params = {"text": query, "size": 20}

        try:
            response = requests.get(url, params=params, timeout=15)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return 1

        objects = data.get("objects", [])
        if not objects:
            print(f'No results for "{query}".')
            return 0

        print(f'Search results for "{query}":\n')
        for obj in objects:
            pkg = obj.get("package", {})
            name = pkg.get("name", "?")
            version = pkg.get("version", "?")
            desc = pkg.get("description", "").strip() or "(no description)"
            print(f"  {name}@{version}")
            print(f"    {desc}")
            print()
        return 0
