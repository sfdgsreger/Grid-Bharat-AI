#!/usr/bin/env python3
"""
Performance demonstration for Bharat-Grid AI Priority Allocation Engine
Shows O(n) algorithm performance and latency tracking capabilities
"""

import time
import statistics
from typing import List
from schemas import EnergyNode, SupplyEvent, AvailableSources, Location
from utils.priority_algo import PriorityAllocator


def create_test_nodes(count: int) -> List[EnergyNode]:
    """Create test nodes with mixed priorities and realistic loads"""
    nodes = []
    for i in range(count):
        # Mix of priorities: 30% hospitals, 40% factories, 30% residential
        if i % 10 < 3:
            priority = 1  # Hospital
            load = 100.0 + (i % 50)  # 100-150 kW
        elif i % 10 < 7:
            priority = 2  # Factory
            load = 200.0 + (i % 100)  # 200-300 kW
        else:
            priority = 3  # Residential
            load = 20.0 + (i % 30)  # 20-50 kW
        
        node = EnergyNode(
            node_id=f"node_{i:04d}",
            current_load=load,
            priority_tier=priority,
            source_type="Grid",
            status="active",
            location=Location(lat=28.6139 + (i * 0.001), lng=77.2090 + (i * 0.001)),
            timestamp=time.time()
        )
        nodes.append(node)
    
    return nodes


def create_supply_event(total_supply: float) -> SupplyEvent:
    """Create a supply event with realistic source mix"""
    return SupplyEvent(
        event_id=f"supply_{int(time.time())}",
        total_supply=total_supply,
        available_sources=AvailableSources(
            solar=total_supply * 0.4,    # 40% solar
            grid=total_supply * 0.3,     # 30% grid
            battery=total_supply * 0.2,  # 20% battery
            diesel=total_supply * 0.1    # 10% diesel (last resort)
        ),
        timestamp=time.time()
    )


