#!/usr/bin/env python3
"""
Integration test for Task 11.1: Connect all system components

This test validates:
- Pathway engine to FastAPI server connection
- React dashboard to WebSocket endpoints connection
- RAG system with API endpoints integration
- End-to-end data flow from ingestion to dashboard

Requirements: 4.1, 8.1, 8.3, 8.5
"""

import asyncio
import time
import json
import websockets
import requests
from pathlib import Path

# Test configuration
API_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"
TEST_TIMEOUT = 30  # seconds


async def test_websocket_connection():
    """Test WebSocket connection and real-time data flow"""
    print("Testing WebSocket connection...")
    
    try:
        uri = f"{WS_BASE_URL}/ws/allocations"
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connected successfully")
            
            # Wait for connection confirmation
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)
            
            if data.get("type") == "connection_established":
                print("✓ Connection confirmation received")
                return True
            else:
                print(f"✗ Unexpected initial message: {data}")
                return False
                
    except Exception as e:
        print(f"✗ WebSocket connection failed: {e}")
        return False


def test_api_endpoints():
    """Test REST API endpoints"""
    print("Testing API endpoints...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health endpoint working")
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
            return False
        
        # Test integration status endpoint
        response = requests.get(f"{API_BASE_URL}/integration/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"✓ Integration status endpoint working")
            print(f"  Integration running: {status.get('integration_running', False)}")
            print(f"  WebSocket connections: {status.get('websocket_connections', 0)}")
        else:
            print(f"✗ Integration status endpoint failed: {response.status_code}")
            return False
        
        # Test insights endpoint (RAG system)
        response = requests.get(f"{API_BASE_URL}/insights", timeout=10)
        if response.status_code == 200:
            insights = response.json()
            print("✓ RAG insights endpoint working")
            print(f"  Response time: {insights.get('response_time_ms', 0):.2f}ms")
        else:
            print(f"✗ RAG insights endpoint failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ API endpoint test failed: {e}")
        return False


def test_grid_failure_simulation():
    """Test grid failure simulation and WebSocket broadcasting"""
    print("Testing grid failure simulation...")
    
    try:
        # Trigger grid failure simulation
        response = requests.post(
            f"{API_BASE_URL}/simulate/grid-failure",
            json={"failure_percentage": 0.3},  # 30% failure
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Grid failure simulation triggered")
            print(f"  Status: {result.get('status')}")
            print(f"  Reduction: {result.get('reduction', 0) * 100:.1f}%")
            return True
        else:
            print(f"✗ Grid failure simulation failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Grid failure simulation test failed: {e}")
        return False


async def test_end_to_end_flow():
    """Test complete end-to-end data flow"""
    print("Testing end-to-end data flow...")
    
    try:
        # Connect to WebSocket
        uri = f"{WS_BASE_URL}/ws/allocations"
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connected for end-to-end test")
            
            # Wait for initial connection message
            await asyncio.wait_for(websocket.recv(), timeout=5)
            
            # Trigger grid failure to generate allocation results
            response = requests.post(
                f"{API_BASE_URL}/simulate/grid-failure",
                json={"failure_percentage": 0.2},  # 20% failure
                timeout=10
            )
            
            if response.status_code != 200:
                print("✗ Failed to trigger simulation for end-to-end test")
                return False
            
            print("✓ Grid failure triggered, waiting for WebSocket updates...")
            
            # Wait for allocation results via WebSocket
            allocation_received = False
            for _ in range(10):  # Wait up to 10 messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3)
                    data = json.loads(message)
                    
                    if data.get("type") == "allocation_results":
                        print("✓ Allocation results received via WebSocket")
                        allocations = data.get("allocations", [])
                        print(f"  Received {len(allocations)} allocation results")
                        allocation_received = True
                        break
                        
                except asyncio.TimeoutError:
                    continue
            
            if allocation_received:
                print("✓ End-to-end data flow working correctly")
                return True
            else:
                print("✗ No allocation results received via WebSocket")
                return False
                
    except Exception as e:
        print(f"✗ End-to-end test failed: {e}")
        return False


async def test_integration_validation():
    """Test integration validation endpoint"""
    print("Testing integration validation...")
    
    try:
        response = requests.post(f"{API_BASE_URL}/integration/test", timeout=15)
        
        if response.status_code == 200:
            results = response.json()
            print("✓ Integration test endpoint working")
            
            test_results = results.get("results", {})
            all_passed = results.get("status") == "passed"
            
            print("  Component validation results:")
            for component, passed in test_results.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"    {component}: {status}")
            
            if all_passed:
                print("✓ All integration tests passed")
                return True
            else:
                print("✗ Some integration tests failed")
                return False
        else:
            print(f"✗ Integration test endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Integration validation test failed: {e}")
        return False


def check_server_running():
    """Check if the server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


async def main():
    """Run comprehensive integration test for Task 11.1"""
    print("=" * 60)
    print("Task 11.1 Integration Test: Connect All System Components")
    print("=" * 60)
    
    # Check if server is running
    if not check_server_running():
        print("✗ Server is not running. Please start the server first:")
        print("  cd backend && python start_server.py")
        return False
    
    print("✓ Server is running")
    print()
    
    # Run all tests
    test_results = {}
    
    # Test 1: WebSocket connection
    test_results["websocket"] = await test_websocket_connection()
    print()
    
    # Test 2: API endpoints
    test_results["api_endpoints"] = test_api_endpoints()
    print()
    
    # Test 3: Grid failure simulation
    test_results["simulation"] = test_grid_failure_simulation()
    print()
    
    # Test 4: End-to-end data flow
    test_results["end_to_end"] = await test_end_to_end_flow()
    print()
    
    # Test 5: Integration validation
    test_results["integration_validation"] = await test_integration_validation()
    print()
    
    # Summary
    print("=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in test_results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED - Task 11.1 Integration Complete!")
        print()
        print("System components successfully connected:")
        print("  ✓ Pathway engine → FastAPI server")
        print("  ✓ React dashboard → WebSocket endpoints")
        print("  ✓ RAG system → API endpoints")
        print("  ✓ End-to-end data flow working")
        print()
        print("The system is ready for full operation!")
    else:
        print("❌ SOME TESTS FAILED - Integration needs attention")
        print()
        print("Please check the failed components and ensure:")
        print("  - All services are running")
        print("  - Network connections are available")
        print("  - Configuration is correct")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)