# 🚀 Bharat-Grid AI - Complete Deployment Guide

## 📋 Deployment Options Overview

| Method | Best For | Complexity | Scalability |
|--------|----------|------------|-------------|
| **Docker Compose** | Quick deployment, testing | Low | Medium |
| **Cloud Platforms** | Production, auto-scaling | Medium | High |
| **Kubernetes** | Enterprise, high availability | High | Very High |
| **Manual VPS** | Custom setups, learning | Medium | Low |

---

## 🐳 Option 1: Docker Compose (Recommended)

### Prerequisites
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- 4GB+ RAM, 10GB+ disk space

### Quick Start
```bash
# 1. Clone/navigate to project
cd bharat-grid-ai

# 2. Create environment file
cp .env.example .env
# Edit .env with your settings (OpenAI API key, etc.)

# 3. Deploy development environment
./scripts/deploy.sh dev

# 4. Deploy production environment
./scripts/deploy.sh prod
```

### Manual Docker Compose Commands
```bash
# Development (with hot reload)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production (with nginx proxy)
docker-compose --profile production up -d

# Standard deployment
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ChromaDB**: http://localhost:8001
- **Health Check**: http://localhost:8000/health

---

## ☁️ Option 2: Cloud Platform Deployment

### 2.1 AWS Deployment

#### Using AWS ECS (Elastic Container Service)
```bash
# 1. Install AWS CLI and configure
aws configure

# 2. Create ECR repositories
aws ecr create-repository --repository-name bharat-grid-ai/backend
aws ecr create-repository --repository-name bharat-grid-ai/frontend

# 3. Build and push images
$(aws ecr get-login --no-include-email --region us-east-1)
docker build -t bharat-grid-ai/backend ./backend
docker tag bharat-grid-ai/backend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/bharat-grid-ai/backend:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/bharat-grid-ai/backend:latest

# 4. Deploy using ECS task definition (see aws-ecs-task-definition.json)
aws ecs create-service --cluster bharat-grid-cluster --service-name bharat-grid-service --task-definition bharat-grid-task
```

#### Using AWS App Runner (Simplest)
```bash
# 1. Create apprunner.yaml in project root
# 2. Connect GitHub repository to App Runner
# 3. Auto-deploys on git push
```

### 2.2 Google Cloud Platform (GCP)

#### Using Cloud Run
```bash
# 1. Install gcloud CLI
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Build and deploy backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/bharat-grid-backend ./backend
gcloud run deploy bharat-grid-backend --image gcr.io/YOUR_PROJECT_ID/bharat-grid-backend --platform managed

# 3. Build and deploy frontend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/bharat-grid-frontend ./frontend
gcloud run deploy bharat-grid-frontend --image gcr.io/YOUR_PROJECT_ID/bharat-grid-frontend --platform managed
```

### 2.3 Microsoft Azure

#### Using Azure Container Instances
```bash
# 1. Install Azure CLI
az login

# 2. Create resource group
az group create --name bharat-grid-rg --location eastus

# 3. Create container registry
az acr create --resource-group bharat-grid-rg --name bharatgridacr --sku Basic

# 4. Build and push images
az acr build --registry bharatgridacr --image bharat-grid-backend ./backend
az acr build --registry bharatgridacr --image bharat-grid-frontend ./frontend

# 5. Deploy container group
az container create --resource-group bharat-grid-rg --file azure-container-group.yaml
```

### 2.4 DigitalOcean App Platform
```yaml
# app.yaml
name: bharat-grid-ai
services:
- name: backend
  source_dir: /backend
  github:
    repo: your-username/bharat-grid-ai
    branch: main
  run_command: uvicorn api:app --host 0.0.0.0 --port 8080
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  
- name: frontend
  source_dir: /frontend
  github:
    repo: your-username/bharat-grid-ai
    branch: main
  build_command: npm run build
  run_command: npm start
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs
```

---

## ⚓ Option 3: Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (minikube, EKS, GKE, AKS)
- kubectl configured
- Helm (optional)

### Kubernetes Manifests
```bash
# 1. Apply namespace
kubectl apply -f k8s/namespace.yaml

# 2. Apply ConfigMaps and Secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# 3. Deploy ChromaDB
kubectl apply -f k8s/chromadb-deployment.yaml
kubectl apply -f k8s/chromadb-service.yaml

# 4. Deploy Backend
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml

# 5. Deploy Frontend
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml

# 6. Apply Ingress
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n bharat-grid-ai
kubectl get services -n bharat-grid-ai
```

### Helm Deployment (Recommended for K8s)
```bash
# 1. Install Helm chart
helm install bharat-grid-ai ./helm/bharat-grid-ai

# 2. Upgrade deployment
helm upgrade bharat-grid-ai ./helm/bharat-grid-ai

# 3. Uninstall
helm uninstall bharat-grid-ai
```

---

## 🖥️ Option 4: Manual VPS Deployment

### Prerequisites
- Ubuntu 20.04+ VPS
- 4GB+ RAM, 20GB+ disk
- Domain name (optional)

### Setup Script
```bash
#!/bin/bash
# deploy-vps.sh

# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Clone repository
git clone https://github.com/your-username/bharat-grid-ai.git
cd bharat-grid-ai

# 5. Configure environment
cp .env.example .env
nano .env  # Edit configuration

# 6. Deploy
./scripts/deploy.sh prod

# 7. Setup nginx (if not using docker nginx)
sudo apt install nginx -y
sudo cp nginx/nginx.conf /etc/nginx/sites-available/bharat-grid-ai
sudo ln -s /etc/nginx/sites-available/bharat-grid-ai /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 8. Setup SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

---

## 🔧 Environment Configuration

### Required Environment Variables (.env)
```bash
# API Configuration
OPENAI_API_KEY=your_openai_api_key_here
LOG_LEVEL=INFO
BACKEND_WORKERS=4

# Database Configuration
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# Frontend Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Production Configuration
DOMAIN=yourdomain.com
SSL_EMAIL=your-email@domain.com

# Security (generate random strings)
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# Monitoring
ENABLE_MONITORING=true
PROMETHEUS_PORT=9090
```

---

## 📊 Production Considerations

### Performance Optimization
```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    environment:
      - WORKERS=4
      - WORKER_CLASS=uvicorn.workers.UvicornWorker
      
  frontend:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

### Security Hardening
```bash
# 1. Use secrets management
docker secret create openai_key openai_key.txt
docker secret create jwt_secret jwt_secret.txt

# 2. Enable firewall
sudo ufw enable
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22

# 3. Setup monitoring
docker run -d --name prometheus prom/prometheus
docker run -d --name grafana grafana/grafana
```

### Backup Strategy
```bash
# Automated backup script
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/$DATE"

# Create backup
./scripts/deploy.sh backup

# Upload to S3 (optional)
aws s3 cp backups/$DATE s3://your-backup-bucket/$DATE --recursive

# Cleanup old backups (keep last 7 days)
find /backups -type d -mtime +7 -exec rm -rf {} \;
```

---

## 🚀 Quick Deployment Commands

### Development
```bash
# Local development
./scripts/deploy.sh dev

# Access: http://localhost:3000
```

### Production
```bash
# Production with nginx
./scripts/deploy.sh prod

# Access: http://localhost or https://yourdomain.com
```

### Cloud (Example: AWS)
```bash
# Build for cloud
docker build -t bharat-grid-ai/backend ./backend
docker build -t bharat-grid-ai/frontend ./frontend

# Push to registry
docker tag bharat-grid-ai/backend:latest your-registry/backend:latest
docker push your-registry/backend:latest
```

---

## 🔍 Monitoring & Maintenance

### Health Checks
```bash
# Check all services
./scripts/deploy.sh health

# Individual service health
curl http://localhost:8000/health
curl http://localhost:3000
curl http://localhost:8001/api/v1/heartbeat
```

### Log Management
```bash
# View all logs
./scripts/deploy.sh logs

# View specific service logs
./scripts/deploy.sh logs backend
./scripts/deploy.sh logs frontend
./scripts/deploy.sh logs chromadb
```

### Scaling
```bash
# Scale backend service
docker-compose up -d --scale backend=3

# Scale in Kubernetes
kubectl scale deployment backend --replicas=3 -n bharat-grid-ai
```

---

## 🆘 Troubleshooting

### Common Issues

**Port conflicts:**
```bash
# Check what's using ports
netstat -tulpn | grep :8000
sudo lsof -i :8000

# Kill process
sudo kill -9 PID
```

**Memory issues:**
```bash
# Check memory usage
docker stats
free -h

# Increase swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**SSL certificate issues:**
```bash
# Renew Let's Encrypt certificate
sudo certbot renew --dry-run
sudo certbot renew
```

### Recovery Commands
```bash
# Complete reset
./scripts/deploy.sh cleanup
docker system prune -a

# Restore from backup
./scripts/deploy.sh restore backups/20231201_120000
```

---

## 🎯 Deployment Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] Domain name configured (if applicable)
- [ ] SSL certificates ready (for production)
- [ ] Database backups created
- [ ] Resource requirements met

### Post-deployment
- [ ] Health checks passing
- [ ] Grid failure simulation working
- [ ] WebSocket connections active
- [ ] Priority Controller functional
- [ ] Monitoring dashboards accessible
- [ ] Backup strategy implemented

### Production Readiness
- [ ] Load balancer configured
- [ ] Auto-scaling enabled
- [ ] Monitoring alerts set up
- [ ] Log aggregation configured
- [ ] Security scanning completed
- [ ] Performance testing done

---

## 📞 Support & Resources

- **Documentation**: Check `/docs` folder
- **Health Endpoint**: `GET /health`
- **API Documentation**: `GET /docs`
- **Monitoring**: `GET /monitoring/dashboard`

The deployment includes the complete Grid Failure Simulation feature with the red/green toggle button and visual effects for critical vs non-essential loads!