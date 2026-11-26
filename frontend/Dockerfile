# ----------------------------------------------------
# Stage 1: Base Alpine Image with libc compatibility
# ----------------------------------------------------
FROM node:20-alpine AS base
RUN apk add --no-cache libc6-compat
WORKDIR /app

# ----------------------------------------------------
# Stage 2: Install dependencies strictly via npm ci
# ----------------------------------------------------
FROM base AS deps
COPY package.json package-lock.json ./
COPY scripts/copy-monaco.js ./scripts/
RUN npm ci

# ----------------------------------------------------
# Stage 3: Build Next.js standalone bundle
# ----------------------------------------------------
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set production environment and placeholder keys for static prerendering
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_placeholder_for_build_only \
    NEXT_PUBLIC_API_URL=http://backend:8000

RUN npm run build

# ----------------------------------------------------
# Stage 4: Minimal Production Runner (non-root)
# ----------------------------------------------------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

# Create unprivileged system group and user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy static assets and public directory (includes Monaco AMD distribution)
COPY --from=builder /app/public ./public

# Set correct permissions for Next.js prerender cache
RUN mkdir .next && chown nextjs:nodejs .next

# Copy standalone bundle and static assets
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
