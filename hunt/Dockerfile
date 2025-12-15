FROM node:20-slim AS base

RUN apt-get update -y && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*
WORKDIR /app

FROM base AS deps
COPY package.json package-lock.json* ./
RUN --mount=type=cache,target=/root/.npm npm ci

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN --mount=type=cache,target=/root/.npm npx prisma generate
RUN --mount=type=cache,target=/app/.next/cache npm run build

FROM base AS runner
RUN apt-get update -y && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN groupadd --system --gid 1001 nodejs
RUN useradd --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=builder --chown=nextjs:nodejs /app/node_modules/@prisma ./node_modules/@prisma
COPY --from=builder --chown=nextjs:nodejs /app/node_modules/.bin ./node_modules/.bin
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/node_modules/prisma ./node_modules/prisma
COPY --from=builder /app/package.json ./package.json
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown nextjs:nodejs /entrypoint.sh

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV PATH="/app/node_modules/.bin:$PATH"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["node", "server.js"]
