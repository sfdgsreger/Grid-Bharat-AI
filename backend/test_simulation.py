#!/usr/bin/env python3
"""
Simple test script to verify the grid failure simulation endpoint works.
"""

import requests
import json

def test_simulation_endpoint():
    """Test the grid failure simulation endpoint."""
    url = "http://localhost:8000/simulate/grid-failure"
    
    # Test data
    test_data = {
        "failure_percentage": 0.25
    }
    
    try:
        print("Testing grid failure simulation endpoint...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response Body: {json.dumps(result, indent=2)}")
            print("\n✅ Simulation endpoint test PASSED!")
            return True
        else:
            print(f"❌ Simulation endpoint test FAILED!")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_health_endpoint():
    """Test the health check endpoint."""
    url = "http://localhost:8000/health"
    
    try:
        print("Testing health endpoint...")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Health check: {json.dumps(result, indent=2)}")
            print("✅ Health endpoint test PASSED!")
            return True
        else:
            print(f"❌ Health endpoint test FAILED! Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Bharat-Grid AI API Endpoints")
    print("=" * 50)
    
    # Test health endpoint first
    health_ok = test_health_endpoint()
    print()
    
    # Test simulation endpoint
    simulation_ok = test_simulation_endpoint()
    print()
    
    if health_ok and simulation_ok:
        print("🎉 All tests PASSED! The simulation panel should work correctly.")
    else:
        print("⚠️  Some tests FAILED. Check the backend logs for issues.")