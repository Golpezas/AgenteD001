# ──────────────────────────────────────────────
# Frontend Dockerfile — Multi-stage
# ──────────────────────────────────────────────
# Stage 1: Build con Node 20
# Stage 2: Servir con Nginx Alpine
# ──────────────────────────────────────────────

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
