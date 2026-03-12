"""
Enhanced health check endpoints for Bharat-Grid AI system monitoring.

Provides comprehensive health checks for all system components
with detailed status information and monitoring metrics.
"""

import time
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from monitoring import (
    health_monitor, 
    performance_monitor, 
    allocation_auditor,
    api_logger
)


class ComponentHealth(BaseModel):
    """Health status for a single component"""
    component: str
    status: str  # healthy, degraded, unhealthy, stale, unknown
    message: str
    last_update: float
    age_seconds: float
    error_count: int
    warning_count: int
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    resource_usage: Dict[str, float] = Field(default_factory=dict)


class SystemHealthResponse(BaseModel):
    """Complete system health response"""
    overall_status: str
    uptime_seconds: float
    components: Dict[str, ComponentHealth]
    unhealthy_components: list
    timestamp: float


class HealthSummaryResponse(BaseModel):
    """Health summary for monitoring dashboards"""
    overall_status: str
    total_components: int
    status_counts: Dict[str, int]
    uptime_hours: float
    last_check: float


class PerformanceHealthResponse(BaseModel):
    """Performance health metrics"""
    uptime_seconds: float
    total_warnings: int
    warning_counts: Dict[str, int]
    operations: Dict[str, Dict[str, Any]]


class AllocationHealthResponse(BaseModel):
    """Allocation system health metrics"""
    total_allocations: int
    allocation_efficiency: float
    avg_processing_time_ms: float
    decision_counts: Dict[str, int]
    tier_statistics: Dict[str, Dict[str, Any]]


class DetailedHealthResponse(BaseModel):
    """Comprehensive health response with all metrics"""
    system: SystemHealthResponse
    performance: PerformanceHealthResponse
    allocations: AllocationHealthResponse
    timestamp: float


