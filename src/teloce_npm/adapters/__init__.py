"""
Framework-agnostic project adapter for Teloce-NPM.

The adapter abstracts the project layout (where entry_html lives,
where output goes, what URL prefix to use) so the command layer
never has to think about paths or frameworks.
"""

from .adapter import ProjectAdapter, get_adapter

__all__ = [
    "ProjectAdapter",
    "get_adapter",
]
