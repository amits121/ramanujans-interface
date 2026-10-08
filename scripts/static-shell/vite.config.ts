import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The output directory is passed on the command line by scripts/build_site.py.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: { emptyOutDir: true, sourcemap: false },
});
