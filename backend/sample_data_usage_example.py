#!/usr/bin/env python3
"""
Usage examples for generated sample data
Demonstrates how to use the sample data with different system components
"""

import json
import csv
import pandas as pd
from schemas import EnergyNode, SupplyEvent
from rag_system import EnergyRAG, load_historical_data_from_csv, PredictionRequest

def example_1_load_node_data():
    """Example 1: Load and analyze energy node data"""
    print("=== Example 1: Loading Energy Node Data ===")
    
    # Load from CSV
    nodes_df = pd.read_csv("data/generated/nodes_stream.csv")
    print(f"Loaded {len(nodes_df)} node data points")
    
    # Analyze by node type
    node_analysis = nodes_df.groupby('node_id').agg({
        'current_load': ['mean', 'min', 'max'],
        'priority_tier': 'first',
        'source_type': lambda x: x.mode().iloc[0] if not x.empty else 'Unknown'
    }).round(2)
    
    print("\nNode Analysis:")
    print(node_analysis.head())
    
    # Find peak demand periods
    peak_loads = nodes_df.nlargest(5, 'current_load')[['node_id', 'current_load', 'timestamp']]
    print(f"\nTop 5 Peak Loads:")
    print(peak_loads)

def example_2_supply_event_analysis():
    """Example 2: Analyze supply events and source mix"""
    print("\n=== Example 2: Supply Event Analysis ===")
    
    # Load supply events
    supply_events = []
    with open("data/generated/supply_events.jsonl", 'r') as f:
        for line in f:
            supply_events.append(json.loads(line))
    
    print(f"Loaded {len(supply_events)} supply events")
    
    # Analyze source distribution
    total_grid = sum(event['available_sources']['grid'] for event in supply_events)
    total_solar = sum(event['available_sources']['solar'] for event in supply_events)
    total_battery = sum(event['available_sources']['battery'] for event in supply_events)
    total_diesel = sum(event['available_sources']['diesel'] for event in supply_events)
    
    total_all = total_grid + total_solar + total_battery + total_diesel
    
    print(f"\nSource Distribution:")
    print(f"  Grid: {total_grid/total_all*100:.1f}%")
    print(f"  Solar: {total_solar/total_all*100:.1f}%")
    print(f"  Battery: {total_battery/total_all*100:.1f}%")
    print(f"  Diesel: {total_diesel/total_all*100:.1f}%")
    
    # Find supply scenarios
    avg_supply = sum(event['total_supply'] for event in supply_events) / len(supply_events)
    low_supply_events = [e for e in supply_events if e['total_supply'] < avg_supply * 0.8]
    high_supply_events = [e for e in supply_events if e['total_supply'] > avg_supply * 1.2]
    
    print(f"\nSupply Scenarios:")
    print(f"  Average supply: {avg_supply:.1f} kW")
    print(f"  Low supply events: {len(low_supply_events)}")
    print(f"  High supply events: {len(high_supply_events)}")

