#!/usr/bin/env python3
"""
Energy Node Data Generator for Bharat-Grid AI

Generates realistic energy node data streams with:
- Daily consumption cycles
- Seasonal variations
- Different facility types (hospitals, factories, residential)
- Geographic distribution across Indian cities
- Realistic load profiles and priority tiers
"""

import csv
import json
import random
import time
import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

class NodeType(Enum):
    HOSPITAL = "hospital"
    FACTORY = "factory"
    RESIDENTIAL = "residential"

class SourceType(Enum):
    GRID = "Grid"
    SOLAR = "Solar"
    BATTERY = "Battery"
    DIESEL = "Diesel"

class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"

@dataclass
class Location:
    lat: float
    lng: float
    city: str

@dataclass
class NodeProfile:
    base_load: float  # Base load in kW
    peak_multiplier: float  # Peak load multiplier
    daily_pattern: List[float]  # 24-hour pattern multipliers
    seasonal_factor: float  # Seasonal variation factor
    priority_tier: int
    preferred_sources: List[SourceType]

class EnergyNodeGenerator:
    def __init__(self):
        # Indian cities with coordinates (lat, lng)
        self.cities = [
            Location(28.6139, 77.2090, "Delhi"),
            Location(19.0760, 72.8777, "Mumbai"),
            Location(13.0827, 80.2707, "Chennai"),
            Location(22.5726, 88.3639, "Kolkata"),
            Location(12.9716, 77.5946, "Bangalore"),
            Location(17.3850, 78.4867, "Hyderabad"),
            Location(23.0225, 72.5714, "Ahmedabad"),
            Location(18.5204, 73.8567, "Pune"),
            Location(26.9124, 75.7873, "Jaipur"),
            Location(21.1458, 79.0882, "Nagpur"),
        ]
        
        # Node profiles for different facility types
        self.node_profiles = {
            NodeType.HOSPITAL: NodeProfile(
                base_load=120.0,
                peak_multiplier=1.8,
                daily_pattern=[0.7, 0.6, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.3, 1.2, 1.1, 1.0, 1.1, 1.2, 1.3, 1.2, 1.0, 0.9, 0.8, 0.7, 0.7],
                seasonal_factor=0.15,
                priority_tier=1,
                preferred_sources=[SourceType.GRID, SourceType.DIESEL, SourceType.BATTERY, SourceType.SOLAR]
            ),
            NodeType.FACTORY: NodeProfile(
                base_load=250.0,
                peak_multiplier=2.2,
                daily_pattern=[0.3, 0.2, 0.2, 0.3, 0.5, 0.8, 1.0, 1.2, 1.4, 1.5, 1.4, 1.3, 1.2, 1.3, 1.4, 1.5, 1.3, 1.0, 0.8, 0.6, 0.4, 0.3, 0.3, 0.3],
                seasonal_factor=0.25,
                priority_tier=2,
                preferred_sources=[SourceType.GRID, SourceType.SOLAR, SourceType.BATTERY, SourceType.DIESEL]
            ),
            NodeType.RESIDENTIAL: NodeProfile(
                base_load=60.0,
                peak_multiplier=2.0,
                daily_pattern=[0.4, 0.3, 0.3, 0.4, 0.5, 0.7, 0.9, 1.0, 0.8, 0.6, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.5, 1.3, 1.0, 0.8, 0.6, 0.5],
                seasonal_factor=0.3,
                priority_tier=3,
                preferred_sources=[SourceType.GRID, SourceType.SOLAR, SourceType.BATTERY, SourceType.DIESEL]
            )
        }
        
        self.node_counter = {"hospital": 1, "factory": 1, "residential": 1}
    
    def get_seasonal_multiplier(self, timestamp: float) -> float:
        """Calculate seasonal multiplier based on timestamp (higher in summer)"""
        dt = datetime.fromtimestamp(timestamp)
        day_of_year = dt.timetuple().tm_yday
        # Peak summer around day 150 (May-June), minimum around day 350 (December)
        seasonal = 1.0 + 0.3 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
        return max(0.7, min(1.3, seasonal))
    
    def get_daily_multiplier(self, timestamp: float, pattern: List[float]) -> float:
        """Get daily pattern multiplier based on hour of day"""
        dt = datetime.fromtimestamp(timestamp)
        hour = dt.hour
        return pattern[hour]
    
    def add_noise(self, value: float, noise_factor: float = 0.1) -> float:
        """Add realistic noise to values"""
        noise = random.gauss(0, noise_factor)
        return max(0, value * (1 + noise))
    
    def get_random_location(self) -> Location:
        """Get random location with small offset from city center"""
        city = random.choice(self.cities)
        # Add small random offset (within ~5km)
        lat_offset = random.gauss(0, 0.02)
        lng_offset = random.gauss(0, 0.02)
        return Location(
            city.lat + lat_offset,
            city.lng + lng_offset,
            city.city
        )
    
    def get_source_type(self, node_type: NodeType, timestamp: float) -> SourceType:
        """Determine source type based on node type and conditions"""
        profile = self.node_profiles[node_type]
        dt = datetime.fromtimestamp(timestamp)
        hour = dt.hour
        
        # Solar more likely during day (6 AM - 6 PM)
        if 6 <= hour <= 18 and random.random() < 0.4:
            if SourceType.SOLAR in profile.preferred_sources:
                return SourceType.SOLAR
        
        # Battery more likely during evening peak (6 PM - 10 PM)
        if 18 <= hour <= 22 and random.random() < 0.3:
            if SourceType.BATTERY in profile.preferred_sources:
                return SourceType.BATTERY
        
        # Diesel for emergencies (low probability)
        if random.random() < 0.05:
            return SourceType.DIESEL
        
        # Default to grid
        return SourceType.GRID
    
    def get_status(self, node_type: NodeType) -> Status:
        """Determine node status with realistic probabilities"""
        # Hospitals have higher uptime
        if node_type == NodeType.HOSPITAL:
            weights = [0.95, 0.02, 0.03]  # active, inactive, degraded
        elif node_type == NodeType.FACTORY:
            weights = [0.85, 0.05, 0.10]
        else:  # residential
            weights = [0.90, 0.05, 0.05]
        
        return random.choices(list(Status), weights=weights)[0]
    
    def generate_node(self, node_type: NodeType, timestamp: float) -> Dict:
        """Generate a single energy node record"""
        profile = self.node_profiles[node_type]
        location = self.get_random_location()
        
        # Calculate load with daily and seasonal patterns
        seasonal_mult = self.get_seasonal_multiplier(timestamp)
        daily_mult = self.get_daily_multiplier(timestamp, profile.daily_pattern)
        
        # Base calculation
        base_load = profile.base_load * seasonal_mult * daily_mult
        current_load = self.add_noise(base_load, 0.15)
        
        # Adjust for status
        status = self.get_status(node_type)
        if status == Status.INACTIVE:
            current_load = 0
        elif status == Status.DEGRADED:
            current_load *= random.uniform(0.3, 0.7)
        
        # Generate node ID
        node_id = f"{node_type.value}_{self.node_counter[node_type.value]:03d}"
        self.node_counter[node_type.value] += 1
        
        return {
            "node_id": node_id,
            "current_load": round(current_load, 1),
            "priority_tier": profile.priority_tier,
            "source_type": self.get_source_type(node_type, timestamp).value,
            "status": status.value,
            "lat": round(location.lat, 4),
            "lng": round(location.lng, 4),
            "timestamp": timestamp
        }
    
    def generate_batch(self, timestamp: float, num_hospitals: int = 5, 
                      num_factories: int = 8, num_residential: int = 12) -> List[Dict]:
        """Generate a batch of nodes for a given timestamp"""
        nodes = []
        
        # Generate hospitals
        for _ in range(num_hospitals):
            nodes.append(self.generate_node(NodeType.HOSPITAL, timestamp))
        
        # Generate factories
        for _ in range(num_factories):
            nodes.append(self.generate_node(NodeType.FACTORY, timestamp))
        
        # Generate residential
        for _ in range(num_residential):
            nodes.append(self.generate_node(NodeType.RESIDENTIAL, timestamp))
        
        return nodes
    
    def generate_stream(self, start_time: float, duration_hours: int = 24, 
                       interval_seconds: int = 10, output_file: str = "nodes_stream.csv") -> None:
        """Generate a continuous stream of node data"""
        print(f"Generating node data stream for {duration_hours} hours...")
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['node_id', 'current_load', 'priority_tier', 'source_type', 
                         'status', 'lat', 'lng', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            current_time = start_time
            end_time = start_time + (duration_hours * 3600)
            
            while current_time < end_time:
                # Reset counters for each timestamp to maintain consistent node IDs
                self.node_counter = {"hospital": 1, "factory": 1, "residential": 1}
                
                nodes = self.generate_batch(current_time)
                for node in nodes:
                    writer.writerow(node)
                
                current_time += interval_seconds
                
                # Progress indicator
                progress = ((current_time - start_time) / (end_time - start_time)) * 100
                if int(progress) % 10 == 0:
                    print(f"Progress: {progress:.1f}%")
        
        print(f"Generated node data stream: {output_file}")
    
    def generate_varied_scenarios(self, base_time: float, output_file: str = "nodes_varied.csv") -> None:
        """Generate varied scenarios for testing"""
        scenarios = [
            {"name": "normal_day", "hospitals": 5, "factories": 8, "residential": 12},
            {"name": "high_demand", "hospitals": 8, "factories": 12, "residential": 20},
            {"name": "emergency", "hospitals": 10, "factories": 5, "residential": 8},
            {"name": "industrial_peak", "hospitals": 4, "factories": 15, "residential": 10},
            {"name": "residential_peak", "hospitals": 3, "factories": 6, "residential": 25},
        ]
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['scenario', 'node_id', 'current_load', 'priority_tier', 
                         'source_type', 'status', 'lat', 'lng', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, scenario in enumerate(scenarios):
                timestamp = base_time + (i * 3600)  # 1 hour apart
                self.node_counter = {"hospital": 1, "factory": 1, "residential": 1}
                
                nodes = self.generate_batch(
                    timestamp, 
                    scenario["hospitals"], 
                    scenario["factories"], 
                    scenario["residential"]
                )
                
                for node in nodes:
                    node["scenario"] = scenario["name"]
                    writer.writerow(node)
        
        print(f"Generated varied scenarios: {output_file}")

def main():
    """Main function to generate sample data"""
    generator = EnergyNodeGenerator()
    
    # Current time as base
    base_time = time.time()
    
    # Generate 24-hour stream with 10-second intervals
    generator.generate_stream(
        start_time=base_time,
        duration_hours=24,
        interval_seconds=10,
        output_file="data/nodes_stream_generated.csv"
    )
    
    # Generate varied scenarios for testing
    generator.generate_varied_scenarios(
        base_time=base_time,
        output_file="data/nodes_scenarios.csv"
    )
    
    print("Node data generation complete!")

if __name__ == "__main__":
    main()