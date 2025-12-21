# Production Dockerfile for Games Service
FROM node:20-slim AS base

# Install OpenSSL for Prisma
RUN apt-get update && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies stage
FROM base AS deps
COPY games/package.json games/package-lock.json* ./
RUN npm ci --only=production

# Builder stage
FROM base AS builder
COPY games/package.json games/package-lock.json* ./
RUN npm ci
COPY games/ .

# Copy prisma schema from hunt project
COPY hunt/prisma ./prisma
RUN npx prisma generate
RUN npm run build

# Runner stage
FROM base AS runner
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs || true && \
    adduser --system --uid 1001 --ingroup nodejs gameuser

COPY --from=builder --chown=gameuser:nodejs /app/dist ./dist
COPY --from=builder --chown=gameuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=gameuser:nodejs /app/package.json ./package.json
COPY --from=builder --chown=gameuser:nodejs /app/public ./public

USER gameuser

EXPOSE 9000

CMD ["node", "dist/server.js"]
