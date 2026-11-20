import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
const proxy = { '/api': { target: process.env.API_ORIGIN || 'http://127.0.0.1:8000', changeOrigin: true } };
export default defineConfig({ plugins: [react()], server: { port: 5173, strictPort: true, proxy }, preview: { port: 5173, strictPort: true, proxy }, test: { environment: 'jsdom', include: ['src/**/*.test.{ts,tsx}'], setupFiles: ['./src/test-setup.ts'] } });