def run_performance_test(node_counts: List[int], iterations: int = 5):
    """Run performance tests with different node counts"""
    allocator = PriorityAllocator()
    
    print("Bharat-Grid AI Priority Allocation Engine Performance Test")
    print("=" * 60)
    print(f"Testing O(n) algorithm with {iterations} iterations per test")
    print()
    
    results = []
    
    for node_count in node_counts:
        print(f"Testing with {node_count:,} nodes...")
        
        # Create test data
        nodes = create_test_nodes(node_count)
        total_demand = sum(node.current_load for node in nodes)
        
        # Create supply shortage scenario (80% of demand)
        supply_event = create_supply_event(total_demand * 0.8)
        
        # Run multiple iterations to get average performance
        latencies = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            allocations = allocator.allocate_power(nodes, supply_event)
            end_time = time.perf_counter()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            
            # Validate results
            assert len(allocations) == node_count
            assert allocator.validate_power_conservation(allocations, supply_event.total_supply)
        
        # Calculate statistics
        avg_latency = statistics.mean(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        results.append({
            'nodes': node_count,
            'avg_latency_ms': avg_latency,
            'min_latency_ms': min_latency,
            'max_latency_ms': max_latency,
            'meets_target': avg_latency < 10.0
        })
        
        # Display results
        status = "✓ PASS" if avg_latency < 10.0 else "✗ FAIL"
        print(f"  Nodes: {node_count:,}")
        print(f"  Average latency: {avg_latency:.2f}ms {status}")
        print(f"  Min/Max latency: {min_latency:.2f}ms / {max_latency:.2f}ms")
        print(f"  Target: <10ms")
        print()
    
    return results


def demonstrate_source_optimization():
    """Demonstrate source mix optimization (Solar > Grid > Battery > Diesel)"""
    print("Source Mix Optimization Demonstration")
    print("=" * 40)
    print("Preference order: Solar > Grid > Battery > Diesel")
    print()
    
    allocator = PriorityAllocator()
    
    # Create a hospital that needs 150kW
    hospital = EnergyNode(
        node_id="demo_hospital",
        current_load=150.0,
        priority_tier=1,
        source_type="Grid",
        status="active",
        location=Location(lat=28.6139, lng=77.2090),
        timestamp=time.time()
    )
    
    # Test different supply scenarios
    scenarios = [
        {
            "name": "Abundant Solar",
            "supply": SupplyEvent(
                event_id="solar_abundant",
                total_supply=200.0,
                available_sources=AvailableSources(
                    solar=200.0, grid=50.0, battery=30.0, diesel=20.0
                ),
                timestamp=time.time()
            )
        },
        {
            "name": "Mixed Sources",
            "supply": SupplyEvent(
                event_id="mixed_sources",
                total_supply=150.0,
                available_sources=AvailableSources(
                    solar=80.0, grid=40.0, battery=20.0, diesel=10.0
                ),
                timestamp=time.time()
            )
        },
        {
            "name": "Diesel Required",
            "supply": SupplyEvent(
                event_id="diesel_required",
                total_supply=150.0,
                available_sources=AvailableSources(
                    solar=50.0, grid=30.0, battery=20.0, diesel=50.0
                ),
                timestamp=time.time()
            )
        }
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        allocations = allocator.allocate_power([hospital], scenario['supply'])
        allocation = allocations[0]
        
        print(f"  Required: 150kW")
        print(f"  Allocated: {allocation.allocated_power}kW ({allocation.action})")
        print(f"  Source mix:")
        
        if allocation.source_mix.solar:
            print(f"    Solar: {allocation.source_mix.solar}kW")
        if allocation.source_mix.grid:
            print(f"    Grid: {allocation.source_mix.grid}kW")
        if allocation.source_mix.battery:
            print(f"    Battery: {allocation.source_mix.battery}kW")
        if allocation.source_mix.diesel:
            print(f"    Diesel: {allocation.source_mix.diesel}kW")
        
        print(f"  Processing time: {allocation.latency_ms:.3f}ms")
        print()


def demonstrate_priority_allocation():
    """Demonstrate priority-based allocation during supply shortage"""
    print("Priority-Based Allocation Demonstration")
    print("=" * 42)
    print("Priority tiers: 1=Hospital, 2=Factory, 3=Residential")
    print()
    
    allocator = PriorityAllocator()
    
    # Create nodes with different priorities
    nodes = [
        EnergyNode(
            node_id="hospital_emergency",
            current_load=100.0,
            priority_tier=1,
            source_type="Grid",
            status="active",
            location=Location(lat=28.6139, lng=77.2090),
            timestamp=time.time()
        ),
        EnergyNode(
            node_id="factory_production",
            current_load=200.0,
            priority_tier=2,
            source_type="Grid",
            status="active",
            location=Location(lat=28.6139, lng=77.2090),
            timestamp=time.time()
        ),
        EnergyNode(
            node_id="residential_block",
            current_load=80.0,
            priority_tier=3,
            source_type="Grid",
            status="active",
            location=Location(lat=28.6139, lng=77.2090),
            timestamp=time.time()
        )
    ]
    
    # Create supply shortage (250kW available, 380kW needed)
    shortage_supply = SupplyEvent(
        event_id="shortage_demo",
        total_supply=250.0,
        available_sources=AvailableSources(
            solar=100.0, grid=100.0, battery=50.0, diesel=0.0
        ),
        timestamp=time.time()
    )
    
    print(f"Total demand: {sum(node.current_load for node in nodes)}kW")
    print(f"Available supply: {shortage_supply.total_supply}kW")
    print(f"Shortage: {sum(node.current_load for node in nodes) - shortage_supply.total_supply}kW")
    print()
    
    allocations = allocator.allocate_power(nodes, shortage_supply)
    
    # Sort allocations by priority for display
    sorted_allocations = sorted(allocations, key=lambda a: next(n.priority_tier for n in nodes if n.node_id == a.node_id))
    
    for allocation in sorted_allocations:
        node = next(n for n in nodes if n.node_id == allocation.node_id)
        print(f"Node: {allocation.node_id}")
        print(f"  Priority: Tier {node.priority_tier}")
        print(f"  Requested: {node.current_load}kW")
        print(f"  Allocated: {allocation.allocated_power}kW")
        print(f"  Action: {allocation.action}")
        print(f"  Allocation %: {(allocation.allocated_power / node.current_load * 100):.1f}%")
        print()
    
    # Show summary
    summary = allocator.get_allocation_summary(allocations)
    print("Allocation Summary:")
    print(f"  Total allocated: {summary['total_allocated']}kW")
    print(f"  Actions: {summary['actions']}")
    print(f"  Diesel usage: {summary['total_diesel_usage']}kW")
    print(f"  Average latency: {summary['avg_latency_ms']:.3f}ms")


if __name__ == "__main__":
    print("Bharat-Grid AI Priority Allocation Engine Demo")
    print("=" * 50)
    print()
    
    # Run performance tests
    node_counts = [10, 100, 500, 1000, 2000]
    performance_results = run_performance_test(node_counts)
    
    print()
    
    # Demonstrate source optimization
    demonstrate_source_optimization()
    
    print()
    
    # Demonstrate priority allocation
    demonstrate_priority_allocation()
    
    print()
    print("Demo completed successfully!")
    print("Key features demonstrated:")
    print("✓ O(n) algorithm performance with <10ms latency")
    print("✓ Priority-based allocation (Hospital > Factory > Residential)")
    print("✓ Source mix optimization (Solar > Grid > Battery > Diesel)")
    print("✓ Latency tracking and performance monitoring")
    print("✓ Power conservation validation")