# 🔧 WebSocket Fix Guide - Bharat-Grid AI

## 🚨 Problem: WebSocket Connected but No Data

Your frontend shows "Connected" but "No allocation data received yet" because the backend WebSocket is not broadcasting data.

## ✅ Quick Fix Solutions

### **Solution 1: Use Simple Backend Runner (RECOMMENDED)**

```bash
# 1. Stop current backend (Ctrl+C)

# 2. Navigate to backend directory
cd backend

# 3. Activate virtual environment
venv\Scripts\activate

# 4. Run the simple backend with auto data generation
python simple_backend_runner.py
```

**Expected Output:**
```
🚀 Bharat-Grid AI Simple Backend
========================================
Starting server with:
  • API Server: http://localhost:8000
  • WebSocket: ws://localhost:8000/ws/allocations
  • Health Check: http://localhost:8000/health
  • Auto data generation every 3 seconds

Press Ctrl+C to stop
========================================
INFO: Uvicorn running on http://0.0.0.0:8000
✓ Data generation started
Broadcasted data to 1 connections
```

### **Solution 2: Use Complete System Runner**

```bash
cd backend
venv\Scripts\activate
python run_complete_system.py
```

### **Solution 3: Fix Original System**

If you want to use the original integrated system:

```bash
# 1. Generate initial data
cd backend
venv\Scripts\activate
python setup_dev_streams.py

# 2. Start data streams
python dev_stream_manager.py --background

# 3. Start API server
python start_integrated_system.py
```

## 🎯 What Each Solution Does

### Simple Backend Runner
- ✅ **Automatic data generation** every 3 seconds
- ✅ **WebSocket broadcasting** of allocation data
- ✅ **Grid failure simulation** endpoint
- ✅ **Health checks** and monitoring
- ✅ **No complex dependencies** - just works!

### Complete System Runner  
- ✅ All features of simple runner
- ✅ **File-based data streams** 
- ✅ **RAG system integration**
- ✅ **Advanced monitoring**

### Original Integrated System
- ✅ **Full feature set** with Pathway engine
- ✅ **Production-ready** components
- ⚠️ **More complex setup** required

## 🔍 How to Verify It's Working

### 1. Check Backend Logs
You should see:
```
✓ Data generation started
Broadcasted data to 1 connections
WebSocket connected. Total connections: 1
```

### 2. Check Frontend Dashboard
- WebSocket status: **"Connected"** ✅
- Allocations: **Should show numbers > 0** ✅
- Recent Allocations: **Should show data** ✅

### 3. Test Grid Failure Button
- Click red **"SIMULATE GRID FAILURE"** button
- Should turn green → **"RESTORE GRID"**
- Critical loads should **glow emerald**
- Non-essential loads should **fade out**

## 🛠️ Troubleshooting

### Issue: Still No Data After Fix

**Check 1: Backend Running?**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

**Check 2: WebSocket Endpoint?**
```bash
# Test WebSocket connection
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" http://localhost:8000/ws/allocations
```

**Check 3: Frontend Environment?**
Make sure your frontend `.env` has:
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Issue: Port Conflicts

```bash
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Or use different port
python simple_backend_runner.py --port 8001
```

### Issue: CORS Errors

The simple backend runner includes CORS middleware, but if you see CORS errors:

```bash
# Check browser console for errors
# Make sure frontend is running on localhost:3001
# Backend should show CORS middleware loaded
```

## 🎮 Expected User Experience

### Normal Operation
1. **Dashboard loads** with real-time data
2. **Gauges show values** (Supply/Demand)
3. **Stream table updates** every 3 seconds
4. **WebSocket latency** shows ~0.0ms

### Grid Failure Simulation
1. **Click red button** → "SIMULATE GRID FAILURE"
2. **Button turns green** → "RESTORE GRID"  
3. **Hospital gauges glow** (emerald with drop shadow)
4. **Residential areas dim** (opacity + grayscale)
5. **Toast notification** appears

### Priority Controller
1. **Switch to Priority Settings tab**
2. **Drag facilities** between tiers
3. **Save configuration** button works
4. **Visual feedback** on drag operations

## 📊 Data Structure Being Broadcast

The WebSocket sends this data structure:
```json
{
  "type": "allocation_update",
  "allocations": [
    {
      "node_id": "hospital_001",
      "allocated_power": 150,
      "source_mix": {"grid": 150},
      "action": "maintain",
      "latency_ms": 5,
      "timestamp": 1703123456789
    }
  ],
  "summary": {
    "total_nodes": 6,
    "total_allocated": 1025,
    "avg_latency": 5.2
  }
}
```

## 🚀 Quick Commands Summary

```bash
# RECOMMENDED: Simple fix
cd backend && venv\Scripts\activate && python simple_backend_runner.py

# Alternative: Complete system
cd backend && venv\Scripts\activate && python run_complete_system.py

# Original system (if you want full features)
cd backend && venv\Scripts\activate && python setup_dev_streams.py && python start_integrated_system.py

# Frontend (separate terminal)
cd frontend && npm run dev
```

## ✅ Success Checklist

- [ ] Backend shows "Data generation started"
- [ ] Backend shows "Broadcasted data to X connections"  
- [ ] Frontend WebSocket shows "Connected"
- [ ] Frontend shows allocation numbers > 0
- [ ] Grid failure button works (red ↔ green)
- [ ] Priority Controller tab loads
- [ ] Real-time updates every 3 seconds

The simple backend runner should fix your WebSocket data issue immediately!