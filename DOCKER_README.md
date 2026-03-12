# Bharat-Grid AI Docker Configuration

This document provides comprehensive instructions for deploying the Bharat-Grid AI system using Docker containers.

## Overview

The Docker configuration includes:
- **Backend**: Python FastAPI server with Pathway engine and RAG system
- **Frontend**: React TypeScript dashboard with production-optimized build
- **ChromaDB**: Vector database for AI embeddings
- **Redis**: Caching layer for performance optimization
- **Nginx**: Reverse proxy for production deployment

## Quick Start

### Prerequisites

- Docker Engine 20.10+ and Docker Compose 2.0+
- At least 4GB RAM available for containers
- OpenAI API key (for RAG functionality)

### Development Environment

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd bharat-grid-ai
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

2. **Start development environment**:
   ```bash
   # Linux/macOS
   ./scripts/deploy.sh dev
   
   # Windows
   scripts\deploy.bat dev
   ```

3. **Access the application**:
   - Frontend Dashboard: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - ChromaDB: http://localhost:8001

### Production Environment

1. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with production settings
   ```

2. **Start production environment**:
   ```bash
   # Linux/macOS
   ./scripts/deploy.sh prod
   
   # Windows
   scripts\deploy.bat prod
   ```

3. **Access the application**:
   - Application: http://localhost (via Nginx)
   - Direct Backend: http://localhost:8000
   - ChromaDB: http://localhost:8001

## Architecture

### Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │    Frontend     │    │    Backend      │
│  (Production)   │◄──►│   React App     │◄──►│   FastAPI       │
│   Port: 80      │    │   Port: 3000    │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Redis       │    │    ChromaDB     │
                       │   (Caching)     │    │  (Vector DB)    │
                       │   Port: 6379    │    │   Port: 8001    │
                       └─────────────────┘    └─────────────────┘
```

### Container Details

| Service | Image | Purpose | Resources |
|---------|-------|---------|-----------|
| Backend | Custom Python | API server, stream processing | 2GB RAM, 1 CPU |
| Frontend | Custom Node/Nginx | React dashboard | 512MB RAM, 0.5 CPU |
| ChromaDB | chromadb/chroma | Vector database | 1GB RAM, 0.5 CPU |
| Redis | redis:alpine | Caching layer | 512MB RAM, 0.2 CPU |
| Nginx | nginx:alpine | Reverse proxy | 256MB RAM, 0.1 CPU |

## Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional - Backend
LOG_LEVEL=INFO
BACKEND_WORKERS=4
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# Optional - Frontend
NODE_ENV=production
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Optional - Production
DOMAIN=localhost
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
```

### Docker Compose Files

- `docker-compose.yml`: Base configuration for all environments
- `docker-compose.dev.yml`: Development overrides with hot reload
- `nginx/nginx.conf`: Production reverse proxy configuration

## Deployment Commands

### Using Deployment Scripts

The deployment scripts provide convenient commands for managing the Docker environment:

```bash
# Development
./scripts/deploy.sh dev          # Start development environment
./scripts/deploy.sh stop         # Stop all services
./scripts/deploy.sh logs backend # View backend logs

# Production
./scripts/deploy.sh prod         # Start production environment
./scripts/deploy.sh status       # Check service status
./scripts/deploy.sh health       # Check service health

# Maintenance
./scripts/deploy.sh backup       # Backup data volumes
./scripts/deploy.sh cleanup      # Clean up Docker resources
```

### Manual Docker Compose Commands

```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Production
docker-compose --profile production up -d
docker-compose --profile production down

# Standard
docker-compose up -d
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Check status
docker-compose ps
```

## Performance Optimization

### Multi-Stage Builds

Both frontend and backend use multi-stage Docker builds:

- **Builder stage**: Installs dependencies and builds the application
- **Production stage**: Contains only runtime dependencies and built artifacts
- **Development stage**: Includes development tools and hot reload

### Resource Limits

Production containers have resource limits configured:

```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 512M
      cpus: '0.5'
