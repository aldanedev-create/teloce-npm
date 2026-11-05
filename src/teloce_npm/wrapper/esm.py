"""
Wrap ES Module (ESM) packages for the browser using Tree-sitter.
"""

import re

from teloce_npm.utils.errors import TeloceNpmError
from teloce_npm.utils.logging import logger

from .ast_parser import (
    extract_exports,
    extract_imports,
    parse_source,
    replace_node,
)
from .base import BaseWrapper


class EsmWrapper(BaseWrapper):

    def wrap(self) -> str:
        entry_path = self._find_entry_file()
        logger.debug(f"Wrapping ESM entry: {entry_path}")

        source_code = entry_path.read_text(encoding="utf-8")

        # 1. Parse the source code into an AST
        tree = parse_source(source_code)

        # 2. Extract all imports and replace them
        imports = extract_imports(tree)

        # Process imports in reverse order to avoid offset issues
        for imp in sorted(imports, key=lambda x: x["node"].start_byte, reverse=True):
            dep_name = imp["source"]
            if dep_name.startswith((".", "/")):
                raise TeloceNpmError(
                    f"ESM package '{self.package_name}' has relative imports; "
                    "it requires bundling."
                )
            safe_name = (
                dep_name.replace("@", "").replace("/", "_").replace("-", "_").replace(".", "_")
            )

            statement = imp["node"].text.decode("utf-8")
            named = re.match(
                r"import\s+\{([^}]+)\}\s+from\s+['\"][^'\"]+['\"]\s*;?",
                statement,
            )
            default = re.match(
                r"import\s+([A-Za-z_$][\w$]*)\s+from\s+['\"][^'\"]+['\"]\s*;?",
                statement,
            )
            if named:
                replacement = f"const {{{named.group(1)}}} = window.{safe_name};"
            elif default:
                replacement = f"const {default.group(1)} = window.{safe_name};"
            else:
                replacement = f"window.{safe_name};"

            source_code = replace_node(source_code, imp["node"], replacement)

        # 3. Extract all exports and handle them.
        # Each export statement is rewritten in place (by node, never by a
        # global text search) and its exported names are collected so they can
        # be exposed on the window object.
        named: list[tuple[str, str]] = []  # (exported name, local identifier)
        exports = extract_exports(tree)

        for exp in sorted(exports, key=lambda x: x["node"].start_byte, reverse=True):
            node_text = exp["node"].text.decode("utf-8")

            if node_text.startswith("export default"):
                # `export default X` -> `var __default_export = X`
                replacement = node_text.replace("export default", "var __default_export =", 1)
                source_code = replace_node(source_code, exp["node"], replacement)
            elif re.match(r"export\s*\{", node_text):
                if re.search(r"\}\s*from\s", node_text):
                    raise TeloceNpmError(
                        f"ESM package '{self.package_name}' has re-exports; "
                        "it requires bundling."
                    )
                # `export { a, b as c }` -> remove, remember the names.
                default_local = None
                for part in re.search(r"\{([^}]*)\}", node_text).group(1).split(","):
                    pieces = part.strip().split()
                    if not pieces:
                        continue
                    local = pieces[0]
                    exported = pieces[2] if len(pieces) == 3 and pieces[1] == "as" else local
                    if exported == "default":
                        default_local = local
                    else:
                        named.append((exported, local))
                replacement = f"var __default_export = {default_local};" if default_local else ""
                source_code = replace_node(source_code, exp["node"], replacement)
            else:
                # `export const foo = ...` / `export function foo() {}` -> drop the keyword.
                declaration = re.match(
                    r"export\s+(?:async\s+)?(?:const|let|var|function\*?|class)\s+([A-Za-z_$][\w$]*)",
                    node_text,
                )
                if declaration:
                    named.append((declaration.group(1), declaration.group(1)))
                replacement = re.sub(r"^export\s+", "", node_text, count=1)
                source_code = replace_node(source_code, exp["node"], replacement)

        # 4. Re-parse the modified code to get the final AST (optional, for validation)
        # tree = parse_source(source_code)

        window_name = self._window_name()

        # Named exports become properties of the default export when there is
        # one (as in `import lib, { create } from "lib"`), otherwise they form
        # the exported namespace object.
        namespace_lines = "\n".join(
            f"    __namespace[{exported!r}] = {local};" for exported, local in reversed(named)
        )

        # 5. Wrap in IIFE and attach to window
        return f"""
// ============================================================
// Wrapped ESM package: {self.package_name}
// Generated by Teloce-NPM (Tree-sitter)
// ============================================================
(function() {{
    // ---- Original package code ----
    {source_code}
    // ---- End original package code ----

    var __namespace = {{}};
{namespace_lines}

    // Attach the exports to window
    var __main = (typeof __default_export !== 'undefined') ? __default_export : __namespace;
    if (__main !== __namespace && (typeof __main === 'function' || (typeof __main === 'object' && __main !== null))) {{
        for (var __key in __namespace) {{
            if (!(__key in __main)) {{
                try {{ __main[__key] = __namespace[__key]; }} catch (error) {{}}
            }}
        }}
    }}
    window['{window_name}'] = __main;
}})();
"""
