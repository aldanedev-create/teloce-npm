# Supabase Example

This example reads rows from a [Supabase](https://supabase.com/) table with `@supabase/supabase-js`, in a Teloce-Py **HTML component** (`App.html`, with `build.html_mode` turned on).

```bash
cd examples/supabase-example
# 1. put your project URL and ANON key in static/js/App.html (never the service_role key)
teloce-npm install
python app.py
```

Open <http://127.0.0.1:8777>. The component expects a `people` table with `id` and `name` columns that your anon key may read (Row Level Security).

Notes:

- `build.html_mode` makes Teloce-Py treat every `.html` file it scans as a component. The build in `app.py` scans only `static/` (`static_dir`), so the page shell in `templates/` and the cache in `.teloce-npm/` are not mistaken for components.
- The package is declared on the first line of `App.html`. A bare `Use ... from teloce-npm` line works in `.html` components just as in `.vel`; an HTML comment on its own lines works too.
