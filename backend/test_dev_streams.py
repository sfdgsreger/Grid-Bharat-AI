#!/usr/bin/env python3
"""
Test script for development data streams
Demonstrates stream functionality and data rotation
"""

import os
import sys
import time
import json
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dev_stream_manager import DevStreamManager

def test_stream_functionality():
    """Test the development stream functionality"""
    
    print("Testing Bharat-Grid AI Development Streams")
    print("=" * 50)
    
    # Initialize stream manager
    print("1. Initializing stream manager...")
    manager = DevStreamManager()
    
    # Show initial status
    print("\n2. Initial stream status:")
    status = manager.status()
    print(f"   Running: {status['running']}")
    print(f"   Configured streams: {len(status['streams'])}")
    
    for stream_name, stream_info in status['streams'].items():
        print(f"   - {stream_name}: {stream_info['config']['output_format']} format")
        if 'file_info' in stream_info:
            size_mb = stream_info['file_info']['size_mb']
            print(f"     Current file size: {size_mb:.2f} MB")
    
    # List available failure scenarios
    print("\n3. Available failure scenarios:")
    scenarios = manager.list_scenarios()
    for i, scenario in enumerate(scenarios, 1):
        scenario_info = manager.stream_manager.failure_scenarios[scenario]
        print(f"   {i}. {scenario}: {scenario_info.description}")
    
    # Test triggering a failure scenario
    print("\n4. Testing failure scenario trigger...")
    test_scenario = "solar_cloud_cover"
    if manager.trigger_failure(test_scenario, duration=5):  # 5 minute test failure
        print(f"   ✓ Successfully triggered '{test_scenario}' scenario")
    else:
        print(f"   ✗ Failed to trigger '{test_scenario}' scenario")
    
    # Start streams for a short test
    print("\n5. Starting streams for 30-second test...")
    manager.stream_manager.start_streams()
    
    # Monitor for 30 seconds
    for i in range(6):  # 6 iterations of 5 seconds each
        time.sleep(5)
        status = manager.status()
        active_streams = status['active_streams']
        print(f"   Test iteration {i+1}/6: {active_streams} active streams")
        
        # Show file sizes
        for stream_name, stream_info in status['streams'].items():
            if 'file_info' in stream_info:
                size_mb = stream_info['file_info']['size_mb']
                print(f"     {stream_name}: {size_mb:.3f} MB")
    
    # Stop streams
    print("\n6. Stopping streams...")
    manager.stop()
    
    # Show final status
    print("\n7. Final stream status:")
    final_status = manager.status()
    print(f"   Running: {final_status['running']}")
    print(f"   Active streams: {final_status['active_streams']}")
    
    # Check generated files
    print("\n8. Generated stream files:")
    streams_dir = Path("backend/data/streams")
    for file_path in streams_dir.glob("*"):
        if file_path.is_file() and file_path.name != ".gitkeep":
            size_kb = file_path.stat().st_size / 1024
            print(f"   - {file_path.name}: {size_kb:.1f} KB")
    
    print("\n" + "=" * 50)
    print("Stream functionality test completed successfully!")
    
    return True

def demonstrate_stream_data():
    """Demonstrate the structure of generated stream data"""
    
    print("\nDemonstrating Stream Data Structure")
    print("=" * 40)
    
    streams_dir = Path("backend/data/streams")
    
    # Show sample CSV data
    csv_file = streams_dir / "nodes_stream.csv"
    if csv_file.exists():
        print("\n1. Sample CSV data (nodes_stream.csv):")
        with open(csv_file, 'r') as f:
            lines = f.readlines()[:5]  # First 5 lines
            for i, line in enumerate(lines):
                print(f"   {i+1}: {line.strip()}")
    
    # Show sample JSONL data
    jsonl_file = streams_dir / "nodes_stream.jsonl"
    if jsonl_file.exists():
        print("\n2. Sample JSONL data (nodes_stream.jsonl):")
        with open(jsonl_file, 'r') as f:
            lines = f.readlines()[:3]  # First 3 lines
            for i, line in enumerate(lines):
                try:
                    data = json.loads(line.strip())
                    print(f"   Record {i+1}:")
                    print(f"     Node ID: {data.get('node_id', 'N/A')}")
                    print(f"     Load: {data.get('current_load', 'N/A')} kW")
                    print(f"     Priority: {data.get('priority_tier', 'N/A')}")
                    print(f"     Status: {data.get('status', 'N/A')}")
                except json.JSONDecodeError:
                    print(f"   Record {i+1}: Invalid JSON")
    
    # Show sample supply events
    supply_file = streams_dir / "supply_events.jsonl"
    if supply_file.exists():
        print("\n3. Sample supply events (supply_events.jsonl):")
        with open(supply_file, 'r') as f:
            lines = f.readlines()[:2]  # First 2 lines
            for i, line in enumerate(lines):
                try:
                    data = json.loads(line.strip())
                    print(f"   Event {i+1}:")
                    print(f"     Total Supply: {data.get('total_supply', 'N/A')} kW")
                    sources = data.get('available_sources', {})
                    print(f"     Grid: {sources.get('grid', 'N/A')} kW")
                    print(f"     Solar: {sources.get('solar', 'N/A')} kW")
                    print(f"     Battery: {sources.get('battery', 'N/A')} kW")
                    print(f"     Diesel: {sources.get('diesel', 'N/A')} kW")
                except json.JSONDecodeError:
                    print(f"   Event {i+1}: Invalid JSON")
    
    # Show sample failure scenarios
    failure_file = streams_dir / "failure_scenarios.jsonl"
    if failure_file.exists():
        print("\n4. Sample failure scenarios (failure_scenarios.jsonl):")
        with open(failure_file, 'r') as f:
            lines = f.readlines()[:2]  # First 2 lines
            for i, line in enumerate(lines):
                try:
                    data = json.loads(line.strip())
                    print(f"   Scenario {i+1}:")
                    print(f"     Type: {data.get('scenario_type', 'N/A')}")
                    print(f"     Severity: {data.get('severity_level', 'N/A')}")
                    print(f"     Duration: {data.get('duration_minutes', 'N/A')} minutes")
                    print(f"     Description: {data.get('impact_description', 'N/A')}")
                except json.JSONDecodeError:
                    print(f"   Scenario {i+1}: Invalid JSON")

if __name__ == "__main__":
    try:
        # Run functionality test
        success = test_stream_functionality()
        
        if success:
            # Demonstrate data structure
            demonstrate_stream_data()
            
        print(f"\nTest completed {'successfully' if success else 'with errors'}")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()