# Create router for health endpoints
health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("/", response_model=SystemHealthResponse)
async def get_system_health():
    """
    Get overall system health status.
    
    Returns comprehensive health information for all monitored components
    including status, error counts, and performance metrics.
    """
    try:
        health_data = health_monitor.get_system_health()
        
        # Convert to Pydantic models
        components = {}
        for name, health in health_data['components'].items():
            components[name] = ComponentHealth(**health)
        
        response = SystemHealthResponse(
            overall_status=health_data['overall_status'],
            uptime_seconds=health_data['uptime_seconds'],
            components=components,
            unhealthy_components=health_data['unhealthy_components'],
            timestamp=health_data['timestamp']
        )
        
        api_logger.info("System health check completed", {
            'overall_status': response.overall_status,
            'component_count': len(components),
            'unhealthy_count': len(response.unhealthy_components)
        })
        
        return response
        
    except Exception as e:
        api_logger.error("Failed to get system health", {'error': str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@health_router.get("/summary", response_model=HealthSummaryResponse)
async def get_health_summary():
    """
    Get health summary for monitoring dashboards.
    
    Returns a condensed view of system health suitable for
    monitoring dashboards and alerting systems.
    """
    try:
        summary = health_monitor.get_health_summary()
        return HealthSummaryResponse(**summary)
        
    except Exception as e:
        api_logger.error("Failed to get health summary", {'error': str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Health summary failed: {str(e)}")


@health_router.get("/component/{component_name}")
async def get_component_health(component_name: str):
    """
    Get detailed health information for a specific component.
    
    Args:
        component_name: Name of the component to check
        
    Returns:
        Detailed health information for the specified component
    """
    try:
        health = health_monitor.check_component_health(component_name)
        
        if health['status'] == 'unknown':
            raise HTTPException(
                status_code=404, 
                detail=f"Component '{component_name}' not found or never reported health"
            )
        
        return ComponentHealth(**health)
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to get health for component {component_name}", 
                        {'error': str(e), 'component': component_name}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Component health check failed: {str(e)}")


@health_router.get("/performance", response_model=PerformanceHealthResponse)
async def get_performance_health():
    """
    Get performance health metrics.
    
    Returns performance monitoring data including latency violations,
    warning counts, and operation statistics.
    """
    try:
        performance_data = performance_monitor.get_performance_summary()
        return PerformanceHealthResponse(**performance_data)
        
    except Exception as e:
        api_logger.error("Failed to get performance health", {'error': str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Performance health check failed: {str(e)}")


@health_router.get("/allocations", response_model=AllocationHealthResponse)
async def get_allocation_health():
    """
    Get allocation system health metrics.
    
    Returns allocation statistics including efficiency metrics,
    processing times, and decision breakdowns.
    """
    try:
        allocation_data = allocation_auditor.get_allocation_stats()
        
        # Handle case where no allocations have been made yet
        if allocation_data.get('total_allocations', 0) == 0:
            return AllocationHealthResponse(
                total_allocations=0,
                allocation_efficiency=0.0,
                avg_processing_time_ms=0.0,
                decision_counts={},
                tier_statistics={}
            )
        
        return AllocationHealthResponse(**allocation_data)
        
    except Exception as e:
        api_logger.error("Failed to get allocation health", {'error': str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Allocation health check failed: {str(e)}")


@health_router.get("/detailed", response_model=DetailedHealthResponse)
async def get_detailed_health():
    """
    Get comprehensive health information for all subsystems.
    
    Returns detailed health data including system status, performance metrics,
    and allocation statistics in a single response.
    """
    try:
        # Gather all health data
        system_health = await get_system_health()
        performance_health = await get_performance_health()
        allocation_health = await get_allocation_health()
        
        response = DetailedHealthResponse(
            system=system_health,
            performance=performance_health,
            allocations=allocation_health,
            timestamp=time.time()
        )
        
        api_logger.info("Detailed health check completed", {
            'system_status': system_health.overall_status,
            'performance_warnings': performance_health.total_warnings,
            'total_allocations': allocation_health.total_allocations
        })
        
        return response
        
    except Exception as e:
        api_logger.error("Failed to get detailed health", {'error': str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Detailed health check failed: {str(e)}")


@health_router.get("/warnings")
async def get_recent_warnings(limit: int = 20):
    """
    Get recent performance warnings.
    
    Args:
        limit: Maximum number of warnings to return (default: 20)
        
    Returns:
        List of recent performance warnings with details
    """
    try:
        if limit > 100:
            limit = 100  # Cap at 100 for performance
        
        warnings = performance_monitor.get_recent_warnings(limit)
        
        api_logger.debug(f"Retrieved {len(warnings)} recent warnings")
        
        return {
            'warnings': warnings,
            'count': len(warnings),
            'limit': limit,
            'timestamp': time.time()
        }
        
    except Exception as e:
        api_logger.error("Failed to get recent warnings", {'error': str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get warnings: {str(e)}")


@health_router.get("/allocations/recent")
async def get_recent_allocations(limit: int = 50):
    """
    Get recent allocation decisions for audit purposes.
    
    Args:
        limit: Maximum number of allocations to return (default: 50)
        
    Returns:
        List of recent allocation decisions with full audit trail
    """
    try:
        if limit > 200:
            limit = 200  # Cap at 200 for performance
        
        allocations = allocation_auditor.get_recent_allocations(limit)
        
        api_logger.debug(f"Retrieved {len(allocations)} recent allocations")
        
        return {
            'allocations': allocations,
            'count': len(allocations),
            'limit': limit,
            'timestamp': time.time()
        }
        
    except Exception as e:
        api_logger.error("Failed to get recent allocations", {'error': str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get allocations: {str(e)}")


@health_router.get("/allocations/search")
async def search_allocations(
    node_id: Optional[str] = None,
    action: Optional[str] = None,
    priority_tier: Optional[int] = None,
    time_range_hours: Optional[int] = None
):
    """
    Search allocation history with filters.
    
    Args:
        node_id: Filter by specific node ID
        action: Filter by allocation action (maintain, reduce, cutoff)
        priority_tier: Filter by priority tier (1, 2, 3)
        time_range_hours: Filter by time range in hours
        
    Returns:
        Filtered list of allocation decisions
    """
    try:
        # Validate inputs
        if action and action not in ['maintain', 'reduce', 'cutoff']:
            raise HTTPException(status_code=400, detail="Invalid action. Must be: maintain, reduce, or cutoff")
        
        if priority_tier and priority_tier not in [1, 2, 3]:
            raise HTTPException(status_code=400, detail="Invalid priority_tier. Must be: 1, 2, or 3")
        
        if time_range_hours and (time_range_hours < 1 or time_range_hours > 168):  # Max 1 week
            raise HTTPException(status_code=400, detail="Invalid time_range_hours. Must be between 1 and 168")
        
        allocations = allocation_auditor.search_allocations(
            node_id=node_id,
            action=action,
            priority_tier=priority_tier,
            time_range_hours=time_range_hours
        )
        
        api_logger.info("Allocation search completed", {
            'filters': {
                'node_id': node_id,
                'action': action,
                'priority_tier': priority_tier,
                'time_range_hours': time_range_hours
            },
            'results_count': len(allocations)
        })
        
        return {
            'allocations': allocations,
            'count': len(allocations),
            'filters': {
                'node_id': node_id,
                'action': action,
                'priority_tier': priority_tier,
                'time_range_hours': time_range_hours
            },
            'timestamp': time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error("Failed to search allocations", {'error': str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Allocation search failed: {str(e)}")


@health_router.post("/component/{component_name}/update")
async def update_component_health_endpoint(
    component_name: str,
    status: str,
    error_count: int = 0,
    warning_count: int = 0,
    performance_metrics: Optional[Dict[str, float]] = None,
    resource_usage: Optional[Dict[str, float]] = None
):
    """
    Update health status for a component (for internal use).
    
    Args:
        component_name: Name of the component
        status: Health status (healthy, degraded, unhealthy)
        error_count: Number of errors
        warning_count: Number of warnings
        performance_metrics: Performance metrics dictionary
        resource_usage: Resource usage metrics dictionary
        
    Returns:
        Confirmation of health update
    """
    try:
        # Validate status
        valid_statuses = ['healthy', 'degraded', 'unhealthy']
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        health_monitor.update_component_health(
            component=component_name,
            status=status,
            error_count=error_count,
            warning_count=warning_count,
            performance_metrics=performance_metrics or {},
            resource_usage=resource_usage or {}
        )
        
        api_logger.info(f"Updated health for component {component_name}", {
            'component': component_name,
            'status': status,
            'error_count': error_count,
            'warning_count': warning_count
        })
        
        return {
            'message': f"Health updated for component {component_name}",
            'component': component_name,
            'status': status,
            'timestamp': time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to update health for component {component_name}", 
                        {'error': str(e), 'component': component_name}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Health update failed: {str(e)}")


# Health check dependency for other endpoints
async def check_system_health_dependency():
    """Dependency to check if system is healthy enough to serve requests"""
    try:
        health_data = health_monitor.get_system_health()
        
        if health_data['overall_status'] == 'unhealthy':
            raise HTTPException(
                status_code=503,
                detail="System is unhealthy and cannot serve requests"
            )
        
        return health_data
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error("Health dependency check failed", {'error': str(e)})
        raise HTTPException(status_code=503, detail="Health check failed")


# Startup health check
async def startup_health_check():
    """Perform health check during application startup"""
    try:
        api_logger.info("Performing startup health check...")
        
        # Initialize component health
        from monitoring import initialize_monitoring
        initialize_monitoring()
        
        # Set initial health status for core components
        health_monitor.update_component_health('api_gateway', 'healthy')
        
        api_logger.info("Startup health check completed successfully")
        
    except Exception as e:
        api_logger.error("Startup health check failed", {'error': str(e)}, exc_info=True)
        raise


if __name__ == "__main__":
    # Test the health endpoints
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(health_router)
    
    @app.on_event("startup")
    async def startup():
        await startup_health_check()
    
    uvicorn.run(app, host="0.0.0.0", port=8001)