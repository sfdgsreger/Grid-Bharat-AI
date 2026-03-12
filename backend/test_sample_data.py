#!/usr/bin/env python3
"""
Test script to validate generated sample data
"""

import json
import csv
import os
from pathlib import Path
from schemas import EnergyNode, SupplyEvent
from rag_system import EnergyRAG, load_historical_data_from_csv, PredictionRequest

def test_node_data():
    """Test generated node data"""
    print("Testing node data...")
    
    # Test CSV format
    csv_path = "data/generated/nodes_stream.csv"
    if not os.path.exists(csv_path):
        print(f"❌ Node CSV file not found: {csv_path}")
        return False
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        nodes = list(reader)
    
    print(f"✅ Loaded {len(nodes)} nodes from CSV")
    
    # Validate data structure
    if nodes:
        sample_node = nodes[0]
        required_fields = ['node_id', 'current_load', 'priority_tier', 'source_type', 'status', 'lat', 'lng', 'timestamp']
        missing_fields = [field for field in required_fields if field not in sample_node]
        
        if missing_fields:
            print(f"❌ Missing fields in node data: {missing_fields}")
            return False
        
        print(f"✅ Node data structure valid")
        print(f"   Sample node: {sample_node['node_id']} - {sample_node['current_load']}kW - Tier {sample_node['priority_tier']}")
    
    # Test JSONL format
    jsonl_path = "data/generated/nodes_stream.jsonl"
    if os.path.exists(jsonl_path):
        with open(jsonl_path, 'r') as f:
            jsonl_nodes = [json.loads(line) for line in f if line.strip()]
        print(f"✅ Loaded {len(jsonl_nodes)} nodes from JSONL")
    
    return True

def test_supply_data():
    """Test generated supply event data"""
    print("\nTesting supply event data...")
    
    jsonl_path = "data/generated/supply_events.jsonl"
    if not os.path.exists(jsonl_path):
        print(f"❌ Supply events file not found: {jsonl_path}")
        return False
    
    with open(jsonl_path, 'r') as f:
        events = [json.loads(line) for line in f if line.strip()]
    
    print(f"✅ Loaded {len(events)} supply events")
    
    if events:
        sample_event = events[0]
        required_fields = ['event_id', 'total_supply', 'available_sources', 'timestamp']
        missing_fields = [field for field in required_fields if field not in sample_event]
        
        if missing_fields:
            print(f"❌ Missing fields in supply data: {missing_fields}")
            return False
        
        # Check source breakdown
        sources = sample_event['available_sources']
        total_from_sources = sum(sources.values())
        total_supply = sample_event['total_supply']
        
        if abs(total_from_sources - total_supply) > 0.1:  # Allow small rounding differences
            print(f"❌ Source breakdown doesn't match total supply: {total_from_sources} vs {total_supply}")
            return False
        
        print(f"✅ Supply event structure valid")
        print(f"   Sample event: {sample_event['event_id']} - {total_supply}kW total")
        print(f"   Sources: Grid={sources['grid']}, Solar={sources['solar']}, Battery={sources['battery']}, Diesel={sources['diesel']}")
    
    return True

def test_historical_patterns():
    """Test generated historical patterns"""
    print("\nTesting historical patterns...")
    
    csv_path = "data/generated/historical_patterns.csv"
    if not os.path.exists(csv_path):
        print(f"❌ Historical patterns file not found: {csv_path}")
        return False
    
    # Load patterns using the RAG system utility
    try:
        patterns = load_historical_data_from_csv(csv_path)
        print(f"✅ Loaded {len(patterns)} historical patterns")
        
        if patterns:
            sample_pattern = patterns[0]
            print(f"   Sample pattern: {sample_pattern.pattern_id}")
            print(f"   Node: {sample_pattern.node_id}")
            print(f"   Context: {sample_pattern.context}")
            print(f"   Consumption: {sample_pattern.consumption_data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load historical patterns: {e}")
        return False

def test_rag_integration():
    """Test RAG system integration with generated data"""
    print("\nTesting RAG system integration...")
    
    try:
        # Initialize RAG system
        rag = EnergyRAG(vector_store_path="data/test_vector_store")
        
        # Load historical patterns
        patterns = load_historical_data_from_csv("data/generated/historical_patterns.csv")
        
        # Add patterns to RAG system
        added_count = rag.add_patterns_batch(patterns[:10])  # Test with first 10 patterns
        print(f"✅ Added {added_count} patterns to RAG system")
        
        # Test prediction
        request = PredictionRequest(
            current_context="Hospital experiencing increased patient load during evening hours",
            node_ids=["hospital_001"],
            time_horizon=2
        )
        
        response = rag.generate_prediction(request)
        print(f"✅ Generated prediction successfully")
        print(f"   Confidence: {response.confidence_score:.2f}")
        print(f"   Similar patterns found: {len(response.similar_patterns)}")
        print(f"   Prediction preview: {response.prediction[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_quality():
    """Test data quality and realism"""
    print("\nTesting data quality...")
    
    # Load node data
    with open("data/generated/nodes_stream.csv", 'r') as f:
        reader = csv.DictReader(f)
        nodes = list(reader)
    
    # Check node types distribution
    node_types = {}
    priority_tiers = {}
    source_types = {}
    
    for node in nodes:
        node_type = node['node_id'].split('_')[0]
        node_types[node_type] = node_types.get(node_type, 0) + 1
        
        tier = int(node['priority_tier'])
        priority_tiers[tier] = priority_tiers.get(tier, 0) + 1
        
        source = node['source_type']
        source_types[source] = source_types.get(source, 0) + 1
    
    print(f"✅ Node type distribution: {node_types}")
    print(f"✅ Priority tier distribution: {priority_tiers}")
    print(f"✅ Source type distribution: {source_types}")
    
    # Check load ranges
    loads = [float(node['current_load']) for node in nodes]
    min_load, max_load = min(loads), max(loads)
    avg_load = sum(loads) / len(loads)
    
    print(f"✅ Load range: {min_load:.1f} - {max_load:.1f} kW (avg: {avg_load:.1f} kW)")
    
    # Validate realistic ranges
    if min_load < 0:
        print("❌ Negative load values found")
        return False
    
    if max_load > 1000:  # Reasonable upper bound
        print("❌ Unrealistically high load values found")
        return False
    
    print("✅ Data quality checks passed")
    return True

def main():
    """Run all tests"""
    print("🔍 Testing Generated Sample Data for Bharat-Grid AI\n")
    
    tests = [
        ("Node Data", test_node_data),
        ("Supply Data", test_supply_data),
        ("Historical Patterns", test_historical_patterns),
        ("Data Quality", test_data_quality),
        ("RAG Integration", test_rag_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name} Test")
        print('='*50)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All tests passed! Sample data is ready for use.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()