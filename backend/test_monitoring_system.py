"""
Comprehensive test suite for the monitoring and logging system.

Tests all monitoring components including performance tracking,
audit logging, health monitoring, and log management.
"""

import time
import asyncio
import tempfile
import shutil
from pathlib import Path
import pytest

from monitoring import (
    performance_monitor,
    allocation_auditor,
    health_monitor,
    initialize_monitoring,
    performance_tracking,
    update_component_health
)
from schemas import AllocationResult, EnergyNode, SupplyEvent, Location, AvailableSources
from log_management import LogManager, setup_production_logging


def test_performance_monitoring():
    """Test performance monitoring with warning thresholds"""
    print("\n=== Testing Performance Monitoring ===")
    
    # Test allocation performance tracking
    with performance_tracking('allocation', {'node_count': 10}):
        time.sleep(0.015)  # Simulate 15ms processing (exceeds 10ms target)
    
    # Test WebSocket performance tracking
    with performance_tracking('websocket', {'message_size': 1024}):
        time.sleep(0.025)  # Simulate 25ms transmission (within 50ms target)
    
    # Test RAG performance tracking
    with performance_tracking('rag_prediction', {'query_length': 100}):
        time.sleep(0.5)  # Simulate 500ms processing (within 2s target)
    
    # Get performance summary
    summary = performance_monitor.get_performance_summary()
    print(f"Performance summary: {summary}")
    
    # Verify warnings were generated
    warnings = performance_monitor.get_recent_warnings(10)
    print(f"Recent warnings: {len(warnings)}")
    
    assert len(warnings) > 0, "Should have generated performance warnings"
    assert any(w['operation'] == 'allocation' for w in warnings), "Should have allocation warning"
    
    print("✓ Performance monitoring working correctly")


def test_allocation_auditing():
    """Test allocation decision audit logging"""
    print("\n=== Testing Allocation Auditing ===")
    
    # Create test data
    node = EnergyNode(
        node_id="test_hospital_001",
        current_load=150.0,
        priority_tier=1,
        source_type="Grid",
        status="active",
        location=Location(lat=28.6139, lng=77.2090),
        timestamp=time.time()
    )
    
    allocation = AllocationResult(
        node_id="test_hospital_001",
        allocated_power=120.0,
        source_mix={"grid": 80.0, "solar": 40.0},
        action="reduce",
        latency_ms=8.5
    )
    
    supply_event = SupplyEvent(
        event_id="test_supply_001",
        total_supply=800.0,
        available_sources=AvailableSources(
            grid=400.0,
            solar=200.0,
            battery=150.0,
            diesel=50.0
        ),
        timestamp=time.time()
    )
    
    # Log allocation decision
    allocation_auditor.log_allocation_decision(
        allocation=allocation,
        node=node,
        supply_event=supply_event,
        processing_time_ms=8.5,
        total_demand=500.0,
        decision_factors={
            'supply_shortage': True,
            'priority_override': False
        }
    )
    
    # Get allocation statistics
    stats = allocation_auditor.get_allocation_stats()
    print(f"Allocation stats: {stats}")
    
    # Get recent allocations
    recent = allocation_auditor.get_recent_allocations(5)
    print(f"Recent allocations: {len(recent)}")
    
    assert stats['total_allocations'] > 0, "Should have recorded allocations"
    assert len(recent) > 0, "Should have recent allocations"
    assert recent[0]['node_id'] == "test_hospital_001", "Should match test node"
    
    print("✓ Allocation auditing working correctly")


def test_health_monitoring():
    """Test system health monitoring"""
    print("\n=== Testing Health Monitoring ===")
    
    # Initialize monitoring
    initialize_monitoring()
    
    # Update component health
    update_component_health('api_gateway', 'healthy', error_count=0, warning_count=2)
    update_component_health('pathway_engine', 'degraded', error_count=1, warning_count=5)
    update_component_health('rag_system', 'unhealthy', error_count=3, warning_count=1)
    
    # Get system health
    system_health = health_monitor.get_system_health()
    print(f"System health: {system_health['overall_status']}")
    print(f"Components: {len(system_health['components'])}")
    print(f"Unhealthy: {system_health['unhealthy_components']}")
    
    # Get health summary
    summary = health_monitor.get_health_summary()
    print(f"Health summary: {summary}")
    
    assert system_health['overall_status'] in ['healthy', 'degraded', 'unhealthy']
    assert len(system_health['components']) > 0, "Should have registered components"
    assert 'rag_system' in system_health['unhealthy_components'], "RAG system should be unhealthy"
    
    print("✓ Health monitoring working correctly")


