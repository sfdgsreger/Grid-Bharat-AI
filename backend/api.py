"""
FastAPI application for Bharat-Grid AI system.

This module provides the API gateway with WebSocket and REST endpoints
for real-time energy distribution optimization.
"""

import logging
import time
import asyncio
import json
from typing import Dict, Any, Optional, List, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import schemas for WebSocket data
from schemas import AllocationResult, LatencyMetric, EnergyNode, SupplyEvent

# Import system components
from rag_system import EnergyRAG, PredictionRequest
from pathway_engine import EnergyDataIngestionPipeline

# Import monitoring system
from monitoring import (
    performance_monitor, 
    allocation_auditor, 
    health_monitor,
    api_logger,
    performance_tracking,
    update_component_health,
    initialize_monitoring
)
from health_endpoints import health_router, startup_health_check
from monitoring_dashboard import dashboard_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Request/Response models
class GridFailureRequest(BaseModel):
    """Request model for grid failure simulation."""
    failure_percentage: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Percentage of grid failure (0.0 to 1.0)"
    )


class GridFailureResponse(BaseModel):
    """Response model for grid failure simulation."""
    status: str
    reduction: float
    timestamp: float


class PredictiveActionResponse(BaseModel):
    """Response model for predictive actions."""
    status: str
    message: str
    action: str
    timestamp: float


class InsightsResponse(BaseModel):
    """Response model for AI insights."""
    insights: str
    timestamp: float
    response_time_ms: float


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: float
    version: str


# Global state for system components
system_state = {
    "pathway_engine": None,
    "rag_system": None,
    "current_supply": 1000.0,  # Default supply in kW
}

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_count = 0
        
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_count += 1
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
            
    async def send_json_to_connection(self, data: Dict[str, Any], websocket: WebSocket):
        """Send JSON data to a specific WebSocket connection."""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Failed to send JSON to connection: {e}")
            self.disconnect(websocket)
            
    async def broadcast_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Broadcast JSON data to all connected WebSocket clients.
        
        Returns:
            Dictionary with broadcast statistics including latency metrics
        """
        if not self.active_connections:
            return {"sent": 0, "failed": 0, "latency_ms": 0}
            
        start_time = time.perf_counter()
        sent_count = 0
        failed_count = 0
        disconnected_connections = set()
        
        # Send to all active connections
        for connection in self.active_connections.copy():
            try:
                await connection.send_json(data)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                failed_count += 1
                disconnected_connections.add(connection)
        
        # Remove failed connections
        for connection in disconnected_connections:
            self.disconnect(connection)
        
        # Calculate broadcast latency
        broadcast_latency = (time.perf_counter() - start_time) * 1000
        
        # Log performance warning if target exceeded
        if broadcast_latency > 50.0:
            logger.warning(f"WebSocket broadcast latency {broadcast_latency:.2f}ms exceeds 50ms target")
        
        return {
            "sent": sent_count,
            "failed": failed_count,
            "latency_ms": broadcast_latency,
            "total_connections": len(self.active_connections)
        }
        
    async def broadcast_allocation_results(self, allocations: List[AllocationResult]) -> Dict[str, Any]:
        """
        Broadcast allocation results to all connected clients with latency tracking.
        
        Args:
            allocations: List of allocation results to broadcast
            
        Returns:
            Broadcast statistics including latency metrics
        """
        # Track WebSocket broadcast performance
        with performance_tracking('websocket', {'message_count': len(allocations)}):
            # Prepare allocation data for broadcast
            allocation_data = {
                "type": "allocation_results",
                "timestamp": time.time(),
                "allocations": [allocation.dict() for allocation in allocations],
                "summary": {
                    "total_nodes": len(allocations),
                    "total_allocated": sum(a.allocated_power for a in allocations),
                    "actions": {
                        "maintain": len([a for a in allocations if a.action == "maintain"]),
                        "reduce": len([a for a in allocations if a.action == "reduce"]),
                        "cutoff": len([a for a in allocations if a.action == "cutoff"])
                    }
                }
            }
            
            # Broadcast to all connections
            broadcast_stats = await self.broadcast_json(allocation_data)
            
            # Send latency metric as separate message
            if broadcast_stats["sent"] > 0:
                latency_data = LatencyMetric(value=broadcast_stats["latency_ms"]).dict()
                await self.broadcast_json(latency_data)
            
            api_logger.info(f"Broadcasted allocation results to {broadcast_stats['sent']} clients "
                           f"in {broadcast_stats['latency_ms']:.2f}ms")
            
            return broadcast_stats

# Global connection manager instance
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    api_logger.info("Starting Bharat-Grid AI API server...")
    
    try:
        # Initialize monitoring system
        initialize_monitoring()
        await startup_health_check()
        
        # Import system integrator
        from system_integration import start_integrated_system, stop_integrated_system
        
        # Start integrated system with all components connected
        api_logger.info("Starting integrated system...")
        if start_integrated_system():
            api_logger.info("✓ Integrated system started successfully")
            api_logger.info("  - All components connected and running")
            api_logger.info("  - Real-time data flow established")
            api_logger.info("  - WebSocket broadcasting active")
            
            # Update component health status
            update_component_health('api_gateway', 'healthy')
            update_component_health('pathway_engine', 'healthy')
            update_component_health('rag_system', 'healthy')
            update_component_health('websocket_manager', 'healthy')
            update_component_health('data_streams', 'healthy')
        else:
            api_logger.error("✗ Failed to start integrated system")
            update_component_health('api_gateway', 'degraded', error_count=1)
            # Continue with basic API functionality
        
    except Exception as e:
        api_logger.error(f"Failed to start integrated system: {e}", exc_info=True)
        update_component_health('api_gateway', 'degraded', error_count=1)
        # Continue without full integration for basic API functionality
    
    yield
    
    api_logger.info("Shutting down Bharat-Grid AI API server...")
    
    # Clean shutdown of integrated system
    try:
        from system_integration import stop_integrated_system
        stop_integrated_system()
        api_logger.info("✓ Integrated system stopped cleanly")
        update_component_health('api_gateway', 'unhealthy')
    except Exception as e:
        api_logger.error(f"Error during integrated system shutdown: {e}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title="Bharat-Grid AI API",
    description="Real-time energy distribution optimization system",
    version="1.0.0",
    lifespan=lifespan
)

# Include health monitoring endpoints
app.include_router(health_router)
app.include_router(dashboard_router)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request logging and error handling
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and track response times."""
    start_time = time.perf_counter()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        
        # Calculate response time
        process_time = (time.perf_counter() - start_time) * 1000
        
        # Log response
        logger.info(
            f"Response: {response.status_code} - "
            f"Time: {process_time:.2f}ms"
        )
        
        # Add response time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = (time.perf_counter() - start_time) * 1000
        logger.error(f"Request failed: {str(e)} - Time: {process_time:.2f}ms")
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": time.time()
        }
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version="1.0.0"
    )


