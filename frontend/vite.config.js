import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {proxy: {
    '/odoo': {target: 'http://127.0.0.1:8069', changeOrigin: false, rewrite: (path) => path.replace(/^\/odoo/, '')},
    '/auth_oauth': {target: 'http://127.0.0.1:8069', changeOrigin: false},
  }},
});
