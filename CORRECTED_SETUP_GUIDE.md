# ✅ Corrected Setup Guide - Bharat-Grid AI

## 🚨 Important: No Separate WebSocket Server Needed!

The WebSocket functionality is **built into the main API server**. You don't need a separate `websocket_server.py` file.

## 🚀 Correct Setup Steps

### **Backend Setup (Terminal 1)**

```bash
# 1. Navigate to backend
cd backend

# 2. Activate virtual environment
venv\Scripts\activate

# 3. Install dependencies (if not done already)
pip install -r requirements.txt

# 4. Run the integrated system (RECOMMENDED)
python start_integrated_system.py
```

**OR use the main API directly:**
```bash
python api.py
```

### **Frontend Setup (Terminal 2)**

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

## 🎯 What Each Method Does

### Option 1: `python start_integrated_system.py` (RECOMMENDED)
- ✅ Starts FastAPI server with WebSocket endpoints
- ✅ Initializes data streams
- ✅ Sets up monitoring
- ✅ Creates required directories
- ✅ Runs on http://localhost:8000 with WebSocket at ws://localhost:8000/ws/allocations

### Option 2: `python api.py` (Simple)
- ✅ Starts just the FastAPI server
- ✅ Includes WebSocket endpoints
- ✅ Runs on http://localhost:8000

## 📊 Expected Output (Success)

### Backend Terminal:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
✓ Data directory structure ready
✓ Monitoring system initialized
✓ RAG system initialized
✓ Pathway engine ready
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Frontend Terminal:
```
  VITE v4.5.14  ready in 1015 ms
  ➜  Local:   http://localhost:3001/
  ➜  Network: use --host to expose
```

## 🌐 Access Your Application

- **Frontend Dashboard**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🎮 Test the Grid Failure Feature

1. Open http://localhost:3001
2. Look for the **red "SIMULATE GRID FAILURE"** button in the header
3. Click it to see:
   - Button turns green → "RESTORE GRID"
   - Critical loads glow emerald (hospitals get priority)
   - Non-essential loads fade out (residential areas lose power)
4. Click again to restore normal operation

## 🔧 WebSocket Endpoints (Built-in)

The API server automatically provides:
- `ws://localhost:8000/ws/allocations` - Real-time allocation updates
- `ws://localhost:8000/ws/latency` - Performance metrics
- REST endpoints at http://localhost:8000

## 🆘 Troubleshooting

### If you get "No such file" error:
- ✅ Use `python start_integrated_system.py` instead of `websocket_server.py`
- ✅ Make sure you're in the `backend` directory
- ✅ Virtual environment is activated

### If ports are busy:
```bash
# Kill processes on ports
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

### If dependencies missing:
```bash
cd backend
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 🎯 Summary

**The key fix**: There's no separate WebSocket server file. Everything runs through the main FastAPI application with integrated WebSocket endpoints!

Use `python start_integrated_system.py` for the complete experience with all features enabled.