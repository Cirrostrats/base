# Docker Compose Usage Guide

This guide explains how to use the different Docker Compose configurations for development, production, and homelab environments.

## Overview

The project uses Docker Compose with a base configuration and environment-specific override files:

- **`docker-compose.yml`** - Base configuration (frontend, backend, nginx)
- **`docker-compose.dev.yml`** - Development environment overrides
- **`docker-compose.prod.yml`** - Production environment overrides
- **`docker-compose.homelab.yml`** - Homelab environment with Celery workers
- **`docker-compose-fallback.yml`** - Complete standalone configuration (all services)

### `-f` flag merge, inheritance and override semantics:
The `-f` flag creates a left-to-right merge pipeline where each subsequent file overrides or extends the previous one. Basically the -f flag is incremental merge with later the file the higher the override priority. Understanding merge semantics is crucial. You can selectively override(from the right) just what you need while inheriting the rest fromt he previously stated file(from left).

### `depends_on` config for a service:
When a `depends_on` is specified into service it creates an upward dependency pull, not a downward one. When you say "start backend," Compose asks "what does backend need?" and starts those dependencies. It does not ask "what needs backend?" The dependency relationship flows one direction.


## Quick Start

### Development Environment

For local development with hot-reload and volume mounting:


*** mind the `-f` flag ***
```bash
# Verify proper .env variables are created/used for dev.
# Spin(for dev only) both backend and frontend in the background. you can later use logs instead of up with -f flag to see logs
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
# Spin individual ones:
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d frontend
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d backend
```


**dev features:**
- Frontend runs on port `5173` (Vite dev server)
- Backend runs on port `8000` with auto-reload(hot-reload)
- Source code is mounted as volumes for live updates
- NODE_ENV set to `development`
- File watching enabled for hot-reload

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

### Production Environment

For production deployment:

