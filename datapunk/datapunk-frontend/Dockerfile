FROM node:20-slim AS datapunk-frontend-builder

WORKDIR /app

# Add build dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy configuration files
COPY svelte.config.js ./
COPY tsconfig.json ./
COPY vite.config.ts ./

# Copy source files
COPY src/ ./src/
COPY static/ ./static/

# Initialize SvelteKit
RUN npm run prepare

# Build the application
RUN npm run build

FROM node:20-slim AS datapunk-frontend

WORKDIR /app

# Copy built files and dependencies
COPY --from=datapunk-frontend-builder /app/build ./build
COPY --from=datapunk-frontend-builder /app/node_modules ./node_modules
COPY --from=datapunk-frontend-builder /app/package.json ./

EXPOSE 3000

CMD ["node", "build"]
