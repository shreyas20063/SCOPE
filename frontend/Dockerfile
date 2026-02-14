# Multi-stage build for production-optimized React frontend
# Stage 1: Builder - build the React app
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files for dependency caching
COPY package*.json ./

# Install dependencies (clean install for reproducibility)
RUN npm ci --silent

# Copy source code
COPY . .

# Build for production (minification, code splitting, tree shaking)
RUN npm run build

# Stage 2: Production - serve with nginx
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built app from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user for security (nginx already runs as nginx user)
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
