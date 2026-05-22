import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { cp } from 'fs/promises';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [
    react(),
    {
      // Copy assets/ → dist/assets/ after build (images aren't imported directly)
      name: 'copy-root-assets',
      async closeBundle() {
        try {
          await cp(
            path.resolve(__dirname, 'assets'),
            path.resolve(__dirname, 'dist/assets'),
            { recursive: true }
          );
        } catch (e) {
          console.warn('[copy-root-assets] skipped:', e.message);
        }
      }
    }
  ],
  base: '/',
  // During dev: allow serving files from project root so /assets/* resolves
  server: {
    fs: { strict: false }
  }
});
