#!/usr/bin/env python3
"""
Minimal test server to check if FastAPI works
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Backend is working!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🧪 Testing minimal backend...")
    print("If this works, the issue is with the complex backend")
    print("Access: http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)