# Python API: injector

`teloce_npm.injector` adds and removes the `<script>` block in your HTML. See [HTML injection](../html-injection.md) for the behaviour.

```python
from pathlib import Path
from teloce_npm.injector import apply_injection, revert_injection

page = Path("templates/index.html")
apply_injection(page, base_path="/static/teloce-npm")   # add (or refresh) the block
revert_injection(page)                                   # remove it
```

## Functions

| Function | Purpose |
| --- | --- |
| `apply_injection(entry_html_path, base_path="/static/teloce-npm")` | Verify the file, build the tags and inject them. The usual entry point. |
| `revert_injection(entry_html_path)` | Remove the injected block. |
| `get_entry_html(entry_html_path)` | Check that the entry HTML exists and return its path. Raises `ConfigError` if it is missing. |
| `generate_script_tags(base_path="/static/teloce-npm")` | The two `<script>` tags as a string, with `base_path` HTML-escaped. |
| `inject_scripts(entry_html_path, scripts_html)` | Low-level: put the given HTML between the markers. |
| `remove_scripts(entry_html_path)` | Low-level: remove the marked block. A missing file is ignored. |

## Guarantees

- **Idempotent.** Injecting twice leaves one block.
- **Atomic.** The file is rewritten in one step, so a crash cannot leave a half-written page.
- **Case-insensitive.** `</HEAD>` and `</head >` are found as well as `</head>`.
- **Placement.** Before `</head>`; otherwise before `</body>`; otherwise at the end of the file.

The markers are `<!-- TELOCE-NPM-START -->` and `<!-- TELOCE-NPM-END -->`.
