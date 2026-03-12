"""
Comprehensive monitoring and logging system for Bharat-Grid AI.

This module provides:
- Performance warning logs when targets are exceeded
- Allocation decision audit logging for traceability
- Health check endpoints for all services
- Structured logging with proper levels and formatting
- Monitoring metrics collection and exposure
"""

import logging
import time
import json
import os
import threading
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, deque
from contextlib import contextmanager

from pydantic import BaseModel, Field

# Import schemas for type hints
from schemas import AllocationResult, EnergyNode, SupplyEvent


@dataclass
class AllocationAuditLog:
    """Audit log entry for allocation decisions"""
    timestamp: float
    allocation_id: str
    node_id: str
    allocated_power: float
    requested_power: float
    priority_tier: int
    action: str  # maintain, reduce, cutoff
    source_mix: Dict[str, float]
    processing_time_ms: float
    total_supply: float
    total_demand: float
    decision_factors: Dict[str, Any]


@dataclass
class PerformanceWarning:
    """Performance warning log entry"""
    timestamp: float
    operation: str
    actual_latency_ms: float
    target_latency_ms: float
    violation_severity: str  # minor, major, critical
    context: Dict[str, Any]
    node_count: Optional[int] = None
    message_size: Optional[int] = None


@dataclass
class SystemHealthMetrics:
    """System health metrics snapshot"""
    timestamp: float
    component: str
    status: str  # healthy, degraded, unhealthy
    uptime_seconds: float
    error_count: int
    warning_count: int
    performance_metrics: Dict[str, float]
    resource_usage: Dict[str, float]