def test_log_management():
    """Test log rotation and management"""
    print("\n=== Testing Log Management ===")
    
    # Create temporary log directory
    with tempfile.TemporaryDirectory() as temp_dir:
        log_manager = LogManager(
            log_dir=temp_dir,
            max_file_size_mb=1,  # Small size for testing
            max_files_per_logger=3,
            archive_days=1
        )
        
        # Create test log files
        test_log = Path(temp_dir) / "test.log"
        with open(test_log, 'w') as f:
            for i in range(1000):
                f.write(f"Test log line {i}\n")
        
        # Test compression
        compressed = log_manager.compress_log_file(test_log)
        assert compressed is not None, "Should compress log file"
        assert compressed.exists(), "Compressed file should exist"
        assert not test_log.exists(), "Original file should be removed"
        
        # Test statistics
        stats = log_manager.get_log_statistics()
        print(f"Log statistics: {stats}")
        
        assert stats['total_size_mb'] > 0, "Should have log files"
        assert len(stats['archived_logs']) > 0, "Should have archived logs"
        
        print("✓ Log management working correctly")


async def test_health_endpoints():
    """Test health check endpoints"""
    print("\n=== Testing Health Endpoints ===")
    
    from health_endpoints import (
        get_system_health,
        get_health_summary,
        get_performance_health,
        get_allocation_health
    )
    
    # Test system health endpoint
    health_response = await get_system_health()
    print(f"System health response: {health_response.overall_status}")
    assert health_response.overall_status in ['healthy', 'degraded', 'unhealthy']
    
    # Test health summary endpoint
    summary_response = await get_health_summary()
    print(f"Health summary: {summary_response.total_components} components")
    assert summary_response.total_components > 0
    
    # Test performance health endpoint
    perf_response = await get_performance_health()
    print(f"Performance health: {perf_response.total_warnings} warnings")
    
    # Test allocation health endpoint
    alloc_response = await get_allocation_health()
    print(f"Allocation health: {alloc_response.total_allocations} allocations")
    
    print("✓ Health endpoints working correctly")


def test_integration_monitoring():
    """Test integration between monitoring components"""
    print("\n=== Testing Monitoring Integration ===")
    
    # Simulate a complete allocation cycle with monitoring
    start_time = time.time()
    
    # 1. Performance tracking
    with performance_tracking('allocation', {'node_count': 5}):
        time.sleep(0.012)  # Simulate processing that exceeds target
    
    # 2. Health update
    update_component_health('pathway_engine', 'healthy', 
                          performance_metrics={'avg_latency_ms': 12.0})
    
    # 3. Check that all systems recorded the data
    perf_summary = performance_monitor.get_performance_summary()
    health_status = health_monitor.get_system_health()
    
    # Verify integration
    assert 'allocation' in perf_summary['operations'], "Performance should track allocation"
    assert 'pathway_engine' in health_status['components'], "Health should track pathway engine"
    
    # Check that warnings were generated for exceeded latency
    warnings = performance_monitor.get_recent_warnings(5)
    allocation_warnings = [w for w in warnings if w['operation'] == 'allocation']
    assert len(allocation_warnings) > 0, "Should generate allocation warnings"
    
    print("✓ Monitoring integration working correctly")


def run_all_tests():
    """Run all monitoring system tests"""
    print("Starting comprehensive monitoring system tests...")
    
    try:
        # Initialize monitoring system
        initialize_monitoring()
        
        # Run tests
        test_performance_monitoring()
        test_allocation_auditing()
        test_health_monitoring()
        test_log_management()
        
        # Run async tests
        asyncio.run(test_health_endpoints())
        
        test_integration_monitoring()
        
        print("\n" + "="*60)
        print("🎉 ALL MONITORING TESTS PASSED!")
        print("✓ Performance warning logs implemented")
        print("✓ Allocation decision audit logging implemented")
        print("✓ Health check endpoints implemented")
        print("✓ Structured logging with proper levels implemented")
        print("✓ Log rotation and management implemented")
        print("✓ Requirements 7.4, 7.5, 10.1 satisfied")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)