import { build } from 'esbuild'

await build({
  entryPoints: ['src/index.ts'],
  outfile: 'lib/client.js',
  bundle: true,
  platform: 'browser',
  format: 'cjs',
  target: ['chrome120', 'firefox121', 'safari17'],
  jsx: 'automatic',
  external: ['react', 'react/jsx-runtime', 'react-dom'],
  minify: true,
  legalComments: 'none',
  banner: {
    js: 'window.__ModuleLoader__.load({ id: "dsh-whale-chan-tv", factory: (require) => { var module = { exports: {} }; var exports = module.exports;',
  },
  footer: { js: 'return module.exports; } });' },
})
console.log('built lib/client.js')
