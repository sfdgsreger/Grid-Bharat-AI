#!/usr/bin/env python3
"""
Supply Event Data Generator for Bharat-Grid AI

Generates realistic supply event data with:
- Realistic source mix variations (grid, solar, battery, diesel)
- Daily solar patterns
- Grid stability fluctuations
- Battery charge/discharge cycles
- Emergency diesel activation
- Seasonal variations
"""

import json
import random
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

class SupplyScenario(Enum):
    NORMAL = "normal"
    GRID_FAILURE = "grid_failure"
    SOLAR_PEAK = "solar_peak"
    BATTERY_LOW = "battery_low"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"

@dataclass
class SupplyProfile:
    grid_base: float
    solar_base: float
    battery_base: float
    diesel_base: float
    variability: float

class SupplyEventGenerator:
    def __init__(self):
        # Base supply capacities (in kW)
        self.supply_profiles = {
            SupplyScenario.NORMAL: SupplyProfile(
                grid_base=800.0,
                solar_base=400.0,
                battery_base=200.0,
                diesel_base=100.0,
                variability=0.15
            ),
            SupplyScenario.GRID_FAILURE: SupplyProfile(
                grid_base=0.0,
                solar_base=300.0,
                battery_base=150.0,
                diesel_base=200.0,
                variability=0.25
            ),
            SupplyScenario.SOLAR_PEAK: SupplyProfile(
                grid_base=600.0,
                solar_base=600.0,
                battery_base=250.0,
                diesel_base=50.0,
                variability=0.10
            ),
            SupplyScenario.BATTERY_LOW: SupplyProfile(
                grid_base=700.0,
                solar_base=350.0,
                battery_base=50.0,
                diesel_base=150.0,
                variability=0.20
            ),
            SupplyScenario.EMERGENCY: SupplyProfile(
                grid_base=200.0,
                solar_base=100.0,
                battery_base=100.0,
                diesel_base=300.0,
                variability=0.30
            ),
            SupplyScenario.MAINTENANCE: SupplyProfile(
                grid_base=500.0,
                solar_base=200.0,
                battery_base=150.0,
                diesel_base=80.0,
                variability=0.20
            )
        }
        
        self.event_counter = 1
        self.battery_charge = 200.0  # Current battery charge level
        self.max_battery_capacity = 250.0
        self.min_battery_capacity = 50.0
    
    def get_solar_multiplier(self, timestamp: float) -> float:
        """Calculate solar generation multiplier based on time of day and season"""
        dt = datetime.fromtimestamp(timestamp)
        hour = dt.hour
        day_of_year = dt.timetuple().tm_yday
        
        # Daily solar pattern (peak at noon)
        if 6 <= hour <= 18:
            # Bell curve centered at noon
            daily_mult = math.exp(-0.5 * ((hour - 12) / 3) ** 2)
        else:
            daily_mult = 0.0
        
        # Seasonal variation (higher in summer)
        seasonal_mult = 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
        
        # Weather variation (random clouds, etc.)
        weather_mult = random.uniform(0.7, 1.0)
        
        return daily_mult * seasonal_mult * weather_mult
    
    def get_grid_stability(self, timestamp: float) -> float:
        """Calculate grid stability factor"""
        dt = datetime.fromtimestamp(timestamp)
        hour = dt.hour
        
        # Grid is less stable during peak hours
        if 18 <= hour <= 22:  # Evening peak
            base_stability = 0.85
        elif 6 <= hour <= 9:  # Morning peak
            base_stability = 0.90
        else:
            base_stability = 0.95
        
        # Add random fluctuations
        fluctuation = random.gauss(0, 0.05)
        return max(0.5, min(1.0, base_stability + fluctuation))
    
    def update_battery_charge(self, solar_available: float, grid_available: float, 
                            current_demand: float, time_delta: float) -> float:
        """Update battery charge level based on supply/demand balance"""
        # Estimate current demand (simplified)
        estimated_demand = current_demand or random.uniform(800, 1200)
        
        # Calculate excess/deficit
        renewable_supply = solar_available
        supply_deficit = estimated_demand - grid_available - renewable_supply
        
        # Battery charging/discharging logic
        if supply_deficit < 0:  # Excess supply - charge battery
            charge_rate = min(abs(supply_deficit), 50.0)  # Max 50kW charging
            self.battery_charge = min(
                self.max_battery_capacity,
                self.battery_charge + (charge_rate * time_delta / 3600)
            )
        elif supply_deficit > 0:  # Supply deficit - discharge battery
            discharge_rate = min(supply_deficit, 100.0)  # Max 100kW discharge
            self.battery_charge = max(
                self.min_battery_capacity,
                self.battery_charge - (discharge_rate * time_delta / 3600)
            )
        
        return min(self.battery_charge, 100.0)  # Max discharge rate
    
    def determine_scenario(self, timestamp: float, previous_scenario: SupplyScenario = None) -> SupplyScenario:
        """Determine supply scenario based on conditions and randomness"""
        dt = datetime.fromtimestamp(timestamp)
        hour = dt.hour
        
        # Scenario probabilities
        if previous_scenario == SupplyScenario.GRID_FAILURE:
            # Grid failures tend to persist
            if random.random() < 0.7:
                return SupplyScenario.GRID_FAILURE
        
        # Time-based scenario preferences
        if 11 <= hour <= 15:  # Solar peak hours
            if random.random() < 0.3:
                return SupplyScenario.SOLAR_PEAK
        
        if 18 <= hour <= 22:  # Evening peak demand
            if random.random() < 0.2:
                return SupplyScenario.BATTERY_LOW
        
        # Random events
        rand = random.random()
        if rand < 0.05:
            return SupplyScenario.GRID_FAILURE
        elif rand < 0.08:
            return SupplyScenario.EMERGENCY
        elif rand < 0.12:
            return SupplyScenario.MAINTENANCE
        elif rand < 0.20 and 11 <= hour <= 15:
            return SupplyScenario.SOLAR_PEAK
        else:
            return SupplyScenario.NORMAL
    
    def add_noise(self, value: float, noise_factor: float) -> float:
        """Add realistic noise to supply values"""
        noise = random.gauss(0, noise_factor)
        return max(0, value * (1 + noise))
    
    def generate_supply_event(self, timestamp: float, scenario: SupplyScenario = None, 
                            time_delta: float = 10.0) -> Dict:
        """Generate a single supply event"""
        if scenario is None:
            scenario = self.determine_scenario(timestamp)
        
        profile = self.supply_profiles[scenario]
        
        # Calculate base supplies
        grid_supply = profile.grid_base * self.get_grid_stability(timestamp)
        solar_supply = profile.solar_base * self.get_solar_multiplier(timestamp)
        
        # Update battery based on supply/demand dynamics
        battery_supply = self.update_battery_charge(
            solar_supply, grid_supply, None, time_delta
        )
        
        # Diesel is used as last resort
        diesel_supply = profile.diesel_base
        if scenario in [SupplyScenario.GRID_FAILURE, SupplyScenario.EMERGENCY]:
            diesel_supply *= random.uniform(1.5, 2.0)
        elif scenario == SupplyScenario.NORMAL:
            diesel_supply *= random.uniform(0.2, 0.5)
        
        # Add noise to all sources
        grid_supply = self.add_noise(grid_supply, profile.variability)
        solar_supply = self.add_noise(solar_supply, profile.variability * 0.5)
        battery_supply = self.add_noise(battery_supply, profile.variability * 0.3)
        diesel_supply = self.add_noise(diesel_supply, profile.variability)
        
        # Calculate total supply
        total_supply = grid_supply + solar_supply + battery_supply + diesel_supply
        
        # Generate event ID
        event_id = f"supply_{self.event_counter:06d}"
        self.event_counter += 1
        
        return {
            "event_id": event_id,
            "total_supply": round(total_supply, 1),
            "grid": round(grid_supply, 1),
            "solar": round(solar_supply, 1),
            "battery": round(battery_supply, 1),
            "diesel": round(diesel_supply, 1),
            "scenario": scenario.value,
            "timestamp": timestamp
        }
    
    def generate_stream(self, start_time: float, duration_hours: int = 24,
                       interval_seconds: int = 10, output_file: str = "supply_stream.jsonl") -> None:
        """Generate a continuous stream of supply events"""
        print(f"Generating supply event stream for {duration_hours} hours...")
        
        with open(output_file, 'w') as jsonfile:
            current_time = start_time
            end_time = start_time + (duration_hours * 3600)
            previous_scenario = None
            
            while current_time < end_time:
                scenario = self.determine_scenario(current_time, previous_scenario)
                event = self.generate_supply_event(current_time, scenario, interval_seconds)
                
                # Write JSONL format
                jsonfile.write(json.dumps(event) + '\n')
                
                previous_scenario = scenario
                current_time += interval_seconds
                
                # Progress indicator
                progress = ((current_time - start_time) / (end_time - start_time)) * 100
                if int(progress) % 10 == 0:
                    print(f"Progress: {progress:.1f}%")
        
        print(f"Generated supply event stream: {output_file}")
    
    def generate_failure_scenarios(self, base_time: float, output_file: str = "supply_failures.jsonl") -> None:
        """Generate specific failure scenarios for testing"""
        scenarios = [
            {"name": "minor_grid_dip", "scenario": SupplyScenario.NORMAL, "duration": 300},
            {"name": "major_grid_failure", "scenario": SupplyScenario.GRID_FAILURE, "duration": 1800},
            {"name": "solar_intermittency", "scenario": SupplyScenario.SOLAR_PEAK, "duration": 600},
            {"name": "battery_depletion", "scenario": SupplyScenario.BATTERY_LOW, "duration": 900},
            {"name": "emergency_response", "scenario": SupplyScenario.EMERGENCY, "duration": 1200},
            {"name": "maintenance_window", "scenario": SupplyScenario.MAINTENANCE, "duration": 3600},
        ]
        
        with open(output_file, 'w') as jsonfile:
            current_time = base_time
            
            for scenario_config in scenarios:
                scenario = SupplyScenario(scenario_config["scenario"].value)
                duration = scenario_config["duration"]
                end_time = current_time + duration
                
                # Reset battery for each scenario
                self.battery_charge = 200.0
                
                while current_time < end_time:
                    event = self.generate_supply_event(current_time, scenario)
                    event["test_scenario"] = scenario_config["name"]
                    jsonfile.write(json.dumps(event) + '\n')
                    current_time += 10  # 10-second intervals
                
                # Add buffer between scenarios
                current_time += 300
        
        print(f"Generated failure scenarios: {output_file}")
    
    def generate_daily_pattern(self, base_time: float, output_file: str = "supply_daily_pattern.jsonl") -> None:
        """Generate a full daily pattern showing all supply variations"""
        print("Generating daily supply pattern...")
        
        with open(output_file, 'w') as jsonfile:
            # Generate 24 hours with 1-minute intervals
            for hour in range(24):
                for minute in range(0, 60, 5):  # Every 5 minutes
                    timestamp = base_time + (hour * 3600) + (minute * 60)
                    
                    # Force different scenarios at specific times for demonstration
                    if 12 <= hour <= 14:  # Solar peak
                        scenario = SupplyScenario.SOLAR_PEAK
                    elif hour == 20:  # Evening grid stress
                        scenario = SupplyScenario.BATTERY_LOW
                    elif hour == 3:  # Night maintenance
                        scenario = SupplyScenario.MAINTENANCE
                    else:
                        scenario = None  # Auto-determine
                    
                    event = self.generate_supply_event(timestamp, scenario)
                    event["hour"] = hour
                    event["minute"] = minute
                    jsonfile.write(json.dumps(event) + '\n')
        
        print(f"Generated daily pattern: {output_file}")

def main():
    """Main function to generate supply data"""
    generator = SupplyEventGenerator()
    
    # Current time as base
    base_time = time.time()
    
    # Generate 24-hour stream with 10-second intervals
    generator.generate_stream(
        start_time=base_time,
        duration_hours=24,
        interval_seconds=10,
        output_file="data/supply_stream_generated.jsonl"
    )
    
    # Generate failure scenarios for testing
    generator.generate_failure_scenarios(
        base_time=base_time,
        output_file="data/supply_failure_scenarios.jsonl"
    )
    
    # Generate daily pattern for analysis
    generator.generate_daily_pattern(
        base_time=base_time,
        output_file="data/supply_daily_pattern.jsonl"
    )
    
    print("Supply data generation complete!")

if __name__ == "__main__":
    main()