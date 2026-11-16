
import { defineConfig } from 'vitepress'

// Vercel and custom domains serve from "/".
// A GitHub project site can use DOCS_BASE=/teloce-npm/.
const base = process.env.DOCS_BASE ?? '/'

const repo = 'https://github.com/aldanedev-create/teloce-npm'
const pypi = 'https://pypi.org/project/teloce-npm/'

export default defineConfig({
  title: 'Teloce-NPM',
  titleTemplate: ':title | Teloce-NPM',
  description:
    'Use npm packages in plain HTML, CSS and JavaScript, or in Teloce components, without Node.js.',
  lang: 'en-US',
  base,
  cleanUrls: true,
  lastUpdated: true,

  srcExclude: ['README.md', 'node_modules/**'],

  ignoreDeadLinks: [
    // Ignore relative links pointing outside /docs to the repository's /examples directory.
    /^\.\.\/examples\/.*/,
  ],

  markdown: {
    // .vel files are single-file components: highlight them like Vue.
    languageAlias: {
      vel: 'vue',
      gitignore: 'ini',
    },
  },

  head: [
    [
      'link',
      {
        rel: 'icon',
        type: 'image/svg+xml',
        href: `${base}logo.svg`,
      },
    ],
    ['meta', { name: 'theme-color', content: '#1f9d8b' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'Teloce-NPM' }],
    [
      'meta',
      {
        property: 'og:description',
        content: 'npm packages without Node.js, for plain HTML or Teloce.',
      },
    ],
  ],

  themeConfig: {
    logo: `${base}logo.svg`,
    siteTitle: 'Teloce-NPM',

    nav: [
      {
        text: 'Guide',
        link: '/guide/introduction',
        activeMatch: '/guide/',
      },
      {
        text: 'Reference',
        link: '/reference/commands',
        activeMatch: '/(reference|api)/',
      },
      {
        text: 'Examples',
        link: '/examples/',
        activeMatch: '/examples/',
      },
      {
        text: 'Teloce',
        activeMatch: '/teloce/',
        items: [
          { text: 'Overview', link: '/teloce/' },
          { text: 'Flaxon', link: '/teloce/flaxon' },
          {
            text: 'Server-side rendering',
            link: '/teloce/ssr',
          },
          {
            text: 'HTML components',
            link: '/teloce/html-components',
          },
        ],
      },
      {
        text: 'v0.1',
        items: [
          {
            text: 'Changelog',
            link: `${repo}/blob/main/CHANGELOG.md`,
          },
          {
            text: 'Works with Teloce-Py 0.3+ and Flaxon 0.3+',
            link: '/teloce/#version-support',
          },
          {
            text: 'PyPI',
            link: pypi,
          },
        ],
      },
    ],

    sidebar: {
      '/guide/': [
        {
          text: 'Getting started',
          items: [
            { text: 'Introduction', link: '/guide/introduction' },
            { text: 'Installation', link: '/guide/installation' },
            {
              text: 'Plain HTML, CSS and JavaScript',
              link: '/guide/plain-html',
            },
            {
              text: 'A Teloce project',
              link: '/guide/getting-started',
            },
          ],
        },
        {
          text: 'Essentials',
          items: [
            {
              text: 'Use declarations',
              link: '/guide/use-declarations',
            },
            {
              text: 'Runtime API',
              link: '/reference/runtime',
            },
            {
              text: 'Configuration',
              link: '/reference/configuration',
            },
            {
              text: 'Commands',
              link: '/reference/commands',
            },
          ],
        },
        {
          text: 'Security and reliability',
          items: [
            { text: 'Security', link: '/guide/security' },
            { text: 'Lockfile', link: '/guide/lockfile' },
            { text: 'Cache', link: '/guide/cache' },
          ],
        },
        {
          text: 'How it works',
          items: [
            {
              text: 'Wrapper formats and bundling',
              link: '/guide/wrapper-formats',
            },
            {
              text: 'HTML injection',
              link: '/guide/html-injection',
            },
          ],
        },
        {
          text: 'Help',
          items: [
            { text: 'FAQ', link: '/guide/faq' },
            {
              text: 'Troubleshooting',
              link: '/guide/troubleshooting',
            },
          ],
        },
      ],

      '/reference/': [
        {
          text: 'Reference',
          items: [
            { text: 'Commands', link: '/reference/commands' },
            {
              text: 'Configuration',
              link: '/reference/configuration',
            },
            { text: 'Runtime API', link: '/reference/runtime' },
          ],
        },
        {
          text: 'Python API',
          items: [
            { text: 'Commands', link: '/api/commands' },
            { text: 'Generator', link: '/api/generator' },
            { text: 'Injector', link: '/api/injector' },
            { text: 'Security', link: '/api/security' },
          ],
        },
      ],

      '/api/': [
        {
          text: 'Reference',
          items: [
            { text: 'Commands', link: '/reference/commands' },
            {
              text: 'Configuration',
              link: '/reference/configuration',
            },
            { text: 'Runtime API', link: '/reference/runtime' },
          ],
        },
        {
          text: 'Python API',
          items: [
            { text: 'Commands', link: '/api/commands' },
            { text: 'Generator', link: '/api/generator' },
            { text: 'Injector', link: '/api/injector' },
            { text: 'Security', link: '/api/security' },
          ],
        },
      ],

      '/teloce/': [
        {
          text: 'Teloce',
          items: [
            { text: 'Overview', link: '/teloce/' },
            {
              text: 'HTML components',
              link: '/teloce/html-components',
            },
            { text: 'Flaxon', link: '/teloce/flaxon' },
            {
              text: 'Server-side rendering',
              link: '/teloce/ssr',
            },
            {
              text: 'Build contract',
              link: '/teloce/build-contract',
            },
          ],
        },
      ],

      '/examples/': [
        {
          text: 'Examples',
          items: [
            { text: 'Overview', link: '/examples/' },
            { text: 'Lodash', link: '/examples/lodash' },
            { text: 'Chart.js', link: '/examples/chartjs' },
            { text: 'Supabase', link: '/examples/supabase' },
          ],
        },
      ],
    },

    socialLinks: [
      {
        icon: 'github',
        link: repo,
      },
    ],

    search: {
      provider: 'local',
    },

    editLink: {
      pattern: `${repo}/edit/main/docs/:path`,
      text: 'Edit this page on GitHub',
    },

    outline: {
      level: [2, 3],
      label: 'On this page',
    },

    docFooter: {
      prev: 'Previous',
      next: 'Next',
    },

    lastUpdated: {
      text: 'Last updated',
    },

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © Aldane Hutchinson',
    },
  },
})
