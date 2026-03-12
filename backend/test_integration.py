#!/usr/bin/env python3
"""
Integration test for priority allocation engine with enhanced latency tracking
"""

import time
from backend.schemas import EnergyNode, SupplyEvent, AvailableSources, Location
from backend.utils.priority_algo import PriorityAllocator
from backend.utils.latency_tracker import global_tracker


def test_enhanced_latency_tracking():
    """Test that the enhanced latency tracking works correctly"""
    print("Testing Enhanced Latency Tracking Integration")
    print("=" * 50)
    
    # Clear any existing metrics
    global_tracker.clear_history()
    
    # Create test data
    allocator = PriorityAllocator()
    
    nodes = [
        EnergyNode(
            node_id="hospital_test",
            current_load=100.0,
            priority_tier=1,
            source_type="Grid",
            status="active",
            location=Location(lat=28.6139, lng=77.2090),
            timestamp=time.time()
        ),
        EnergyNode(
            node_id="factory_test",
            current_load=200.0,
            priority_tier=2,
            source_type="Grid",
            status="active",
            location=Location(lat=28.6139, lng=77.2090),
            timestamp=time.time()
        )
    ]
    
    supply_event = SupplyEvent(
        event_id="test_supply",
        total_supply=300.0,
        available_sources=AvailableSources(
            solar=150.0,
            grid=100.0,
            battery=50.0,
            diesel=0.0
        ),
        timestamp=time.time()
    )
    
    # Run allocation multiple times
    print("Running 10 allocation operations...")
    for i in range(10):
        allocations = allocator.allocate_power(nodes, supply_event)
        assert len(allocations) == 2
        assert all(a.action == 'maintain' for a in allocations)
    
    # Check that latency metrics were recorded
    stats = global_tracker.get_stats('allocation')
    assert stats is not None, "No allocation latency stats recorded"
    assert stats.count == 10, f"Expected 10 measurements, got {stats.count}"
    
    print(f"✓ Recorded {stats.count} allocation measurements")
    print(f"✓ Average latency: {stats.avg_ms:.3f}ms")
    print(f"✓ Target: <{stats.target_ms}ms")
    print(f"✓ Violations: {stats.violations}/{stats.count} ({stats.violation_rate:.1f}%)")
    
    # Verify performance is good
    if stats.avg_ms < 10.0:
        print("✓ Performance target met!")
    else:
        print("⚠ Performance target exceeded")
    
    print("\nLatency tracking integration test completed successfully!")


if __name__ == "__main__":
    test_enhanced_latency_tracking()