# Grid failure simulation endpoint
@app.post("/simulate/grid-failure", response_model=GridFailureResponse)
async def simulate_grid_failure(request: GridFailureRequest):
    """
    Simulate grid failure by reducing total supply.
    
    This endpoint injects a supply event with reduced total supply
    to test the system's response to power shortages.
    """
    try:
        api_logger.info(f"Simulating grid failure: {request.failure_percentage * 100}%")
        
        # Validate input
        if not 0.0 <= request.failure_percentage <= 1.0:
            raise HTTPException(
                status_code=400,
                detail="failure_percentage must be between 0.0 and 1.0"
            )
        
        # Track simulation performance
        with performance_tracking('grid_simulation', {'failure_percentage': request.failure_percentage}):
            # Calculate new supply after failure
            original_supply = system_state["current_supply"]
            new_supply = original_supply * (1 - request.failure_percentage)
            
            # Update system state
            system_state["current_supply"] = new_supply
            
            # Inject supply event into Pathway stream if available
            pathway_engine = system_state.get("pathway_engine")
            if pathway_engine:
                try:
                    # Create supply event
                    supply_event = SupplyEvent(
                        event_id=f"grid_failure_{int(time.time())}",
                        total_supply=new_supply,
                        available_sources={
                            "grid": new_supply * 0.4,  # Reduced grid supply
                            "solar": new_supply * 0.3,
                            "battery": new_supply * 0.2,
                            "diesel": new_supply * 0.1
                        },
                        timestamp=time.time()
                    )
                    
                    # Inject the event and trigger allocation
                    allocations = pathway_engine.inject_supply_event(supply_event)
                    
                    if allocations:
                        # Broadcast allocation results to WebSocket clients
                        await manager.broadcast_allocation_results(allocations)
                        api_logger.info(f"Broadcasted {len(allocations)} allocation results")
                    
                except Exception as e:
                    api_logger.warning(f"Failed to inject supply event into Pathway: {e}")
                    update_component_health('pathway_engine', 'degraded', error_count=1)
            
            api_logger.info(
                f"Grid failure simulated: Supply reduced from {original_supply}kW "
                f"to {new_supply}kW ({request.failure_percentage * 100}% reduction)"
            )
        
        return GridFailureResponse(
            status="simulated",
            reduction=request.failure_percentage,
            timestamp=time.time()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Grid failure simulation failed: {str(e)}", exc_info=True)
        update_component_health('api_gateway', 'degraded', error_count=1)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to simulate grid failure: {str(e)}"
        )


# Predictive AI Simulation Endpoints
@app.post("/simulate/storm-warning", response_model=PredictiveActionResponse)
async def simulate_storm_warning():
    """
    Simulate Scenario B: Weather predicts a storm. 
    Pre-charges batteries to 100% and pre-fills water tanks before the grid fails.
    """
    try:
        api_logger.info("Triggering Storm Warning scenario")
        
        # Broadcast the action to UI
        await manager.broadcast_json({
            "type": "predictive_action",
            "action": "storm_warning",
            "message": "Weather API: Severe storm predicted. Pre-charging batteries and water tanks to 100%.",
            "timestamp": time.time()
        })
        
        return PredictiveActionResponse(
            status="success",
            message="Storm warning activated. Batteries and tanks are pre-charging.",
            action="storm_warning",
            timestamp=time.time()
        )
    except Exception as e:
        api_logger.error(f"Storm warning simulation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate/peak-load", response_model=PredictiveActionResponse)
async def simulate_peak_load():
    """
    Simulate Scenario A: AI predicts peak load.
    Reduces non-essential cooling and lighting to save power.
    """
    try:
        api_logger.info("Triggering Peak Load Forecast scenario")
        
        # Broadcast the action to UI
        await manager.broadcast_json({
            "type": "predictive_action",
            "action": "peak_load",
            "message": "Predictive AI: High peak load expected. Proactively reducing non-essential factory/residential loads to conserve power.",
            "timestamp": time.time()
        })
        
        # We could also temporarily reduce supply here to simulate the conservation if desired
        return PredictiveActionResponse(
            status="success",
            message="Peak load forecast activated. Non-essential loads are being reduced.",
            action="peak_load",
            timestamp=time.time()
        )
    except Exception as e:
        api_logger.error(f"Peak load simulation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))




# AI insights endpoint
@app.get("/insights", response_model=InsightsResponse)
async def get_insights():
    """
    Get AI-powered demand predictions and optimization insights.
    
    This endpoint queries the RAG system for demand forecasts
    and optimization recommendations.
    """
    try:
        api_logger.info("Generating AI insights...")
        
        # Track RAG system performance
        with performance_tracking('rag_prediction'):
            # Get RAG system from global state
            rag_system = system_state.get("rag_system")
            
            if not rag_system:
                # Fallback response if RAG system is not available
                insights = (
                    "RAG system not available. Based on current consumption patterns, "
                    "demand is expected to increase by 15% in the next hour. "
                    "Recommend increasing solar allocation and preparing battery reserves."
                )
                update_component_health('rag_system', 'unhealthy', error_count=1)
            else:
                try:
                    # Get current system context
                    pathway_engine = system_state.get("pathway_engine")
                    current_context = "Current grid status: "
                    
                    if pathway_engine:
                        allocation_state = pathway_engine.get_current_allocation_state()
                        current_context += (
                            f"Total supply: {system_state['current_supply']}kW, "
                            f"Active nodes: {allocation_state.get('total_nodes', 0)}, "
                            f"Total demand: {allocation_state.get('total_demand', 0)}kW"
                        )
                    else:
                        current_context += f"Total supply: {system_state['current_supply']}kW"
                    
                    # Create prediction request
                    prediction_request = PredictionRequest(
                        current_context=current_context,
                        time_horizon_hours=1,
                        include_optimization=True
                    )
                    
                    # Generate prediction using RAG system
                    prediction_response = rag_system.generate_prediction(prediction_request)
                    insights = prediction_response.prediction
                    
                    # Add optimization recommendations if available
                    if prediction_response.optimization_recommendations:
                        insights += "\n\nOptimization Recommendations:\n"
                        for i, rec in enumerate(prediction_response.optimization_recommendations, 1):
                            insights += f"{i}. {rec}\n"
                    
                    update_component_health('rag_system', 'healthy')
                    
                except Exception as e:
                    api_logger.warning(f"RAG system query failed: {e}")
                    update_component_health('rag_system', 'degraded', error_count=1)
                    # Fallback to standard response
                    insights = (
                        "AI prediction temporarily unavailable. Based on current patterns, "
                        "recommend monitoring supply levels and optimizing renewable sources."
                    )
        
        return InsightsResponse(
            insights=insights,
            timestamp=time.time(),
            response_time_ms=0  # Will be set by performance tracking
        )
        
    except Exception as e:
        api_logger.error(f"Failed to generate insights: {str(e)}", exc_info=True)
        update_component_health('rag_system', 'unhealthy', error_count=1)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insights: {str(e)}"
        )


