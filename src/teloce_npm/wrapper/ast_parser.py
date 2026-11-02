"""
Tree-sitter based JavaScript AST parser for Teloce-NPM.

This module provides a shared parser instance and utility functions
for querying and transforming JavaScript source code.
"""

from typing import Any

# We assume tree_sitter and tree_sitter_javascript are installed
import tree_sitter
import tree_sitter_javascript as tsjs

# Initialize the language and parser once
JS_LANGUAGE = tree_sitter.Language(tsjs.language())
PARSER = tree_sitter.Parser(JS_LANGUAGE)


def parse_source(source_code: str) -> tree_sitter.Tree:
    """
    Parse JavaScript source code into a Tree-sitter AST.

    Args:
        source_code: The JavaScript source code as a string.

    Returns:
        A Tree-sitter Tree object.
    """
    return PARSER.parse(bytes(source_code, "utf-8"))


def find_nodes(tree: tree_sitter.Tree, query_string: str) -> list[tree_sitter.Node]:
    """
    Run a Tree-sitter query against the AST and return matching nodes.

    Args:
        tree: The parsed AST.
        query_string: A Tree-sitter query in S-expression format.

    Returns:
        A list of matching nodes.
    """
    legacy_query = getattr(JS_LANGUAGE, "query", None)
    if legacy_query is not None:
        captures = legacy_query(query_string).captures(tree.root_node)
    else:
        query = tree_sitter.Query(JS_LANGUAGE, query_string)
        captures = tree_sitter.QueryCursor(query).captures(tree.root_node)

    # captures is a dict of capture_name -> list of nodes
    # We flatten to a single list of nodes
    all_nodes = []
    for nodes in captures.values():
        all_nodes.extend(nodes)
    return all_nodes


def replace_node(source_code: str, node: tree_sitter.Node, replacement: str) -> str:
    """
    Replace a node in the source code with a new string.

    Args:
        source_code: The original source code.
        node: The node to replace.
        replacement: The replacement string.

    Returns:
        The modified source code.
    """
    start_byte = node.start_byte
    end_byte = node.end_byte

    # Convert byte offsets to string indices
    # This is safe for UTF-8 because Tree-sitter operates on bytes
    source_bytes = source_code.encode("utf-8")
    new_bytes = source_bytes[:start_byte] + replacement.encode("utf-8") + source_bytes[end_byte:]
    return new_bytes.decode("utf-8")


def extract_imports(tree: tree_sitter.Tree) -> list[dict[str, Any]]:
    """
    Extract all import statements from the AST.

    Returns:
        A list of dicts with 'source' (the module being imported) and 'node'.
    """
    # Query for import statements
    import_query = """
    (import_statement
      source: (string (string_fragment) @source)
    ) @import
    """
    nodes = find_nodes(tree, import_query)

    imports = []
    for node in nodes:
        if node.type == "string_fragment":
            statement = node.parent
            while statement is not None and statement.type != "import_statement":
                statement = statement.parent
            if statement is None or node.text is None:
                continue
            imports.append(
                {
                    "source": node.text.decode("utf-8"),
                    "node": statement,
                }
            )
    return imports


def extract_exports(tree: tree_sitter.Tree) -> list[dict[str, Any]]:
    """
    Extract all export statements from the AST.

    Returns:
        A list of dicts with 'type' (default/named) and 'node'.
    """
    # Query for default exports
    # Query for named exports

    # Simplified: just find export_statement nodes
    export_query = "(export_statement) @export"
    nodes = find_nodes(tree, export_query)

    exports = []
    for node in nodes:
        exports.append({"type": "export", "node": node})
    return exports


def extract_requires(tree: tree_sitter.Tree) -> list[dict[str, Any]]:
    """
    Extract all require() calls from the AST.

    Returns:
        A list of dicts with 'source' (the module being required) and 'node'.
    """
    require_query = """
    (call_expression
      function: (identifier) @func
      arguments: (arguments
        (string (string_fragment) @source)
      )
    )
    """

    nodes = find_nodes(tree, require_query)

    requires = []
    for node in nodes:
        if node.type == "string_fragment":
            call = node.parent
            while call is not None and call.type != "call_expression":
                call = call.parent
            if call is None or node.text is None:
                continue
            requires.append(
                {
                    "source": node.text.decode("utf-8"),
                    "node": call,
                }
            )
    return requires
