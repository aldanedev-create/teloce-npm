"""
Bundler module for Teloce-NPM.

Provides an optional MinifyJS-backed fallback for packages that cannot
be handled by the static Tree-sitter wrapper (complex import graphs,
worker dependencies, or explicit user opt-in).
"""

from .minifyjs_bundler import MinifyJSBundler, MinifyJSNotAvailable

__all__ = [
    "MinifyJSBundler",
    "MinifyJSNotAvailable",
]