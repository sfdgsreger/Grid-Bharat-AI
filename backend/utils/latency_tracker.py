# Latency tracking and performance monitoring utilities
import time
import statistics
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque


@dataclass
class LatencyMetric:
    """Individual latency measurement"""
    operation: str
    latency_ms: float
    timestamp: float
    metadata: Optional[Dict] = None


@dataclass
class LatencyStats:
    """Aggregated latency statistics"""
    operation: str
    count: int
    avg_ms: float
    min_ms: float
    max_ms: float
    p95_ms: float
    p99_ms: float
    target_ms: float
    violations: int
    violation_rate: float


class LatencyTracker:
    """
    Performance monitoring system for tracking allocation latencies.
    
    Tracks individual operation latencies and provides aggregated statistics
    to ensure the <10ms allocation target and <50ms WebSocket target are met.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize latency tracker.
        
        Args:
            max_history: Maximum number of latency measurements to keep in memory
        """
        self.max_history = max_history
        self.metrics: Dict[str, deque] = {}
        self.targets = {
            'allocation': 10.0,      # <10ms for allocation decisions
            'websocket': 50.0,       # <50ms for WebSocket transmission
            'rag_prediction': 2000.0 # <2s for RAG predictions
        }
    
    def record_latency(
        self, 
        operation: str, 
        latency_ms: float, 
        metadata: Optional[Dict] = None
    ):
        """
        Record a latency measurement.
        
        Args:
            operation: Name of the operation (e.g., 'allocation', 'websocket')
            latency_ms: Latency in milliseconds
            metadata: Optional metadata about the operation
        """
        if operation not in self.metrics:
            self.metrics[operation] = deque(maxlen=self.max_history)
        
        metric = LatencyMetric(
            operation=operation,
            latency_ms=latency_ms,
            timestamp=time.time(),
            metadata=metadata
        )
        
        self.metrics[operation].append(metric)
        
        # Log performance warnings
        target = self.targets.get(operation)
        if target and latency_ms > target:
            print(f"WARNING: {operation} latency {latency_ms:.2f}ms exceeds {target}ms target")
    
    def get_stats(self, operation: str) -> Optional[LatencyStats]:
        """
        Get aggregated statistics for an operation.
        
        Args:
            operation: Name of the operation
            
        Returns:
            LatencyStats object or None if no data available
        """
        if operation not in self.metrics or not self.metrics[operation]:
            return None
        
        latencies = [m.latency_ms for m in self.metrics[operation]]
        target = self.targets.get(operation, float('inf'))
        violations = sum(1 for lat in latencies if lat > target)
        
        return LatencyStats(
            operation=operation,
            count=len(latencies),
            avg_ms=statistics.mean(latencies),
            min_ms=min(latencies),
            max_ms=max(latencies),
            p95_ms=statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
            p99_ms=statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
            target_ms=target,
            violations=violations,
            violation_rate=violations / len(latencies) * 100
        )
    
    def get_all_stats(self) -> Dict[str, LatencyStats]:
        """Get statistics for all tracked operations"""
        return {op: self.get_stats(op) for op in self.metrics.keys() if self.get_stats(op)}
    
    def print_summary(self):
        """Print a summary of all latency statistics"""
        print("Latency Performance Summary")
        print("=" * 50)
        
        for operation, stats in self.get_all_stats().items():
            status = "✓ PASS" if stats.violation_rate < 5.0 else "✗ FAIL"
            print(f"\n{operation.upper()} Performance {status}")
            print(f"  Measurements: {stats.count}")
            print(f"  Average: {stats.avg_ms:.2f}ms")
            print(f"  Min/Max: {stats.min_ms:.2f}ms / {stats.max_ms:.2f}ms")
            print(f"  P95/P99: {stats.p95_ms:.2f}ms / {stats.p99_ms:.2f}ms")
            print(f"  Target: <{stats.target_ms}ms")
            print(f"  Violations: {stats.violations}/{stats.count} ({stats.violation_rate:.1f}%)")
    
    def clear_history(self, operation: Optional[str] = None):
        """
        Clear latency history.
        
        Args:
            operation: Specific operation to clear, or None to clear all
        """
        if operation:
            if operation in self.metrics:
                self.metrics[operation].clear()
        else:
            for queue in self.metrics.values():
                queue.clear()
    
    def set_target(self, operation: str, target_ms: float):
        """
        Set or update the latency target for an operation.
        
        Args:
            operation: Name of the operation
            target_ms: Target latency in milliseconds
        """
        self.targets[operation] = target_ms
    
    def is_healthy(self, operation: str, max_violation_rate: float = 5.0) -> bool:
        """
        Check if an operation is performing within acceptable limits.
        
        Args:
            operation: Name of the operation
            max_violation_rate: Maximum acceptable violation rate (%)
            
        Returns:
            True if the operation is healthy
        """
        stats = self.get_stats(operation)
        if not stats:
            return True  # No data means no problems yet
        
        return stats.violation_rate <= max_violation_rate


class PerformanceContext:
    """Context manager for automatic latency tracking"""
    
    def __init__(self, tracker: LatencyTracker, operation: str, metadata: Optional[Dict] = None):
        self.tracker = tracker
        self.operation = operation
        self.metadata = metadata
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            latency_ms = (time.perf_counter() - self.start_time) * 1000
            self.tracker.record_latency(self.operation, latency_ms, self.metadata)


# Global latency tracker instance
global_tracker = LatencyTracker()


def track_latency(operation: str, metadata: Optional[Dict] = None):
    """
    Decorator for automatic latency tracking.
    
    Args:
        operation: Name of the operation
        metadata: Optional metadata about the operation
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceContext(global_tracker, operation, metadata):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Convenience functions
def record_allocation_latency(latency_ms: float, node_count: int = None):
    """Record allocation operation latency"""
    metadata = {'node_count': node_count} if node_count else None
    global_tracker.record_latency('allocation', latency_ms, metadata)


def record_websocket_latency(latency_ms: float, message_size: int = None):
    """Record WebSocket transmission latency"""
    metadata = {'message_size': message_size} if message_size else None
    global_tracker.record_latency('websocket', latency_ms, metadata)


def record_rag_latency(latency_ms: float, query_length: int = None):
    """Record RAG prediction latency"""
    metadata = {'query_length': query_length} if query_length else None
    global_tracker.record_latency('rag_prediction', latency_ms, metadata)


def get_performance_summary() -> Dict[str, LatencyStats]:
    """Get current performance summary"""
    return global_tracker.get_all_stats()


def print_performance_summary():
    """Print current performance summary"""
    global_tracker.print_summary()


if __name__ == "__main__":
    # Demo usage
    tracker = LatencyTracker()
    
    # Simulate some measurements
    import random
    
    print("Simulating latency measurements...")
    
    # Simulate allocation latencies (mostly good, some violations)
    for i in range(100):
        latency = random.gauss(5.0, 2.0)  # Average 5ms, some outliers
        if random.random() < 0.05:  # 5% violations
            latency += random.uniform(10, 20)
        tracker.record_latency('allocation', max(0.1, latency), {'node_count': random.randint(10, 500)})
    
    # Simulate WebSocket latencies
    for i in range(50):
        latency = random.gauss(25.0, 10.0)  # Average 25ms
        if random.random() < 0.02:  # 2% violations
            latency += random.uniform(50, 100)
        tracker.record_latency('websocket', max(1.0, latency), {'message_size': random.randint(100, 1000)})
    
    # Print summary
    tracker.print_summary()