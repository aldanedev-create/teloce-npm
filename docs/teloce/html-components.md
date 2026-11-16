# Using Teloce-NPM with HTML components

Teloce-Py can compile components written as `.html` files instead of `.vel`. Teloce-NPM works the same way with both: it reads the `Use` declaration, installs the package, and `use()` is available in the component.

## Turn on HTML mode

In `teloce.config.json`:

```json
{
  "build": {
    "out_dir": "dist",
    "static_dir": "static",
    "clean": true,
    "shared_runtime": true,
    "hash_assets": false,
    "html_mode": true
  }
}
```

The `teloce build` command reads this file. If you build from Python with `build_project` (as the examples' `app.py` does), **the call does not read `teloce.config.json`**, so pass the same options yourself:

```python
build_project(ROOT, out_dir=DIST, options={
    "clean": True,
    "shared_runtime": True,
    "static_dir": "static",   # scan only static/ for components and TypeScript
    "html_mode": True,        # .html files are components (.vel still works)
})
```

HTML mode keeps `.vel` support, so you can migrate one component at a time.

## An `.html` component

The sections are the same as in a `.vel` file: `<script>`, `<template>` and `<style>`. Declare packages on their own lines at the top:

```html
Use @supabase/supabase-js from teloce-npm

<script>
let supabase = null;

export default {
  data() { return { people: [], error: null, loading: true }; },
  async mounted() {
    const { createClient } = use('@supabase/supabase-js');
    supabase = createClient('https://YOUR-PROJECT.supabase.co', 'YOUR-ANON-KEY');
    const { data, error } = await supabase.from('people').select('id, name').order('name');
    this.people = data || [];
    this.error = error ? error.message : null;
    this.loading = false;
  }
};
</script>

<template>
  <main>
    <p v-if="loading">Loading...</p>
    <p v-else-if="error">{{ error }}</p>
    <ul v-else><li v-for="p in people" :key="p.id">{{ p.name }}</li></ul>
  </main>
</template>
```

The declaration can also sit in an HTML comment, as long as it is alone on its line:

```html
<!--
Use @supabase/supabase-js from teloce-npm
-->
```

Both forms are found by `teloce-npm install` and accepted by the Teloce-Py compiler. The runnable version is [`examples/supabase-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/supabase-example).

## Keep the page shell out of the component folder

In HTML mode Teloce-Py treats **every `.html` file it scans** as a component. Your page shell (`templates/index.html`) is not one, so it must not be scanned:

- Put components in `static/js/` and the page in `templates/`.
- Set `static_dir` to `static`, as above, so only `static/` is scanned.

Without that, the build fails with `Missing <template> section in .../templates/index.html`.

## Do not let the build scan the cache

By default Teloce-Py scans the whole project folder, which includes Teloce-NPM's `.teloce-npm/` cache. That cache holds unpacked npm packages. Some of them (for example `@supabase/supabase-js`) ship TypeScript sources, and the build then fails with errors such as:

```
.teloce-npm/cache/.../extracted/src/SupabaseClient.ts:318: constructor parameter properties are not supported
```

In HTML mode it can also pick up `.html` files that belong to a package. Passing `static_dir` (or `source_roots: ["static/js"]`) limits the scan to your own files. Flaxon and Teloce-Py's SSR examples already set `source_roots` for you. This applies to `.vel` projects as well. All the examples do it.

## Plain pages without Teloce-Py

You do not need Teloce-Py to use Teloce-NPM. A plain `.html` page can declare a package in a comment, load the generated files, and call `use()` after `teloce-npm-ready`. See [HTML injection](../guide/html-injection.md) and the FAQ.

## Supabase notes

- Use the **anon** key in the browser, never the `service_role` key. Protect tables with Row Level Security.
- Keep the client in a plain variable outside component state (`let supabase`), so the reactivity layer does not wrap it.
- With a Content-Security-Policy, allow your project in `connect-src` (and `wss://YOUR-PROJECT.supabase.co` for realtime).
- Render data with the template bindings or `textContent`, not `innerHTML`.
