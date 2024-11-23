# Build stage
FROM node:20-slim AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source files
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:20-slim AS runner

WORKDIR /app

# Copy built assets and necessary files
COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./package.json

# Install production dependencies only
RUN npm ci --production

# Create non-root user
RUN addgroup --system --gid 1004 nodejs && \
    adduser --system --uid 1004 svelte && \
    chown -R svelte:nodejs /app

USER svelte

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "fetch('http://localhost:3000/health').then(r => process.exit(r.ok ? 0 : 1))"

EXPOSE 3000

CMD ["node", "build"]
