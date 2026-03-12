"""
Monitoring dashboard endpoints for comprehensive system observability.

Provides endpoints for monitoring dashboards, alerting systems,
and operational visibility into the Bharat-Grid AI system.
"""

import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from monitoring import (
    performance_monitor,
    allocation_auditor, 
    health_monitor,
    api_logger
)


class MonitoringDashboardResponse(BaseModel):
    """Complete monitoring dashboard data"""
    timestamp: float
    system_overview: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    allocation_statistics: Dict[str, Any]
    recent_warnings: List[Dict[str, Any]]
    component_health: Dict[str, Any]


class AlertsResponse(BaseModel):
    """System alerts and warnings"""
    critical_alerts: List[Dict[str, Any]]
    warning_alerts: List[Dict[str, Any]]
    total_alerts: int
    timestamp: float


# Create router for monitoring dashboard
dashboard_router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@dashboard_router.get("/dashboard", response_model=MonitoringDashboardResponse)
async def get_monitoring_dashboard():
    """
    Get comprehensive monitoring dashboard data.
    
    Returns all monitoring data needed for operational dashboards
    including system health, performance metrics, and recent alerts.
    """
    try:
        # Gather all monitoring data
        system_health = health_monitor.get_system_health()
        performance_data = performance_monitor.get_performance_summary()
        allocation_data = allocation_auditor.get_allocation_stats()
        recent_warnings = performance_monitor.get_recent_warnings(10)
        
        dashboard_data = MonitoringDashboardResponse(
            timestamp=time.time(),
            system_overview={
                'overall_status': system_health['overall_status'],
                'uptime_hours': system_health['uptime_seconds'] / 3600,
                'total_components': len(system_health['components']),
                'unhealthy_components': len(system_health['unhealthy_components'])
            },
            performance_metrics=performance_data,
            allocation_statistics=allocation_data,
            recent_warnings=recent_warnings,
            component_health=system_health['components']
        )
        
        api_logger.info("Monitoring dashboard data retrieved")
        return dashboard_data
        
    except Exception as e:
        api_logger.error(f"Failed to get monitoring dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dashboard data failed: {str(e)}")


@dashboard_router.get("/alerts", response_model=AlertsResponse)
async def get_system_alerts():
    """Get current system alerts and warnings"""
    try:
        warnings = performance_monitor.get_recent_warnings(50)
        system_health = health_monitor.get_system_health()
        
        # Categorize alerts
        critical_alerts = []
        warning_alerts = []
        
        # Add performance warnings
        for warning in warnings:
            if warning['violation_severity'] == 'critical':
                critical_alerts.append({
                    'type': 'performance',
                    'severity': 'critical',
                    'message': f"{warning['operation']} latency {warning['actual_latency_ms']:.1f}ms exceeds target",
                    'timestamp': warning['timestamp']
                })
            else:
                warning_alerts.append({
                    'type': 'performance', 
                    'severity': warning['violation_severity'],
                    'message': f"{warning['operation']} latency {warning['actual_latency_ms']:.1f}ms exceeds target",
                    'timestamp': warning['timestamp']
                })
        
        # Add component health alerts
        for component, health in system_health['components'].items():
            if health['status'] == 'unhealthy':
                critical_alerts.append({
                    'type': 'component_health',
                    'severity': 'critical',
                    'message': f"Component {component} is unhealthy",
                    'timestamp': health['last_update']
                })
            elif health['status'] == 'degraded':
                warning_alerts.append({
                    'type': 'component_health',
                    'severity': 'warning', 
                    'message': f"Component {component} is degraded",
                    'timestamp': health['last_update']
                })
        
        return AlertsResponse(
            critical_alerts=critical_alerts,
            warning_alerts=warning_alerts,
            total_alerts=len(critical_alerts) + len(warning_alerts),
            timestamp=time.time()
        )
        
    except Exception as e:
        api_logger.error(f"Failed to get system alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Alerts retrieval failed: {str(e)}")


if __name__ == "__main__":
    # Test the monitoring endpoints
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(dashboard_router)
    
    uvicorn.run(app, host="0.0.0.0", port=8002)