# Deployment Guide

This guide covers deploying the Signals & Systems Web Platform to production.

## Prerequisites

- Docker and Docker Compose installed
- GitHub account with repository access
- Cloud provider account (Render, Railway, DigitalOcean, or AWS)

## Quick Start

### Local Development (Docker Compose)

```bash
cd signals-web-platform

# Start development environment
docker-compose up

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Production Test

```bash
# Build and run production images locally
docker-compose -f docker-compose.prod.yml up --build

# Access at http://localhost (port 80)
```

## Cloud Deployment Options

### Option 1: Render.com (Easiest)

**Free tier available, no credit card required.**

1. Go to [render.com](https://render.com) and connect your GitHub account

2. **Deploy Backend:**
   - Create new "Web Service"
   - Select your repository
   - Root Directory: `signals-web-platform/backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`
   - Add environment variables from `.env.production`

3. **Deploy Frontend:**
   - Create new "Static Site"
   - Root Directory: `signals-web-platform/frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `dist`
   - Add environment variable: `VITE_API_URL=https://your-backend.onrender.com`

### Option 2: Railway.app

**Simple deployment with GitHub integration.**

1. Go to [railway.app](https://railway.app)

2. Create new project from GitHub

3. Add two services:
   - **Backend:** Select `signals-web-platform/backend`, use Dockerfile
   - **Frontend:** Select `signals-web-platform/frontend`, use Dockerfile

4. Configure environment variables

5. Deploy automatically on push

### Option 3: DigitalOcean App Platform

**Balanced performance and cost ($12+/month).**

1. Go to [cloud.digitalocean.com/apps](https://cloud.digitalocean.com/apps)

2. Create new App from GitHub

3. Configure components:
   - Add backend service (Docker)
   - Add frontend service (Static Site)

4. Set environment variables

5. Deploy

### Option 4: AWS ECS + CloudFront (Enterprise)

**Production-grade infrastructure for high availability.**

Architecture:
- Backend: ECS Fargate (serverless containers)
- Frontend: S3 + CloudFront CDN
- Database: RDS PostgreSQL (optional)
- Monitoring: CloudWatch

Setup steps:
1. Create ECR repositories for backend and frontend images
2. Push Docker images to ECR
3. Create ECS task definitions
4. Create ECS service with Application Load Balancer
5. Deploy frontend to S3
6. Create CloudFront distribution
7. Configure Route53 DNS

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy.yml`) automatically:

1. **On Pull Request:**
   - Runs backend tests
   - Builds frontend
   - Validates Docker builds

2. **On Push to `develop`:**
   - All PR checks
   - Builds and pushes Docker images
   - Deploys to staging environment

3. **On Push to `main`:**
   - All checks and builds
   - Deploys to production

### Required GitHub Secrets

Configure in: Repository Settings > Secrets and variables > Actions

| Secret | Description |
|--------|-------------|
| `DOCKER_USERNAME` | Docker Hub username (optional) |
| `DOCKER_PASSWORD` | Docker Hub access token (optional) |
| `RENDER_DEPLOY_HOOK` | Render deployment webhook URL |
| `DO_APP_ID` | DigitalOcean App ID |

### Required GitHub Variables

Configure in: Repository Settings > Secrets and variables > Actions > Variables

| Variable | Description |
|----------|-------------|
| `PRODUCTION_URL` | Production URL for health checks |
| `STAGING_URL` | Staging URL for health checks |

## Health Checks

Verify deployment with these endpoints:

```bash
# Basic health check
curl https://yourdomain.com/health
# Expected: {"status": "ok"}

# Detailed readiness check
curl https://yourdomain.com/health/ready
# Expected: {"status": "ready", "uptime_seconds": ..., "cache_hit_rate": ...}

# Performance analytics
curl https://yourdomain.com/api/v1/analytics
# Expected: Full performance metrics
```

## SSL/HTTPS Setup

Most cloud platforms provide automatic SSL:

- **Render:** Automatic HTTPS with Let's Encrypt
- **Railway:** Automatic HTTPS
- **DigitalOcean:** Free Let's Encrypt certificates
- **AWS:** AWS Certificate Manager (free)

For custom domains:
1. Purchase domain (Namecheap, GoDaddy, etc.)
2. Add domain in cloud provider dashboard
3. Configure DNS records (CNAME or A record)
4. SSL certificate auto-provisioned

## Scaling for 100+ Concurrent Users

### Horizontal Scaling

For 100 concurrent users, run 4 backend instances:

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 4
```

Cloud platforms handle this automatically:
- **Render:** Set "Num of Instances" to 4
- **Railway:** Enable auto-scaling
- **DigitalOcean:** Increase container count
- **AWS:** Configure Auto Scaling Groups

### Performance Optimization

Already configured:
- GZip compression (60-80% bandwidth reduction)
- LRU caching (80%+ hit rate expected)
- WebSocket connection pooling
- Plot data subsampling

### Load Testing

Before launch, verify with:

```bash
# Install Apache Bench
apt-get install apache2-utils

# Test 100 concurrent users, 1000 total requests
ab -n 1000 -c 100 https://yourdomain.com/api/v1/simulations

# Expected results:
# - Response time: <100ms
# - Failed requests: 0
# - Requests/sec: >100
```

## Monitoring Setup

### Uptime Monitoring (Free)

1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Create HTTP(s) monitor for `https://yourdomain.com/health`
3. Set check interval: 5 minutes
4. Configure email alerts

### Error Tracking (Optional)

Add Sentry for production error tracking:

```python
# backend/main.py
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=0.1,
    environment="production"
)
```

### Performance Metrics

Access built-in analytics:
```bash
curl https://yourdomain.com/api/v1/analytics
```

Returns:
- Request counts and latencies
- Cache hit rates
- WebSocket connection stats
- Error rates

## Troubleshooting

### Container Logs

```bash
# Local Docker
docker-compose logs backend
docker-compose logs frontend

# Production (varies by platform)
# Render: Dashboard > Logs
# Railway: Dashboard > Deployments > Logs
# AWS: CloudWatch Logs
```

### Common Issues

**Backend not starting:**
- Check `LOG_LEVEL=DEBUG` in environment
- Verify all dependencies in requirements.txt
- Check port 8000 is not in use

**Frontend build fails:**
- Clear node_modules: `rm -rf node_modules && npm ci`
- Check Node version matches (18.x)

**WebSocket connection drops:**
- Verify nginx WebSocket proxy configuration
- Check proxy timeouts (should be 86400s for long connections)

**High response times:**
- Check cache hit rate in `/api/v1/analytics`
- Verify GZip compression is working
- Consider adding more backend replicas

## Post-Deployment Checklist

- [ ] Health check responding (`/health`)
- [ ] All 13 simulations loading
- [ ] WebSocket real-time updates working
- [ ] HTTPS/SSL configured
- [ ] Custom domain set up
- [ ] Uptime monitoring active
- [ ] Error tracking configured (optional)
- [ ] Load tested with 100 concurrent users
- [ ] Response times < 100ms
- [ ] Cache hit rate > 80%
- [ ] Team access configured
