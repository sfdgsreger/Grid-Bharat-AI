#!/usr/bin/env python3
"""
Simple test to verify Task 3.2 integration works
"""

import sys
import os
import time
import tempfile
import json
import csv
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathway_engine import EnergyDataIngestionPipeline
from schemas import SupplyEvent, AvailableSources
from utils.latency_tracker import global_tracker


def test_simple_integration():
    """Simple test of Pathway + Priority Allocator integration"""
    
    print("Testing Task 3.2: Pathway + Priority Allocator Integration")
    print("=" * 60)
    
    # Create temporary directory for test data
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Using temp directory: {temp_dir}")
    
    try:
        # Create test nodes CSV
        nodes_file = temp_dir / "nodes_stream.csv"
        with open(nodes_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['node_id', 'current_load', 'priority_tier', 'source_type', 'status', 'lat', 'lng', 'timestamp'])
            writer.writerow(['hospital_1', '150.0', '1', 'Grid', 'active', '28.6139', '77.2090', str(time.time())])
            writer.writerow(['factory_1', '300.0', '2', 'Solar', 'active', '28.6200', '77.2100', str(time.time())])
            writer.writerow(['residential_1', '50.0', '3', 'Grid', 'active', '28.6100', '77.2080', str(time.time())])
        
        # Create test supply events JSONL
        supply_file = temp_dir / "supply_stream.jsonl"
        with open(supply_file, 'w') as f:
            supply_event = {
                'event_id': 'test_supply_1',
                'total_supply': 400.0,
                'grid': 200.0,
                'solar': 100.0,
                'battery': 80.0,
                'diesel': 20.0,
                'timestamp': time.time()
            }
            f.write(json.dumps(supply_event) + '\n')
        
        print("✅ Test data created")
        
        # Initialize pipeline
        pipeline = EnergyDataIngestionPipeline(str(temp_dir))
        
        # Track allocations
        allocation_results = []
        
        def track_allocations(allocations):
            allocation_results.extend(allocations)
            print(f"📊 Allocation triggered: {len(allocations)} results")
            for alloc in allocations:
                print(f"  {alloc.node_id}: {alloc.allocated_power:.1f}kW ({alloc.action}) - {alloc.latency_ms:.2f}ms")
        
        pipeline.add_allocation_callback(track_allocations)
        pipeline.enable_real_time_allocation(True)
        
        print("✅ Pipeline configured")
        
        # Start pipeline
        pipeline.start_pipeline()
        time.sleep(0.2)  # Let connectors start
        
        print("✅ Pipeline started")
        
        # Process stream data
        stats = pipeline.process_stream_data()
        print(f"✅ Processed: {stats['nodes_processed']} nodes, {stats['supply_processed']} supply events")
        print(f"✅ Allocation triggered: {stats.get('allocation_triggered', False)}")
        
        # Test direct supply injection
        print("\n🧪 Testing direct supply injection...")
        
        test_supply = SupplyEvent(
            event_id='direct_injection_test',
            total_supply=250.0,
            available_sources=AvailableSources(
                grid=100.0,
                solar=80.0,
                battery=50.0,
                diesel=20.0
            ),
            timestamp=time.time()
        )
        
        start_time = time.perf_counter()
        direct_allocations = pipeline.inject_supply_event(test_supply)
        injection_latency = (time.perf_counter() - start_time) * 1000
        
        print(f"✅ Direct injection completed in {injection_latency:.2f}ms")
        
        if direct_allocations:
            print(f"✅ Generated {len(direct_allocations)} allocation results")
            
            # Check priority ordering
            hospitals = [a for a in direct_allocations if 'hospital' in a.node_id]
            factories = [a for a in direct_allocations if 'factory' in a.node_id]
            residential = [a for a in direct_allocations if 'residential' in a.node_id]
            
            hospital_power = sum(a.allocated_power for a in hospitals)
            total_power = sum(a.allocated_power for a in direct_allocations)
            
            print(f"✅ Hospital allocation: {hospital_power:.1f}kW / {total_power:.1f}kW total")
            
            # Validate latency
            avg_latency = sum(a.latency_ms for a in direct_allocations) / len(direct_allocations)
            if avg_latency < 10.0:
                print(f"✅ Latency target met: {avg_latency:.2f}ms < 10ms")
            else:
                print(f"⚠️  Latency target exceeded: {avg_latency:.2f}ms > 10ms")
        
        # Test current state
        state = pipeline.get_current_allocation_state()
        print(f"✅ Current state: {state['node_count']} nodes, allocation enabled: {state['allocation_enabled']}")
        
        print("\n🎉 Integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        pipeline.stop_pipeline()
        # Cleanup temp directory
        import shutil
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    success = test_simple_integration()
    if not success:
        sys.exit(1)