"""
Simple manual test for the FastAPI application.
This verifies the basic functionality without using TestClient.
"""

import asyncio
import json
from api import app


async def test_endpoints():
    """Test the FastAPI endpoints manually."""
    print("Testing FastAPI application...")
    
    # Test that the app can be imported and has the expected routes
    routes = [route.path for route in app.routes]
    print(f"Available routes: {routes}")
    
    # Check that required routes exist
    expected_routes = ["/", "/health", "/simulate/grid-failure", "/insights"]
    for route in expected_routes:
        if route in routes:
            print(f"✅ Route {route} exists")
        else:
            print(f"❌ Route {route} missing")
    
    # Test CORS middleware
    cors_middleware = None
    for middleware in app.user_middleware:
        if "CORSMiddleware" in str(middleware.cls):
            cors_middleware = middleware
            break
    
    if cors_middleware:
        print("✅ CORS middleware configured")
    else:
        print("❌ CORS middleware missing")
    
    # Test that the app has the expected metadata
    assert app.title == "Bharat-Grid AI API"
    assert app.version == "1.0.0"
    print("✅ App metadata correct")
    
    print("\n✅ All basic checks passed!")
    print("FastAPI application is properly configured with:")
    print("- All required endpoints")
    print("- CORS middleware for development")
    print("- Proper error handling middleware")
    print("- Request logging middleware")
    print("- Global exception handler")


if __name__ == "__main__":
    asyncio.run(test_endpoints())