#!/usr/bin/env node
/**
 * validate.js — check our addon manifest with Stremio's own protocol linter.
 *
 * The point is to stop saying "the manifest is valid" because I read two other manifests and
 * it looked fine. This asks the reference implementation, which is also MIT and maintained by
 * the people who define the protocol.
 *
 *   ./validate.js http://127.0.0.1:8890/<token>/manifest.json
 *   ./validate.js manifest.json
 *
 * Prints one JSON line. Exit 0 = valid, 1 = invalid, 2 = could not read the manifest.
 */
const fs = require('fs');
const { lintManifest } = require('stremio-addon-linter');

async function load(arg) {
  if (arg.startsWith('http://') || arg.startsWith('https://')) {
    const res = await fetch(arg);
    if (!res.ok) throw new Error(`HTTP ${res.status} for ${arg}`);
    return await res.json();
  }
  return JSON.parse(fs.readFileSync(arg, 'utf8'));
}

(async () => {
  const arg = process.argv[2];
  if (!arg) {
    console.log(JSON.stringify({ ok: false, error: 'usage: validate.js <manifest-url|file>' }));
    process.exit(2);
  }
  let manifest;
  try {
    manifest = await load(arg);
  } catch (err) {
    console.log(JSON.stringify({ ok: false, error: String(err.message || err) }));
    process.exit(2);
  }

  const result = lintManifest(manifest);
  const errors = (result.errors || []).map((e) => String(e.message || e));
  const warnings = (result.warnings || []).map((e) => String(e.message || e));

  console.log(JSON.stringify({
    ok: result.valid,
    addon: manifest.id,
    name: manifest.name,
    version: manifest.version,
    resources: manifest.resources,
    catalogs: (manifest.catalogs || []).length,
    errors,
    warnings,
  }));
  process.exit(result.valid ? 0 : 1);
})();