def example_3_rag_system_demo():
    """Example 3: Demonstrate RAG system with historical patterns"""
    print("\n=== Example 3: RAG System Demo ===")
    
    # Initialize RAG system
    rag = EnergyRAG(vector_store_path="data/demo_vector_store")
    
    # Load historical patterns
    patterns = load_historical_data_from_csv("data/generated/historical_patterns.csv")
    print(f"Loaded {len(patterns)} historical patterns")
    
    # Add patterns to RAG system
    added_count = rag.add_patterns_batch(patterns)
    print(f"Added {added_count} patterns to vector store")
    
    # Test different prediction scenarios
    scenarios = [
        {
            "context": "Hospital experiencing emergency surge during night hours",
            "node_ids": ["hospital_001", "hospital_002"],
            "description": "Emergency Hospital Scenario"
        },
        {
            "context": "Factory operating at peak efficiency during business hours",
            "node_ids": ["factory_001", "factory_002"],
            "description": "Peak Factory Operations"
        },
        {
            "context": "Residential area during evening peak consumption",
            "node_ids": ["residential_001", "residential_002"],
            "description": "Residential Evening Peak"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['description']} ---")
        
        request = PredictionRequest(
            current_context=scenario["context"],
            node_ids=scenario["node_ids"],
            time_horizon=2
        )
        
        response = rag.generate_prediction(request)
        
        print(f"Confidence: {response.confidence_score:.2f}")
        print(f"Similar patterns: {len(response.similar_patterns)}")
        print(f"Prediction: {response.prediction[:200]}...")
        print(f"Recommendations: {response.optimization_recommendations[:2]}")

def example_4_data_streaming_simulation():
    """Example 4: Simulate real-time data streaming"""
    print("\n=== Example 4: Data Streaming Simulation ===")
    
    # Load node data
    with open("data/generated/nodes_stream.jsonl", 'r') as f:
        nodes_data = [json.loads(line) for line in f]
    
    # Load supply events
    with open("data/generated/supply_events.jsonl", 'r') as f:
        supply_data = [json.loads(line) for line in f]
    
    print(f"Simulating streaming with {len(nodes_data)} node updates and {len(supply_data)} supply events")
    
    # Group by timestamp to simulate real-time updates
    from collections import defaultdict
    
    nodes_by_time = defaultdict(list)
    for node in nodes_data:
        timestamp = int(node['timestamp'])
        nodes_by_time[timestamp].append(node)
    
    supply_by_time = {int(event['timestamp']): event for event in supply_data}
    
    # Simulate first few time periods
    timestamps = sorted(nodes_by_time.keys())[:3]  # First 3 time periods
    
    for timestamp in timestamps:
        print(f"\n--- Time: {timestamp} ---")
        
        # Show node updates
        nodes_at_time = nodes_by_time[timestamp]
        total_demand = sum(node['current_load'] for node in nodes_at_time)
        print(f"Total demand: {total_demand:.1f} kW from {len(nodes_at_time)} nodes")
        
        # Show supply event if available
        if timestamp in supply_by_time:
            supply_event = supply_by_time[timestamp]
            total_supply = supply_event['total_supply']
            print(f"Total supply: {total_supply:.1f} kW")
            
            # Calculate supply-demand balance
            balance = total_supply - total_demand
            if balance >= 0:
                print(f"✅ Supply surplus: {balance:.1f} kW")
            else:
                print(f"⚠️  Supply deficit: {abs(balance):.1f} kW - Priority allocation needed")

def example_5_integration_with_api():
    """Example 5: Show how data integrates with API endpoints"""
    print("\n=== Example 5: API Integration Examples ===")
    
    # Show sample data formats for API
    print("Sample data formats for API integration:")
    
    # Node data for WebSocket streaming
    with open("data/generated/nodes_stream.jsonl", 'r') as f:
        sample_node = json.loads(f.readline())
    
    print(f"\nWebSocket Node Update Format:")
    print(json.dumps(sample_node, indent=2))
    
    # Supply event for grid failure simulation
    with open("data/generated/supply_events.jsonl", 'r') as f:
        sample_supply = json.loads(f.readline())
    
    print(f"\nGrid Failure Simulation Format:")
    failure_simulation = {
        "event_type": "grid_failure",
        "original_supply": sample_supply['total_supply'],
        "reduced_supply": sample_supply['total_supply'] * 0.7,  # 30% reduction
        "available_sources": {
            "grid": 0,  # Grid failed
            "solar": sample_supply['available_sources']['solar'],
            "battery": sample_supply['available_sources']['battery'],
            "diesel": sample_supply['available_sources']['diesel']
        }
    }
    print(json.dumps(failure_simulation, indent=2))

def main():
    """Run all examples"""
    print("🚀 Sample Data Usage Examples for Bharat-Grid AI\n")
    
    examples = [
        example_1_load_node_data,
        example_2_supply_event_analysis,
        example_3_rag_system_demo,
        example_4_data_streaming_simulation,
        example_5_integration_with_api
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"❌ Error in {example.__name__}: {e}")
    
    print(f"\n{'='*60}")
    print("✅ All examples completed! The sample data is ready for use in:")
    print("  - Pathway stream processing")
    print("  - RAG system training and predictions")
    print("  - API endpoint testing")
    print("  - Dashboard visualization")
    print("  - Performance benchmarking")

if __name__ == "__main__":
    main()