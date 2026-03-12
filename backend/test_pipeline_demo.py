#!/usr/bin/env python3
"""
Demo script to test the data ingestion pipeline functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import json
import csv
from pathlib import Path
import tempfile
import threading

from backend.pathway_engine import EnergyDataIngestionPipeline


def create_test_data(data_dir: Path):
    """Create test data files for the pipeline"""
    
    # Create CSV test data
    csv_file = data_dir / "nodes_stream.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['node_id', 'current_load', 'priority_tier', 'source_type', 
                        'status', 'lat', 'lng', 'timestamp'])
        writer.writerow(['hospital_01', '150.5', '1', 'Grid', 'active', '28.6139', '77.2090', '1703001600.0'])
        writer.writerow(['factory_01', '300.0', '2', 'Solar', 'active', '28.6200', '77.2100', '1703001600.0'])
    
    # Create JSON test data
    json_file = data_dir / "supply_stream.jsonl"
    with open(json_file, 'w') as f:
        supply_event = {
            "event_id": "supply_001",
            "total_supply": 1000.0,
            "grid": 400.0,
            "solar": 300.0,
            "battery": 200.0,
            "diesel": 100.0,
            "timestamp": 1703001600.0
        }
        f.write(json.dumps(supply_event) + '\n')


def add_more_data(data_dir: Path):
    """Add more data to test streaming"""
    time.sleep(2)  # Wait a bit
    
    try:
        # Add more CSV data
        csv_file = data_dir / "nodes_stream.csv"
        if csv_file.exists():
            with open(csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['residential_01', '75.2', '3', 'Grid', 'active', '28.6100', '77.2080', '1703001610.0'])
        
        # Add more JSON data
        json_file = data_dir / "supply_stream.jsonl"
        if json_file.exists():
            with open(json_file, 'a') as f:
                supply_event = {
                    "event_id": "supply_002",
                    "total_supply": 800.0,
                    "grid": 300.0,
                    "solar": 250.0,
                    "battery": 150.0,
                    "diesel": 100.0,
                    "timestamp": 1703001610.0
                }
                f.write(json.dumps(supply_event) + '\n')
    except Exception as e:
        print(f"Error adding more data: {e}")


def main():
    """Test the data ingestion pipeline"""
    print("Testing Bharat-Grid AI Data Ingestion Pipeline")
    print("=" * 50)
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = Path(temp_dir)
        
        # Create test data
        create_test_data(data_dir)
        
        # Initialize pipeline
        pipeline = EnergyDataIngestionPipeline(str(data_dir))
        
        # Set up callbacks to track processed data
        processed_nodes = []
        processed_supply = []
        
        def on_node(node):
            processed_nodes.append(node)
            print(f"✓ Processed node: {node.node_id} (load: {node.current_load}kW, tier: {node.priority_tier})")
        
        def on_supply(supply):
            processed_supply.append(supply)
            print(f"✓ Processed supply: {supply.event_id} (total: {supply.total_supply}kW)")
        
        pipeline.add_node_callback(on_node)
        pipeline.add_supply_callback(on_supply)
        
        # Start pipeline
        pipeline.start_pipeline()
        
        # Start thread to add more data
        data_thread = threading.Thread(target=add_more_data, args=(data_dir,))
        data_thread.start()
        
        # Process data for 5 seconds
        print("\nProcessing stream data...")
        start_time = time.time()
        while time.time() - start_time < 5:
            stats = pipeline.process_stream_data()
            if stats['total_processed'] > 0:
                print(f"Batch processed: {stats}")
            time.sleep(0.1)
        
        # Stop pipeline
        pipeline.stop_pipeline()
        data_thread.join()
        
        # Show results
        print(f"\nResults:")
        print(f"- Processed {len(processed_nodes)} energy nodes")
        print(f"- Processed {len(processed_supply)} supply events")
        print(f"- Error count: {pipeline.error_count}")
        
        # Show processing stats
        stats = pipeline.get_processing_stats()
        print(f"- Success rate: {stats['success_rate']:.1f}%")
        
        print("\n✅ Pipeline test completed successfully!")


if __name__ == "__main__":
    main()