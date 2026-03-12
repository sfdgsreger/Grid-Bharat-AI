"""
Simple WebSocket endpoint test for real-time allocation updates.

This test validates the WebSocket endpoint functionality without complex dependencies.
"""

import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock

from api import manager, broadcast_allocation_results
from schemas import AllocationResult, SourceMix


async def test_connection_manager():
    """Test the WebSocket connection manager functionality."""
    print("Testing ConnectionManager...")
    
    # Clear any existing connections
    manager.active_connections.clear()
    
    # Create mock WebSocket connections with AsyncMock
    mock_ws1 = Mock()
    mock_ws1.send_json = AsyncMock()
    
    mock_ws2 = Mock()
    mock_ws2.send_json = AsyncMock()
    
    # Test adding connections
    manager.active_connections.add(mock_ws1)
    manager.active_connections.add(mock_ws2)
    assert len(manager.active_connections) == 2
    
    # Test broadcasting
    test_data = {"type": "test", "message": "Hello WebSocket"}
    stats = await manager.broadcast_json(test_data)
    
    assert stats["sent"] == 2
    assert stats["failed"] == 0
    assert stats["latency_ms"] >= 0
    assert stats["total_connections"] == 2
    
    # Verify both connections received the data
    mock_ws1.send_json.assert_called_once_with(test_data)
    mock_ws2.send_json.assert_called_once_with(test_data)
    
    print("✓ ConnectionManager tests passed")


async def test_allocation_broadcasting():
    """Test broadcasting allocation results."""
    print("Testing allocation broadcasting...")
    
    # Clear connections
    manager.active_connections.clear()
    
    # Create mock WebSocket connection with AsyncMock
    mock_ws = Mock()
    mock_ws.send_json = AsyncMock()
    manager.active_connections.add(mock_ws)
    
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
    
    # Test broadcasting
    stats = await broadcast_allocation_results(allocations)
    
    assert stats["sent"] == 1
    assert stats["failed"] == 0
    assert stats["latency_ms"] >= 0
    
    # Verify the connection received allocation data and latency metric
    assert mock_ws.send_json.call_count == 2  # allocation data + latency metric
    
    # Check first call (allocation data)
    first_call_args = mock_ws.send_json.call_args_list[0][0][0]
    assert first_call_args["type"] == "allocation_results"
    assert len(first_call_args["allocations"]) == 2
    assert first_call_args["summary"]["total_nodes"] == 2
    assert first_call_args["summary"]["total_allocated"] == 350.5
    
    # Check second call (latency metric)
    second_call_args = mock_ws.send_json.call_args_list[1][0][0]
    assert second_call_args["type"] == "latency"
    assert "value" in second_call_args
    
    print("✓ Allocation broadcasting tests passed")


async def test_latency_tracking():
    """Test WebSocket latency tracking."""
    print("Testing latency tracking...")
    
    # Clear connections
    manager.active_connections.clear()
    
    # Create mock WebSocket with artificial delay
    mock_ws = Mock()
    
    async def slow_send_json(data):
        await asyncio.sleep(0.01)  # 10ms delay
        
    mock_ws.send_json = slow_send_json
    manager.active_connections.add(mock_ws)
    
    # Test broadcast with latency measurement
    test_data = {"type": "test", "message": "latency test"}
    start_time = time.perf_counter()
    stats = await manager.broadcast_json(test_data)
    actual_time = (time.perf_counter() - start_time) * 1000
    
    # Verify latency tracking
    assert stats["latency_ms"] >= 10  # Should be at least 10ms due to delay
    assert abs(stats["latency_ms"] - actual_time) < 5  # Within 5ms tolerance
    
    print(f"✓ Latency tracking tests passed (measured: {stats['latency_ms']:.2f}ms)")


async def test_failed_connections():
    """Test handling of failed WebSocket connections."""
    print("Testing failed connection handling...")
    
    # Clear connections
    manager.active_connections.clear()
    
    # Create mock WebSocket that works
    mock_ws_good = Mock()
    mock_ws_good.send_json = AsyncMock()
    
    # Create mock WebSocket that fails
    mock_ws_bad = Mock()
    mock_ws_bad.send_json = AsyncMock(side_effect=Exception("Connection failed"))
    
    manager.active_connections.add(mock_ws_good)
    manager.active_connections.add(mock_ws_bad)
    
    # Test broadcast with one failing connection
    test_data = {"type": "test", "message": "failure test"}
    stats = await manager.broadcast_json(test_data)
    
    assert stats["sent"] == 1  # Only good connection succeeded
    assert stats["failed"] == 1  # Bad connection failed
    assert len(manager.active_connections) == 1  # Bad connection removed
    
    # Verify good connection still received data
    mock_ws_good.send_json.assert_called_once_with(test_data)
    
    print("✓ Failed connection handling tests passed")


async def test_performance_targets():
    """Test that performance targets are met."""
    print("Testing performance targets...")
    
    # Clear connections
    manager.active_connections.clear()
    
    # Create multiple mock connections to simulate load
    connections = []
    for i in range(10):
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        connections.append(mock_ws)
        manager.active_connections.add(mock_ws)
    
    # Test broadcast latency with multiple connections
    test_data = {"type": "performance_test", "data": "x" * 1000}  # 1KB data
    stats = await manager.broadcast_json(test_data)
    
    # Verify performance target (should be well under 50ms for mock connections)
    assert stats["latency_ms"] < 50, f"Broadcast latency {stats['latency_ms']:.2f}ms exceeds 50ms target"
    assert stats["sent"] == 10
    assert stats["failed"] == 0
    
    print(f"✓ Performance targets met (latency: {stats['latency_ms']:.2f}ms < 50ms)")


async def run_all_tests():
    """Run all WebSocket tests."""
    print("Running WebSocket endpoint tests...\n")
    
    try:
        await test_connection_manager()
        await test_allocation_broadcasting()
        await test_latency_tracking()
        await test_failed_connections()
        await test_performance_targets()
        
        print("\n✓ All WebSocket tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ WebSocket tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)