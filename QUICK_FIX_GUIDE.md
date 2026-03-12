# 🔧 Quick Fix for FastAPI Error

## ❌ Error You're Seeing:
```
ModuleNotFoundError: No module named 'fastapi'
```

## ✅ Solution Steps:

### Step 1: Navigate to Backend Directory
```bash
cd backend
```

### Step 2: Create and Activate Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows Command Prompt)
venv\Scripts\activate

# OR if using Git Bash
source venv/Scripts/activate

# OR if using PowerShell
venv\Scripts\Activate.ps1
```

### Step 3: Upgrade pip (Important!)
```bash
python -m pip install --upgrade pip
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Verify Installation
```bash
pip list | findstr fastapi
# Should show: fastapi==0.104.1
```

### Step 6: Run the API Server
```bash
python api.py
```

## 🚨 If Still Getting Errors:

### Option A: Install FastAPI Manually
```bash
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install websockets==12.0
pip install pydantic==2.5.0
```

### Option B: Use the Integrated System Starter
```bash
python start_integrated_system.py
```

### Option C: Check Python Version
```bash
python --version
# Should be Python 3.8 or higher
```

## 🎯 Expected Output When Working:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## 📱 Next Steps After Backend is Running:

### Terminal 2 - Frontend:
```bash
cd frontend
npm install
npm run dev
```

### Access Application:
- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- Test Grid Failure Button in the header!

## 🆘 Still Having Issues?

Try this simplified approach:
```bash
# 1. Clean start
cd backend
rmdir /s venv
python -m venv venv
venv\Scripts\activate

# 2. Install core dependencies only
pip install fastapi uvicorn websockets pydantic

# 3. Run basic API
python api.py
```

The key is making sure your virtual environment is activated before installing packages!