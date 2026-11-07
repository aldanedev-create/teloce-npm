# Example: Lodash

[`examples/lodash-example`](../../examples/lodash-example) uses [Lodash](https://lodash.com/) to compute values from text you type: unique sorted words, counts and chunks.

It shows:

- a **CommonJS package** wrapped for the browser (no bundling needed);
- calling `use('lodash')` inside **computed values**, so results update as you type;
- a package that needs a reviewed `security.allow` entry.

## Run it

```bash
cd examples/lodash-example
teloce-npm install
python app.py
```

Open <http://127.0.0.1:8765>. Edit the word list or the chunk size; the three panels update.

## Declare the package

The component's first line:

```vel
Use lodash from teloce-npm
```

## Use it

```vel
<script>
export default {
  data() {
    return {
      raw: 'banana, apple, cherry, apple, date, banana, elderberry, fig, apple',
      size: 3
    };
  },
  computed: {
    words() {
      const _ = use('lodash');
      return _.compact(_.map(_.split(this.raw, ','), _.trim));
    },
    unique() {
      const _ = use('lodash');
      return _.sortBy(_.uniq(this.words));
    },
    counts() {
      const _ = use('lodash');
      return _.orderBy(_.toPairs(_.countBy(this.words)), [1, 0], ['desc', 'asc']);
    },
    chunks() {
      const _ = use('lodash');
      return _.chunk(this.unique, Math.max(1, Number(this.size) || 1));
    }
  },
  methods: {
    shuffle() {
      const _ = use('lodash');
      this.raw = _.shuffle(this.words).join(', ');
    }
  }
};
</script>
```

`use('lodash')` is called inside each computed value instead of once at the top. The component's code runs when it is created, and the app mounts only after `teloce-npm-ready`, so `use()` is ready by then. Calling it where it is needed also keeps the file easy to read.

The template shows the results with ordinary bindings:

```vel
<template>
  <main class="shell">
    <header>
      <span class="eyebrow">Teloce-NPM example</span>
      <h1>Lodash in a .vel component</h1>
      <p>Everything below is computed with <code>use('lodash')</code>. No node_modules.</p>
    </header>

    <section class="card">
      <label for="raw">Comma-separated words</label>
      <textarea id="raw" rows="3" :value="raw" @input="raw = $event.target.value"></textarea>
      <div class="row">
        <label for="size">Chunk size</label>
        <input id="size" type="number" min="1" max="10" :value="size" @input="size = $event.target.value">
        <button @click="shuffle">Shuffle (_.shuffle)</button>
      </div>
    </section>

    <section class="grid">
      <div class="card">
        <h2>_.uniq + _.sortBy</h2>
        <p class="mono">{{ unique.join(', ') }}</p>
      </div>
      <div class="card">
        <h2>_.countBy</h2>
        <ul>
          <li v-for="pair in counts" :key="pair[0]"><strong>{{ pair[0] }}</strong> × {{ pair[1] }}</li>
        </ul>
      </div>
      <div class="card">
        <h2>_.chunk</h2>
        <ul>
          <li v-for="(group, index) in chunks" :key="index" class="mono">{{ group.join(', ') }}</li>
        </ul>
      </div>
    </section>
  </main>
</template>
```

## The security entry

Lodash uses `Function` to compile `_.template`, so the scanner blocks it until you allow that finding:

```json
{
  "packages": [
    "lodash"
  ],
  "security": {
    "allow": {
      "lodash": [
        "dynamic_function"
      ]
    }
  }
}
```

This allows only `dynamic_function`, only for `lodash`. Anything else the scanner finds in a future Lodash release still blocks. See [Security](../security.md#allowing-reviewed-findings).

## Files

| File | Purpose |
| --- | --- |
| `static/js/App.vel` | The component |
| `templates/index.html` | The page; the script block is injected by `install` |
| `teloce-npm.json` | Package list and the `security.allow` entry |
| `teloce-npm.lock` | Pinned version and integrity hash |
| `app.py` | Builds and serves the page on port 8765 |