# Integration status endpoint
@app.get("/integration/status")
async def get_integration_status():
    """Get system integration status for monitoring."""
    try:
        from system_integration import get_integration_status
        status = get_integration_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get integration status: {e}")
        return {
            "error": "Integration status unavailable",
            "message": str(e),
            "timestamp": time.time()
        }


# Integration test endpoint
@app.post("/integration/test")
async def run_integration_test():
    """Run integration test to validate all connections."""
    try:
        from system_integration import run_integration_test
        results = await run_integration_test()
        
        all_passed = all(results.values())
        
        return {
            "status": "passed" if all_passed else "failed",
            "results": results,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Bharat-Grid AI API",
        "version": "1.0.0",
        "description": "Real-time energy distribution optimization system",
        "endpoints": {
            "health": "/health",
            "websocket": "/ws/allocations",
            "simulate_failure": "/simulate/grid-failure",
            "insights": "/insights"
        },
        "websocket_connections": len(manager.active_connections),
        "timestamp": time.time()
    }


# WebSocket endpoint for real-time allocation updates
@app.websocket("/ws/allocations")
async def websocket_allocations(websocket: WebSocket):
    """
    WebSocket endpoint for real-time allocation updates.
    
    This endpoint provides:
    - Real-time allocation result broadcasts
    - Latency metrics for performance monitoring
    - Connection status updates
    - Automatic reconnection support
    """
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": time.time(),
            "message": "Connected to Bharat-Grid AI real-time updates",
            "total_connections": len(manager.active_connections)
        })
        
        # Send current system state if available
        if system_state.get("pathway_engine"):
            try:
                # Get current allocation state from pathway engine
                current_state = system_state["pathway_engine"].get_current_allocation_state()
                await websocket.send_json({
                    "type": "system_state",
                    "timestamp": time.time(),
                    "state": current_state
                })
            except Exception as e:
                logger.error(f"Failed to send current system state: {e}")
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (ping/pong, etc.)
                data = await websocket.receive_text()
                
                # Handle client messages
                try:
                    message = json.loads(data)
                    await handle_websocket_message(websocket, message)
                except json.JSONDecodeError:
                    # Handle plain text messages
                    if data.strip().lower() == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": time.time()
                        })
                    else:
                        logger.warning(f"Received unknown message: {data}")
                        
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected normally")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket)


async def handle_websocket_message(websocket: WebSocket, message: Dict[str, Any]):
    """
    Handle incoming WebSocket messages from clients.
    
    Args:
        websocket: The WebSocket connection
        message: Parsed JSON message from client
    """
    message_type = message.get("type", "unknown")
    
    if message_type == "ping":
        # Respond to ping with pong
        await websocket.send_json({
            "type": "pong",
            "timestamp": time.time()
        })
        
    elif message_type == "request_state":
        # Send current system state
        if system_state.get("pathway_engine"):
            try:
                current_state = system_state["pathway_engine"].get_current_allocation_state()
                await websocket.send_json({
                    "type": "system_state",
                    "timestamp": time.time(),
                    "state": current_state
                })
            except Exception as e:
                logger.error(f"Failed to send system state: {e}")
                await websocket.send_json({
                    "type": "error",
                    "timestamp": time.time(),
                    "message": "Failed to retrieve system state"
                })
        else:
            await websocket.send_json({
                "type": "system_state",
                "timestamp": time.time(),
                "state": {"message": "System not initialized"}
            })
            
    elif message_type == "subscribe":
        # Handle subscription requests (future enhancement)
        await websocket.send_json({
            "type": "subscription_confirmed",
            "timestamp": time.time(),
            "message": "Subscribed to all allocation updates"
        })
        
    else:
        logger.warning(f"Unknown WebSocket message type: {message_type}")
        await websocket.send_json({
            "type": "error",
            "timestamp": time.time(),
            "message": f"Unknown message type: {message_type}"
        })


# Function to broadcast allocation results (called by pathway engine)
async def broadcast_allocation_results(allocations: List[AllocationResult]) -> Dict[str, Any]:
    """
    Broadcast allocation results to all connected WebSocket clients.
    
    This function is called by the pathway engine when new allocation
    results are available.
    
    Args:
        allocations: List of allocation results to broadcast
        
    Returns:
        Broadcast statistics including latency metrics
    """
    return await manager.broadcast_allocation_results(allocations)


# Function to get WebSocket connection statistics
@app.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "active_connections": len(manager.active_connections),
        "total_connections_created": manager.connection_count,
        "timestamp": time.time()
    }


if __name__ == "__main__":
    # Development server configuration
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )