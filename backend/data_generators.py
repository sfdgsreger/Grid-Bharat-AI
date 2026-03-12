# Sample Data Generators for Bharat-Grid AI
import json
import csv
import random
import time
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np

from schemas import EnergyNode, SupplyEvent, Location, AvailableSources
from rag_system import ConsumptionPattern

class EnergyNodeGenerator:
    """Generate realistic energy node data streams"""
    
    def __init__(self, seed: int = 42):
        """Initialize generator with random seed for reproducibility"""
        random.seed(seed)
        np.random.seed(seed)
        
        # Define node types and their characteristics
        self.node_types = {
            'hospital': {
                'priority_tier': 1,
                'base_load': (120, 200),  # kW range
                'load_variance': 0.3,
                'peak_hours': [(7, 9), (18, 22)],  # Morning and evening peaks
                'source_preference': ['Grid', 'Battery', 'Diesel'],
                'locations': [  # Major Indian cities
                    (28.6139, 77.2090),  # Delhi
                    (19.0760, 72.8777),  # Mumbai
                    (13.0827, 80.2707),  # Chennai
                    (22.5726, 88.3639),  # Kolkata
                    (12.9716, 77.5946),  # Bangalore
                ]
            },
            'factory': {
                'priority_tier': 2,
                'base_load': (200, 400),
                'load_variance': 0.4,
                'peak_hours': [(8, 18)],  # Business hours
                'source_preference': ['Grid', 'Solar', 'Battery'],
                'locations': [
                    (28.4595, 77.0266),  # Gurgaon
                    (19.0896, 72.8656),  # Andheri
                    (13.0358, 80.2297),  # Guindy
                    (22.6708, 88.0977),  # Salt Lake
                    (12.8406, 77.6602),  # Electronic City
                ]
            },
            'residential': {
                'priority_tier': 3,
                'base_load': (50, 120),
                'load_variance': 0.5,
                'peak_hours': [(6, 8), (19, 23)],  # Morning and evening
                'source_preference': ['Grid', 'Solar'],
                'locations': [
                    (28.5355, 77.3910),  # Noida
                    (19.1136, 72.8697),  # Bandra
                    (13.0475, 80.2209),  # T Nagar
                    (22.5448, 88.3426),  # Park Street
                    (12.9698, 77.7500),  # Whitefield
                ]
            }
        }
    
    def generate_node_stream(self, 
                           duration_hours: int = 24,
                           nodes_per_type: int = 5,
                           interval_seconds: int = 60) -> List[EnergyNode]:
        """Generate a stream of energy node data over time"""
        nodes = []
        start_time = time.time()
        
        # Create node IDs and base configurations
        node_configs = []
        for node_type, config in self.node_types.items():
            for i in range(nodes_per_type):
                location = random.choice(config['locations'])
                base_load = random.uniform(*config['base_load'])
                
                if node_type == 'hospital':
                    sub_nodes = [
                        ('icu', 1, 0.35),
                        ('ventilators', 1, 0.15),
                        ('hallways', 3, 0.35),
                        ('canteen', 3, 0.15)
                    ]
                    for sub_name, tier, fraction in sub_nodes:
                        sub_id = f"hospital_{i+1:03d}_{sub_name}"
                        sub_config = dict(config)
                        sub_config['priority_tier'] = tier
                        node_configs.append({
                            'node_id': sub_id,
                            'type': f"hospital_{sub_name}",
                            'config': sub_config,
                            'location': Location(lat=location[0], lng=location[1]),
                            'base_load': base_load * fraction
                        })
                else:
                    node_id = f"{node_type}_{i+1:03d}"
                    node_configs.append({
                        'node_id': node_id,
                        'type': node_type,
                        'config': config,
                        'location': Location(lat=location[0], lng=location[1]),
                        'base_load': base_load
                    })
        
        # Generate time series data
        total_points = int(duration_hours * 3600 / interval_seconds)
        
        for point in range(total_points):
            timestamp = start_time + (point * interval_seconds)
            current_hour = datetime.fromtimestamp(timestamp).hour
            
            for node_config in node_configs:
                # Calculate load based on time of day and node characteristics
                load = self._calculate_realistic_load(
                    node_config, current_hour, timestamp
                )
                
                # Determine status based on load and random factors
                status = self._determine_node_status(load, node_config['base_load'])
                
                # Select source type based on preferences and time
                source_type = self._select_source_type(
                    node_config['config']['source_preference'], current_hour
                )
                
                node = EnergyNode(
                    node_id=node_config['node_id'],
                    current_load=round(load, 2),
                    priority_tier=node_config['config']['priority_tier'],
                    source_type=source_type,
                    status=status,
                    location=node_config['location'],
                    timestamp=timestamp
                )
                
                nodes.append(node)
        
        return nodes
    
    def _calculate_realistic_load(self, node_config: Dict, current_hour: int, timestamp: float) -> float:
        """Calculate realistic load based on time patterns and node type"""
        base_load = node_config['base_load']
        config = node_config['config']
        
        # Base load with some random variation
        load = base_load * (1 + random.uniform(-0.1, 0.1))
        
        # Apply time-of-day patterns
        peak_multiplier = 1.0
        for peak_start, peak_end in config['peak_hours']:
            if peak_start <= current_hour <= peak_end:
                peak_multiplier = 1.3 + random.uniform(0, 0.4)
                break
        
        # Apply day-of-week patterns (weekends are different)
        day_of_week = datetime.fromtimestamp(timestamp).weekday()
        if day_of_week >= 5:  # Weekend
            if node_config['type'] == 'factory':
                peak_multiplier *= 0.3  # Factories run less on weekends
            elif node_config['type'] == 'residential':
                peak_multiplier *= 1.2  # Residential higher on weekends
        
        # Apply seasonal/weather simulation (simplified)
        season_factor = 1 + 0.2 * math.sin(timestamp / (365 * 24 * 3600) * 2 * math.pi)
        
        # Add some noise for realism
        noise = random.uniform(-config['load_variance'], config['load_variance'])
        
        final_load = load * peak_multiplier * season_factor * (1 + noise)
        return max(0, final_load)  # Ensure non-negative
    
    def _determine_node_status(self, current_load: float, base_load: float) -> str:
        """Determine node status based on load patterns"""
        load_ratio = current_load / base_load
        
        if load_ratio < 0.1:
            return 'inactive'
        elif load_ratio < 0.7 or random.random() < 0.05:  # 5% chance of degraded
            return 'degraded'
        else:
            return 'active'
    
    def _select_source_type(self, preferences: List[str], current_hour: int) -> str:
        """Select source type based on preferences and time of day"""
        # Solar is more likely during day hours
        if 'Solar' in preferences and 6 <= current_hour <= 18:
            if random.random() < 0.6:  # 60% chance during day
                return 'Solar'
        
        # Battery is more likely during peak hours
        if 'Battery' in preferences and (7 <= current_hour <= 9 or 18 <= current_hour <= 22):
            if random.random() < 0.3:  # 30% chance during peaks
                return 'Battery'
        
        # Default to grid or first preference
        return preferences[0] if preferences else 'Grid'

