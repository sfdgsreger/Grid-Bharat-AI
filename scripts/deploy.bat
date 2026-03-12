@echo off
REM Bharat-Grid AI Docker Deployment Script for Windows
REM This script provides easy deployment commands for different environments

setlocal enabledelayedexpansion

REM Function to print colored output (simplified for Windows)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

REM Function to check if Docker is running
:check_docker
docker info >nul 2>&1
if errorlevel 1 (
    echo %ERROR% Docker is not running. Please start Docker and try again.
    exit /b 1
)
goto :eof

REM Function to check if .env file exists
:check_env
if not exist .env (
    echo %WARNING% .env file not found. Creating from .env.example...
    if exist .env.example (
        copy .env.example .env >nul
        echo %WARNING% Please edit .env file with your configuration before proceeding.
        exit /b 1
    ) else (
        echo %ERROR% .env.example file not found. Cannot create .env file.
        exit /b 1
    )
)
goto :eof

REM Function to build images
:build_images
echo %INFO% Building Docker images...
if "%~1"=="dev" (
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
) else (
    docker-compose build
)
if errorlevel 1 (
    echo %ERROR% Failed to build images
    exit /b 1
)
echo %SUCCESS% Images built successfully!
goto :eof

REM Function to start services
:start_services
set env_type=%~1
echo %INFO% Starting Bharat-Grid AI services in %env_type% mode...

if "%env_type%"=="development" (
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
) else if "%env_type%"=="production" (
    docker-compose --profile production up -d
) else (
    docker-compose up -d
)

if errorlevel 1 (
    echo %ERROR% Failed to start services
    exit /b 1
)

echo %SUCCESS% Services started successfully!
echo %INFO% Waiting for services to be healthy...
timeout /t 10 /nobreak >nul
call :check_health
goto :eof

REM Function to stop services
:stop_services
echo %INFO% Stopping Bharat-Grid AI services...
docker-compose down
echo %SUCCESS% Services stopped successfully!
goto :eof

REM Function to check service health
:check_health
echo %INFO% Checking service health...

REM Check backend health
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo %WARNING% Backend service is not responding
) else (
    echo %SUCCESS% Backend service is healthy
)

REM Check frontend health
curl -f http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo %WARNING% Frontend service is not responding
) else (
    echo %SUCCESS% Frontend service is healthy
)

REM Check ChromaDB health
curl -f http://localhost:8001/api/v1/heartbeat >nul 2>&1
if errorlevel 1 (
    echo %WARNING% ChromaDB service is not responding
) else (
    echo %SUCCESS% ChromaDB service is healthy
)
goto :eof

REM Function to show logs
:show_logs
if "%~1"=="" (
    docker-compose logs -f
) else (
    docker-compose logs -f %~1
)
goto :eof

REM Function to clean up
:cleanup
echo %INFO% Cleaning up Docker resources...
docker-compose down -v --remove-orphans
docker system prune -f
echo %SUCCESS% Cleanup completed!
goto :eof

REM Function to show service status
:status
echo %INFO% Service Status:
docker-compose ps
echo.
echo %INFO% Resource Usage:
docker stats --no-stream
goto :eof

REM Main script logic
if "%1"=="dev" (
    call :check_docker
    call :check_env
    call :build_images dev
    call :start_services development
    echo %SUCCESS% Development environment is ready!
    echo %INFO% Frontend: http://localhost:3000
    echo %INFO% Backend API: http://localhost:8000
    echo %INFO% ChromaDB: http://localhost:8001
) else if "%1"=="prod" (
    call :check_docker
    call :check_env
    call :build_images
    call :start_services production
    echo %SUCCESS% Production environment is ready!
    echo %INFO% Application: http://localhost
    echo %INFO% Backend API: http://localhost:8000
    echo %INFO% ChromaDB: http://localhost:8001
) else if "%1"=="start" (
    call :check_docker
    call :check_env
    call :start_services standard
) else if "%1"=="stop" (
    call :stop_services
) else if "%1"=="restart" (
    call :stop_services
    timeout /t 2 /nobreak >nul
    call :start_services standard
) else if "%1"=="build" (
    call :check_docker
    call :build_images
) else if "%1"=="logs" (
    call :show_logs %2
) else if "%1"=="status" (
    call :status
) else if "%1"=="health" (
    call :check_health
) else if "%1"=="cleanup" (
    call :cleanup
) else (
    echo Bharat-Grid AI Docker Deployment Script for Windows
    echo.
    echo Usage: %0 {dev^|prod^|start^|stop^|restart^|build^|logs^|status^|health^|cleanup}
    echo.
    echo Commands:
    echo   dev       - Start development environment with hot reload
    echo   prod      - Start production environment with nginx proxy
    echo   start     - Start standard environment
    echo   stop      - Stop all services
    echo   restart   - Restart all services
    echo   build     - Build Docker images
    echo   logs      - Show logs (optionally specify service name^)
    echo   status    - Show service status and resource usage
    echo   health    - Check service health
    echo   cleanup   - Stop services and clean up Docker resources
    echo.
    echo Examples:
    echo   %0 dev                    # Start development environment
    echo   %0 prod                   # Start production environment
    echo   %0 logs backend           # Show backend logs
    exit /b 1
)