#!/usr/bin/env python3
"""Check the documentation Markdown: JSON and Python code blocks must parse.

Link checking is done by `npm run build` in docs/ (VitePress fails on a dead link).
Run from anywhere:  python scripts/check_docs.py
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"```(\w*)[^\n]*\n(.*?)```", re.S)


def markdown_files() -> list[Path]:
    files = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "CHANGELOG.md"]
    files += [p for p in (ROOT / "docs").rglob("*.md") if "node_modules" not in p.parts]
    return sorted(p for p in files if p.exists())


def main() -> int:
    problems: list[str] = []
    blocks = 0
    for path in markdown_files():
        for language, code in FENCE.findall(path.read_text(encoding="utf-8")):
            blocks += 1
            try:
                if language == "json":
                    json.loads(code)
                elif language == "python":
                    ast.parse(code)
            except (ValueError, SyntaxError) as error:
                problems.append(f"{path.relative_to(ROOT)}: invalid {language} block: {error}")
    for problem in problems:
        print(problem)
    print(f"Checked {blocks} code blocks in {len(markdown_files())} files: {len(problems)} problem(s).")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
