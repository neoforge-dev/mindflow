#!/usr/bin/env node

/**
 * esbuild configuration for ChatGPT Apps SDK bundle
 * Compiles TypeScript React components into a single JavaScript file
 */

const esbuild = require('esbuild');
const path = require('path');

const isWatch = process.argv.includes('--watch');
const isDev = process.argv.includes('--dev') || isWatch;

const config = {
  entryPoints: ['src/index.tsx'],
  bundle: true,
  outfile: 'dist/index.js',
  platform: 'browser',
  target: ['es2020'],
  format: 'esm',
  sourcemap: isDev,
  minify: !isDev,
  treeShaking: true,

  // External dependencies (provided by ChatGPT Apps SDK runtime)
  external: ['react', 'react-dom'],

  // JSX configuration
  jsx: 'automatic',
  jsxImportSource: 'react',

  // Loader configuration
  loader: {
    '.ts': 'tsx',
    '.tsx': 'tsx',
  },

  // Define environment variables
  define: {
    'process.env.NODE_ENV': isDev ? '"development"' : '"production"',
  },

  // Log level
  logLevel: 'info',
};

async function build() {
  try {
    console.log(`Building ${isDev ? 'development' : 'production'} bundle...`);

    if (isWatch) {
      const ctx = await esbuild.context(config);
      await ctx.watch();
      console.log('Watching for changes...');
    } else {
      await esbuild.build(config);
      console.log('Build complete!');
      console.log(`Output: ${path.resolve('dist/index.js')}`);
    }
  } catch (error) {
    console.error('Build failed:', error);
    process.exit(1);
  }
}

build();
