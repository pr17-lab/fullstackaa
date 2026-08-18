import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        port: 3000,
        // Bind to all interfaces so the container is reachable from the host.
        host: '0.0.0.0',
        proxy: {
            '/api': {
                // In Docker Compose the backend service is named "backend".
                // For non-Docker local dev, set VITE_BACKEND_URL=http://127.0.0.1:8000
                // in frontend/.env.local (git-ignored).
                target: process.env.VITE_BACKEND_URL || 'http://backend:8000',
                changeOrigin: true,
                // Forward WebSocket upgrades through the dev proxy
                ws: true,
            }
        }
    }
})

