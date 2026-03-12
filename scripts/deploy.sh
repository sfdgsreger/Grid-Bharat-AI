#!/bin/bash

# Bharat-Grid AI Docker Deployment Script
# This script provides easy deployment commands for different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your configuration before proceeding."
            exit 1
        else
            print_error ".env.example file not found. Cannot create .env file."
            exit 1
        fi
    fi
}

# Function to build images
build_images() {
    print_status "Building Docker images..."
    
    if [ "$1" = "dev" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
    else
        docker-compose build
    fi
    
    print_success "Images built successfully!"
}

# Function to start services
start_services() {
    local env_type=$1
    
    print_status "Starting Bharat-Grid AI services in $env_type mode..."
    
    if [ "$env_type" = "development" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    elif [ "$env_type" = "production" ]; then
        docker-compose --profile production up -d
    else
        docker-compose up -d
    fi
    
    print_success "Services started successfully!"
    print_status "Waiting for services to be healthy..."
    
    # Wait for services to be healthy
    sleep 10
    
    # Check service health
    check_health
}

# Function to stop services
stop_services() {
    print_status "Stopping Bharat-Grid AI services..."
    docker-compose down
    print_success "Services stopped successfully!"
}

# Function to check service health
check_health() {
    print_status "Checking service health..."
    
    # Check backend health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend service is healthy"
    else
        print_warning "Backend service is not responding"
    fi
    
    # Check frontend health
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend service is healthy"
    else
        print_warning "Frontend service is not responding"
    fi
    
    # Check ChromaDB health
    if curl -f http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1; then
        print_success "ChromaDB service is healthy"
    else
        print_warning "ChromaDB service is not responding"
    fi
}

# Function to show logs
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    print_success "Cleanup completed!"
}

# Function to show service status
status() {
    print_status "Service Status:"
    docker-compose ps
    echo ""
    print_status "Resource Usage:"
    docker stats --no-stream
}

# Function to backup data
backup() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    print_status "Creating backup in $backup_dir..."
    
    # Backup ChromaDB data
    docker run --rm -v bharat-grid-ai_chromadb_data:/data -v "$(pwd)/$backup_dir":/backup alpine tar czf /backup/chromadb_data.tar.gz -C /data .
    
    # Backup logs
    docker run --rm -v bharat-grid-ai_backend_logs:/data -v "$(pwd)/$backup_dir":/backup alpine tar czf /backup/backend_logs.tar.gz -C /data .
    
    print_success "Backup created in $backup_dir"
}

# Function to restore data
restore() {
    local backup_dir=$1
    if [ -z "$backup_dir" ]; then
        print_error "Please specify backup directory"
        exit 1
    fi
    
    if [ ! -d "$backup_dir" ]; then
        print_error "Backup directory $backup_dir does not exist"
        exit 1
    fi
    
    print_status "Restoring from $backup_dir..."
    
    # Stop services first
    docker-compose down
    
    # Restore ChromaDB data
    if [ -f "$backup_dir/chromadb_data.tar.gz" ]; then
        docker run --rm -v bharat-grid-ai_chromadb_data:/data -v "$(pwd)/$backup_dir":/backup alpine tar xzf /backup/chromadb_data.tar.gz -C /data
        print_success "ChromaDB data restored"
    fi
    
    # Restore logs
    if [ -f "$backup_dir/backend_logs.tar.gz" ]; then
        docker run --rm -v bharat-grid-ai_backend_logs:/data -v "$(pwd)/$backup_dir":/backup alpine tar xzf /backup/backend_logs.tar.gz -C /data
        print_success "Backend logs restored"
    fi
    
    print_success "Restore completed"
}

# Main script logic
case "$1" in
    "dev")
        check_docker
        check_env
        build_images dev
        start_services development
        print_success "Development environment is ready!"
        print_status "Frontend: http://localhost:3000"
        print_status "Backend API: http://localhost:8000"
        print_status "ChromaDB: http://localhost:8001"
        ;;
    "prod")
        check_docker
        check_env
        build_images
        start_services production
        print_success "Production environment is ready!"
        print_status "Application: http://localhost"
        print_status "Backend API: http://localhost:8000"
        print_status "ChromaDB: http://localhost:8001"
        ;;
    "start")
        check_docker
        check_env
        start_services standard
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        sleep 2
        start_services standard
        ;;
    "build")
        check_docker
        build_images
        ;;
    "logs")
        show_logs "$2"
        ;;
    "status")
        status
        ;;
    "health")
        check_health
        ;;
    "cleanup")
        cleanup
        ;;
    "backup")
        backup
        ;;
    "restore")
        restore "$2"
        ;;
    *)
        echo "Bharat-Grid AI Docker Deployment Script"
        echo ""
        echo "Usage: $0 {dev|prod|start|stop|restart|build|logs|status|health|cleanup|backup|restore}"
        echo ""
        echo "Commands:"
        echo "  dev       - Start development environment with hot reload"
        echo "  prod      - Start production environment with nginx proxy"
        echo "  start     - Start standard environment"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  build     - Build Docker images"
        echo "  logs      - Show logs (optionally specify service name)"
        echo "  status    - Show service status and resource usage"
        echo "  health    - Check service health"
        echo "  cleanup   - Stop services and clean up Docker resources"
        echo "  backup    - Create backup of data volumes"
        echo "  restore   - Restore from backup directory"
        echo ""
        echo "Examples:"
        echo "  $0 dev                    # Start development environment"
        echo "  $0 prod                   # Start production environment"
        echo "  $0 logs backend           # Show backend logs"
        echo "  $0 restore backups/20231201_120000  # Restore from backup"
        exit 1
        ;;
esac