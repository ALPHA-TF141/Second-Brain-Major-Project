/**
 * One-shot codemod: route every backend request through the authenticated
 * `apiFetch` helper instead of a bare `fetch()`.
 *
 *   fetch(`${apiClient.baseUrl}/api/...`   ->   apiFetch(`${apiClient.baseUrl}/api/...`
 *   fetch(`${baseUrl}/api/...`             ->   apiFetch(`${baseUrl}/api/...
 *
 * Adds the import if missing. Safe to re-run (idempotent).
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const SRC = path.join(ROOT, 'src');

function walk(dir, acc = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) walk(full, acc);
    else if (/\.(jsx?|tsx?)$/.test(e.name)) acc.push(full);
  }
  return acc;
}

const files = walk(SRC);
let touched = 0;
const report = [];

for (const file of files) {
  let text = fs.readFileSync(file, 'utf8');
  const original = text;

  // Only rewrite calls that target our own backend
  text = text.replace(/fetch\((\s*`\$\{(?:apiClient\.baseUrl|baseUrl)\}\/api\/)/g, 'apiFetch($1');
  text = text.replace(/fetch\((\s*[`'"]\/api\/)/g, 'apiFetch($1');

  // Never add an import to the module that DEFINES apiFetch
  const definesApiFetch = /export async function apiFetch/.test(text);
  const usedApiFetch = /\bapiFetch\(/.test(text) && !definesApiFetch;
  const usesFetch = /\bfetch\(/.test(text);
  const alreadyImported = /import\s*\{[^}]*\bapiFetch\b[^}]*\}\s*from\s*['"][^'"]*apiClient\.js['"]/.test(text);

  if (usedApiFetch && !alreadyImported) {
    const rel = path
      .relative(path.dirname(file), path.join(SRC, 'services', 'apiClient.js'))
      .replace(/\\/g, '/');
    const spec = rel.startsWith('.') ? rel : `./${rel}`;

    // Merge into an existing apiClient import when possible, else add a new line
    const existing = text.match(/import\s*\{([^}]*)\}\s*from\s*(['"][^'"]*apiClient\.js['"]);?/);
    if (existing) {
      const names = existing[1].trim();
      text = text.replace(
        existing[0],
        `import { ${names}, apiFetch } from ${existing[2]};`
      );
    } else {
      const imports = [...text.matchAll(/^import .*?;$/gm)];
      const anchor = imports.length ? imports[imports.length - 1] : null;
      const line = `import { apiFetch } from '${spec}';`;
      text = anchor
        ? text.replace(anchor[0], `${anchor[0]}\n${line}`)
        : `${line}\n${text}`;
    }
  }

  if (text !== original) {
    fs.writeFileSync(file, text);
    touched += 1;
    report.push(`  patched  ${path.relative(ROOT, file)}  (bare fetch left: ${usesFetch && !/apiClient|baseUrl/.test(text) ? 'n/a' : 'checked'})`);
  }
}

console.log(`\nAuth-fetch codemod complete. Files modified: ${touched}\n`);
report.forEach((r) => console.log(r));
