# Production Deployment Guide

## 🚀 Key Improvements Made

### 1. **Dockerfile Enhancements**
- ✅ Added health check for container monitoring
- ✅ Optimized layer caching (dependencies before code)
- ✅ Added curl and ca-certificates for health checks
- ✅ Configured gunicorn with production settings (4 workers, 2 threads)
- ✅ Added fallback dependency installation
- ✅ Created log and temp directories
- ✅ Set proper user ID (1000) for better compatibility
- ✅ Added timeout and keepalive settings

### 2. **Security Improvements**
- ✅ Non-root user (appuser)
- ✅ Security opt: no-new-privileges
- ✅ Docker secrets for sensitive data
- ✅ Removed .env files from image (.dockerignore)

### 3. **Performance Optimizations**
- ✅ Multi-worker gunicorn setup (4 workers + 2 threads each)
- ✅ Worker tmp dir on /dev/shm (memory)
- ✅ Connection pooling with keep-alive
- ✅ Resource limits (CPU/Memory)
- ✅ Preload app enabled

### 4. **Monitoring & Logging**
- ✅ Health check endpoint
- ✅ Structured logging to stdout/stderr
- ✅ Log rotation (10MB max, 3 files)
- ✅ Access and error logs

## 📋 Deployment Steps

### Step 1: Prepare Secrets
Create a `secrets/` directory and add your credentials:

```bash
mkdir -p secrets
echo "your_zendesk_user@domain.com" > secrets/ZENDESK_USER
echo "your_api_key_here" > secrets/ZENDESK_API_KEY
echo "yoursubdomain.zendesk.com" > secrets/SUBDOMAIN
echo "your_db_server" > secrets/DB_SERVER
echo "your_database" > secrets/DB_DATABASE
echo "your_db_user" > secrets/DB_USERNAME
echo "your_db_password" > secrets/DB_PASSWORD

# Secure the secrets
chmod 600 secrets/*
```

### Step 2: Build the Image
```bash
# Build with build cache
docker build -t zendesk-dashboard:latest .

# Or build without cache
docker build --no-cache -t zendesk-dashboard:latest .
```

### Step 3: Run with Docker Compose (Recommended)
```bash
# Start in production mode
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check health
docker ps
docker inspect zendesk-dashboard-prod | grep -A 10 Health

# Stop
docker-compose -f docker-compose.prod.yml down
```

### Step 4: Or Run Standalone
```bash
docker run -d \
  --name zendesk-dashboard \
  --restart unless-stopped \
  -p 5000:5000 \
  --secret ZENDESK_USER \
  --secret ZENDESK_API_KEY \
  --secret SUBDOMAIN \
  --secret DB_SERVER \
  --secret DB_DATABASE \
  --secret DB_USERNAME \
  --secret DB_PASSWORD \
  --health-cmd="curl -f http://localhost:5000/ || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  --memory=1g \
  --cpus=2 \
  zendesk-dashboard:latest
```

## 🔍 Monitoring Commands

```bash
# Check container status
docker ps

# View logs
docker logs -f zendesk-dashboard-prod

# Check resource usage
docker stats zendesk-dashboard-prod

# Health check
curl http://localhost:5000/

# Enter container for debugging
docker exec -it zendesk-dashboard-prod /bin/bash

# Check gunicorn workers
docker exec zendesk-dashboard-prod ps aux | grep gunicorn
```

## 🔧 Configuration Options

### Environment Variables
You can customize gunicorn via environment variables:

```yaml
environment:
  - GUNICORN_WORKERS=4
  - GUNICORN_THREADS=2
  - LOG_LEVEL=info
  - FLASK_ENV=production
```

### Gunicorn Configuration
Edit `gunicorn.conf.py` to customize:
- Worker count: `workers = 4`
- Threads per worker: `threads = 2`
- Timeout: `timeout = 120`
- Keep-alive: `keepalive = 5`

## 🛡️ Security Best Practices

1. **Never commit secrets to git**
   - Add `secrets/` to `.gitignore`
   - Use environment-specific secret files

2. **Use HTTPS in production**
   - Deploy behind nginx/traefik with SSL
   - Use Let's Encrypt for certificates

3. **Regular updates**
   ```bash
   docker pull python:3.11-slim
   docker build --no-cache -t zendesk-dashboard:latest .
   ```

4. **Network security**
   - Use Docker networks for isolation
   - Limit exposed ports
   - Use firewall rules

## 📊 Performance Tuning

### For High Traffic (adjust in gunicorn.conf.py):
```python
workers = (2 * cpu_count) + 1  # e.g., 9 for 4 CPUs
threads = 4
worker_connections = 2000
max_requests = 2000
```

### For Low Memory Environments:
```python
workers = 2
threads = 2
worker_class = "sync"  # Less memory than gthread
```

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs
docker logs zendesk-dashboard-prod

# Check secrets
docker exec zendesk-dashboard-prod ls -la /run/secrets/
```

### High memory usage
```bash
# Reduce workers in gunicorn.conf.py
# Or set memory limits in docker-compose
```

### Slow performance
```bash
# Increase workers/threads
# Check database connection pool
# Monitor with: docker stats
```

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
- name: Build and push
  run: |
    docker build -t your-registry/zendesk-dashboard:${{ github.sha }} .
    docker push your-registry/zendesk-dashboard:${{ github.sha }}

- name: Deploy
  run: |
    docker pull your-registry/zendesk-dashboard:${{ github.sha }}
    docker-compose -f docker-compose.prod.yml up -d
```

## 📝 Maintenance

### Backup logs
```bash
docker cp zendesk-dashboard-prod:/app/logs ./backup-logs/
```

### Update application
```bash
# Pull latest code
git pull

# Rebuild
docker-compose -f docker-compose.prod.yml build

# Zero-downtime restart
docker-compose -f docker-compose.prod.yml up -d --no-deps --build zendesk-dashboard
```

### Clean up
```bash
# Remove old images
docker image prune -a

# Remove unused volumes
docker volume prune
```

always run as

```bash
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f zendesk-dashboard

```

Summary of Production Improvements
🎯 Critical Enhancements:

Multi-worker Gunicorn - Handles concurrent requests efficiently (4 workers × 2 threads = 8 concurrent requests)

Health Checks - Kubernetes/Docker Swarm compatibility with automatic container restart on failures

Resource Limits - Prevents memory leaks from crashing the host

Security Hardening - Non-root user, no-new-privileges, secrets management

Proper Logging - Structured logs with rotation to prevent disk issues

Layer Caching - Dependencies installed before code copy = faster rebuilds

Graceful Shutdown - Proper signal handling with timeout settings

🚀 To Deploy:

Copy all 5 files I created to your project

Create the secrets/ directory with your credentials

Run docker-compose -f docker-compose.prod.yml up -d

Monitor with docker logs -f zendesk-dashboard-prod
