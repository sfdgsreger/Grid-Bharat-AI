"""
Development server startup script for Bharat-Grid AI API.

This script starts the FastAPI server with proper configuration
for development use.
"""

import uvicorn
from api import app

if __name__ == "__main__":
    print("Starting Bharat-Grid AI API server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Health check at: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server")
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )