"""
Development Data Stream Configuration for Bharat-Grid AI
Configures continuous data streams with rotation, variation, and failure scenarios
"""

import json
import time
import random
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import logging

from data_generators import EnergyNodeGenerator, SupplyEventGenerator, DataExporter
from schemas import EnergyNode, SupplyEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StreamConfig:
    """Configuration for a data stream"""
    name: str
    output_format: str  # 'csv', 'jsonl'
    output_path: str
    update_interval_seconds: int
    rotation_interval_minutes: int
    variation_factor: float  # 0.0 to 1.0
    enable_failures: bool
    failure_probability: float  # 0.0 to 1.0
    max_file_size_mb: int
    keep_history_files: int

@dataclass
class FailureScenario:
    """Configuration for grid failure scenarios"""
    name: str
    description: str
    trigger_probability: float
    duration_minutes: tuple  # (min, max)
    supply_reduction_percent: tuple  # (min, max)
    affected_sources: List[str]  # ['grid', 'solar', 'battery', 'diesel']
    recovery_pattern: str  # 'immediate', 'gradual', 'stepped'

class DataStreamManager:
    """Manages continuous data streams for development environment"""
    
    def __init__(self, config_path: str = "backend/data/stream_config.json"):
        self.config_path = config_path
        self.streams: Dict[str, StreamConfig] = {}
        self.failure_scenarios: Dict[str, FailureScenario] = {}
        self.active_streams: Dict[str, threading.Thread] = {}
        self.stream_states: Dict[str, Dict] = {}
        self.running = False
        
        # Initialize generators
        self.node_generator = EnergyNodeGenerator(seed=int(time.time()))
        self.supply_generator = SupplyEventGenerator(seed=int(time.time()))
        
        # Load configuration
        self.load_config()
        
        # Initialize failure scenarios
        self._init_failure_scenarios()
    
    def _init_failure_scenarios(self):
        """Initialize predefined failure scenarios"""
        self.failure_scenarios = {
            'grid_outage': FailureScenario(
                name='grid_outage',
                description='Complete grid power failure',
                trigger_probability=0.02,  # 2% chance per check
                duration_minutes=(15, 120),  # 15 minutes to 2 hours
                supply_reduction_percent=(80, 100),  # 80-100% grid reduction
                affected_sources=['grid'],
                recovery_pattern='gradual'
            ),
            'solar_cloud_cover': FailureScenario(
                name='solar_cloud_cover',
                description='Heavy cloud cover reducing solar output',
                trigger_probability=0.05,  # 5% chance
                duration_minutes=(30, 180),  # 30 minutes to 3 hours
                supply_reduction_percent=(40, 80),  # 40-80% solar reduction
                affected_sources=['solar'],
                recovery_pattern='gradual'
            ),
            'battery_degradation': FailureScenario(
                name='battery_degradation',
                description='Battery system performance degradation',
                trigger_probability=0.01,  # 1% chance
                duration_minutes=(60, 480),  # 1-8 hours
                supply_reduction_percent=(30, 60),  # 30-60% battery reduction
                affected_sources=['battery'],
                recovery_pattern='stepped'
            ),
            'diesel_shortage': FailureScenario(
                name='diesel_shortage',
                description='Diesel generator fuel shortage',
                trigger_probability=0.008,  # 0.8% chance
                duration_minutes=(120, 600),  # 2-10 hours
                supply_reduction_percent=(70, 100),  # 70-100% diesel reduction
                affected_sources=['diesel'],
                recovery_pattern='immediate'
            ),
            'cascade_failure': FailureScenario(
                name='cascade_failure',
                description='Cascading failure affecting multiple sources',
                trigger_probability=0.005,  # 0.5% chance
                duration_minutes=(45, 240),  # 45 minutes to 4 hours
                supply_reduction_percent=(50, 90),  # 50-90% reduction
                affected_sources=['grid', 'solar', 'battery'],
                recovery_pattern='stepped'
            )
        }
    
    def load_config(self):
        """Load stream configuration from file"""
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    
                # Load stream configs
                for stream_name, stream_data in config_data.get('streams', {}).items():
                    self.streams[stream_name] = StreamConfig(**stream_data)
                
                logger.info(f"Loaded configuration for {len(self.streams)} streams")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default stream configuration"""
        self.streams = {
            'nodes_csv': StreamConfig(
                name='nodes_csv',
                output_format='csv',
                output_path='backend/data/streams/nodes_stream.csv',
                update_interval_seconds=30,  # Update every 30 seconds
                rotation_interval_minutes=60,  # Rotate hourly
                variation_factor=0.3,  # 30% variation
                enable_failures=True,
                failure_probability=0.02,  # 2% chance per update
                max_file_size_mb=10,
                keep_history_files=24  # Keep 24 hours of history
            ),
            'nodes_jsonl': StreamConfig(
                name='nodes_jsonl',
                output_format='jsonl',
                output_path='backend/data/streams/nodes_stream.jsonl',
                update_interval_seconds=15,  # More frequent updates
                rotation_interval_minutes=30,
                variation_factor=0.2,
                enable_failures=True,
                failure_probability=0.02,
                max_file_size_mb=5,
                keep_history_files=48
            ),
            'supply_events': StreamConfig(
                name='supply_events',
                output_format='jsonl',
                output_path='backend/data/streams/supply_events.jsonl',
                update_interval_seconds=60,  # Every minute
                rotation_interval_minutes=120,  # Rotate every 2 hours
                variation_factor=0.4,  # Higher variation for supply
                enable_failures=True,
                failure_probability=0.03,  # 3% chance
                max_file_size_mb=5,
                keep_history_files=12
            )
        }
        
        self.save_config()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            config_data = {
                'streams': {name: asdict(config) for name, config in self.streams.items()},
                'failure_scenarios': {name: asdict(scenario) for name, scenario in self.failure_scenarios.items()}
            }
            
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def start_streams(self):
        """Start all configured data streams"""
        if self.running:
            logger.warning("Streams are already running")
            return
        
        self.running = True
        logger.info("Starting data streams...")
        
        for stream_name, config in self.streams.items():
            if stream_name not in self.active_streams:
                # Initialize stream state
                self.stream_states[stream_name] = {
                    'last_update': 0,
                    'last_rotation': time.time(),
                    'current_file_size': 0,
                    'active_failures': [],
                    'data_variation_seed': random.randint(1, 10000)
                }
                
                # Start stream thread
                thread = threading.Thread(
                    target=self._run_stream,
                    args=(stream_name, config),
                    daemon=True
                )
                thread.start()
                self.active_streams[stream_name] = thread
                
                logger.info(f"Started stream: {stream_name}")
    
    def stop_streams(self):
        """Stop all running data streams"""
        logger.info("Stopping data streams...")
        self.running = False
        
        # Wait for threads to finish
        for stream_name, thread in self.active_streams.items():
            if thread.is_alive():
                thread.join(timeout=5)
                logger.info(f"Stopped stream: {stream_name}")
        
        self.active_streams.clear()
        logger.info("All streams stopped")
    
    def _run_stream(self, stream_name: str, config: StreamConfig):
        """Run a single data stream"""
        logger.info(f"Stream {stream_name} started")
        
        while self.running:
            try:
                current_time = time.time()
                state = self.stream_states[stream_name]
                
                # Check if it's time to update
                if current_time - state['last_update'] >= config.update_interval_seconds:
                    self._update_stream_data(stream_name, config, state)
                    state['last_update'] = current_time
                
                # Check if it's time to rotate files
                if current_time - state['last_rotation'] >= config.rotation_interval_minutes * 60:
                    self._rotate_stream_file(stream_name, config, state)
                    state['last_rotation'] = current_time
                
                # Check file size for rotation
                if state['current_file_size'] > config.max_file_size_mb * 1024 * 1024:
                    self._rotate_stream_file(stream_name, config, state)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in stream {stream_name}: {e}")
                time.sleep(5)  # Wait before retrying
        
        logger.info(f"Stream {stream_name} stopped")
    
    def _update_stream_data(self, stream_name: str, config: StreamConfig, state: Dict):
        """Update stream with new data"""
        try:
            # Check for failure scenarios
            if config.enable_failures:
                self._check_failure_scenarios(stream_name, config, state)
            
            # Generate new data based on stream type
            if 'nodes' in stream_name:
                data = self._generate_node_data(config, state)
            elif 'supply' in stream_name:
                data = self._generate_supply_data(config, state)
            else:
                logger.warning(f"Unknown stream type: {stream_name}")
                return
            
            # Write data to file
            self._write_stream_data(config, data, state)
            
        except Exception as e:
            logger.error(f"Failed to update stream {stream_name}: {e}")
    
    def _generate_node_data(self, config: StreamConfig, state: Dict) -> List[EnergyNode]:
        """Generate node data with variation"""
        # Apply variation to generator seed
        variation_seed = state['data_variation_seed'] + int(time.time() / 60)  # Change every minute
        self.node_generator = EnergyNodeGenerator(seed=variation_seed)
        
        # Generate nodes with current timestamp
        nodes = self.node_generator.generate_node_stream(
            duration_hours=0.1,  # 6 minutes of data
            nodes_per_type=3,  # Smaller set for streaming
            interval_seconds=config.update_interval_seconds
        )
        
        # Apply variation factor
        for node in nodes:
            if random.random() < config.variation_factor:
                # Add random variation to load
                variation = random.uniform(-0.2, 0.2)  # ±20% variation
                node.current_load = max(0, node.current_load * (1 + variation))
                
                # Occasionally change status
                if random.random() < 0.1:  # 10% chance
                    statuses = ['active', 'degraded', 'inactive']
                    node.status = random.choice(statuses)
        
        return nodes
    
    def _generate_supply_data(self, config: StreamConfig, state: Dict) -> List[SupplyEvent]:
        """Generate supply data with variation and failures"""
        # Apply variation to generator seed
        variation_seed = state['data_variation_seed'] + int(time.time() / 300)  # Change every 5 minutes
        self.supply_generator = SupplyEventGenerator(seed=variation_seed)
        
        # Generate supply events
        events = self.supply_generator.generate_supply_events(
            duration_hours=0.1,  # 6 minutes of data
            interval_minutes=config.update_interval_seconds / 60
        )
        
        # Apply active failures
        for event in events:
            for failure_name in state['active_failures']:
                if failure_name in self.failure_scenarios:
                    self._apply_failure_to_event(event, self.failure_scenarios[failure_name])
        
        # Apply variation factor
        for event in events:
            if random.random() < config.variation_factor:
                # Add random variation to total supply
                variation = random.uniform(-0.15, 0.15)  # ±15% variation
                event.total_supply = max(0, event.total_supply * (1 + variation))
                
                # Redistribute sources proportionally
                total_sources = sum([
                    event.available_sources.grid,
                    event.available_sources.solar,
                    event.available_sources.battery,
                    event.available_sources.diesel
                ])
                
                if total_sources > 0:
                    ratio = event.total_supply / total_sources
                    event.available_sources.grid *= ratio
                    event.available_sources.solar *= ratio
                    event.available_sources.battery *= ratio
                    event.available_sources.diesel *= ratio
        
        return events
    
    def _check_failure_scenarios(self, stream_name: str, config: StreamConfig, state: Dict):
        """Check and trigger failure scenarios"""
        current_time = time.time()
        
        # Check for new failures
        if random.random() < config.failure_probability:
            # Select a random failure scenario
            scenario_name = random.choice(list(self.failure_scenarios.keys()))
            scenario = self.failure_scenarios[scenario_name]
            
            if random.random() < scenario.trigger_probability:
                # Trigger failure
                duration = random.uniform(*scenario.duration_minutes) * 60  # Convert to seconds
                failure_info = {
                    'scenario': scenario_name,
                    'start_time': current_time,
                    'end_time': current_time + duration,
                    'reduction_percent': random.uniform(*scenario.supply_reduction_percent)
                }
                
                state['active_failures'].append(failure_info)
                logger.warning(f"Triggered failure scenario '{scenario_name}' for {duration/60:.1f} minutes")
        
        # Remove expired failures
        state['active_failures'] = [
            failure for failure in state['active_failures']
            if current_time < failure['end_time']
        ]
    
    def _apply_failure_to_event(self, event: SupplyEvent, scenario: FailureScenario):
        """Apply failure scenario effects to supply event"""
        # This is a simplified implementation - in reality, you'd have more complex failure modeling
        reduction_factor = 0.5  # Simplified 50% reduction
        
        for source in scenario.affected_sources:
            if hasattr(event.available_sources, source):
                current_value = getattr(event.available_sources, source)
                setattr(event.available_sources, source, current_value * reduction_factor)
        
        # Recalculate total supply
        event.total_supply = (
            event.available_sources.grid +
            event.available_sources.solar +
            event.available_sources.battery +
            event.available_sources.diesel
        )
    
    def _write_stream_data(self, config: StreamConfig, data: List, state: Dict):
        """Write data to stream file"""
        output_path = Path(config.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if config.output_format == 'csv':
            # Append to CSV file
            if isinstance(data[0], EnergyNode):
                DataExporter.export_nodes_to_csv(data, str(output_path))
            else:
                logger.warning(f"CSV export not supported for {type(data[0])}")
        
        elif config.output_format == 'jsonl':
            # Append to JSONL file
            with open(output_path, 'a') as f:
                for item in data:
                    if hasattr(item, 'dict'):
                        json.dump(item.dict(), f)
                    else:
                        json.dump(item, f)
                    f.write('\n')
        
        # Update file size tracking
        if output_path.exists():
            state['current_file_size'] = output_path.stat().st_size
    
    def _rotate_stream_file(self, stream_name: str, config: StreamConfig, state: Dict):
        """Rotate stream file to maintain history"""
        output_path = Path(config.output_path)
        
        if not output_path.exists():
            return
        
        # Create timestamp for rotated file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated_path = output_path.with_name(f"{output_path.stem}_{timestamp}{output_path.suffix}")
        
        try:
            # Move current file to rotated name
            output_path.rename(rotated_path)
            
            # Clean up old files
            self._cleanup_old_files(output_path.parent, output_path.stem, config.keep_history_files)
            
            # Reset file size tracking
            state['current_file_size'] = 0
            
            logger.info(f"Rotated stream file: {stream_name} -> {rotated_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to rotate file for {stream_name}: {e}")
    
    def _cleanup_old_files(self, directory: Path, file_stem: str, keep_count: int):
        """Clean up old rotated files"""
        try:
            # Find all rotated files
            pattern = f"{file_stem}_*"
            rotated_files = list(directory.glob(pattern))
            
            # Sort by modification time (newest first)
            rotated_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove excess files
            for old_file in rotated_files[keep_count:]:
                old_file.unlink()
                logger.debug(f"Removed old file: {old_file.name}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
    
    def get_stream_status(self) -> Dict[str, Any]:
        """Get status of all streams"""
        status = {
            'running': self.running,
            'active_streams': len(self.active_streams),
            'streams': {}
        }
        
        for stream_name, config in self.streams.items():
            stream_status = {
                'active': stream_name in self.active_streams,
                'config': asdict(config),
                'state': self.stream_states.get(stream_name, {})
            }
            
            # Add file info
            output_path = Path(config.output_path)
            if output_path.exists():
                stat = output_path.stat()
                stream_status['file_info'] = {
                    'size_mb': stat.st_size / (1024 * 1024),
                    'last_modified': stat.st_mtime
                }
            
            status['streams'][stream_name] = stream_status
        
        return status
    
    def trigger_failure_scenario(self, scenario_name: str, duration_minutes: Optional[int] = None) -> bool:
        """Manually trigger a failure scenario"""
        if scenario_name not in self.failure_scenarios:
            logger.error(f"Unknown failure scenario: {scenario_name}")
            return False
        
        scenario = self.failure_scenarios[scenario_name]
        duration = duration_minutes or random.uniform(*scenario.duration_minutes)
        
        # Add failure to all supply streams
        for stream_name, state in self.stream_states.items():
            if 'supply' in stream_name:
                failure_info = {
                    'scenario': scenario_name,
                    'start_time': time.time(),
                    'end_time': time.time() + (duration * 60),
                    'reduction_percent': random.uniform(*scenario.supply_reduction_percent)
                }
                state['active_failures'].append(failure_info)
        
        logger.warning(f"Manually triggered failure scenario '{scenario_name}' for {duration} minutes")
        return True

# Convenience functions for easy usage
def start_development_streams():
    """Start development data streams with default configuration"""
    manager = DataStreamManager()
    manager.start_streams()
    return manager

def stop_development_streams(manager: DataStreamManager):
    """Stop development data streams"""
    manager.stop_streams()

if __name__ == "__main__":
    # Example usage
    manager = DataStreamManager()
    
    try:
        manager.start_streams()
        
        # Let it run for a while
        print("Streams running... Press Ctrl+C to stop")
        while True:
            time.sleep(10)
            status = manager.get_stream_status()
            print(f"Active streams: {status['active_streams']}")
            
    except KeyboardInterrupt:
        print("\nStopping streams...")
        manager.stop_streams()