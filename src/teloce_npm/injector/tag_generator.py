"""
Generate the <script> tags for Teloce-NPM runtime files.
"""


def generate_script_tags(base_path: str = "/static/teloce-npm") -> str:
    """
    Build the HTML <script> block for loader.js and use.js.

    Args:
        base_path: The URL path prefix under which wrapped files are served.

    Returns:
        A string containing the script tags.
    """
    # Clean up the base path (remove trailing slash)
    base_path = base_path.rstrip("/")

    # We use 'defer' so they download in parallel and execute in order
    # after the HTML document has been parsed.
    return f"""<script src="{base_path}/loader.js" defer></script>
<script src="{base_path}/use.js" defer></script>"""
