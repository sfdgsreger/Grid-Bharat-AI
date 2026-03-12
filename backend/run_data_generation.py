#!/usr/bin/env python3
"""Simple script to generate sample data"""

import os
import sys
from pathlib import Path

# Ensure we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from data_generators import (
        EnergyNodeGenerator, 
        SupplyEventGenerator, 
        HistoricalPatternGenerator,
        DataExporter
    )
    
    # Create output directory
    output_dir = "backend/data/generated"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Generating sample data in {output_dir}...")
    
    # Initialize generators
    node_gen = EnergyNodeGenerator()
    supply_gen = SupplyEventGenerator()
    pattern_gen = HistoricalPatternGenerator()
    
    # Generate small test dataset
    print("Generating energy nodes...")
    nodes = node_gen.generate_node_stream(duration_hours=2, nodes_per_type=2, interval_seconds=300)
    
    print("Generating supply events...")
    supply_events = supply_gen.generate_supply_events(duration_hours=2, interval_minutes=10)
    
    print("Generating historical patterns...")
    historical_patterns = pattern_gen.generate_historical_patterns(days_of_history=7, nodes_per_type=2)
    
    # Export data
    print("Exporting files...")
    DataExporter.export_nodes_to_csv(nodes, f"{output_dir}/nodes_stream.csv")
    DataExporter.export_nodes_to_jsonl(nodes, f"{output_dir}/nodes_stream.jsonl")
    DataExporter.export_supply_events_to_jsonl(supply_events, f"{output_dir}/supply_events.jsonl")
    DataExporter.export_patterns_to_csv(historical_patterns, f"{output_dir}/historical_patterns.csv")
    
    print(f"Success! Generated:")
    print(f"  - {len(nodes)} node data points")
    print(f"  - {len(supply_events)} supply events")
    print(f"  - {len(historical_patterns)} historical patterns")
    print(f"Files saved to {output_dir}/")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()