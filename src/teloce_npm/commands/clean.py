"""`teloce-npm clean` — remove generated assets and installation state."""

import shutil

from teloce_npm.commands import BaseCommand


class CleanCommand(BaseCommand):
    """Remove generated package assets, cache data, and HTML injection."""

    def execute(self) -> int:
        self._setup()

        if self.adapter.entry_html.exists():
            self.adapter.remove_scripts()

        if self.adapter.output_dir.exists():
            shutil.rmtree(self.adapter.output_dir)

        try:
            relative = self.adapter.output_dir.relative_to(self.project_root / "dist" / "static")
        except ValueError:
            relative = None
        if relative is not None:
            source_output = self.project_root / "static" / relative
            if source_output.exists():
                shutil.rmtree(source_output)

        if self.adapter.cache_dir.exists():
            shutil.rmtree(self.adapter.cache_dir)
        self.adapter.cache_dir.mkdir(parents=True, exist_ok=True)

        if self.lockfile.exists():
            self.lockfile.path.unlink()

        print("Teloce-NPM cleaned.")
        return 0
