FROM node:20-slim AS datapunk-frontend-builder

WORKDIR /app

# Add build dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json ./
RUN npm install

# Copy the rest and build
COPY . .
RUN npm run build

# Cleanup
RUN npm cache clean --force \
    && rm -rf /root/.npm \
    && apt-get clean autoclean \
    && apt-get autoremove --yes

FROM node:20-slim AS datapunk-frontend

WORKDIR /app

# Copy source files for development
COPY . .
COPY --from=datapunk-frontend-builder /app/node_modules ./node_modules

EXPOSE 3000

# Start the application in development mode
CMD ["npm", "run", "dev", "--", "--host"]
