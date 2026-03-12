"""
Integration test for WebSocket endpoint with pathway engine.

This test validates the complete integration between the WebSocket endpoint
and the pathway engine for real-time allocation broadcasting.
"""

import asyncio
import time
from unittest.mock import Mock, AsyncMock

from api import manager, system_state
from pathway_engine import EnergyDataIngestionPipeline
from schemas import AllocationResult, SourceMix, EnergyNode, SupplyEvent, Location, AvailableSources


async def test_websocket_pathway_integration():
    """Test WebSocket integration with pathway engine."""
    print("Testing WebSocket-Pathway integration...")
    
    # Clear connections and set up mock WebSocket
    manager.active_connections.clear()
    mock_ws = Mock()
    mock_ws.send_json = AsyncMock()
    manager.active_connections.add(mock_ws)
    
    # Create pathway engine
    pipeline = EnergyDataIngestionPipeline(data_dir="./data")
    
    # Set up allocation callback to broadcast via WebSocket
    async def websocket_callback(allocations):
        """Callback to broadcast allocations via WebSocket."""
        from api import broadcast_allocation_results
        await broadcast_allocation_results(allocations)
    
    # Add the callback to the pipeline
    pipeline.add_allocation_callback(lambda allocations: asyncio.create_task(websocket_callback(allocations)))
    
    # Create sample nodes
    nodes = [
        EnergyNode(
            node_id="hospital_01",
            current_load=150.0,
            priority_tier=1,
            source_type="Grid",
            status="active",
            location=Location(lat=28.6139, lng=77.2090),
            timestamp=time.time()
        ),
        EnergyNode(
            node_id="factory_01",
            current_load=200.0,
            priority_tier=2,
            source_type="Solar",
            status="active",
            location=Location(lat=28.6200, lng=77.2100),
            timestamp=time.time()
        )
    ]
    
    # Update pipeline state with nodes
    for node in nodes:
        pipeline.current_nodes[node.node_id] = node
    
    # Create supply event
    supply_event = SupplyEvent(
        event_id="test_supply_001",
        total_supply=400.0,
        available_sources=AvailableSources(
            grid=200.0,
            solar=150.0,
            battery=50.0,
            diesel=0.0
        ),
        timestamp=time.time()
    )
    
    # Inject supply event (should trigger allocation and WebSocket broadcast)
    allocations = pipeline.inject_supply_event(supply_event)
    
    # Wait a moment for async operations
    await asyncio.sleep(0.1)
    
    # Verify allocations were created
    assert allocations is not None
    assert len(allocations) == 2
    
    # Verify WebSocket received the broadcast
    assert mock_ws.send_json.call_count >= 2  # allocation data + latency metric
    
    # Check the allocation broadcast
    allocation_call = None
    for call in mock_ws.send_json.call_args_list:
        if call[0][0].get("type") == "allocation_results":
            allocation_call = call[0][0]
            break
    
    assert allocation_call is not None
    assert len(allocation_call["allocations"]) == 2
    assert allocation_call["summary"]["total_nodes"] == 2
    
    print("✓ WebSocket-Pathway integration test passed")


async def test_real_time_allocation_broadcasting():
    """Test real-time allocation broadcasting through WebSocket."""
    print("Testing real-time allocation broadcasting...")
    
    # Clear connections and set up multiple mock WebSockets
    manager.active_connections.clear()
    
    mock_clients = []
    for i in range(3):
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        mock_clients.append(mock_ws)
        manager.active_connections.add(mock_ws)
    
    # Create pathway engine with real-time allocation enabled
    pipeline = EnergyDataIngestionPipeline(data_dir="./data")
    pipeline.enable_real_time_allocation(True)
    
    # Set up WebSocket broadcasting callback
    async def broadcast_callback(allocations):
        from api import broadcast_allocation_results
        stats = await broadcast_allocation_results(allocations)
        print(f"  Broadcasted to {stats['sent']} clients in {stats['latency_ms']:.2f}ms")
    
    pipeline.add_allocation_callback(lambda allocations: asyncio.create_task(broadcast_callback(allocations)))
    
    # Add sample nodes to pipeline
    sample_nodes = [
        EnergyNode(
            node_id=f"node_{i:02d}",
            current_load=100.0 + i * 50,
            priority_tier=(i % 3) + 1,
            source_type=["Grid", "Solar", "Battery"][i % 3],
            status="active",
            location=Location(lat=28.6 + i * 0.01, lng=77.2 + i * 0.01),
            timestamp=time.time()
        )
        for i in range(5)
    ]
    
    for node in sample_nodes:
        pipeline.current_nodes[node.node_id] = node
    
    # Simulate multiple supply events
    supply_events = [
        SupplyEvent(
            event_id=f"supply_{i:03d}",
            total_supply=800.0 - i * 100,
            available_sources=AvailableSources(
                grid=400.0 - i * 50,
                solar=300.0 - i * 30,
                battery=100.0 - i * 20,
                diesel=0.0
            ),
            timestamp=time.time() + i
        )
        for i in range(3)
    ]
    
    # Inject supply events and measure latency
    total_broadcasts = 0
    for supply_event in supply_events:
        start_time = time.perf_counter()
        allocations = pipeline.inject_supply_event(supply_event)
        
        # Wait for async broadcast
        await asyncio.sleep(0.05)
        
        if allocations:
            total_broadcasts += 1
            latency = (time.perf_counter() - start_time) * 1000
            print(f"  Supply event processed and broadcasted in {latency:.2f}ms")
            
            # Verify latency target
            assert latency < 100, f"Total latency {latency:.2f}ms too high"
    
    # Verify all clients received broadcasts
    for i, client in enumerate(mock_clients):
        assert client.send_json.call_count >= total_broadcasts * 2  # allocation + latency per broadcast
        print(f"  Client {i+1} received {client.send_json.call_count} messages")
    
    print(f"✓ Real-time broadcasting test passed ({total_broadcasts} broadcasts)")


async def test_websocket_latency_monitoring():
    """Test WebSocket latency monitoring and warnings."""
    print("Testing WebSocket latency monitoring...")
    
    # Clear connections
    manager.active_connections.clear()
    
    # Create mock WebSocket with artificial delay
    mock_ws = Mock()
    
    async def slow_send_json(data):
        await asyncio.sleep(0.06)  # 60ms delay (exceeds 50ms target)
    
    mock_ws.send_json = slow_send_json
    manager.active_connections.add(mock_ws)
    
    # Create sample allocation results
    allocations = [
        AllocationResult(
            node_id="test_node",
            allocated_power=100.0,
            source_mix=SourceMix(grid=100.0),
            action="maintain",
            latency_ms=5.0
        )
    ]
    
    # Broadcast and measure latency
    from api import broadcast_allocation_results
    start_time = time.perf_counter()
    stats = await broadcast_allocation_results(allocations)
    total_time = (time.perf_counter() - start_time) * 1000
    
    # Verify latency tracking
    assert stats["latency_ms"] >= 60  # Should detect the artificial delay
    assert stats["sent"] == 1
    
    print(f"✓ Latency monitoring test passed (detected {stats['latency_ms']:.2f}ms latency)")


async def run_integration_tests():
    """Run all WebSocket integration tests."""
    print("Running WebSocket integration tests...\n")
    
    try:
        await test_websocket_pathway_integration()
        await test_real_time_allocation_broadcasting()
        await test_websocket_latency_monitoring()
        
        print("\n✓ All WebSocket integration tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ WebSocket integration tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the integration tests
    success = asyncio.run(run_integration_tests())
    print(f"\nIntegration test result: {'PASSED' if success else 'FAILED'}")