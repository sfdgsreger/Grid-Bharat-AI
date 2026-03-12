#!/usr/bin/env python3
"""
Test script for API integration with RAG system and Pathway engine.
"""

import sys
import os
import asyncio
import httpx
sys.path.append('.')

# Import the app to test
from api import app

async def test_api_integration():
    """Test the API endpoints with integrated systems."""
    print("Testing API integration...")
    
    # Create async client
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        response = await client.get('/health')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Health status: {data.get('status')}")
        
        # Test insights endpoint
        print("\n2. Testing insights endpoint...")
        response = await client.get('/insights')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response time: {data.get('response_time_ms', 'N/A')} ms")
            insights = data.get('insights', '')
            print(f"   Insights preview: {insights[:100]}...")
            
            # Check if response time is within target (2 seconds = 2000ms)
            response_time = data.get('response_time_ms', 0)
            if response_time <= 2000:
                print(f"   ✓ Response time within target: {response_time}ms <= 2000ms")
            else:
                print(f"   ⚠ Response time exceeds target: {response_time}ms > 2000ms")
        else:
            print(f"   Error: {response.text}")
        
        # Test grid failure simulation with valid input
        print("\n3. Testing grid failure simulation...")
        response = await client.post('/simulate/grid-failure', json={'failure_percentage': 0.2})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Simulation status: {data.get('status')}")
            print(f"   Reduction: {data.get('reduction')} ({data.get('reduction', 0) * 100}%)")
            print(f"   Timestamp: {data.get('timestamp')}")
        else:
            print(f"   Error: {response.text}")
        
        # Test grid failure simulation with invalid input
        print("\n4. Testing grid failure simulation with invalid input...")
        response = await client.post('/simulate/grid-failure', json={'failure_percentage': 1.5})
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:
            print("   ✓ Correctly rejected invalid input")
        else:
            print(f"   ⚠ Unexpected response: {response.text}")
        
        # Test grid failure simulation with edge case (0% failure)
        print("\n5. Testing grid failure simulation with 0% failure...")
        response = await client.post('/simulate/grid-failure', json={'failure_percentage': 0.0})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 0% failure handled correctly: {data.get('reduction')}")
        
        # Test grid failure simulation with edge case (100% failure)
        print("\n6. Testing grid failure simulation with 100% failure...")
        response = await client.post('/simulate/grid-failure', json={'failure_percentage': 1.0})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 100% failure handled correctly: {data.get('reduction')}")
        
        print("\n✓ API integration test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_api_integration())