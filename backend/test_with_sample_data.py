#!/usr/bin/env python3
"""
Test the data ingestion pipeline with the actual sample data files
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
from pathlib import Path

from backend.pathway_engine import EnergyDataIngestionPipeline


def main():
    """Test pipeline with actual sample data"""
    print("Testing Data Ingestion Pipeline with Sample Data")
    print("=" * 50)
    
    # Use the actual data directory
    data_dir = Path("../data")
    if not data_dir.exists():
        data_dir = Path("./data")
    
    if not data_dir.exists():
        print("❌ Data directory not found")
        return 1
    
    # Initialize pipeline
    pipeline = EnergyDataIngestionPipeline(str(data_dir))
    
    # Set up callbacks to track processed data
    processed_nodes = []
    processed_supply = []
    
    def on_node(node):
        processed_nodes.append(node)
        print(f"✓ Processed node: {node.node_id} (load: {node.current_load}kW, tier: {node.priority_tier}, source: {node.source_type})")
    
    def on_supply(supply):
        processed_supply.append(supply)
        print(f"✓ Processed supply: {supply.event_id} (total: {supply.total_supply}kW)")
        print(f"  Sources: Grid={supply.available_sources.grid}kW, Solar={supply.available_sources.solar}kW, Battery={supply.available_sources.battery}kW, Diesel={supply.available_sources.diesel}kW")
    
    pipeline.add_node_callback(on_node)
    pipeline.add_supply_callback(on_supply)
    
    # Start pipeline
    print("\nStarting pipeline...")
    pipeline.start_pipeline()
    
    # Process existing data
    print("\nProcessing existing sample data...")
    for i in range(10):  # Process for 1 second
        stats = pipeline.process_stream_data()
        if stats['total_processed'] > 0:
            print(f"Batch processed: {stats}")
        time.sleep(0.1)
    
    # Stop pipeline
    pipeline.stop_pipeline()
    
    # Show results
    print(f"\nResults:")
    print(f"- Processed {len(processed_nodes)} energy nodes")
    print(f"- Processed {len(processed_supply)} supply events")
    print(f"- Error count: {pipeline.error_count}")
    
    # Show processing stats
    stats = pipeline.get_processing_stats()
    print(f"- Total processed: {stats['processed_count']}")
    print(f"- Success rate: {stats['success_rate']:.1f}%")
    
    # Validate the processed data
    if processed_nodes:
        print(f"\nSample Energy Node:")
        node = processed_nodes[0]
        print(f"  ID: {node.node_id}")
        print(f"  Load: {node.current_load}kW")
        print(f"  Priority: Tier {node.priority_tier}")
        print(f"  Source: {node.source_type}")
        print(f"  Status: {node.status}")
        print(f"  Location: ({node.location.lat}, {node.location.lng})")
    
    if processed_supply:
        print(f"\nSample Supply Event:")
        supply = processed_supply[0]
        print(f"  ID: {supply.event_id}")
        print(f"  Total Supply: {supply.total_supply}kW")
        print(f"  Grid: {supply.available_sources.grid}kW")
        print(f"  Solar: {supply.available_sources.solar}kW")
        print(f"  Battery: {supply.available_sources.battery}kW")
        print(f"  Diesel: {supply.available_sources.diesel}kW")
    
    print("\n✅ Sample data processing completed successfully!")
    return 0


if __name__ == "__main__":
    exit(main())