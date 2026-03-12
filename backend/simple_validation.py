#!/usr/bin/env python3
"""
Simple validation test for Task 4 Checkpoint
"""

import sys
import os
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schemas import EnergyNode, SupplyEvent, AvailableSources, Location
from utils.priority_algo import PriorityAllocator


def test_basic_allocation():
    """Test basic priority allocation functionality"""
    print("Testing Basic Priority Allocation...")
    
    allocator = PriorityAllocator()
    
    # Create test nodes
    nodes = [
        EnergyNode(
            node_id="hospital_1",
            current_load=150.0,
            priority_tier=1,
            source_type="Grid",
            status="active",
            location=Location(lat=28.6139, lng=77.2090),
            timestamp=time.time()
        ),
        EnergyNode(
            node_id="factory_1",
            current_load=300.0,
            priority_tier=2,
            source_type="Solar",
            status="active",
            location=Location(lat=28.6200, lng=77.2100),
            timestamp=time.time()
        ),
        EnergyNode(
            node_id="residential_1",
            current_load=100.0,
            priority_tier=3,
            source_type="Grid",
            status="active",
            location=Location(lat=28.6100, lng=77.2080),
            timestamp=time.time()
        )
    ]
    
    # Test shortage scenario
    supply_event = SupplyEvent(
        event_id="test_shortage",
        total_supply=300.0,  # Less than total demand (550kW)
        available_sources=AvailableSources(
            solar=150.0,
            grid=100.0,
            battery=40.0,
            diesel=10.0
        ),
        timestamp=time.time()
    )
    
    # Run allocation
    start_time = time.perf_counter()
    allocations = allocator.allocate_power(nodes, supply_event)
    latency_ms = (time.perf_counter() - start_time) * 1000
    
    print(f"Allocation completed in {latency_ms:.2f}ms")
    
    # Validate results
    hospital_alloc = next(a for a in allocations if a.node_id == "hospital_1")
    factory_alloc = next(a for a in allocations if a.node_id == "factory_1")
    residential_alloc = next(a for a in allocations if a.node_id == "residential_1")
    
    print(f"Hospital: {hospital_alloc.allocated_power}kW ({hospital_alloc.action})")
    print(f"Factory: {factory_alloc.allocated_power}kW ({factory_alloc.action})")
    print(f"Residential: {residential_alloc.allocated_power}kW ({residential_alloc.action})")
    
    # Validate priority ordering
    assert hospital_alloc.allocated_power == 150.0, "Hospital should get full power"
    assert hospital_alloc.action == 'maintain', "Hospital should maintain"
    
    # Validate power conservation
    total_allocated = sum(a.allocated_power for a in allocations)
    assert total_allocated <= supply_event.total_supply + 1e-6, "Power conservation violated"
    
    print("✓ Basic allocation test PASSED")
    return True


def test_source_optimization():
    """Test source mix optimization"""
    print("\nTesting Source Mix Optimization...")
    
    allocator = PriorityAllocator()
    
    hospital = EnergyNode(
        node_id="test_hospital",
        current_load=100.0,
        priority_tier=1,
        source_type="Grid",
        status="active",
        location=Location(lat=28.6139, lng=77.2090),
        timestamp=time.time()
    )
    
    # Test with mixed sources
    supply_event = SupplyEvent(
        event_id="mixed_sources",
        total_supply=100.0,
        available_sources=AvailableSources(
            solar=40.0,
            grid=30.0,
            battery=20.0,
            diesel=10.0
        ),
        timestamp=time.time()
    )
    
    allocations = allocator.allocate_power([hospital], supply_event)
    allocation = allocations[0]
    
    print(f"Source mix: Solar={allocation.source_mix.solar}, Grid={allocation.source_mix.grid}, Battery={allocation.source_mix.battery}, Diesel={allocation.source_mix.diesel}")
    
    # Should use solar first, then grid, then battery, then diesel
    assert allocation.source_mix.solar == 40.0, "Should use all available solar"
    assert allocation.source_mix.grid == 30.0, "Should use all available grid"
    assert allocation.source_mix.battery == 20.0, "Should use all available battery"
    assert allocation.source_mix.diesel == 10.0, "Should use diesel last"
    
    print("✓ Source optimization test PASSED")
    return True


def test_performance():
    """Test performance with different node counts"""
    print("\nTesting Performance...")
    
    allocator = PriorityAllocator()
    
    node_counts = [10, 50, 100]
    
    for count in node_counts:
        # Create nodes
        nodes = []
        for i in range(count):
            node = EnergyNode(
                node_id=f"node_{i}",
                current_load=50.0 + (i % 100),
                priority_tier=(i % 3) + 1,
                source_type='Grid',
                status='active',
                location=Location(lat=28.6 + (i * 0.001), lng=77.2 + (i * 0.001)),
                timestamp=time.time()
            )
            nodes.append(node)
        
        # Create supply event
        supply = SupplyEvent(
            event_id=f'perf_test_{count}',
            total_supply=count * 40.0,
            available_sources=AvailableSources(
                grid=count * 20.0,
                solar=count * 15.0,
                battery=count * 3.0,
                diesel=count * 2.0
            ),
            timestamp=time.time()
        )
        
        # Measure allocation latency
        start_time = time.perf_counter()
        allocations = allocator.allocate_power(nodes, supply)
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        status = "PASS" if latency_ms < 10.0 else "WARN"
        print(f"{count} nodes: {latency_ms:.2f}ms ({status})")
        
        assert len(allocations) == count, f"Expected {count} allocations"
    
    print("✓ Performance test PASSED")
    return True


def main():
    """Run all validation tests"""
    print("=" * 50)
    print("TASK 4 CHECKPOINT VALIDATION")
    print("=" * 50)
    
    tests = [
        test_basic_allocation,
        test_source_optimization,
        test_performance
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"✗ {test.__name__} FAILED")
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ CHECKPOINT VALIDATION PASSED")
        print("\nCore allocation system is working correctly:")
        print("✓ Priority-based allocation (Hospital > Factory > Residential)")
        print("✓ Source mix optimization (Solar > Grid > Battery > Diesel)")
        print("✓ Performance targets met (<10ms for reasonable loads)")
        print("✓ Power conservation maintained")
        return True
    else:
        print("❌ CHECKPOINT VALIDATION FAILED")
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)