```

### Caching Strategies

- **Docker layer caching**: Dependencies installed before copying source code
- **Redis caching**: Optional Redis service for application-level caching
- **Nginx caching**: Static asset caching and gzip compression

## Health Checks

All services include health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

Health check endpoints:
- Backend: `GET /health`
- Frontend: `GET /health` (via nginx)
- ChromaDB: `GET /api/v1/heartbeat`
- Redis: `redis-cli ping`

## Data Persistence

### Named Volumes

```yaml
volumes:
  chromadb_data:      # Vector database storage
  backend_logs:       # Application logs
  backend_cache:      # Python cache
  redis_data:         # Redis persistence
  nginx_logs:         # Nginx access/error logs
```

### Backup and Restore

```bash
# Create backup
./scripts/deploy.sh backup

# Restore from backup
./scripts/deploy.sh restore backups/20231201_120000
```

## Security

### Container Security

- **Non-root users**: All containers run as non-root users
- **Resource limits**: Memory and CPU limits prevent resource exhaustion
- **Health checks**: Automatic restart of unhealthy containers
- **Network isolation**: Custom Docker network for service communication

### Application Security

- **CORS configuration**: Proper CORS headers for API access
- **Rate limiting**: Nginx rate limiting for API endpoints
- **Security headers**: XSS protection, content type sniffing prevention
- **Input validation**: Pydantic models for request validation

## Monitoring

### Service Monitoring

```bash
# Check service status
docker-compose ps

# View resource usage
docker stats

# Check health status
./scripts/deploy.sh health
```

### Log Management

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f chromadb

# Follow logs with timestamps
docker-compose logs -f -t
```

## Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Check port usage
   netstat -tulpn | grep :8000
   
   # Stop conflicting services
   sudo systemctl stop apache2  # Example
   ```

2. **Memory issues**:
   ```bash
   # Check available memory
   free -h
   
   # Reduce container resources in docker-compose.yml
   ```

3. **Permission issues**:
   ```bash
   # Fix volume permissions
   sudo chown -R $USER:$USER ./data
   ```

4. **Network issues**:
   ```bash
   # Recreate network
   docker network prune
   docker-compose down
   docker-compose up -d
   ```

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or edit .env file
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart backend
```

### Container Shell Access

```bash
# Access backend container
docker-compose exec backend bash

# Access frontend container
docker-compose exec frontend sh

# Access ChromaDB container
docker-compose exec chromadb bash
```

## Development Workflow

### Hot Reload Development

The development configuration includes hot reload:

```bash
# Start development environment
./scripts/deploy.sh dev

# Code changes are automatically reflected:
# - Backend: uvicorn --reload
# - Frontend: vite dev server
# - Volumes mounted for live editing
```

### Testing in Containers

```bash
# Run backend tests
docker-compose exec backend pytest

# Run frontend tests
docker-compose exec frontend npm test

# Run integration tests
docker-compose exec backend python -m pytest tests/integration/
```

### Database Management

```bash
# Access ChromaDB
curl http://localhost:8001/api/v1/collections

# Reset ChromaDB data
docker-compose down
docker volume rm bharat-grid-ai_chromadb_data
docker-compose up -d
```

## Production Deployment

### SSL/HTTPS Setup

1. **Obtain SSL certificates**:
   ```bash
   # Using Let's Encrypt (example)
   certbot certonly --standalone -d your-domain.com
   ```

2. **Configure SSL in nginx**:
   ```bash
   # Copy certificates
   mkdir -p nginx/ssl
   cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
   cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
   
   # Update nginx.conf to enable HTTPS server block
   ```

3. **Update environment**:
   ```bash
   # Edit .env
   DOMAIN=your-domain.com
   SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
   SSL_KEY_PATH=/etc/nginx/ssl/key.pem
   ```

### Scaling

```bash
# Scale backend service
docker-compose up -d --scale backend=3

# Use load balancer (nginx upstream)
# Edit nginx/nginx.conf to add multiple backend servers
```

### Monitoring and Logging

```bash
# Set up log rotation
# Add to /etc/logrotate.d/docker-compose

# Monitor with external tools
# - Prometheus + Grafana
# - ELK Stack
# - Docker stats API
```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Docker and service logs
3. Verify environment configuration
4. Check system resources and requirements

## Performance Targets

The Docker configuration is optimized to meet these performance targets:

- **Allocation Latency**: <10ms (Priority algorithm execution)
- **WebSocket Latency**: <50ms (Real-time updates)
- **RAG Response Time**: <2s (AI predictions)
- **Dashboard FPS**: 60fps (Smooth UI updates)
- **Container Startup**: <30s (Service availability)