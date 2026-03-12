#!/usr/bin/env python3
"""
Setup script for Bharat-Grid AI development data streams
Initializes stream configuration and generates initial data
"""

import os
import sys
import json
import time
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_generators import generate_complete_dataset
from failure_scenarios import generate_failure_scenarios
from stream_config import DataStreamManager

def setup_development_streams():
    """Set up development data streams with initial data"""
    
    print("Setting up Bharat-Grid AI development data streams...")
    
    # Create necessary directories
    directories = [
        "backend/data/streams",
        "backend/data/generated",
        "backend/data/failure_scenarios",
        "backend/data/historical"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Generate initial sample data
    print("\nGenerating initial sample data...")
    try:
        stats = generate_complete_dataset(
            output_dir="backend/data/generated",
            duration_hours=2,  # 2 hours of initial data
            history_days=7,    # 1 week of historical patterns
            nodes_per_type=3   # 3 nodes per type for development
        )
        print(f"Generated {stats['total_nodes']} node data points")
        print(f"Generated {stats['total_supply_events']} supply events")
        print(f"Generated {stats['total_historical_patterns']} historical patterns")
    except Exception as e:
        print(f"Warning: Failed to generate sample data: {e}")
    
    # Generate failure scenarios
    print("\nGenerating failure scenario data...")
    try:
        failure_stats = generate_failure_scenarios(
            output_dir="backend/data/failure_scenarios",
            num_scenarios=20,  # 20 scenarios for development
            timeline_hours=24  # 24-hour timeline
        )
        print(f"Generated {failure_stats['total_scenarios']} failure scenarios")
        print(f"Scenario types: {list(failure_stats['scenario_types'].keys())}")
    except Exception as e:
        print(f"Warning: Failed to generate failure scenarios: {e}")
    
    # Initialize stream manager to validate configuration
    print("\nValidating stream configuration...")
    try:
        manager = DataStreamManager("backend/data/stream_config.json")
        status = manager.get_stream_status()
        print(f"Stream configuration loaded successfully")
        print(f"Configured streams: {list(status['streams'].keys())}")
    except Exception as e:
        print(f"Error: Failed to initialize stream manager: {e}")
        return False
    
    # Create initial stream files with sample data
    print("\nCreating initial stream files...")
    try:
        # Copy some generated data to stream files for immediate use
        import shutil
        
        # Copy nodes data
        generated_nodes_csv = "backend/data/generated/nodes_stream.csv"
        stream_nodes_csv = "backend/data/streams/nodes_stream.csv"
        if Path(generated_nodes_csv).exists():
            shutil.copy2(generated_nodes_csv, stream_nodes_csv)
            print(f"Copied initial nodes data to {stream_nodes_csv}")
        
        generated_nodes_jsonl = "backend/data/generated/nodes_stream.jsonl"
        stream_nodes_jsonl = "backend/data/streams/nodes_stream.jsonl"
        if Path(generated_nodes_jsonl).exists():
            shutil.copy2(generated_nodes_jsonl, stream_nodes_jsonl)
            print(f"Copied initial nodes data to {stream_nodes_jsonl}")
        
        # Copy supply events
        generated_supply = "backend/data/generated/supply_events.jsonl"
        stream_supply = "backend/data/streams/supply_events.jsonl"
        if Path(generated_supply).exists():
            shutil.copy2(generated_supply, stream_supply)
            print(f"Copied initial supply events to {stream_supply}")
        
        # Copy failure scenarios
        generated_failures = "backend/data/failure_scenarios/failure_events.jsonl"
        stream_failures = "backend/data/streams/failure_scenarios.jsonl"
        if Path(generated_failures).exists():
            shutil.copy2(generated_failures, stream_failures)
            print(f"Copied initial failure scenarios to {stream_failures}")
            
    except Exception as e:
        print(f"Warning: Failed to copy initial stream files: {e}")
    
    print("\n" + "="*60)
    print("Development streams setup complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Start the development streams:")
    print("   python backend/dev_stream_manager.py")
    print("\n2. Or start with data generation:")
    print("   python backend/dev_stream_manager.py --generate-data")
    print("\n3. Run in background mode:")
    print("   python backend/dev_stream_manager.py --background")
    print("\nStream files will be created in: backend/data/streams/")
    print("Configuration file: backend/data/stream_config.json")
    
    return True

def validate_stream_setup():
    """Validate that stream setup is working correctly"""
    
    print("Validating development stream setup...")
    
    # Check required files exist
    required_files = [
        "backend/data/stream_config.json",
        "backend/stream_config.py",
        "backend/data_generators.py",
        "backend/failure_scenarios.py",
        "backend/dev_stream_manager.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("Error: Missing required files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    # Test stream manager initialization
    try:
        from stream_config import DataStreamManager
        manager = DataStreamManager("backend/data/stream_config.json")
        status = manager.get_stream_status()
        print(f"✓ Stream manager initialized successfully")
        print(f"✓ Found {len(status['streams'])} configured streams")
    except Exception as e:
        print(f"✗ Stream manager initialization failed: {e}")
        return False
    
    # Test data generators
    try:
        from data_generators import EnergyNodeGenerator, SupplyEventGenerator
        node_gen = EnergyNodeGenerator()
        supply_gen = SupplyEventGenerator()
        
        # Generate small test samples
        test_nodes = node_gen.generate_node_stream(duration_hours=0.1, nodes_per_type=1)
        test_supply = supply_gen.generate_supply_events(duration_hours=0.1, interval_minutes=5)
        
        print(f"✓ Data generators working (generated {len(test_nodes)} nodes, {len(test_supply)} supply events)")
    except Exception as e:
        print(f"✗ Data generators failed: {e}")
        return False
    
    # Test failure scenario generator
    try:
        from failure_scenarios import GridFailureScenarioGenerator
        failure_gen = GridFailureScenarioGenerator()
        print(f"✓ Failure scenario generator initialized")
        print(f"✓ Available scenarios: {list(failure_gen.scenario_templates.keys())}")
    except Exception as e:
        print(f"✗ Failure scenario generator failed: {e}")
        return False
    
    print("\n✓ All validation checks passed!")
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Bharat-Grid AI development streams")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate setup, don't generate data")
    
    args = parser.parse_args()
    
    if args.validate_only:
        success = validate_stream_setup()
    else:
        success = setup_development_streams()
        if success:
            success = validate_stream_setup()
    
    sys.exit(0 if success else 1)