class SupplyEventGenerator:
    """Generate realistic supply event simulation data"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
        
        # Define supply scenarios
        self.scenarios = {
            'normal': {
                'total_supply_range': (2000, 3000),  # kW
                'source_distribution': {
                    'grid': 0.6, 'solar': 0.25, 'battery': 0.1, 'diesel': 0.05
                },
                'variability': 0.1
            },
            'peak_demand': {
                'total_supply_range': (1800, 2500),
                'source_distribution': {
                    'grid': 0.5, 'solar': 0.2, 'battery': 0.2, 'diesel': 0.1
                },
                'variability': 0.2
            },
            'grid_failure': {
                'total_supply_range': (800, 1200),
                'source_distribution': {
                    'grid': 0.0, 'solar': 0.4, 'battery': 0.35, 'diesel': 0.25
                },
                'variability': 0.3
            },
            'renewable_peak': {
                'total_supply_range': (2500, 3500),
                'source_distribution': {
                    'grid': 0.3, 'solar': 0.6, 'battery': 0.08, 'diesel': 0.02
                },
                'variability': 0.15
            }
        }
    
    def generate_supply_events(self, 
                             duration_hours: int = 24,
                             interval_minutes: int = 5) -> List[SupplyEvent]:
        """Generate supply events with realistic scenarios"""
        events = []
        start_time = time.time()
        total_points = int(duration_hours * 60 / interval_minutes)
        
        for point in range(total_points):
            timestamp = start_time + (point * interval_minutes * 60)
            current_hour = datetime.fromtimestamp(timestamp).hour
            
            # Select scenario based on time and random events
            scenario = self._select_scenario(current_hour, timestamp)
            scenario_config = self.scenarios[scenario]
            
            # Generate total supply
            total_supply = random.uniform(*scenario_config['total_supply_range'])
            
            # Add time-based variations
            total_supply *= self._get_time_multiplier(current_hour)
            
            # Distribute across sources
            sources = self._distribute_supply(total_supply, scenario_config)
            
            event = SupplyEvent(
                event_id=f"supply_{int(timestamp)}_{point:04d}",
                total_supply=round(total_supply, 2),
                available_sources=sources,
                timestamp=timestamp
            )
            
            events.append(event)
        
        return events
    
    def _select_scenario(self, current_hour: int, timestamp: float) -> str:
        """Select supply scenario based on time and conditions"""
        # Grid failures more likely during extreme weather (simulated)
        if random.random() < 0.02:  # 2% chance of grid failure
            return 'grid_failure'
        
        # Renewable peak during sunny hours
        if 10 <= current_hour <= 16 and random.random() < 0.3:
            return 'renewable_peak'
        
        # Peak demand during evening hours
        if 18 <= current_hour <= 22:
            return 'peak_demand'
        
        return 'normal'
    
    def _get_time_multiplier(self, current_hour: int) -> float:
        """Get supply multiplier based on time of day"""
        # Solar production curve (simplified)
        if 6 <= current_hour <= 18:
            solar_factor = 0.5 + 0.5 * math.sin((current_hour - 6) / 12 * math.pi)
        else:
            solar_factor = 0.1
        
        # Grid stability (lower at night)
        grid_factor = 0.9 if 22 <= current_hour or current_hour <= 6 else 1.0
        
        return 0.8 + 0.4 * (solar_factor + grid_factor) / 2
    
    def _distribute_supply(self, total_supply: float, scenario_config: Dict) -> AvailableSources:
        """Distribute total supply across different sources"""
        distribution = scenario_config['source_distribution']
        variability = scenario_config['variability']
        
        # Add some randomness to distribution
        adjusted_dist = {}
        for source, ratio in distribution.items():
            adjusted_dist[source] = max(0, ratio + random.uniform(-variability, variability))
        
        # Normalize to ensure sum = 1
        total_ratio = sum(adjusted_dist.values())
        if total_ratio > 0:
            for source in adjusted_dist:
                adjusted_dist[source] /= total_ratio
        
        return AvailableSources(
            grid=round(total_supply * adjusted_dist.get('grid', 0), 2),
            solar=round(total_supply * adjusted_dist.get('solar', 0), 2),
            battery=round(total_supply * adjusted_dist.get('battery', 0), 2),
            diesel=round(total_supply * adjusted_dist.get('diesel', 0), 2)
        )

class HistoricalPatternGenerator:
    """Generate historical consumption patterns for RAG training"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
        
        # Define pattern templates
        self.pattern_templates = {
            'normal_operation': {
                'description': "Normal operational pattern",
                'load_multiplier': (0.8, 1.2),
                'duration_hours': (4, 12),
                'frequency': 0.6
            },
            'emergency_surge': {
                'description': "Emergency or surge demand pattern",
                'load_multiplier': (1.5, 2.5),
                'duration_hours': (1, 6),
                'frequency': 0.1
            },
            'maintenance_mode': {
                'description': "Reduced load during maintenance",
                'load_multiplier': (0.1, 0.4),
                'duration_hours': (2, 8),
                'frequency': 0.15
            },
            'peak_efficiency': {
                'description': "Optimized high-efficiency operation",
                'load_multiplier': (1.1, 1.4),
                'duration_hours': (6, 16),
                'frequency': 0.15
            }
        }
    
    def generate_historical_patterns(self, 
                                   days_of_history: int = 30,
                                   nodes_per_type: int = 5) -> List[ConsumptionPattern]:
        """Generate historical consumption patterns for RAG training"""
        patterns = []
        start_time = time.time() - (days_of_history * 24 * 3600)
        
        # Generate patterns for each node type
        for node_type, config in EnergyNodeGenerator(42).node_types.items():
            for node_idx in range(nodes_per_type):
                if node_type == 'hospital':
                    sub_nodes = [
                        ('icu', 1), ('ventilators', 1), ('hallways', 3), ('canteen', 3)
                    ]
                    for sub_name, tier in sub_nodes:
                        sub_id = f"hospital_{node_idx+1:03d}_{sub_name}"
                        sub_config = dict(config)
                        sub_config['priority_tier'] = tier
                        patterns.extend(self._generate_node_patterns(
                            sub_id, f"hospital_{sub_name}", sub_config, start_time, days_of_history
                        ))
                else:
                    node_id = f"{node_type}_{node_idx+1:03d}"
                    patterns.extend(self._generate_node_patterns(
                        node_id, node_type, config, start_time, days_of_history
                    ))
        
        return patterns
    
    def _generate_node_patterns(self, 
                              node_id: str, 
                              node_type: str, 
                              node_config: Dict,
                              start_time: float,
                              days: int) -> List[ConsumptionPattern]:
        """Generate patterns for a specific node"""
        patterns = []
        base_load = random.uniform(*node_config['base_load'])
        
        # Generate patterns across the time period
        current_time = start_time
        end_time = start_time + (days * 24 * 3600)
        pattern_id = 0
        
        while current_time < end_time:
            # Select pattern type
            pattern_type = self._select_pattern_type()
            template = self.pattern_templates[pattern_type]
            
            # Generate pattern duration
            duration_hours = random.uniform(*template['duration_hours'])
            pattern_end = current_time + (duration_hours * 3600)
            
            # Calculate consumption metrics
            load_multiplier = random.uniform(*template['load_multiplier'])
            current_load = base_load * load_multiplier
            peak_load = current_load * random.uniform(1.1, 1.5)
            avg_load = current_load * random.uniform(0.8, 1.0)
            
            # Create pattern
            pattern = ConsumptionPattern(
                pattern_id=f"{node_id}_pattern_{pattern_id:04d}",
                timestamp=current_time,
                node_id=node_id,
                consumption_data={
                    'current_load': round(current_load, 2),
                    'peak_load': round(peak_load, 2),
                    'avg_load': round(avg_load, 2),
                    'duration_hours': round(duration_hours, 2),
                    'load_multiplier': round(load_multiplier, 2)
                },
                context=f"{template['description']} for {node_type} during {self._get_time_context(current_time)}",
                metadata={
                    'node_type': node_type,
                    'pattern_type': pattern_type,
                    'priority_tier': node_config['priority_tier'],
                    'base_load': base_load,
                    'weather_condition': self._simulate_weather_condition(current_time),
                    'day_of_week': datetime.fromtimestamp(current_time).strftime('%A'),
                    'hour_of_day': datetime.fromtimestamp(current_time).hour
                }
            )
            
            patterns.append(pattern)
            
            # Move to next pattern
            current_time = pattern_end + random.uniform(0.5, 4) * 3600  # Gap between patterns
            pattern_id += 1
        
        return patterns
    
    def _select_pattern_type(self) -> str:
        """Select pattern type based on frequency weights"""
        rand = random.random()
        cumulative = 0
        
        for pattern_type, template in self.pattern_templates.items():
            cumulative += template['frequency']
            if rand <= cumulative:
                return pattern_type
        
        return 'normal_operation'  # Fallback
    
    def _get_time_context(self, timestamp: float) -> str:
        """Get contextual description of time period"""
        dt = datetime.fromtimestamp(timestamp)
        hour = dt.hour
        
        if 6 <= hour < 12:
            return "morning hours"
        elif 12 <= hour < 17:
            return "afternoon period"
        elif 17 <= hour < 22:
            return "evening peak"
        else:
            return "night hours"
    
    def _simulate_weather_condition(self, timestamp: float) -> str:
        """Simulate weather conditions affecting energy consumption"""
        conditions = ['clear', 'cloudy', 'hot', 'mild', 'stormy']
        weights = [0.3, 0.25, 0.2, 0.2, 0.05]
        return random.choices(conditions, weights=weights)[0]

