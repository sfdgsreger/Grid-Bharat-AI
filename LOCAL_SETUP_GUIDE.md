# 🚀 Bharat-Grid AI - Local Setup Guide (Windows)

## 📋 Prerequisites

### Required Software
1. **Python 3.8+** - [Download from python.org](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download from nodejs.org](https://nodejs.org/)
3. **Git** - [Download from git-scm.com](https://git-scm.com/)

### Verify Installation
```bash
python --version    # Should show Python 3.8+
node --version      # Should show Node 18+
npm --version       # Should show npm 8+
```

## 🔧 Quick Start (Recommended)

### Option 1: Docker Setup (Easiest)
```bash
# 1. Start the complete system
docker-compose up -d

# 2. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# WebSocket: ws://localhost:8001
```

### Option 2: Manual Setup (Full Control)

## 📁 Project Structure
```
bharat-grid-ai/
├── backend/          # Python FastAPI backend
├── frontend/         # React TypeScript frontend
├── docker-compose.yml
└── .env.example
```

## 🐍 Backend Setup

### 1. Navigate to Backend
```bash
cd backend
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# For Git Bash on Windows
source venv/Scripts/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start Backend Services

**Terminal 1 - Main API Server:**
```bash
python api.py
```
*Runs on: http://localhost:8000*

**Terminal 2 - WebSocket Server:**
```bash
python websocket_server.py
```
*Runs on: ws://localhost:8001*

**Terminal 3 - Stream Processing (Optional):**
```bash
python dev_stream_manager.py
```
*Generates real-time data streams*

## ⚛️ Frontend Setup

### 1. Navigate to Frontend (New Terminal)
```bash
cd frontend
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Start Development Server
```bash
npm run dev
```
*Runs on: http://localhost:3001 (or next available port)*

## 🌐 Access the Application

### Main Dashboard
- **URL**: http://localhost:3001
- **Features**: 
  - Real-time energy distribution dashboard
  - Priority Controller (drag-and-drop interface)
  - Grid Failure Simulation button
  - Live WebSocket data streams

### API Endpoints
- **Main API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Grid Failure**: http://localhost:8000/simulate_failure
- **AI Insights**: http://localhost:8000/insights

## 🎮 Using the System

### 1. Dashboard Tab
- View real-time energy allocation
- Monitor system metrics (Supply/Demand gauges)
- Use "SIMULATE GRID FAILURE" button (red → green)
- Watch live stream table updates

### 2. Priority Settings Tab
- Drag and drop facilities between priority tiers
- Configure: Critical → Essential → Non-Essential
- Save configuration for power allocation rules

### 3. Grid Failure Simulation
- Click red "SIMULATE GRID FAILURE" button
- Watch critical loads glow (hospitals get priority)
- See non-essential loads dim (residential areas cut)
- Click green "RESTORE GRID" to return to normal

## 🔧 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Kill process on port 3000/8000
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F
```

**Python Virtual Environment Issues:**
```bash
# Recreate virtual environment
rmdir /s venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Node Modules Issues:**
```bash
# Clean install
rmdir /s node_modules
del package-lock.json
npm install
```

**WebSocket Connection Failed:**
- Ensure backend WebSocket server is running on port 8001
- Check Windows Firewall settings
- Try restarting both backend and frontend

### Performance Optimization
- **Backend**: Runs Pathway stream processing for real-time data
- **Frontend**: 60fps dashboard updates with WebSocket connections
- **Targets**: <10ms allocation, <50ms WebSocket, <2s RAG queries

## 📊 System Architecture

```
┌─────────────────┐    WebSocket    ┌──────────────────┐
│   React Frontend│◄──────────────►│  Python Backend │
│   (Port 3001)   │                 │   (Port 8000)    │
└─────────────────┘                 └──────────────────┘
         │                                    │
         │ HTTP API                          │
         └────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   Pathway   │
                    │ Stream Proc │
                    └─────────────┘
```

## 🎯 Key Features Working
✅ Real-time energy distribution dashboard  
✅ Priority Controller with drag-and-drop  
✅ Grid failure simulation with visual effects  
✅ WebSocket live data streams  
✅ RAG system for AI insights  
✅ Pathway stream processing  
✅ Performance monitoring  

## 🆘 Need Help?
- Check console logs in browser (F12)
- Check terminal outputs for errors
- Ensure all services are running
- Verify port availability

The system demonstrates real-time energy grid optimization with AI-powered priority allocation during failures!