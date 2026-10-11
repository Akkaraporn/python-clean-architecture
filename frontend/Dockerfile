# syntax=docker/dockerfile:1

# ---- build: compile the static site with Node -----------------------------------------
FROM node:24-alpine AS build

WORKDIR /app

# Install dependencies in their own layer so code-only changes reuse it.
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund

COPY . .

# Vite inlines VITE_* values into the JavaScript at build time; changing the API URL
# therefore needs a rebuild, not just a new runtime environment variable.
ARG VITE_API_BASE_URL
RUN test -n "$VITE_API_BASE_URL" || (echo "VITE_API_BASE_URL build arg is required" && exit 1)
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# ---- runtime: only nginx and the built files; no Node, no sources ---------------------
FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:8080/ || exit 1
