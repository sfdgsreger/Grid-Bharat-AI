"""
Test WebSocket endpoint for real-time allocation updates.

This test validates:
- WebSocket connection establishment
- Real-time allocation broadcasting
- Latency tracking for 50ms target
- Connection management and error handling
"""

import asyncio
import json
import time
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import websockets
import threading

from api import app, manager, broadcast_allocation_results
from schemas import AllocationResult, SourceMix


class TestWebSocketEndpoint:
    """Test suite for WebSocket endpoint functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear any existing connections
        manager.active_connections.clear()
        manager.connection_count = 0
    
    def test_websocket_connection_establishment(self):
        """Test WebSocket connection can be established."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/allocations") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            
            assert data["type"] == "connection_established"
            assert "timestamp" in data
            assert data["total_connections"] == 1
            assert "Connected to Bharat-Grid AI" in data["message"]
    
    def test_websocket_ping_pong(self):
        """Test WebSocket ping/pong functionality."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/allocations") as websocket:
            # Skip connection confirmation
            websocket.receive_json()
            
            # Send ping
            websocket.send_text("ping")
            
            # Should receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
            assert "timestamp" in response
    
    def test_websocket_json_ping_pong(self):
        """Test WebSocket JSON ping/pong functionality."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/allocations") as websocket:
            # Skip connection confirmation
            websocket.receive_json()
            
            # Send JSON ping
            websocket.send_json({"type": "ping"})
            
            # Should receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
            assert "timestamp" in response
    
    def test_websocket_request_state(self):
        """Test WebSocket state request functionality."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/allocations") as websocket:
            # Skip connection confirmation
            websocket.receive_json()
            
            # Request system state
            websocket.send_json({"type": "request_state"})
            
            # Should receive system state
            response = websocket.receive_json()
            assert response["type"] == "system_state"
            assert "timestamp" in response
            assert "state" in response
    
    def test_websocket_unknown_message(self):
        """Test WebSocket handling of unknown messages."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/allocations") as websocket:
            # Skip connection confirmation
            websocket.receive_json()
            
            # Send unknown message type
            websocket.send_json({"type": "unknown_type"})
            
            # Should receive error response
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Unknown message type" in response["message"]
    
    def test_multiple_websocket_connections(self):
        """Test multiple WebSocket connections."""
        client = TestClient(app)
        
        # Connect first client
        with client.websocket_connect("/ws/allocations") as ws1:
            data1 = ws1.receive_json()
            assert data1["total_connections"] == 1
            
            # Connect second client
            with client.websocket_connect("/ws/allocations") as ws2:
                data2 = ws2.receive_json()
                assert data2["total_connections"] == 2
                
                # Both should be active
                assert len(manager.active_connections) == 2
            
            # After second client disconnects
            assert len(manager.active_connections) == 1
        
        # After all clients disconnect
        assert len(manager.active_connections) == 0


class TestAllocationBroadcasting:
    """Test suite for allocation result broadcasting."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear any existing connections
        manager.active_connections.clear()
        manager.connection_count = 0
    
    @pytest.mark.asyncio
    async def test_broadcast_allocation_results(self):
        """Test broadcasting allocation results to WebSocket clients."""
        # Create sample allocation results
        allocations = [
            AllocationResult(
                node_id="hospital_01",
                allocated_power=150.5,
                source_mix=SourceMix(grid=100.0, solar=50.5),
                action="maintain",
                latency_ms=5.2
            ),
            AllocationResult(
                node_id="factory_01",
                allocated_power=200.0,
                source_mix=SourceMix(solar=200.0),
                action="reduce",
                latency_ms=3.8
            )
        ]
        
        # Test with no connections (should not fail)
        stats = await broadcast_allocation_results(allocations)
        assert stats["sent"] == 0
        assert stats["failed"] == 0
        assert stats["total_connections"] == 0
    
    def test_websocket_stats_endpoint(self):
        """Test WebSocket statistics endpoint."""
        client = TestClient(app)
        
        # Test with no connections
        response = client.get("/ws/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["active_connections"] == 0
        assert data["total_connections_created"] == 0
        
        # Test with active connection
        with client.websocket_connect("/ws/allocations"):
            response = client.get("/ws/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["active_connections"] == 1
            assert data["total_connections_created"] == 1


class TestLatencyTracking:
    """Test suite for WebSocket latency tracking."""
    
    def setup_method(self):
        """Set up test environment."""
        manager.active_connections.clear()
        manager.connection_count = 0
    
    @pytest.mark.asyncio
    async def test_broadcast_latency_tracking(self):
        """Test that broadcast latency is tracked correctly."""
        # Create mock WebSocket connection
        mock_websocket = Mock()
        mock_websocket.send_json = Mock()
        
        # Add to manager
        manager.active_connections.add(mock_websocket)
        
        # Create test data
        test_data = {"type": "test", "message": "test broadcast"}
        
        # Measure broadcast time
        start_time = time.perf_counter()
        stats = await manager.broadcast_json(test_data)
        actual_time = (time.perf_counter() - start_time) * 1000
        
        # Verify latency tracking
        assert "latency_ms" in stats
        assert stats["latency_ms"] >= 0
        assert abs(stats["latency_ms"] - actual_time) < 10  # Within 10ms tolerance
        assert stats["sent"] == 1
        assert stats["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_broadcast_with_failed_connection(self):
        """Test broadcast handling when connections fail."""
        # Create mock WebSocket that fails
        mock_websocket = Mock()
        mock_websocket.send_json = Mock(side_effect=Exception("Connection failed"))
        
        # Add to manager
        manager.active_connections.add(mock_websocket)
        
        # Test broadcast
        test_data = {"type": "test", "message": "test broadcast"}
        stats = await manager.broadcast_json(test_data)
        
        # Should handle failure gracefully
        assert stats["sent"] == 0
        assert stats["failed"] == 1
        assert len(manager.active_connections) == 0  # Failed connection removed


def test_websocket_integration_with_api():
    """Test WebSocket endpoint integration with main API."""
    client = TestClient(app)
    
    # Test root endpoint shows WebSocket info
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "websocket" in data["endpoints"]
    assert data["endpoints"]["websocket"] == "/ws/allocations"
    assert "websocket_connections" in data
    
    # Connect WebSocket and verify stats update
    with client.websocket_connect("/ws/allocations"):
        response = client.get("/")
        data = response.json()
        assert data["websocket_connections"] == 1


if __name__ == "__main__":
    # Run basic connection test
    print("Testing WebSocket endpoint...")
    
    client = TestClient(app)
    
    try:
        with client.websocket_connect("/ws/allocations") as websocket:
            # Receive connection confirmation
            data = websocket.receive_json()
            print(f"✓ Connection established: {data['message']}")
            
            # Test ping/pong
            websocket.send_text("ping")
            pong = websocket.receive_json()
            print(f"✓ Ping/pong works: {pong['type']}")
            
            # Test state request
            websocket.send_json({"type": "request_state"})
            state = websocket.receive_json()
            print(f"✓ State request works: {state['type']}")
            
        print("✓ All WebSocket tests passed!")
        
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")
        raise