# =============================================================================
# Stage 1: Build — compile TypeScript and bundle with Vite
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first — Docker layer cache means npm install only re-runs
# when package.json / package-lock.json change, not on every source change.
COPY package.json package-lock.json ./

# Install all dependencies (including devDeps needed for tsc + vite build)
RUN npm ci --prefer-offline

# Copy source files (honoring .dockerignore)
COPY . .

# Build — runs `tsc && vite build` (from package.json "build" script)
# VITE_API_URL is intentionally NOT baked in here — all API calls go through
# the nginx proxy, so the frontend always uses relative paths (/api/...).
RUN npm run build

# =============================================================================
# Stage 2: Serve — nginx serves the static bundle + proxies /api/* to backend
# =============================================================================
FROM nginx:1.27-alpine AS runtime

# Install gettext for envsubst (used to inject BACKEND_URL at container start)
RUN apk add --no-cache gettext

# Security: remove default nginx config and site
RUN rm -f /etc/nginx/conf.d/default.conf /etc/nginx/nginx.conf

# Copy our nginx config TEMPLATE (contains ${BACKEND_URL} placeholder)
# envsubst rewrites this to /tmp/nginx.conf at container start.
COPY nginx.conf.template /etc/nginx/nginx.conf.template

# Copy the Vite build output from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# nginx needs to write its PID and logs; set up directories.
# The template file is owned by nginx so envsubst output goes to /tmp (world-writable).
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run \
 && chown -R nginx:nginx /var/cache/nginx /var/log/nginx /var/run \
                         /usr/share/nginx/html /etc/nginx/nginx.conf.template

# Switch to non-root nginx user
USER nginx

# Expose port 80 (nginx default)
EXPOSE 80

# Health check — nginx serves a 200 on /
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

# At startup:
#   1. Set default BACKEND_URL fallback if unset (http://localhost:8000)
#   2. Substitute ${BACKEND_URL} in the template → /tmp/nginx.conf
#   3. Start nginx pointing at the rendered config
CMD ["/bin/sh", "-c", "export BACKEND_URL=\"${BACKEND_URL:-http://localhost:8000}\" && envsubst '$BACKEND_URL' < /etc/nginx/nginx.conf.template > /tmp/nginx.conf && nginx -g 'daemon off;' -c /tmp/nginx.conf"]
