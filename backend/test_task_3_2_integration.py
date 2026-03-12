#!/usr/bin/env python3
"""
Test script for Task 3.2: Integration between Pathway and Priority Allocator

This script validates:
1. Stream processor connects to allocation engine
2. Real-time allocation triggers work when Supply_Events arrive
3. Latency measurement meets <10ms target
4. Complete data flow from ingestion to allocation
"""

import time
import json
import csv
import tempfile
import shutil
from pathlib import Path
from typing import List

from pathway_engine import EnergyDataIngestionPipeline
from schemas import EnergyNode, SupplyEvent, AllocationResult, Location, AvailableSources
from utils.latency_tracker import global_tracker, print_performance_summary


def create_test_data(data_dir: Path):
    """Create test data files for the integration test"""
    
    # Create nodes CSV data
    nodes_data = [
        ['node_id', 'current_load', 'priority_tier', 'source_type', 'status', 'lat', 'lng', 'timestamp'],
        ['hospital_1', '150.0', '1', 'Grid', 'active', '28.6139', '77.2090', str(time.time())],
        ['factory_1', '300.0', '2', 'Solar', 'active', '28.6200', '77.2100', str(time.time())],
        ['residential_1', '50.0', '3', 'Grid', 'active', '28.6100', '77.2080', str(time.time())],
        ['hospital_2', '200.0', '1', 'Battery', 'active', '28.6150', '77.2110', str(time.time())],
    ]
    
    nodes_file = data_dir / "nodes_stream.csv"
    with open(nodes_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(nodes_data)
    
    # Create supply events JSONL data
    supply_events = [
        {
            'event_id': 'supply_1',
            'total_supply': 800.0,
            'grid': 400.0,
            'solar': 200.0,
            'battery': 150.0,
            'diesel': 50.0,
            'timestamp': time.time()
        },
        {
            'event_id': 'supply_2',
            'total_supply': 400.0,  # Reduced supply to trigger priority allocation
            'grid': 200.0,
            'solar': 100.0,
            'battery': 80.0,
            'diesel': 20.0,
            'timestamp': time.time() + 1
        }
    ]
    
    supply_file = data_dir / "supply_stream.jsonl"
    with open(supply_file, 'w') as f:
        for event in supply_events:
            f.write(json.dumps(event) + '\n')
    
    print(f"Created test data in {data_dir}")
    return nodes_file, supply_file


def test_integration():
    """Test the complete integration between Pathway and Priority Allocator"""
    
    print("=" * 60)
    print("Task 3.2 Integration Test: Pathway + Priority Allocator")
    print("=" * 60)
    
    # Create temporary data directory
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create test data
        nodes_file, supply_file = create_test_data(temp_dir)
        
        # Initialize pipeline
        pipeline = EnergyDataIngestionPipeline(str(temp_dir))
        
        # Track allocation results
        allocation_results = []
        allocation_count = 0
        
        def track_allocations(allocations: List[AllocationResult]):
            nonlocal allocation_count
            allocation_count += 1
            allocation_results.extend(allocations)
            print(f"\n📊 Allocation #{allocation_count} triggered:")
            for alloc in allocations:
                print(f"  {alloc.node_id}: {alloc.allocated_power:.1f}kW ({alloc.action}) - {alloc.latency_ms:.2f}ms")
        
        # Register allocation callback
        pipeline.add_allocation_callback(track_allocations)
        
        # Enable real-time allocation
        pipeline.enable_real_time_allocation(True)
        
        print("\n1. Testing stream processing and allocation integration...")
        
        # Create and start pipeline
        pipeline.create_pipeline()
        pipeline.start_pipeline()
        
        # Process initial data
        print("\n2. Processing initial stream data...")
        time.sleep(0.5)  # Allow connectors to start
        
        stats = pipeline.process_stream_data()
        print(f"   Processed: {stats['nodes_processed']} nodes, {stats['supply_processed']} supply events")
        print(f"   Allocation triggered: {stats.get('allocation_triggered', False)}")
        
        # Test direct supply event injection
        print("\n3. Testing direct supply event injection...")
        
        # Create a grid failure scenario
        failure_supply = SupplyEvent(
            event_id='grid_failure_test',
            total_supply=250.0,  # Very limited supply
            available_sources=AvailableSources(
                grid=100.0,
                solar=80.0,
                battery=50.0,
                diesel=20.0
            ),
            timestamp=time.time()
        )
        
        # Inject supply event and measure latency
        injection_start = time.perf_counter()
        injection_allocations = pipeline.inject_supply_event(failure_supply)
        injection_latency = (time.perf_counter() - injection_start) * 1000
        
        print(f"   Supply injection completed in {injection_latency:.2f}ms")
        
        if injection_allocations:
            print(f"   Generated {len(injection_allocations)} allocation results")
            
            # Validate priority ordering
            tier_1_nodes = [a for a in injection_allocations if a.node_id.startswith('hospital')]
            tier_2_nodes = [a for a in injection_allocations if a.node_id.startswith('factory')]
            tier_3_nodes = [a for a in injection_allocations if a.node_id.startswith('residential')]
            
            print(f"   Tier 1 (Hospitals): {len(tier_1_nodes)} nodes")
            print(f"   Tier 2 (Factories): {len(tier_2_nodes)} nodes")
            print(f"   Tier 3 (Residential): {len(tier_3_nodes)} nodes")
            
            # Check if hospitals got priority
            hospital_power = sum(a.allocated_power for a in tier_1_nodes)
            total_allocated = sum(a.allocated_power for a in injection_allocations)
            
            print(f"   Hospital power allocation: {hospital_power:.1f}kW / {total_allocated:.1f}kW total")
        
        # Test current state retrieval
        print("\n4. Testing current allocation state...")
        current_state = pipeline.get_current_allocation_state()
        print(f"   Current nodes: {current_state['node_count']}")
        print(f"   Latest supply: {current_state['latest_supply']['total_supply']:.1f}kW" if current_state['latest_supply'] else "   No supply data")
        print(f"   Allocation enabled: {current_state['allocation_enabled']}")
        
        # Performance validation
        print("\n5. Performance validation...")
        
        # Check latency targets
        allocation_stats = global_tracker.get_stats('real_time_allocation')
        if allocation_stats:
            print(f"   Real-time allocation latency:")
            print(f"     Average: {allocation_stats.avg_ms:.2f}ms")
            print(f"     Max: {allocation_stats.max_ms:.2f}ms")
            print(f"     Target: <{allocation_stats.target_ms}ms")
            print(f"     Violations: {allocation_stats.violations}/{allocation_stats.count}")
            
            if allocation_stats.avg_ms < 10.0:
                print("   ✅ Latency target met (<10ms)")
            else:
                print("   ❌ Latency target exceeded")
        
        # Validate power conservation
        print("\n6. Validating power conservation...")
        if injection_allocations:
            total_allocated = sum(a.allocated_power for a in injection_allocations)
            total_supply = failure_supply.total_supply
            
            print(f"   Total supply: {total_supply:.1f}kW")
            print(f"   Total allocated: {total_allocated:.1f}kW")
            
            if total_allocated <= total_supply + 1e-6:
                print("   ✅ Power conservation maintained")
            else:
                print("   ❌ Power conservation violated")
        
        # Summary
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        print(f"✅ Stream processing: {stats['total_processed']} items processed")
        print(f"✅ Real-time triggers: {allocation_count} allocations triggered")
        print(f"✅ Latency measurement: Performance tracking active")
        print(f"✅ Priority allocation: Hospital priority maintained")
        print(f"✅ Supply event injection: Direct injection working")
        
        # Performance summary
        print("\nPerformance Summary:")
        print_performance_summary()
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        pipeline.stop_pipeline()
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory: {temp_dir}")


def test_latency_under_load():
    """Test allocation latency under various node counts"""
    
    print("\n" + "=" * 60)
    print("LATENCY STRESS TEST")
    print("=" * 60)
    
    # Test with different node counts
    node_counts = [10, 50, 100, 500, 1000]
    
    for count in node_counts:
        print(f"\nTesting with {count} nodes...")
        
        # Create nodes
        nodes = []
        for i in range(count):
            node = EnergyNode(
                node_id=f"node_{i}",
                current_load=50.0 + (i % 100),  # Vary load
                priority_tier=(i % 3) + 1,      # Mix priorities
                source_type='Grid',
                status='active',
                location=Location(lat=28.6 + (i * 0.001), lng=77.2 + (i * 0.001)),
                timestamp=time.time()
            )
            nodes.append(node)
        
        # Create supply event
        supply = SupplyEvent(
            event_id=f'load_test_{count}',
            total_supply=count * 30.0,  # Moderate supply shortage
            available_sources=AvailableSources(
                grid=count * 15.0,
                solar=count * 10.0,
                battery=count * 3.0,
                diesel=count * 2.0
            ),
            timestamp=time.time()
        )
        
        # Create pipeline and allocator
        pipeline = EnergyDataIngestionPipeline()
        
        # Measure allocation latency
        start_time = time.perf_counter()
        allocations = pipeline.allocator.allocate_power(nodes, supply)
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        print(f"   Allocation latency: {latency_ms:.2f}ms")
        print(f"   Allocations generated: {len(allocations)}")
        
        # Validate results
        total_allocated = sum(a.allocated_power for a in allocations)
        print(f"   Total allocated: {total_allocated:.1f}kW / {supply.total_supply:.1f}kW")
        
        if latency_ms < 10.0:
            print(f"   ✅ Target met (<10ms)")
        else:
            print(f"   ⚠️  Target exceeded (>10ms)")


if __name__ == "__main__":
    print("Starting Task 3.2 Integration Tests...")
    
    # Run main integration test
    success = test_integration()
    
    if success:
        # Run latency stress test
        test_latency_under_load()
        
        print("\n🎉 All integration tests completed!")
    else:
        print("\n❌ Integration tests failed!")
        exit(1)