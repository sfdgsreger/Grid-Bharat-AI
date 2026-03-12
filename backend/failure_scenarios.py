"""
Grid Failure Scenario Data Generator for Bharat-Grid AI
Creates comprehensive failure scenarios for testing emergency response systems
"""

import json
import time
import random
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging

from schemas import SupplyEvent, EnergyNode, AvailableSources
from data_generators import SupplyEventGenerator, EnergyNodeGenerator

logger = logging.getLogger(__name__)

@dataclass
class FailureEvent:
    """Represents a grid failure event"""
    event_id: str
    scenario_type: str
    start_time: float
    duration_minutes: float
    affected_sources: List[str]
    severity_level: int  # 1-5 scale
    recovery_pattern: str
    impact_description: str
    pre_failure_supply: Dict[str, float]
    during_failure_supply: Dict[str, float]
    post_failure_supply: Dict[str, float]
    metadata: Dict[str, Any]

@dataclass
class EmergencyResponse:
    """Emergency response actions during failures"""
    response_id: str
    trigger_time: float
    action_type: str  # 'load_shedding', 'source_switching', 'priority_reallocation'
    affected_nodes: List[str]
    parameters: Dict[str, Any]
    expected_outcome: str

class GridFailureScenarioGenerator:
    """Generate comprehensive grid failure scenarios for testing"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.supply_generator = SupplyEventGenerator(seed)
        self.node_generator = EnergyNodeGenerator(seed)
        
        # Define failure scenario templates
        self.scenario_templates = {
            'grid_blackout': {
                'name': 'Complete Grid Blackout',
                'description': 'Total loss of grid power supply',
                'duration_range': (30, 240),  # 30 minutes to 4 hours
                'severity_levels': {
                    1: {'grid_reduction': 0.3, 'cascade_probability': 0.1},
                    2: {'grid_reduction': 0.5, 'cascade_probability': 0.2},
                    3: {'grid_reduction': 0.7, 'cascade_probability': 0.3},
                    4: {'grid_reduction': 0.9, 'cascade_probability': 0.4},
                    5: {'grid_reduction': 1.0, 'cascade_probability': 0.5}
                },
                'recovery_patterns': ['immediate', 'gradual', 'stepped'],
                'affected_sources': ['grid'],
                'cascade_sources': ['battery', 'diesel']
            },
            'renewable_intermittency': {
                'name': 'Renewable Energy Intermittency',
                'description': 'Sudden drop in solar/wind power generation',
                'duration_range': (15, 180),  # 15 minutes to 3 hours
                'severity_levels': {
                    1: {'solar_reduction': 0.2, 'cascade_probability': 0.05},
                    2: {'solar_reduction': 0.4, 'cascade_probability': 0.1},
                    3: {'solar_reduction': 0.6, 'cascade_probability': 0.15},
                    4: {'solar_reduction': 0.8, 'cascade_probability': 0.2},
                    5: {'solar_reduction': 1.0, 'cascade_probability': 0.25}
                },
                'recovery_patterns': ['gradual', 'stepped'],
                'affected_sources': ['solar'],
                'cascade_sources': ['grid', 'battery']
            },
            'equipment_failure': {
                'name': 'Critical Equipment Failure',
                'description': 'Failure of transformers, generators, or distribution equipment',
                'duration_range': (60, 480),  # 1 to 8 hours
                'severity_levels': {
                    1: {'multi_source_reduction': 0.15, 'cascade_probability': 0.2},
                    2: {'multi_source_reduction': 0.25, 'cascade_probability': 0.3},
                    3: {'multi_source_reduction': 0.4, 'cascade_probability': 0.4},
                    4: {'multi_source_reduction': 0.6, 'cascade_probability': 0.5},
                    5: {'multi_source_reduction': 0.8, 'cascade_probability': 0.6}
                },
                'recovery_patterns': ['stepped', 'gradual'],
                'affected_sources': ['grid', 'solar', 'battery'],
                'cascade_sources': ['diesel']
            },
            'fuel_shortage': {
                'name': 'Diesel Fuel Shortage',
                'description': 'Shortage of diesel fuel for backup generators',
                'duration_range': (120, 720),  # 2 to 12 hours
                'severity_levels': {
                    1: {'diesel_reduction': 0.3, 'cascade_probability': 0.1},
                    2: {'diesel_reduction': 0.5, 'cascade_probability': 0.15},
                    3: {'diesel_reduction': 0.7, 'cascade_probability': 0.2},
                    4: {'diesel_reduction': 0.9, 'cascade_probability': 0.25},
                    5: {'diesel_reduction': 1.0, 'cascade_probability': 0.3}
                },
                'recovery_patterns': ['immediate', 'stepped'],
                'affected_sources': ['diesel'],
                'cascade_sources': ['battery']
            },
            'cyber_attack': {
                'name': 'Cyber Security Attack',
                'description': 'Cyber attack on grid control systems',
                'duration_range': (45, 360),  # 45 minutes to 6 hours
                'severity_levels': {
                    1: {'system_disruption': 0.2, 'cascade_probability': 0.3},
                    2: {'system_disruption': 0.35, 'cascade_probability': 0.4},
                    3: {'system_disruption': 0.5, 'cascade_probability': 0.5},
                    4: {'system_disruption': 0.7, 'cascade_probability': 0.6},
                    5: {'system_disruption': 0.9, 'cascade_probability': 0.7}
                },
                'recovery_patterns': ['stepped', 'gradual'],
                'affected_sources': ['grid', 'solar', 'battery', 'diesel'],
                'cascade_sources': []
            },
            'natural_disaster': {
                'name': 'Natural Disaster Impact',
                'description': 'Earthquake, flood, or severe weather affecting infrastructure',
                'duration_range': (180, 1440),  # 3 to 24 hours
                'severity_levels': {
                    1: {'infrastructure_damage': 0.25, 'cascade_probability': 0.4},
                    2: {'infrastructure_damage': 0.4, 'cascade_probability': 0.5},
                    3: {'infrastructure_damage': 0.6, 'cascade_probability': 0.6},
                    4: {'infrastructure_damage': 0.8, 'cascade_probability': 0.7},
                    5: {'infrastructure_damage': 0.95, 'cascade_probability': 0.8}
                },
                'recovery_patterns': ['stepped', 'gradual'],
                'affected_sources': ['grid', 'solar', 'battery', 'diesel'],
                'cascade_sources': []
            }
        }
    
    def generate_failure_scenario_dataset(self, 
                                        output_dir: str = "backend/data/failure_scenarios",
                                        num_scenarios: int = 50,
                                        timeline_hours: int = 48) -> Dict[str, Any]:
        """Generate comprehensive failure scenario dataset"""
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        scenarios = []
        supply_events = []
        node_responses = []
        emergency_responses = []
        
        logger.info(f"Generating {num_scenarios} failure scenarios over {timeline_hours} hours")
        
        base_time = time.time()
        
        for scenario_idx in range(num_scenarios):
            # Select random scenario type and severity
            scenario_type = random.choice(list(self.scenario_templates.keys()))
            severity = random.randint(1, 5)
            
            # Generate failure event
            failure_event = self._generate_failure_event(
                scenario_idx, scenario_type, severity, base_time, timeline_hours
            )
            scenarios.append(failure_event)
            
            # Generate supply events for this scenario
            scenario_supply_events = self._generate_scenario_supply_events(failure_event)
            supply_events.extend(scenario_supply_events)
            
            # Generate node response data
            scenario_node_responses = self._generate_node_responses(failure_event)
            node_responses.extend(scenario_node_responses)
            
            # Generate emergency response actions
            scenario_emergency_responses = self._generate_emergency_responses(failure_event)
            emergency_responses.extend(scenario_emergency_responses)
        
        # Export all data
        self._export_scenario_data(
            output_dir, scenarios, supply_events, node_responses, emergency_responses
        )
        
        # Generate summary statistics
        stats = self._generate_scenario_stats(scenarios, supply_events, node_responses)
        
        with open(f"{output_dir}/scenario_stats.json", 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Generated failure scenario dataset in {output_dir}")
        return stats
    
    def _generate_failure_event(self, 
                               scenario_idx: int,
                               scenario_type: str,
                               severity: int,
                               base_time: float,
                               timeline_hours: int) -> FailureEvent:
        """Generate a single failure event"""
        
        template = self.scenario_templates[scenario_type]
        
        # Random start time within timeline
        start_offset = random.uniform(0, timeline_hours * 3600)
        start_time = base_time + start_offset
        
        # Random duration within template range
        duration = random.uniform(*template['duration_range'])
        
        # Select recovery pattern
        recovery_pattern = random.choice(template['recovery_patterns'])
        
        # Generate baseline supply levels
        baseline_supply = self._generate_baseline_supply()
        
        # Apply failure effects
        during_failure_supply = self._apply_failure_effects(
            baseline_supply, template, severity
        )
        
        # Generate recovery supply levels
        post_failure_supply = self._generate_recovery_supply(
            baseline_supply, during_failure_supply, recovery_pattern
        )
        
        return FailureEvent(
            event_id=f"failure_{scenario_idx:04d}_{scenario_type}",
            scenario_type=scenario_type,
            start_time=start_time,
            duration_minutes=duration,
            affected_sources=template['affected_sources'],
            severity_level=severity,
            recovery_pattern=recovery_pattern,
            impact_description=f"{template['name']} (Severity {severity}): {template['description']}",
            pre_failure_supply=baseline_supply,
            during_failure_supply=during_failure_supply,
            post_failure_supply=post_failure_supply,
            metadata={
                'template': template['name'],
                'cascade_probability': template['severity_levels'][severity]['cascade_probability'],
                'generation_time': time.time(),
                'weather_condition': self._simulate_weather_condition(),
                'time_of_day': datetime.fromtimestamp(start_time).hour,
                'day_of_week': datetime.fromtimestamp(start_time).strftime('%A')
            }
        )
    
    def _generate_baseline_supply(self) -> Dict[str, float]:
        """Generate baseline supply levels before failure"""
        # Use supply generator to get realistic baseline
        events = self.supply_generator.generate_supply_events(duration_hours=0.1, interval_minutes=5)
        if events:
            event = events[0]
            return {
                'grid': event.available_sources.grid,
                'solar': event.available_sources.solar,
                'battery': event.available_sources.battery,
                'diesel': event.available_sources.diesel,
                'total': event.total_supply
            }
        
        # Fallback to default values
        return {
            'grid': 1500.0,
            'solar': 400.0,
            'battery': 300.0,
            'diesel': 200.0,
            'total': 2400.0
        }
    
    def _apply_failure_effects(self, 
                              baseline: Dict[str, float],
                              template: Dict,
                              severity: int) -> Dict[str, float]:
        """Apply failure effects to supply levels"""
        
        affected_supply = baseline.copy()
        severity_config = template['severity_levels'][severity]
        
        # Apply direct effects based on scenario type
        if 'grid_reduction' in severity_config:
            affected_supply['grid'] *= (1 - severity_config['grid_reduction'])
        
        if 'solar_reduction' in severity_config:
            affected_supply['solar'] *= (1 - severity_config['solar_reduction'])
        
        if 'diesel_reduction' in severity_config:
            affected_supply['diesel'] *= (1 - severity_config['diesel_reduction'])
        
        if 'multi_source_reduction' in severity_config:
            reduction = severity_config['multi_source_reduction']
            for source in template['affected_sources']:
                if source in affected_supply:
                    affected_supply[source] *= (1 - reduction)
        
        if 'system_disruption' in severity_config:
            disruption = severity_config['system_disruption']
            for source in template['affected_sources']:
                if source in affected_supply:
                    affected_supply[source] *= (1 - disruption)
        
        if 'infrastructure_damage' in severity_config:
            damage = severity_config['infrastructure_damage']
            for source in template['affected_sources']:
                if source in affected_supply:
                    affected_supply[source] *= (1 - damage)
        
        # Apply cascade effects
        cascade_prob = severity_config['cascade_probability']
        if random.random() < cascade_prob:
            for cascade_source in template['cascade_sources']:
                if cascade_source in affected_supply:
                    cascade_reduction = random.uniform(0.1, 0.4)  # 10-40% cascade reduction
                    affected_supply[cascade_source] *= (1 - cascade_reduction)
        
        # Recalculate total
        affected_supply['total'] = sum([
            affected_supply['grid'],
            affected_supply['solar'],
            affected_supply['battery'],
            affected_supply['diesel']
        ])
        
        return affected_supply
    
    def _generate_recovery_supply(self, 
                                 baseline: Dict[str, float],
                                 during_failure: Dict[str, float],
                                 recovery_pattern: str) -> Dict[str, float]:
        """Generate supply levels during recovery phase"""
        
        recovery_supply = during_failure.copy()
        
        if recovery_pattern == 'immediate':
            # Immediate full recovery
            recovery_supply = baseline.copy()
        
        elif recovery_pattern == 'gradual':
            # Gradual recovery to 80-95% of baseline
            recovery_factor = random.uniform(0.8, 0.95)
            for source in ['grid', 'solar', 'battery', 'diesel']:
                recovery_supply[source] = baseline[source] * recovery_factor
        
        elif recovery_pattern == 'stepped':
            # Stepped recovery to 70-90% of baseline
            recovery_factor = random.uniform(0.7, 0.9)
            for source in ['grid', 'solar', 'battery', 'diesel']:
                recovery_supply[source] = baseline[source] * recovery_factor
        
        # Recalculate total
        recovery_supply['total'] = sum([
            recovery_supply['grid'],
            recovery_supply['solar'],
            recovery_supply['battery'],
            recovery_supply['diesel']
        ])
        
        return recovery_supply
    
    def _generate_scenario_supply_events(self, failure_event: FailureEvent) -> List[SupplyEvent]:
        """Generate supply events for a failure scenario"""
        events = []
        
        # Pre-failure events (30 minutes before)
        pre_failure_duration = 30  # minutes
        pre_failure_start = failure_event.start_time - (pre_failure_duration * 60)
        
        for i in range(6):  # 6 events, 5 minutes apart
            timestamp = pre_failure_start + (i * 5 * 60)
            event = SupplyEvent(
                event_id=f"{failure_event.event_id}_pre_{i:02d}",
                total_supply=failure_event.pre_failure_supply['total'],
                available_sources=AvailableSources(
                    grid=failure_event.pre_failure_supply['grid'],
                    solar=failure_event.pre_failure_supply['solar'],
                    battery=failure_event.pre_failure_supply['battery'],
                    diesel=failure_event.pre_failure_supply['diesel']
                ),
                timestamp=timestamp
            )
            events.append(event)
        
        # During-failure events
        failure_duration_seconds = failure_event.duration_minutes * 60
        num_failure_events = max(1, int(failure_duration_seconds / (5 * 60)))  # Every 5 minutes
        
        for i in range(num_failure_events):
            timestamp = failure_event.start_time + (i * 5 * 60)
            event = SupplyEvent(
                event_id=f"{failure_event.event_id}_during_{i:02d}",
                total_supply=failure_event.during_failure_supply['total'],
                available_sources=AvailableSources(
                    grid=failure_event.during_failure_supply['grid'],
                    solar=failure_event.during_failure_supply['solar'],
                    battery=failure_event.during_failure_supply['battery'],
                    diesel=failure_event.during_failure_supply['diesel']
                ),
                timestamp=timestamp
            )
            events.append(event)
        
        # Post-failure recovery events (60 minutes after)
        recovery_start = failure_event.start_time + failure_duration_seconds
        
        for i in range(12):  # 12 events, 5 minutes apart
            timestamp = recovery_start + (i * 5 * 60)
            event = SupplyEvent(
                event_id=f"{failure_event.event_id}_recovery_{i:02d}",
                total_supply=failure_event.post_failure_supply['total'],
                available_sources=AvailableSources(
                    grid=failure_event.post_failure_supply['grid'],
                    solar=failure_event.post_failure_supply['solar'],
                    battery=failure_event.post_failure_supply['battery'],
                    diesel=failure_event.post_failure_supply['diesel']
                ),
                timestamp=timestamp
            )
            events.append(event)
        
        return events
    
    def _generate_node_responses(self, failure_event: FailureEvent) -> List[EnergyNode]:
        """Generate node response data during failure scenario"""
        nodes = []
        
        # Generate baseline nodes
        baseline_nodes = self.node_generator.generate_node_stream(
            duration_hours=0.5, nodes_per_type=3, interval_seconds=300
        )
        
        # Modify nodes based on failure scenario
        for node in baseline_nodes:
            # Adjust node behavior during failure
            if failure_event.severity_level >= 3:
                # High severity - some nodes may go inactive
                if node.priority_tier == 3 and random.random() < 0.3:  # 30% chance for residential
                    node.status = 'inactive'
                    node.current_load = 0
                elif node.priority_tier == 2 and random.random() < 0.1:  # 10% chance for factories
                    node.status = 'degraded'
                    node.current_load *= 0.5
            
            # Hospitals (tier 1) try to maintain operation
            if node.priority_tier == 1:
                if failure_event.severity_level >= 4:
                    # Switch to backup power
                    node.source_type = 'Diesel' if 'diesel' not in failure_event.affected_sources else 'Battery'
                    if node.source_type in failure_event.affected_sources:
                        node.status = 'degraded'
                        node.current_load *= 0.7
            
            # Update timestamp to match failure event
            node.timestamp = failure_event.start_time + random.uniform(0, failure_event.duration_minutes * 60)
            
            nodes.append(node)
        
        return nodes
    
    def _generate_emergency_responses(self, failure_event: FailureEvent) -> List[EmergencyResponse]:
        """Generate emergency response actions for failure scenario"""
        responses = []
        
        # Response timing based on severity
        response_delay = max(60, 300 - (failure_event.severity_level * 60))  # 1-5 minutes delay
        
        # Load shedding response
        if failure_event.severity_level >= 3:
            responses.append(EmergencyResponse(
                response_id=f"{failure_event.event_id}_load_shedding",
                trigger_time=failure_event.start_time + response_delay,
                action_type='load_shedding',
                affected_nodes=['residential_001', 'residential_002', 'factory_002'],
                parameters={
                    'reduction_percentage': min(50, failure_event.severity_level * 10),
                    'duration_minutes': failure_event.duration_minutes * 0.8
                },
                expected_outcome='Reduce total demand by 20-30%'
            ))
        
        # Source switching response
        if 'grid' in failure_event.affected_sources:
            responses.append(EmergencyResponse(
                response_id=f"{failure_event.event_id}_source_switch",
                trigger_time=failure_event.start_time + (response_delay * 0.5),
                action_type='source_switching',
                affected_nodes=['hospital_001', 'hospital_002'],
                parameters={
                    'from_source': 'grid',
                    'to_source': 'diesel',
                    'priority_tiers': [1]
                },
                expected_outcome='Maintain critical infrastructure power'
            ))
        
        # Priority reallocation response
        if failure_event.severity_level >= 4:
            responses.append(EmergencyResponse(
                response_id=f"{failure_event.event_id}_priority_realloc",
                trigger_time=failure_event.start_time + (response_delay * 1.5),
                action_type='priority_reallocation',
                affected_nodes=['all'],
                parameters={
                    'new_priority_weights': {'tier_1': 0.7, 'tier_2': 0.2, 'tier_3': 0.1},
                    'emergency_mode': True
                },
                expected_outcome='Maximize power to critical infrastructure'
            ))
        
        return responses
    
    def _simulate_weather_condition(self) -> str:
        """Simulate weather conditions that might affect failures"""
        conditions = ['clear', 'cloudy', 'stormy', 'extreme_heat', 'extreme_cold', 'high_wind']
        weights = [0.3, 0.25, 0.15, 0.1, 0.1, 0.1]
        return random.choices(conditions, weights=weights)[0]
    
    def _export_scenario_data(self, 
                             output_dir: str,
                             scenarios: List[FailureEvent],
                             supply_events: List[SupplyEvent],
                             node_responses: List[EnergyNode],
                             emergency_responses: List[EmergencyResponse]):
        """Export all scenario data to files"""
        
        # Export failure events
        with open(f"{output_dir}/failure_events.jsonl", 'w') as f:
            for scenario in scenarios:
                json.dump(asdict(scenario), f)
                f.write('\n')
        
        # Export supply events
        with open(f"{output_dir}/supply_events.jsonl", 'w') as f:
            for event in supply_events:
                json.dump(event.dict(), f)
                f.write('\n')
        
        # Export node responses
        with open(f"{output_dir}/node_responses.jsonl", 'w') as f:
            for node in node_responses:
                json.dump(node.dict(), f)
                f.write('\n')
        
        # Export emergency responses
        with open(f"{output_dir}/emergency_responses.jsonl", 'w') as f:
            for response in emergency_responses:
                json.dump(asdict(response), f)
                f.write('\n')
        
        # Export scenario summary
        scenario_summary = []
        for scenario in scenarios:
            summary = {
                'event_id': scenario.event_id,
                'scenario_type': scenario.scenario_type,
                'severity_level': scenario.severity_level,
                'duration_minutes': scenario.duration_minutes,
                'affected_sources': scenario.affected_sources,
                'impact_description': scenario.impact_description,
                'supply_reduction_percent': (
                    (scenario.pre_failure_supply['total'] - scenario.during_failure_supply['total']) /
                    scenario.pre_failure_supply['total'] * 100
                )
            }
            scenario_summary.append(summary)
        
        with open(f"{output_dir}/scenario_summary.json", 'w') as f:
            json.dump(scenario_summary, f, indent=2)
    
    def _generate_scenario_stats(self, 
                                scenarios: List[FailureEvent],
                                supply_events: List[SupplyEvent],
                                node_responses: List[EnergyNode]) -> Dict[str, Any]:
        """Generate statistics for the scenario dataset"""
        
        scenario_types = {}
        severity_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_supply_reduction = 0
        
        for scenario in scenarios:
            # Count scenario types
            scenario_types[scenario.scenario_type] = scenario_types.get(scenario.scenario_type, 0) + 1
            
            # Count severity levels
            severity_distribution[scenario.severity_level] += 1
            
            # Calculate supply reduction
            reduction = (
                (scenario.pre_failure_supply['total'] - scenario.during_failure_supply['total']) /
                scenario.pre_failure_supply['total']
            )
            total_supply_reduction += reduction
        
        avg_supply_reduction = total_supply_reduction / len(scenarios) if scenarios else 0
        
        return {
            'generation_timestamp': time.time(),
            'total_scenarios': len(scenarios),
            'total_supply_events': len(supply_events),
            'total_node_responses': len(node_responses),
            'scenario_types': scenario_types,
            'severity_distribution': severity_distribution,
            'average_supply_reduction_percent': avg_supply_reduction * 100,
            'scenario_templates': list(self.scenario_templates.keys())
        }

def generate_failure_scenarios(output_dir: str = "backend/data/failure_scenarios",
                             num_scenarios: int = 50,
                             timeline_hours: int = 48) -> Dict[str, Any]:
    """Convenience function to generate failure scenarios"""
    generator = GridFailureScenarioGenerator()
    return generator.generate_failure_scenario_dataset(output_dir, num_scenarios, timeline_hours)

if __name__ == "__main__":
    # Generate failure scenarios
    stats = generate_failure_scenarios(
        num_scenarios=30,
        timeline_hours=24
    )
    
    print("Failure Scenario Generation Complete!")
    print(f"Generated {stats['total_scenarios']} scenarios")
    print(f"Scenario types: {list(stats['scenario_types'].keys())}")
    print(f"Average supply reduction: {stats['average_supply_reduction_percent']:.1f}%")