class StructuredLogger:
    """Structured logging with JSON output and proper formatting"""
    
    def __init__(self, name: str, log_dir: str = "./logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger with structured formatting
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup file and console handlers with structured formatting"""
        
        # Console handler with readable format
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with JSON format for structured logging
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Custom JSON formatter
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': record.created,
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                
                # Add extra fields if present
                if hasattr(record, 'extra_data'):
                    log_entry.update(record.extra_data)
                
                return json.dumps(log_entry)
        
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)
        
        # Audit log handler for allocation decisions
        if self.name == 'allocation_audit':
            audit_file = self.log_dir / "allocation_audit.log"
            audit_handler = logging.FileHandler(audit_file)
            audit_handler.setLevel(logging.INFO)
            audit_handler.setFormatter(JSONFormatter())
            self.logger.addHandler(audit_handler)
    
    def info(self, message: str, extra_data: Optional[Dict] = None):
        """Log info message with optional structured data"""
        self.logger.info(message, extra={'extra_data': extra_data or {}})
    
    def warning(self, message: str, extra_data: Optional[Dict] = None):
        """Log warning message with optional structured data"""
        self.logger.warning(message, extra={'extra_data': extra_data or {}})
    
    def error(self, message: str, extra_data: Optional[Dict] = None, exc_info: bool = False):
        """Log error message with optional structured data"""
        self.logger.error(message, extra={'extra_data': extra_data or {}}, exc_info=exc_info)
    
    def debug(self, message: str, extra_data: Optional[Dict] = None):
        """Log debug message with optional structured data"""
        self.logger.debug(message, extra={'extra_data': extra_data or {}})


class PerformanceMonitor:
    """
    Performance monitoring system with warning thresholds.
    
    Implements Requirements 7.4 and 7.5:
    - Log performance warnings when allocation latency exceeds 10ms
    - Log performance warnings when WebSocket latency exceeds 50ms
    """
    
    def __init__(self, log_dir: str = "./logs"):
        self.logger = StructuredLogger('performance_monitor', log_dir)
        self.warnings: deque = deque(maxlen=1000)  # Keep last 1000 warnings
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Performance thresholds (Requirements 7.4, 7.5)
        self.thresholds = {
            'allocation': {
                'target_ms': 10.0,
                'minor_threshold': 15.0,    # 50% over target
                'major_threshold': 25.0,    # 150% over target
                'critical_threshold': 50.0  # 400% over target
            },
            'websocket': {
                'target_ms': 50.0,
                'minor_threshold': 75.0,    # 50% over target
                'major_threshold': 125.0,   # 150% over target
                'critical_threshold': 250.0 # 400% over target
            },
            'rag_prediction': {
                'target_ms': 2000.0,
                'minor_threshold': 3000.0,  # 50% over target
                'major_threshold': 5000.0,  # 150% over target
                'critical_threshold': 10000.0 # 400% over target
            }
        }
        
        self.warning_counts = defaultdict(int)
        self.start_time = time.time()
    
    def record_performance(self, operation: str, latency_ms: float, context: Optional[Dict] = None):
        """
        Record performance measurement and check for violations.
        
        Args:
            operation: Operation name (allocation, websocket, rag_prediction)
            latency_ms: Measured latency in milliseconds
            context: Additional context for logging
        """
        context = context or {}
        
        # Store metric for trending
        self.metrics_history[operation].append({
            'timestamp': time.time(),
            'latency_ms': latency_ms,
            'context': context
        })
        
        # Check for threshold violations
        if operation in self.thresholds:
            threshold_config = self.thresholds[operation]
            target_ms = threshold_config['target_ms']
            
            if latency_ms > target_ms:
                # Determine severity
                severity = self._determine_severity(latency_ms, threshold_config)
                
                # Create warning
                warning = PerformanceWarning(
                    timestamp=time.time(),
                    operation=operation,
                    actual_latency_ms=latency_ms,
                    target_latency_ms=target_ms,
                    violation_severity=severity,
                    context=context,
                    node_count=context.get('node_count'),
                    message_size=context.get('message_size')
                )
                
                self.warnings.append(warning)
                self.warning_counts[f"{operation}_{severity}"] += 1
                
                # Log the warning (Requirements 7.4, 7.5)
                self._log_performance_warning(warning)
    
    def _determine_severity(self, latency_ms: float, threshold_config: Dict) -> str:
        """Determine warning severity based on latency"""
        if latency_ms >= threshold_config['critical_threshold']:
            return 'critical'
        elif latency_ms >= threshold_config['major_threshold']:
            return 'major'
        elif latency_ms >= threshold_config['minor_threshold']:
            return 'minor'
        else:
            return 'minor'  # Any violation is at least minor
    
    def _log_performance_warning(self, warning: PerformanceWarning):
        """Log performance warning with structured data"""
        message = (
            f"{warning.operation.upper()} performance warning: "
            f"{warning.actual_latency_ms:.2f}ms exceeds {warning.target_latency_ms}ms target "
            f"(severity: {warning.violation_severity})"
        )
        
        extra_data = {
            'operation': warning.operation,
            'actual_latency_ms': warning.actual_latency_ms,
            'target_latency_ms': warning.target_latency_ms,
            'violation_severity': warning.violation_severity,
            'context': warning.context,
            'warning_type': 'performance_violation'
        }
        
        if warning.violation_severity == 'critical':
            self.logger.error(message, extra_data)
        else:
            self.logger.warning(message, extra_data)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary with violation statistics"""
        summary = {
            'uptime_seconds': time.time() - self.start_time,
            'total_warnings': len(self.warnings),
            'warning_counts': dict(self.warning_counts),
            'operations': {}
        }
        
        for operation, metrics in self.metrics_history.items():
            if metrics:
                latencies = [m['latency_ms'] for m in metrics]
                target = self.thresholds.get(operation, {}).get('target_ms', 0)
                violations = sum(1 for lat in latencies if lat > target)
                
                summary['operations'][operation] = {
                    'measurement_count': len(latencies),
                    'avg_latency_ms': sum(latencies) / len(latencies),
                    'max_latency_ms': max(latencies),
                    'min_latency_ms': min(latencies),
                    'target_ms': target,
                    'violations': violations,
                    'violation_rate': (violations / len(latencies)) * 100 if latencies else 0
                }
        
        return summary
    
    def get_recent_warnings(self, limit: int = 10) -> List[Dict]:
        """Get recent performance warnings"""
        recent = list(self.warnings)[-limit:]
        return [asdict(warning) for warning in recent]


class AllocationAuditor:
    """
    Audit logging system for allocation decisions.
    
    Provides traceability for all power allocation decisions
    with detailed context and decision factors.
    """
    
    def __init__(self, log_dir: str = "./logs"):
        self.logger = StructuredLogger('allocation_audit', log_dir)
        self.audit_history: deque = deque(maxlen=10000)  # Keep last 10k allocations
        self.decision_stats = defaultdict(int)
    
    def log_allocation_decision(
        self,
        allocation: AllocationResult,
        node: EnergyNode,
        supply_event: SupplyEvent,
        processing_time_ms: float,
        total_demand: float,
        decision_factors: Optional[Dict] = None
    ):
        """
        Log allocation decision with full audit trail.
        
        Args:
            allocation: The allocation result
            node: The energy node being allocated to
            supply_event: The supply event that triggered allocation
            processing_time_ms: Time taken to make the decision
            total_demand: Total system demand at time of decision
            decision_factors: Additional factors that influenced the decision
        """
        decision_factors = decision_factors or {}
        
        # Create audit log entry
        audit_entry = AllocationAuditLog(
            timestamp=time.time(),
            allocation_id=f"alloc_{int(time.time() * 1000)}_{node.node_id}",
            node_id=node.node_id,
            allocated_power=allocation.allocated_power,
            requested_power=node.current_load,
            priority_tier=node.priority_tier,
            action=allocation.action,
            source_mix=allocation.source_mix,
            processing_time_ms=processing_time_ms,
            total_supply=supply_event.total_supply,
            total_demand=total_demand,
            decision_factors={
                'node_status': node.status,
                'source_type': node.source_type,
                'location': node.location.dict(),
                'supply_sources': supply_event.available_sources.dict(),
                'allocation_efficiency': (allocation.allocated_power / node.current_load) * 100 if node.current_load > 0 else 100,
                **decision_factors
            }
        )
        
        # Store in memory for quick access
        self.audit_history.append(audit_entry)
        self.decision_stats[allocation.action] += 1
        
        # Log to structured audit log
        message = (
            f"Allocation decision: {node.node_id} ({node.priority_tier}) "
            f"allocated {allocation.allocated_power:.2f}kW of {node.current_load:.2f}kW requested "
            f"(action: {allocation.action})"
        )
        
        extra_data = asdict(audit_entry)
        self.logger.info(message, extra_data)
    
    def get_allocation_stats(self) -> Dict[str, Any]:
        """Get allocation decision statistics"""
        total_allocations = len(self.audit_history)
        
        if total_allocations == 0:
            return {'total_allocations': 0}
        
        # Calculate statistics
        total_allocated = sum(entry.allocated_power for entry in self.audit_history)
        total_requested = sum(entry.requested_power for entry in self.audit_history)
        avg_processing_time = sum(entry.processing_time_ms for entry in self.audit_history) / total_allocations
        
        # Priority tier breakdown
        tier_stats = defaultdict(lambda: {'count': 0, 'allocated': 0, 'requested': 0})
        for entry in self.audit_history:
            tier_stats[entry.priority_tier]['count'] += 1
            tier_stats[entry.priority_tier]['allocated'] += entry.allocated_power
            tier_stats[entry.priority_tier]['requested'] += entry.requested_power
        
        return {
            'total_allocations': total_allocations,
            'total_allocated_power': total_allocated,
            'total_requested_power': total_requested,
            'allocation_efficiency': (total_allocated / total_requested) * 100 if total_requested > 0 else 0,
            'avg_processing_time_ms': avg_processing_time,
            'decision_counts': dict(self.decision_stats),
            'tier_statistics': dict(tier_stats)
        }
    
    def get_recent_allocations(self, limit: int = 50) -> List[Dict]:
        """Get recent allocation decisions"""
        recent = list(self.audit_history)[-limit:]
        return [asdict(entry) for entry in recent]
    
    def search_allocations(
        self,
        node_id: Optional[str] = None,
        action: Optional[str] = None,
        priority_tier: Optional[int] = None,
        time_range_hours: Optional[int] = None
    ) -> List[Dict]:
        """Search allocation history with filters"""
        results = list(self.audit_history)
        
        # Apply filters
        if node_id:
            results = [entry for entry in results if entry.node_id == node_id]
        
        if action:
            results = [entry for entry in results if entry.action == action]
        
        if priority_tier:
            results = [entry for entry in results if entry.priority_tier == priority_tier]
        
        if time_range_hours:
            cutoff_time = time.time() - (time_range_hours * 3600)
            results = [entry for entry in results if entry.timestamp >= cutoff_time]
        
        return [asdict(entry) for entry in results]


class HealthMonitor:
    """
    System health monitoring with component status tracking.
    
    Monitors health of all system components and provides
    comprehensive health check endpoints.
    """
    
    def __init__(self, log_dir: str = "./logs"):
        self.logger = StructuredLogger('health_monitor', log_dir)
        self.component_health: Dict[str, SystemHealthMetrics] = {}
        self.start_time = time.time()
        self.health_history: deque = deque(maxlen=1000)
        
        # Component registry
        self.components = {
            'api_gateway': {'required': True, 'timeout': 5.0},
            'pathway_engine': {'required': True, 'timeout': 10.0},
            'rag_system': {'required': True, 'timeout': 15.0},
            'vector_store': {'required': True, 'timeout': 10.0},
            'websocket_manager': {'required': True, 'timeout': 5.0},
            'data_streams': {'required': True, 'timeout': 5.0}
        }
    
    def register_component(self, component: str, required: bool = True, timeout: float = 10.0):
        """Register a component for health monitoring"""
        self.components[component] = {'required': required, 'timeout': timeout}
        self.logger.info(f"Registered component for health monitoring: {component}")
    
    def update_component_health(
        self,
        component: str,
        status: str,
        error_count: int = 0,
        warning_count: int = 0,
        performance_metrics: Optional[Dict[str, float]] = None,
        resource_usage: Optional[Dict[str, float]] = None
    ):
        """Update health status for a component"""
        health_metrics = SystemHealthMetrics(
            timestamp=time.time(),
            component=component,
            status=status,
            uptime_seconds=time.time() - self.start_time,
            error_count=error_count,
            warning_count=warning_count,
            performance_metrics=performance_metrics or {},
            resource_usage=resource_usage or {}
        )
        
        self.component_health[component] = health_metrics
        self.health_history.append(health_metrics)
        
        # Log status changes
        if component in self.component_health:
            previous_status = self.component_health[component].status
            if previous_status != status:
                self.logger.info(
                    f"Component {component} status changed: {previous_status} -> {status}",
                    {'component': component, 'old_status': previous_status, 'new_status': status}
                )
    
    def check_component_health(self, component: str) -> Dict[str, Any]:
        """Check health of a specific component"""
        if component not in self.component_health:
            return {
                'component': component,
                'status': 'unknown',
                'message': 'Component not registered or never reported health'
            }
        
        health = self.component_health[component]
        age_seconds = time.time() - health.timestamp
        
        # Determine if health data is stale
        timeout = self.components.get(component, {}).get('timeout', 30.0)
        if age_seconds > timeout:
            status = 'stale'
            message = f"Health data is {age_seconds:.1f}s old (timeout: {timeout}s)"
        else:
            status = health.status
            message = f"Component is {status}"
        
        return {
            'component': component,
            'status': status,
            'message': message,
            'last_update': health.timestamp,
            'age_seconds': age_seconds,
            'error_count': health.error_count,
            'warning_count': health.warning_count,
            'performance_metrics': health.performance_metrics,
            'resource_usage': health.resource_usage
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        component_statuses = {}
        overall_status = 'healthy'
        unhealthy_components = []
        
        for component in self.components:
            health = self.check_component_health(component)
            component_statuses[component] = health
            
            # Determine impact on overall health
            if health['status'] in ['unhealthy', 'stale']:
                if self.components[component]['required']:
                    overall_status = 'unhealthy'
                    unhealthy_components.append(component)
                elif overall_status == 'healthy':
                    overall_status = 'degraded'
            elif health['status'] == 'degraded' and overall_status == 'healthy':
                overall_status = 'degraded'
        
        return {
            'overall_status': overall_status,
            'uptime_seconds': time.time() - self.start_time,
            'components': component_statuses,
            'unhealthy_components': unhealthy_components,
            'timestamp': time.time()
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for monitoring dashboards"""
        system_health = self.get_system_health()
        
        # Count components by status
        status_counts = defaultdict(int)
        for component_health in system_health['components'].values():
            status_counts[component_health['status']] += 1
        
        return {
            'overall_status': system_health['overall_status'],
            'total_components': len(self.components),
            'status_counts': dict(status_counts),
            'uptime_hours': system_health['uptime_seconds'] / 3600,
            'last_check': time.time()
        }


# Global monitoring instances
performance_monitor = PerformanceMonitor()
allocation_auditor = AllocationAuditor()
health_monitor = HealthMonitor()

# Structured loggers for different subsystems
api_logger = StructuredLogger('api_gateway')
pathway_logger = StructuredLogger('pathway_engine')
rag_logger = StructuredLogger('rag_system')
websocket_logger = StructuredLogger('websocket_manager')


@contextmanager
def performance_tracking(operation: str, context: Optional[Dict] = None):
    """Context manager for automatic performance tracking"""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        latency_ms = (time.perf_counter() - start_time) * 1000
        performance_monitor.record_performance(operation, latency_ms, context)


def log_allocation_decision(
    allocation: AllocationResult,
    node: EnergyNode,
    supply_event: SupplyEvent,
    processing_time_ms: float,
    total_demand: float,
    decision_factors: Optional[Dict] = None
):
    """Convenience function for logging allocation decisions"""
    allocation_auditor.log_allocation_decision(
        allocation, node, supply_event, processing_time_ms, total_demand, decision_factors
    )


def update_component_health(component: str, status: str, **kwargs):
    """Convenience function for updating component health"""
    health_monitor.update_component_health(component, status, **kwargs)


# Initialize component health monitoring
def initialize_monitoring():
    """Initialize monitoring system with default components"""
    components = [
        'api_gateway',
        'pathway_engine', 
        'rag_system',
        'vector_store',
        'websocket_manager',
        'data_streams'
    ]
    
    for component in components:
        health_monitor.register_component(component)
    
    api_logger.info("Monitoring system initialized", {
        'components_registered': len(components),
        'log_directory': './logs'
    })


if __name__ == "__main__":
    # Demo usage
    initialize_monitoring()
    
    # Simulate some performance measurements
    with performance_tracking('allocation', {'node_count': 10}):
        time.sleep(0.015)  # Simulate 15ms processing (exceeds 10ms target)
    
    with performance_tracking('websocket', {'message_size': 1024}):
        time.sleep(0.025)  # Simulate 25ms transmission (within 50ms target)
    
    # Update component health
    update_component_health('api_gateway', 'healthy', error_count=0, warning_count=2)
    update_component_health('pathway_engine', 'degraded', error_count=1, warning_count=5)
    
    # Print summaries
    print("Performance Summary:")
    print(json.dumps(performance_monitor.get_performance_summary(), indent=2))
    
    print("\nHealth Summary:")
    print(json.dumps(health_monitor.get_health_summary(), indent=2))