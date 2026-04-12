FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json /frontend/package.json
COPY frontend/package-lock.json /frontend/package-lock.json
COPY frontend/tsconfig.json /frontend/tsconfig.json
COPY frontend/tsconfig.app.json /frontend/tsconfig.app.json
COPY frontend/tsconfig.node.json /frontend/tsconfig.node.json
COPY frontend/vite.config.ts /frontend/vite.config.ts
COPY frontend/index.html /frontend/index.html
COPY frontend/logo /frontend/logo
COPY frontend/src /frontend/src

RUN npm ci && npm run build

FROM caddy:2.8-alpine

COPY deploy/caddy/Caddyfile /etc/caddy/Caddyfile
COPY --from=frontend-builder /frontend/dist /srv/frontend
