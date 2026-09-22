// Jarvis OS - static error-check configuration.
// Purpose: catch runtime crash causes BEFORE the app boots in Electron.
// Run with:  npm run lint     (fails on any error)
//            npm run lint:fix (auto-fixes what it safely can)
import js from '@eslint/js';
import globals from 'globals';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';

export default [
  { ignores: ['dist/**', 'dist_installer/**', 'node_modules/**', 'memory_vault/**', 'backend/**'] },
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.es2021,
      },
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: { react, 'react-hooks': reactHooks },
    settings: { react: { version: 'detect' } },
    rules: {
      // --- CRASH-CLASS RULES: these catch ReferenceError / undefined component bugs ---
      'no-undef': 'error',              // e.g. <Activity /> used but never imported
      'react/jsx-no-undef': 'error',    // e.g. <Foo /> with no Foo in scope
      'react/jsx-uses-vars': 'error',
      'react/jsx-uses-react': 'off',

      // --- Correctness ---
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^[A-Z_]' }],
      'no-dupe-keys': 'error',
      'no-dupe-args': 'error',
      'no-dupe-class-members': 'error',
      'no-duplicate-case': 'error',
      'no-redeclare': 'error',
      'no-self-assign': 'error',
      'no-unreachable': 'error',
      'no-constant-condition': ['error', { checkLoops: false }],
      'no-empty': ['warn', { allowEmptyCatch: true }],
      'use-isnan': 'error',
      'valid-typeof': 'error',
      'no-fallthrough': 'error',
      'no-cond-assign': ['error', 'except-parens'],
      'require-atomic-updates': 'off',
      'no-async-promise-executor': 'warn',

      // --- React correctness (kept lenient where the codebase is intentionally loose) ---
      'react/jsx-key': 'warn',
      'react/no-children-prop': 'error',
      'react/no-direct-mutation-state': 'error',
      'react/jsx-no-duplicate-props': 'error',
      'react/no-unknown-property': 'warn',
      'react-hooks/rules-of-hooks': 'error',
    },
  },
  {
    files: ['electron/**/*.js', '*.config.js', 'eslint.config.js', 'run_backend.js'],
    languageOptions: {
      globals: { ...globals.node },
    },
    rules: {
      'no-undef': 'error',
    },
  },
];