```bash
# Verify proper .env variables are created/used for prod before running this command since it'll be baked into the image.
# NOTE: may have to build first if you were already running dev previously since some dev stuff wouldve hard baked into the image.
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Features:**
- Frontend built and served via Nginx (production build)
- Backend runs in production mode (no auto-reload)
- NODE_ENV set to `production`
- ENV set to `production`
- Only port 80 exposed (via Nginx)
- No volume mounting (uses containerized code)

**Access:**
- Application: http://localhost:80 (via Nginx)

### Homelab Environment

For homelab deployment with Celery workers and Redis:

```bash
# NOTE: Mind that base compose is not stated since otherwise i'll also spin up frontend and backend and for homelab theyre not needed.
docker compose -f docker-compose.homelab.yml up -d
```

**Features:**
- Adds Redis service (port 6379)
- Adds Celery worker for async task processing
- Adds Celery Beat for scheduled tasks
- Uses Docker Compose profiles to conditionally start those services

**Services:**
- `redis` - Message broker for Celery
- `celery` - Worker process for async tasks
- `celery-beat` - Scheduler for periodic tasks

**Note:** The Celery services use the `production` profile, so they only start when explicitly enabled.

### Fallback Configuration

The `docker-compose-fallback.yml` is a complete standalone configuration that includes all services and is only to be used as a fallback:

```bash
docker compose -f docker-compose-fallback.yml up -d
```

This file contains everything in one place and can be used as a reference or when you need a single-file configuration.

## Service Details

### Frontend Service

- **Build Context:** `./cirrostrats-frontend`
- **Dockerfile:** `Dockerfile.frontend`
- **Development:** 
  - Port: `5173:5173` (Vite dev server)
  - Volumes: Source code mounted for hot-reload
  - Environment: `NODE_ENV=development`
- **Production:**
  - Build args: `NODE_ENV=production`
  - Served via Nginx (no direct port exposure)

### Backend Service

- **Build Context:** `./cirrostrats-backend`
- **Dockerfile:** `Dockerfile.backend`
- **Development:**
  - Port: `8000:8000`
  - Volumes: Source code mounted
  - Environment: `ENV=development`
  - Auto-reload enabled
- **Production:**
  - Environment: `ENV=production`
  - No auto-reload
  - Accessible via Nginx proxy

### Nginx Service - (prod only)

- **Image:** `nginx:latest`
- **Port:** `80:80` (in prod)
- **Configuration:** `./nginx/nginx.conf`
- **Function:** 
  - Proxies frontend requests to frontend service
  - Proxies `/api/*` requests to backend service
  - Configured for `cirrostrats.us` domain

### Redis Service (Homelab only - requires production profiles tag)

- **Image:** `redis:latest`
- **Port:** `6379:6379`
- **Purpose:** Message broker for Celery tasks
- **Profile:** `production` (only starts with `--profile production`)

### Celery Worker (Homelab only - requires production profiles tag)

- **Build Context:** `./cirrostrats-backend`
- **Dockerfile:** `routes/Dockerfile.celery`
- **Command:** `celery -A routes.celery_app worker --loglevel=info`
- **Depends on:** Redis
- **Profile:** `production`
- **Note:** Code changes require container restart (volumes don't auto-reload)

### Celery Beat (Homelab only - requires production profiles tag)

- **Build Context:** `./cirrostrats-backend`
- **Dockerfile:** `routes/Dockerfile.celery`
- **Command:** `celery -A routes.celery_app beat --loglevel=info`
- **Depends on:** Redis, Celery worker
- **Profile:** `production`
- **Purpose:** Scheduler for periodic tasks

## Common Commands

### Starting Services

```bash
# Development
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Homelab with Celery
docker compose -f docker-compose.yml -f docker-compose.homelab.yml --profile production up -d
```

### Stopping Services

```bash
# Stop all services
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# Stop and remove volumes
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

### Rebuilding Services

```bash
# Rebuild all services
docker compose -f docker-compose.yml -f docker-compose.dev.yml build

# Rebuild specific service
docker compose -f docker-compose.yml -f docker-compose.dev.yml build frontend

# Rebuild without cache
docker compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache
```

### Viewing Logs

```bash
# All services
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Specific service
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f backend

# Last 100 lines
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs --tail=100
```

### Restarting Services

```bash
# Restart all services
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart

# Restart specific service
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart backend
```

### Checking Service Status

```bash
# List running containers
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps

# View service status
docker compose -f docker-compose.yml -f docker-compose.dev.yml top
```

## Environment Differences

| Feature | Development | Production | Homelab |
|---------|------------|------------|---------|
| **Frontend Port** | 5173 (direct) | 80 (via Nginx) | 80 (via Nginx) |
| **Backend Port** | 8000 (direct) | 8000 (via Nginx) | 8000 (via Nginx) |
| **Hot Reload** | ✅ Enabled | ❌ Disabled | ❌ Disabled |
| **Volume Mounting** | ✅ Yes | ❌ No | ❌ No (except Celery) |
| **NODE_ENV** | development | production | production |
| **ENV** | development | production | production |
| **Celery Workers** | ❌ No | ❌ No | ✅ Yes |
| **Redis** | ❌ No | ❌ No | ✅ Yes |
| **Build Mode** | Development | Production | Production |

## Network Configuration

All services are connected via the `base-network` bridge network, allowing them to communicate using service names:

- Frontend can reach backend at `http://backend:8000`
- Nginx can reach frontend at `http://frontend:80`
- Nginx can reach backend at `http://backend:8000`
- Celery workers can reach Redis at `redis:6379`

## Volume Management

### Development Volumes

- `./cirrostrats-frontend:/app` - Frontend source code
- `./cirrostrats-backend:/app` - Backend source code
- `node_modules:/app/node_modules` - Prevents overwriting container node_modules
- `./nginx/nginx.conf:/etc/nginx/nginx.conf` - Nginx configuration commented out for prod

### Production Volumes

- No source code volumes (code is baked into images)
- Only Nginx config volume (if needed)

## Troubleshooting

### Port Already in Use

If you get a port conflict error:

```bash
# Check what's using the port
lsof -i :80
lsof -i :5173
lsof -i :8000

# Stop conflicting services or change ports in compose files
```

### Services Not Starting

```bash
# Check logs for errors
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs

# Verify Docker is running
docker ps

# Rebuild images
docker compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache
```

### Celery Not Working

```bash
# Ensure Redis is running
docker compose -f docker-compose.yml -f docker-compose.homelab.yml ps redis

# Check Celery logs
docker compose -f docker-compose.yml -f docker-compose.homelab.yml logs celery

# Restart Celery services
docker compose -f docker-compose.yml -f docker-compose.homelab.yml restart celery celery-beat
```

### Changes Not Reflecting

**Development:**
- Frontend: Changes should hot-reload automatically
- Backend: Changes should auto-reload (if `--reload` flag is used)
- Nginx: Restart nginx service after config changes

**Production:**
- Rebuild images after code changes:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.prod.yml build
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
  ```

**Celery:**
- Celery workers require container restart for code changes:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.homelab.yml restart celery celery-beat
  ```

## Best Practices

1. **Development:** Use `docker-compose.dev.yml` for local development with hot-reload
2. **Production:** Use `docker-compose.prod.yml` for production deployments
3. **Testing:** Test production builds locally before deploying:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up
   ```
4. **Cleanup:** Regularly clean up unused images and volumes:
   ```bash
   docker system prune -a
   docker volume prune
   ```
5. **Security:** Never commit sensitive environment variables. Use `.env` files or secrets management.

## Additional Notes

- The base `docker-compose.yml` defines the core services and network
- Override files (`*.dev.yml`, `*.prod.yml`) extend and modify the base configuration
- Multiple `-f` flags allow composing multiple override files
- Docker Compose profiles (`--profile production`) enable conditional service startup
- The `node_modules` volume prevents conflicts between host and container dependencies

