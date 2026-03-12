#!/usr/bin/env python3
"""
Sample Data Generation Script for Bharat-Grid AI
Generates realistic energy node streams, supply events, and historical patterns
"""

import os
import sys
import argparse
from pathlib import Path

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generators import (
    EnergyNodeGenerator, 
    SupplyEventGenerator, 
    HistoricalPatternGenerator,
    DataExporter,
    generate_complete_dataset
)
from rag_system import EnergyRAG

def main():
    parser = argparse.ArgumentParser(description='Generate sample data for Bharat-Grid AI')
    parser.add_argument('--output-dir', default='backend/data/generated', 
                       help='Output directory for generated data')
    parser.add_argument('--duration-hours', type=int, default=24,
                       help='Duration in hours for node/supply data streams')
    parser.add_argument('--history-days', type=int, default=30,
                       help='Days of historical patterns to generate')
    parser.add_argument('--nodes-per-type', type=int, default=5,
                       help='Number of nodes per type (hospital, factory, residential)')
    parser.add_argument('--populate-rag', action='store_true',
                       help='Populate RAG system with generated historical patterns')
    parser.add_argument('--quick', action='store_true',
                       help='Generate smaller dataset for quick testing')
    
    args = parser.parse_args()
    
    if args.quick:
        # Quick generation for testing
        print("Generating quick test dataset...")
        args.duration_hours = 2
        args.history_days = 7
        args.nodes_per_type = 2
    
    # Generate complete dataset
    stats = generate_complete_dataset(
        output_dir=args.output_dir,
        duration_hours=args.duration_hours,
        history_days=args.history_days,
        nodes_per_type=args.nodes_per_type
    )
    
    # Populate RAG system if requested
    if args.populate_rag:
        print("\nPopulating RAG system with historical patterns...")
        try:
            # Initialize RAG system
            rag = EnergyRAG(vector_store_path=f"{args.output_dir}/vector_store")
            
            # Load and add historical patterns
            pattern_gen = HistoricalPatternGenerator()
            patterns = pattern_gen.generate_historical_patterns(
                days_of_history=args.history_days,
                nodes_per_type=args.nodes_per_type
            )
            
            # Add patterns to RAG system
            added_count = rag.add_patterns_batch(patterns)
            print(f"Added {added_count} patterns to RAG vector store")
            
            # Get and display stats
            rag_stats = rag.get_store_stats()
            print(f"RAG system stats: {rag_stats}")
            
        except Exception as e:
            print(f"Failed to populate RAG system: {e}")
    
    print(f"\nGeneration complete! Check {args.output_dir}/ for generated files.")

if __name__ == "__main__":
    main()