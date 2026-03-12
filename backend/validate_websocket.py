#!/usr/bin/env python3
"""
Simple WebSocket validation script for Task 11.1
"""

import asyncio
import json
import websockets
import requests

async def test_websocket():
    """Test WebSocket connection and data flow"""
    print("Testing WebSocket connection...")
    
    try:
        uri = "ws://localhost:8000/ws/allocations"
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connected")
            
            # Wait for connection confirmation
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)
            print(f"✓ Received: {data.get('type', 'unknown')}")
            
            # Trigger a grid failure to generate data
            print("Triggering grid failure simulation...")
            response = requests.post(
                "http://localhost:8000/simulate/grid-failure",
                json={"failure_percentage": 0.2}
            )
            
            if response.status_code == 200:
                print("✓ Grid failure triggered")
                
                # Wait for allocation results
                for i in range(5):
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=3)
                        data = json.loads(message)
                        
                        if data.get("type") == "allocation_results":
                            allocations = data.get("allocations", [])
                            print(f"✓ Received {len(allocations)} allocation results")
                            return True
                        else:
                            print(f"  Received: {data.get('type', 'unknown')}")
                    except asyncio.TimeoutError:
                        continue
                
                print("⚠ No allocation results received")
                return False
            else:
                print("✗ Failed to trigger grid failure")
                return False
                
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    print(f"\nWebSocket test: {'PASSED' if result else 'FAILED'}")