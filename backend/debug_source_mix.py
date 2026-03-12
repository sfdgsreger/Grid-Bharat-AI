#!/usr/bin/env python3
"""
Debug script for source mix optimization issue
"""

import sys
import os
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schemas import EnergyNode, SupplyEvent, AvailableSources, Location
from utils.priority_algo import PriorityAllocator


def debug_source_mix():
    """Debug the source mix optimization issue"""
    print("Debugging Source Mix Optimization")
    print("-" * 40)
    
    allocator = PriorityAllocator()
    print(f"Source preference order: {allocator.source_preference}")
    
    hospital = EnergyNode(
        node_id="test_hospital",
        current_load=100.0,
        priority_tier=1,
        source_type="Grid",
        status="active",
        location=Location(lat=28.6139, lng=77.2090),
        timestamp=time.time()
    )
    
    # Test solar preference
    solar_supply = SupplyEvent(
        event_id="solar_test",
        total_supply=150.0,
        available_sources=AvailableSources(
            solar=120.0,
            grid=20.0,
            battery=10.0,
            diesel=0.0
        ),
        timestamp=time.time()
    )
    
    print(f"Hospital needs: {hospital.current_load}kW")
    print(f"Available sources: Solar={solar_supply.available_sources.solar}, Grid={solar_supply.available_sources.grid}, Battery={solar_supply.available_sources.battery}, Diesel={solar_supply.available_sources.diesel}")
    
    allocations = allocator.allocate_power([hospital], solar_supply)
    allocation = allocations[0]
    
    print(f"Allocation result:")
    print(f"  Solar: {allocation.source_mix.solar}")
    print(f"  Grid: {allocation.source_mix.grid}")
    print(f"  Battery: {allocation.source_mix.battery}")
    print(f"  Diesel: {allocation.source_mix.diesel}")
    print(f"  Total allocated: {allocation.allocated_power}")
    print(f"  Action: {allocation.action}")
    
    # Test the _optimize_source_mix method directly
    print("\nTesting _optimize_source_mix directly:")
    available_sources = {
        'solar': 120.0,
        'grid': 20.0,
        'battery': 10.0,
        'diesel': 0.0
    }
    
    source_mix = allocator._optimize_source_mix(100.0, available_sources)
    print(f"Direct source mix result: {source_mix}")
    
    # Test the _allocate_to_node method directly
    print("\nTesting _allocate_to_node directly:")
    remaining_sources = {
        'solar': 120.0,
        'grid': 20.0,
        'battery': 10.0,
        'diesel': 0.0
    }
    
    allocated_power, source_mix, action = allocator._allocate_to_node(hospital, remaining_sources)
    print(f"Direct allocation result:")
    print(f"  Allocated power: {allocated_power}")
    print(f"  Source mix: {source_mix}")
    print(f"  Action: {action}")


if __name__ == "__main__":
    debug_source_mix()