class DataExporter:
    """Export generated data to various formats"""
    
    @staticmethod
    def export_nodes_to_csv(nodes: List[EnergyNode], filepath: str):
        """Export energy nodes to CSV format"""
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'node_id', 'current_load', 'priority_tier', 'source_type', 
                'status', 'lat', 'lng', 'timestamp'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for node in nodes:
                writer.writerow({
                    'node_id': node.node_id,
                    'current_load': node.current_load,
                    'priority_tier': node.priority_tier,
                    'source_type': node.source_type,
                    'status': node.status,
                    'lat': node.location.lat,
                    'lng': node.location.lng,
                    'timestamp': node.timestamp
                })
    
    @staticmethod
    def export_nodes_to_jsonl(nodes: List[EnergyNode], filepath: str):
        """Export energy nodes to JSON Lines format"""
        with open(filepath, 'w') as jsonfile:
            for node in nodes:
                json.dump(node.dict(), jsonfile)
                jsonfile.write('\n')
    
    @staticmethod
    def export_supply_events_to_jsonl(events: List[SupplyEvent], filepath: str):
        """Export supply events to JSON Lines format"""
        with open(filepath, 'w') as jsonfile:
            for event in events:
                json.dump(event.dict(), jsonfile)
                jsonfile.write('\n')
    
    @staticmethod
    def export_patterns_to_csv(patterns: List[ConsumptionPattern], filepath: str):
        """Export consumption patterns to CSV format"""
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'pattern_id', 'timestamp', 'node_id', 'context',
                'current_load', 'peak_load', 'avg_load', 'duration_hours',
                'node_type', 'pattern_type', 'priority_tier', 'weather_condition'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for pattern in patterns:
                consumption = pattern.consumption_data
                metadata = pattern.metadata
                
                writer.writerow({
                    'pattern_id': pattern.pattern_id,
                    'timestamp': pattern.timestamp,
                    'node_id': pattern.node_id,
                    'context': pattern.context,
                    'current_load': consumption.get('current_load', 0),
                    'peak_load': consumption.get('peak_load', 0),
                    'avg_load': consumption.get('avg_load', 0),
                    'duration_hours': consumption.get('duration_hours', 0),
                    'node_type': metadata.get('node_type', ''),
                    'pattern_type': metadata.get('pattern_type', ''),
                    'priority_tier': metadata.get('priority_tier', 3),
                    'weather_condition': metadata.get('weather_condition', '')
                })

