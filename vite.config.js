import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      allowedHosts: ['localhost', '.e2b.app'],
      proxy: {
        '/api': { target: env.SECONDBRAIN_BACKEND_TARGET || 'http://127.0.0.1:8000', changeOrigin: true },
        '/ws': { target: env.SECONDBRAIN_BACKEND_TARGET || 'http://127.0.0.1:8000', ws: true },
      },
    },
    build: { outDir: 'dist' },
  };
});
