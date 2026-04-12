FROM node:20-alpine

WORKDIR /frontend

COPY frontend/package.json /frontend/package.json
COPY frontend/package-lock.json /frontend/package-lock.json
COPY frontend/tsconfig.json /frontend/tsconfig.json
COPY frontend/tsconfig.app.json /frontend/tsconfig.app.json
COPY frontend/tsconfig.node.json /frontend/tsconfig.node.json
COPY frontend/vite.config.ts /frontend/vite.config.ts
COPY frontend/index.html /frontend/index.html
COPY frontend/src /frontend/src

RUN npm ci