def generate_complete_dataset(output_dir: str = "backend/data/generated", 
                            duration_hours: int = 24,
                            history_days: int = 30,
                            nodes_per_type: int = 5):
    """Generate complete dataset with all components"""
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Generating complete dataset in {output_dir}...")
    
    # Initialize generators
    node_gen = EnergyNodeGenerator()
    supply_gen = SupplyEventGenerator()
    pattern_gen = HistoricalPatternGenerator()
    
    # Generate energy node streams
    print("Generating energy node data streams...")
    nodes = node_gen.generate_node_stream(
        duration_hours=duration_hours,
        nodes_per_type=nodes_per_type,
        interval_seconds=60  # 1-minute intervals
    )
    
    # Generate supply events
    print("Generating supply event data...")
    supply_events = supply_gen.generate_supply_events(
        duration_hours=duration_hours,
        interval_minutes=5  # 5-minute intervals
    )
    
    # Generate historical patterns
    print("Generating historical consumption patterns...")
    historical_patterns = pattern_gen.generate_historical_patterns(
        days_of_history=history_days,
        nodes_per_type=nodes_per_type
    )
    
    # Export data
    print("Exporting data files...")
    
    # Export nodes
    DataExporter.export_nodes_to_csv(nodes, f"{output_dir}/nodes_stream.csv")
    DataExporter.export_nodes_to_jsonl(nodes, f"{output_dir}/nodes_stream.jsonl")
    
    # Export supply events
    DataExporter.export_supply_events_to_jsonl(supply_events, f"{output_dir}/supply_events.jsonl")
    
    # Export historical patterns
    DataExporter.export_patterns_to_csv(historical_patterns, f"{output_dir}/historical_patterns.csv")
    
    # Generate summary statistics
    stats = {
        'generation_timestamp': time.time(),
        'duration_hours': duration_hours,
        'history_days': history_days,
        'nodes_per_type': nodes_per_type,
        'total_nodes': len(nodes),
        'total_supply_events': len(supply_events),
        'total_historical_patterns': len(historical_patterns),
        'node_types': list(node_gen.node_types.keys()),
        'supply_scenarios': list(supply_gen.scenarios.keys()),
        'pattern_types': list(pattern_gen.pattern_templates.keys())
    }
    
    with open(f"{output_dir}/dataset_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"Dataset generation complete!")
    print(f"Generated {len(nodes)} node data points")
    print(f"Generated {len(supply_events)} supply events")
    print(f"Generated {len(historical_patterns)} historical patterns")
    print(f"Files saved to {output_dir}/")
    
    return stats

# Quick generation functions for testing
def generate_sample_nodes(count: int = 50) -> List[EnergyNode]:
    """Generate a small sample of nodes for quick testing"""
    gen = EnergyNodeGenerator()
    return gen.generate_node_stream(duration_hours=1, nodes_per_type=count//3, interval_seconds=300)

def generate_sample_supply_events(count: int = 20) -> List[SupplyEvent]:
    """Generate a small sample of supply events for quick testing"""
    gen = SupplyEventGenerator()
    return gen.generate_supply_events(duration_hours=2, interval_minutes=10)

def generate_sample_patterns(count: int = 30) -> List[ConsumptionPattern]:
    """Generate a small sample of historical patterns for quick testing"""
    gen = HistoricalPatternGenerator()
    return gen.generate_historical_patterns(days_of_history=7, nodes_per_type=count//9)

if __name__ == "__main__":
    # Generate complete dataset
    stats = generate_complete_dataset(
        duration_hours=24,
        history_days=30,
        nodes_per_type=5
    )
    
    print("\nDataset Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")