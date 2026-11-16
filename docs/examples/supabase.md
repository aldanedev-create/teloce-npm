# Example: Supabase

[`examples/supabase-example`](https://github.com/aldanedev-create/teloce-npm/tree/main/examples/supabase-example) reads rows from a [Supabase](https://supabase.com/) table with `@supabase/supabase-js`, in a Teloce **HTML component**.

It shows:

- a package with many dependencies, bundled automatically;
- an `.html` component (Teloce-Py HTML mode);
- keeping a client object out of component state;
- loading and error states.

## Run it

```bash
cd examples/supabase-example
# put your project URL and anon key in static/js/App.html
teloce-npm install
python app.py
```

Open <http://127.0.0.1:8777>. The component expects a `people` table with `id` and `name` columns that your anon key may read.

## The component

```html [static/js/App.html]
Use @supabase/supabase-js from teloce-npm

<script>
let supabase = null;

export default {
  data() { return { people: [], error: null, loading: true }; },
  async mounted() {
    await use.ready;
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

## Plain HTML instead

The same package works in a plain page:

```html
<head>
  <!--
  Use @supabase/supabase-js from teloce-npm
  -->
</head>
<body>
  <ul id="list"></ul>
  <script type="module">
    await use.ready;
    const { createClient } = use("@supabase/supabase-js");
    const supabase = createClient("https://YOUR-PROJECT.supabase.co", "YOUR-ANON-KEY");
    const { data } = await supabase.from("people").select("id, name").order("name");
    for (const person of data) {
      const li = document.createElement("li");
      li.textContent = person.name;      // textContent, never innerHTML, for data
      document.getElementById("list").append(li);
    }
  </script>
</body>
```

Use `{ "entry_html": "index.html", "output_dir": "static/teloce-npm" }` in `teloce-npm.json`. See [Plain HTML, CSS and JavaScript](/guide/plain-html).

## Notes

::: danger Use the anon key only
Put only the **anon (public)** key in browser code. Never ship the `service_role` key. Protect your tables with Row Level Security.
:::

- Keep the client in a plain variable outside component state (`let supabase`), so the reactivity layer does not wrap it.
- With a Content-Security-Policy, allow your project in `connect-src` (and `wss://YOUR-PROJECT.supabase.co` for realtime).
- Render database values with template bindings or `textContent`, not `innerHTML`.
- Pin the version: `teloce-npm install @supabase/supabase-js@2.119.0`.

## What was tested

The page was run in a browser with the Supabase network calls intercepted: the request URL was `.../rest/v1/people?select=id%2Cname&order=name.asc`, rows rendered, and an error response ("Invalid API key") showed in the page. It was not run against a real Supabase project, and realtime and sign-in flows were not tested.
