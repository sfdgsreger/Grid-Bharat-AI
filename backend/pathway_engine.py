# Pathway stream processing engine for Bharat-Grid AI
# Implements real-time data ingestion, validation, and normalization

import time
import logging
import json
import csv
import threading
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime

try:
    from .schemas import EnergyNode, SupplyEvent, AllocationResult, Location, AvailableSources
    from .utils.priority_algo import PriorityAllocator
    from .utils.latency_tracker import global_tracker, PerformanceContext
    from .monitoring import (
        pathway_logger, 
        allocation_auditor, 
        performance_monitor,
        update_component_health,
        performance_tracking
    )
except ImportError:
    # Handle direct execution
    from schemas import EnergyNode, SupplyEvent, AllocationResult, Location, AvailableSources
    from utils.priority_algo import PriorityAllocator
    from utils.latency_tracker import global_tracker, PerformanceContext
    from monitoring import (
        pathway_logger, 
        allocation_auditor, 
        performance_monitor,
        update_component_health,
        performance_tracking
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamConnector:
    """Base class for stream connectors"""
    
    def __init__(self, file_path: str, mode: str = "streaming"):
        self.file_path = Path(file_path)
        self.mode = mode
        self.is_running = False
        self.data_queue = Queue()
        self.thread = None
    
    def start(self):
        """Start the stream connector"""
        self.is_running = True
        self.thread = threading.Thread(target=self._stream_data)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Started stream connector for {self.file_path}")
    
    def stop(self):
        """Stop the stream connector"""
        self.is_running = False
        if self.thread:
            self.thread.join()
        logger.info(f"Stopped stream connector for {self.file_path}")
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """Get next data item from stream"""
        try:
            return self.data_queue.get_nowait()
        except Empty:
            return None
    
    def _stream_data(self):
        """Override in subclasses"""
        pass


class CSVStreamConnector(StreamConnector):
    """CSV stream connector with real-time monitoring"""
    
    def __init__(self, file_path: str, schema: Dict[str, type], mode: str = "streaming"):
        super().__init__(file_path, mode)
        self.schema = schema
        self.last_position = 0
        self.header_read = False
    
    def _stream_data(self):
        """Stream CSV data with file monitoring"""
        while self.is_running:
            try:
                if self.file_path.exists():
                    with open(self.file_path, 'r', newline='') as file:
                        # Skip to last position
                        file.seek(self.last_position)
                        
                        reader = csv.DictReader(file)
                        
                        # Skip header if already read
                        if not self.header_read and self.last_position == 0:
                            self.header_read = True
                        
                        for row in reader:
                            if not self.is_running:
                                break
                            
                            # Convert types according to schema
                            typed_row = self._convert_types(row)
                            self.data_queue.put(typed_row)
                        
                        # Update position
                        self.last_position = file.tell()
                
                # Check for new data every 100ms
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error reading CSV stream: {e}")
                time.sleep(1)
    
    def _convert_types(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Convert string values to appropriate types"""
        typed_row = {}
        for key, value in row.items():
            if key in self.schema:
                try:
                    if self.schema[key] == float:
                        typed_row[key] = float(value)
                    elif self.schema[key] == int:
                        typed_row[key] = int(value)
                    else:
                        typed_row[key] = value
                except (ValueError, TypeError):
                    typed_row[key] = value
            else:
                typed_row[key] = value
        return typed_row


class JSONLStreamConnector(StreamConnector):
    """JSONL stream connector with real-time monitoring"""
    
    def __init__(self, file_path: str, schema: Dict[str, type], mode: str = "streaming"):
        super().__init__(file_path, mode)
        self.schema = schema
        self.last_position = 0
    
    def _stream_data(self):
        """Stream JSONL data with file monitoring"""
        while self.is_running:
            try:
                if self.file_path.exists():
                    with open(self.file_path, 'r') as file:
                        # Skip to last position
                        file.seek(self.last_position)
                        
                        for line in file:
                            if not self.is_running:
                                break
                            
                            line = line.strip()
                            if line:
                                try:
                                    data = json.loads(line)
                                    self.data_queue.put(data)
                                except json.JSONDecodeError as e:
                                    logger.error(f"Invalid JSON line: {line}, error: {e}")
                        
                        # Update position
                        self.last_position = file.tell()
                
                # Check for new data every 100ms
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error reading JSONL stream: {e}")
                time.sleep(1)


class EnergyDataIngestionPipeline:
    """
    Stream-based data ingestion pipeline for real-time energy data processing.
    
    Handles:
    - CSV and JSON stream ingestion
    - Data validation and normalization
    - Error handling for malformed data
    - Real-time processing with <10ms latency target
    """
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.allocator = PriorityAllocator()
        self.processed_count = 0
        self.error_count = 0
        
        # Stream connectors
        self.csv_connector = None
        self.json_connector = None
        
        # Processing callbacks
        self.node_callbacks: List[Callable[[EnergyNode], None]] = []
        self.supply_callbacks: List[Callable[[SupplyEvent], None]] = []
        self.allocation_callbacks: List[Callable[[List[AllocationResult]], None]] = []
        
        # Real-time allocation state
        self.current_nodes: Dict[str, EnergyNode] = {}
        self.latest_supply: Optional[SupplyEvent] = None
        self.allocation_enabled = True
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized EnergyDataIngestionPipeline with data_dir: {data_dir}")
    
    def add_node_callback(self, callback: Callable[[EnergyNode], None]):
        """Add callback for processed energy nodes"""
        self.node_callbacks.append(callback)
    
    def add_supply_callback(self, callback: Callable[[SupplyEvent], None]):
        """Add callback for processed supply events"""
        self.supply_callbacks.append(callback)
    
    def add_allocation_callback(self, callback: Callable[[List[AllocationResult]], None]):
        """Add callback for allocation results"""
        self.allocation_callbacks.append(callback)
    
    def enable_real_time_allocation(self, enabled: bool = True):
        """Enable or disable real-time allocation triggers"""
        self.allocation_enabled = enabled
        logger.info(f"Real-time allocation {'enabled' if enabled else 'disabled'}")
    
    def trigger_allocation(self) -> Optional[List[AllocationResult]]:
        """
        Trigger power allocation using current nodes and latest supply event.
        
        Returns:
            List of allocation results or None if insufficient data
        """
        if not self.allocation_enabled:
            return None
            
        if not self.current_nodes or not self.latest_supply:
            pathway_logger.debug("Insufficient data for allocation - nodes: {}, supply: {}".format(
                len(self.current_nodes), bool(self.latest_supply)))
            return None
        
        # Track allocation performance
        with performance_tracking('allocation', {'node_count': len(self.current_nodes)}):
            # Convert nodes dict to list for allocation
            nodes_list = list(self.current_nodes.values())
            
            # Calculate total demand for audit logging
            total_demand = sum(node.current_load for node in nodes_list)
            
            # Perform allocation
            allocations = self.allocator.allocate_power(nodes_list, self.latest_supply)
            
            # Log allocation decisions for audit trail
            for allocation, node in zip(allocations, nodes_list):
                try:
                    allocation_auditor.log_allocation_decision(
                        allocation=allocation,
                        node=node,
                        supply_event=self.latest_supply,
                        processing_time_ms=allocation.latency_ms,
                        total_demand=total_demand,
                        decision_factors={
                            'total_nodes': len(nodes_list),
                            'supply_utilization': (sum(a.allocated_power for a in allocations) / self.latest_supply.total_supply) * 100,
                            'demand_coverage': (sum(a.allocated_power for a in allocations) / total_demand) * 100 if total_demand > 0 else 100
                        }
                    )
                except Exception as e:
                    pathway_logger.error(f"Failed to log allocation decision for {node.node_id}: {e}")
            
            # Call registered allocation callbacks
            for callback in self.allocation_callbacks:
                try:
                    callback(allocations)
                except Exception as e:
                    pathway_logger.error(f"Allocation callback error: {e}")
            
            pathway_logger.info(f"Triggered allocation for {len(nodes_list)} nodes, "
                               f"total allocated: {sum(a.allocated_power for a in allocations):.2f} kW")
            
            # Update component health
            update_component_health('pathway_engine', 'healthy')
            
            return allocations
    
    def get_current_allocation_state(self) -> Dict[str, Any]:
        """
        Get current state of the allocation system.
        
        Returns:
            Dictionary with current system state
        """
        return {
            'node_count': len(self.current_nodes),
            'nodes': {node_id: {
                'current_load': node.current_load,
                'priority_tier': node.priority_tier,
                'status': node.status
            } for node_id, node in self.current_nodes.items()},
            'latest_supply': {
                'total_supply': self.latest_supply.total_supply,
                'available_sources': self.latest_supply.available_sources.dict(),
                'timestamp': self.latest_supply.timestamp
            } if self.latest_supply else None,
            'allocation_enabled': self.allocation_enabled
        }
    
    def inject_supply_event(self, supply_event: SupplyEvent) -> Optional[List[AllocationResult]]:
        """
        Inject a supply event directly (for testing/simulation).
        
        Args:
            supply_event: Supply event to inject
            
        Returns:
            Allocation results if triggered
        """
        pathway_logger.info(f"Injecting supply event: {supply_event.event_id}")
        
        try:
            # Update latest supply
            self.latest_supply = supply_event
            
            # Call supply callbacks
            for callback in self.supply_callbacks:
                try:
                    callback(supply_event)
                except Exception as e:
                    pathway_logger.error(f"Supply callback error: {e}")
            
            # Trigger allocation
            allocations = self.trigger_allocation()
            
            if allocations:
                pathway_logger.info(f"Supply event {supply_event.event_id} triggered {len(allocations)} allocations")
            
            return allocations
            
        except Exception as e:
            pathway_logger.error(f"Failed to inject supply event {supply_event.event_id}: {e}", exc_info=True)
            update_component_health('pathway_engine', 'degraded', error_count=1)
            return None
    
    def create_node_schema(self) -> Dict[str, type]:
        """Define schema for energy node CSV data"""
        return {
            'node_id': str,
            'current_load': float,
            'priority_tier': int,
            'source_type': str,
            'status': str,
            'lat': float,
            'lng': float,
            'timestamp': float
        }
    
    def create_supply_schema(self) -> Dict[str, type]:
        """Define schema for supply event JSON data"""
        return {
            'event_id': str,
            'total_supply': float,
            'grid': float,
            'solar': float,
            'battery': float,
            'diesel': float,
            'timestamp': float
        }
    
    def validate_node_data(self, row: Dict[str, Any]) -> Optional[EnergyNode]:
        """
        Validate and normalize energy node data.
        
        Args:
            row: Raw data row from CSV stream
            
        Returns:
            Validated EnergyNode or None if invalid
        """
        try:
            # Validate priority tier
            if row['priority_tier'] not in [1, 2, 3]:
                pathway_logger.warning(f"Invalid priority_tier {row['priority_tier']} for node {row.get('node_id', 'unknown')}")
                self.error_count += 1
                update_component_health('pathway_engine', 'degraded', error_count=self.error_count)
                return None
            
            # Validate source type
            valid_sources = ['Grid', 'Solar', 'Battery', 'Diesel']
            if row['source_type'] not in valid_sources:
                pathway_logger.warning(f"Invalid source_type {row['source_type']} for node {row.get('node_id', 'unknown')}")
                self.error_count += 1
                update_component_health('pathway_engine', 'degraded', error_count=self.error_count)
                return None
            
            # Validate status
            valid_statuses = ['active', 'inactive', 'degraded']
            if row['status'] not in valid_statuses:
                pathway_logger.warning(f"Invalid status {row['status']} for node {row.get('node_id', 'unknown')}")
                self.error_count += 1
                update_component_health('pathway_engine', 'degraded', error_count=self.error_count)
                return None
            
            # Validate numeric fields
            if row['current_load'] < 0:
                pathway_logger.warning(f"Negative current_load {row['current_load']} for node {row.get('node_id', 'unknown')}")
                self.error_count += 1
                update_component_health('pathway_engine', 'degraded', error_count=self.error_count)
                return None
            
            # Create validated EnergyNode
            node = EnergyNode(
                node_id=str(row['node_id']),
                current_load=float(row['current_load']),
                priority_tier=int(row['priority_tier']),
                source_type=row['source_type'],
                status=row['status'],
                location=Location(
                    lat=float(row['lat']),
                    lng=float(row['lng'])
                ),
                timestamp=float(row['timestamp'])
            )
            
            self.processed_count += 1
            return node
            
        except (KeyError, ValueError, TypeError) as e:
            pathway_logger.error(f"Data validation error for node data: {e}")
            self.error_count += 1
            update_component_health('pathway_engine', 'degraded', error_count=self.error_count)
            return None
    
    def validate_supply_data(self, row: Dict[str, Any]) -> Optional[SupplyEvent]:
        """
        Validate and normalize supply event data.
        
        Args:
            row: Raw data row from JSON stream
            
        Returns:
            Validated SupplyEvent or None if invalid
        """
        try:
            # Validate numeric fields are non-negative
            numeric_fields = ['total_supply', 'grid', 'solar', 'battery', 'diesel']
            for field in numeric_fields:
                if row[field] < 0:
                    logger.warning(f"Negative {field} {row[field]} for event {row.get('event_id', 'unknown')}")
                    self.error_count += 1
                    return None
            
            # Validate total_supply matches sum of sources
            source_sum = row['grid'] + row['solar'] + row['battery'] + row['diesel']
            if abs(row['total_supply'] - source_sum) > 1e-6:  # Allow for floating point precision
                logger.warning(f"Total supply {row['total_supply']} doesn't match source sum {source_sum} for event {row.get('event_id', 'unknown')}")
                self.error_count += 1
                return None
            
            # Create validated SupplyEvent
            supply_event = SupplyEvent(
                event_id=str(row['event_id']),
                total_supply=float(row['total_supply']),
                available_sources=AvailableSources(
                    grid=float(row['grid']),
                    solar=float(row['solar']),
                    battery=float(row['battery']),
                    diesel=float(row['diesel'])
                ),
                timestamp=float(row['timestamp'])
            )
            
            self.processed_count += 1
            return supply_event
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Data validation error for supply data: {e}")
            self.error_count += 1
            return None
    
    def create_pipeline(self) -> tuple:
        """
        Create the main data processing pipeline with stream connectors.
        
        Returns:
            Tuple of (csv_connector, json_connector) for external control
        """
        logger.info("Creating data ingestion pipeline...")
        
        # Set up CSV stream connector for energy nodes
        nodes_csv_path = self.data_dir / "nodes_stream.csv"
        if not nodes_csv_path.exists():
            # Create empty file with header if it doesn't exist
            with open(nodes_csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['node_id', 'current_load', 'priority_tier', 'source_type', 
                               'status', 'lat', 'lng', 'timestamp'])
            logger.info(f"Created empty nodes stream file: {nodes_csv_path}")
        
        self.csv_connector = CSVStreamConnector(
            str(nodes_csv_path),
            self.create_node_schema(),
            mode="streaming"
        )
        
        # Set up JSON stream connector for supply events
        supply_json_path = self.data_dir / "supply_stream.jsonl"
        if not supply_json_path.exists():
            # Create empty file if it doesn't exist
            supply_json_path.touch()
            logger.info(f"Created empty supply stream file: {supply_json_path}")
        
        self.json_connector = JSONLStreamConnector(
            str(supply_json_path),
            self.create_supply_schema(),
            mode="streaming"
        )
        
        logger.info("Pipeline created successfully with validation and error handling")
        return self.csv_connector, self.json_connector
    
    def start_pipeline(self):
        """Start the data ingestion pipeline"""
        if not self.csv_connector or not self.json_connector:
            self.create_pipeline()
        
        # Start stream connectors
        self.csv_connector.start()
        self.json_connector.start()
        
        logger.info("Data ingestion pipeline started")
    
    def stop_pipeline(self):
        """Stop the data ingestion pipeline"""
        if self.csv_connector:
            self.csv_connector.stop()
        if self.json_connector:
            self.json_connector.stop()
        
        logger.info("Data ingestion pipeline stopped")
    
    def process_stream_data(self) -> Dict[str, int]:
        """
        Process available stream data and return processing stats.
        
        Returns:
            Dictionary with processing statistics
        """
        processed_nodes = 0
        processed_supply = 0
        allocation_triggered = False
        
        # Process CSV node data
        if self.csv_connector:
            while True:
                raw_data = self.csv_connector.get_data()
                if raw_data is None:
                    break
                
                with PerformanceContext(global_tracker, "node_validation"):
                    validated_node = self.validate_node_data(raw_data)
                    if validated_node:
                        processed_nodes += 1
                        
                        # Update current nodes state for real-time allocation
                        self.current_nodes[validated_node.node_id] = validated_node
                        
                        # Call registered callbacks
                        for callback in self.node_callbacks:
                            try:
                                callback(validated_node)
                            except Exception as e:
                                logger.error(f"Node callback error: {e}")
        
        # Process JSON supply data
        if self.json_connector:
            while True:
                raw_data = self.json_connector.get_data()
                if raw_data is None:
                    break
                
                with PerformanceContext(global_tracker, "supply_validation"):
                    validated_supply = self.validate_supply_data(raw_data)
                    if validated_supply:
                        processed_supply += 1
                        
                        # Update latest supply for real-time allocation
                        self.latest_supply = validated_supply
                        
                        # Call registered callbacks
                        for callback in self.supply_callbacks:
                            try:
                                callback(validated_supply)
                            except Exception as e:
                                logger.error(f"Supply callback error: {e}")
                        
                        # Trigger real-time allocation when supply event arrives
                        if self.allocation_enabled:
                            allocation_start = time.perf_counter()
                            allocations = self.trigger_allocation()
                            allocation_latency = (time.perf_counter() - allocation_start) * 1000
                            
                            if allocations:
                                allocation_triggered = True
                                logger.info(f"Supply event triggered allocation in {allocation_latency:.2f}ms")
                                
                                # Log performance warning if target exceeded
                                if allocation_latency > 10.0:
                                    logger.warning(f"Allocation latency {allocation_latency:.2f}ms exceeds 10ms target")
        
        return {
            'nodes_processed': processed_nodes,
            'supply_processed': processed_supply,
            'total_processed': processed_nodes + processed_supply,
            'allocation_triggered': allocation_triggered
        }
    
    def _validate_node_row(self, node_id: str, current_load: float, priority_tier: int,
                          source_type: str, status: str, lat: float, lng: float) -> bool:
        """Helper function for node validation in pipeline"""
        try:
            # Validate priority tier
            if priority_tier not in [1, 2, 3]:
                self.error_count += 1
                return False
            
            # Validate source type
            if source_type not in ['Grid', 'Solar', 'Battery', 'Diesel']:
                self.error_count += 1
                return False
            
            # Validate status
            if status not in ['active', 'inactive', 'degraded']:
                self.error_count += 1
                return False
            
            # Validate numeric fields
            if current_load < 0:
                self.error_count += 1
                return False
            
            self.processed_count += 1
            return True
            
        except Exception as e:
            logger.error(f"Node validation error: {e}")
            self.error_count += 1
            return False
    
    def _validate_supply_row(self, event_id: str, total_supply: float,
                           grid: float, solar: float, battery: float, diesel: float) -> bool:
        """Helper function for supply validation in pipeline"""
        try:
            # Validate numeric fields are non-negative
            if any(val < 0 for val in [total_supply, grid, solar, battery, diesel]):
                self.error_count += 1
                return False
            
            # Validate total_supply matches sum of sources
            source_sum = grid + solar + battery + diesel
            if abs(total_supply - source_sum) > 1e-6:
                self.error_count += 1
                return False
            
            self.processed_count += 1
            return True
            
        except Exception as e:
            logger.error(f"Supply validation error: {e}")
            self.error_count += 1
            return False
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Get pipeline processing statistics"""
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'success_rate': (self.processed_count / max(1, self.processed_count + self.error_count)) * 100
        }
    
    def run_pipeline(self, output_path: Optional[str] = None, duration: Optional[float] = None):
        """
        Run the data ingestion pipeline.
        
        Args:
            output_path: Optional path to write processed data
            duration: Optional duration to run pipeline (None for indefinite)
        """
        logger.info("Starting data ingestion pipeline...")
        
        try:
            # Create and start the pipeline
            self.start_pipeline()
            
            # Set up output if specified
            output_nodes = []
            output_supply = []
            
            if output_path:
                output_dir = Path(output_path)
                output_dir.mkdir(exist_ok=True)
                
                # Set up callbacks to collect data for output
                def collect_node(node: EnergyNode):
                    output_nodes.append(node.dict())
                
                def collect_supply(supply: SupplyEvent):
                    output_supply.append(supply.dict())
                
                self.add_node_callback(collect_node)
                self.add_supply_callback(collect_supply)
                
                logger.info(f"Pipeline output configured to: {output_path}")
            
            # Run the pipeline
            start_time = time.time()
            while True:
                # Process available data
                stats = self.process_stream_data()
                
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    break
                
                # Small delay to prevent busy waiting
                time.sleep(0.01)  # 10ms delay for <10ms processing target
            
            # Write output if specified
            if output_path and (output_nodes or output_supply):
                with open(output_dir / "validated_nodes.jsonl", 'w') as f:
                    for node in output_nodes:
                        f.write(json.dumps(node) + '\n')
                
                with open(output_dir / "validated_supply.jsonl", 'w') as f:
                    for supply in output_supply:
                        f.write(json.dumps(supply) + '\n')
                
                logger.info(f"Wrote {len(output_nodes)} nodes and {len(output_supply)} supply events to output")
            
        except KeyboardInterrupt:
            logger.info("Pipeline interrupted by user")
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise
        finally:
            self.stop_pipeline()


# Convenience functions for external usage
def create_energy_pipeline(data_dir: str = "./data") -> EnergyDataIngestionPipeline:
    """
    Create and return a configured energy data ingestion pipeline.
    
    Args:
        data_dir: Directory containing data streams
        
    Returns:
        Configured pipeline instance
    """
    return EnergyDataIngestionPipeline(data_dir)


def validate_energy_node_data(data: Dict[str, Any]) -> Optional[EnergyNode]:
    """
    Standalone function to validate energy node data.
    
    Args:
        data: Raw node data dictionary
        
    Returns:
        Validated EnergyNode or None if invalid
    """
    pipeline = EnergyDataIngestionPipeline()
    return pipeline.validate_node_data(data)


def validate_supply_event_data(data: Dict[str, Any]) -> Optional[SupplyEvent]:
    """
    Standalone function to validate supply event data.
    
    Args:
        data: Raw supply event data dictionary
        
    Returns:
        Validated SupplyEvent or None if invalid
    """
    pipeline = EnergyDataIngestionPipeline()
    return pipeline.validate_supply_data(data)