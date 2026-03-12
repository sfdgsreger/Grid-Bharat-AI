#!/usr/bin/env python3
"""
Ultra Simple Backend - No threading, pure asyncio
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Bharat-Grid AI Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections = set()

# Sample nodes configuration
NODES_CONFIG = [
    {"node_id": "hospital_001", "priority_tier": 1, "base_load": 150, "source_type": "Grid"},
    {"node_id": "hospital_002", "priority_tier": 1, "base_load": 200, "source_type": "Diesel"},
    {"node_id": "factory_001", "priority_tier": 2, "base_load": 300, "source_type": "Solar"},
    {"node_id": "factory_002", "priority_tier": 2, "base_load": 250, "source_type": "Grid"},
    {"node_id": "residential_001", "priority_tier": 3, "base_load": 75, "source_type": "Battery"},
    {"node_id": "residential_002", "priority_tier": 3, "base_load": 50, "source_type": "Solar"},
]

async def broadcast_json(data):
    """Broadcast JSON data to all connected WebSockets"""
    if not active_connections:
        return
    
    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except Exception as e:
            logger.error(f"Failed to send to WebSocket: {e}")
            disconnected.add(connection)
    
    # Remove disconnected connections
    for conn in disconnected:
        active_connections.discard(conn)

def generate_allocation_data():
    """Generate allocation data"""
    allocations = []
    timestamp = int(time.time() * 1000)
    
    for node in NODES_CONFIG:
        # Add variation to load
        variation = random.uniform(0.8, 1.2)
        allocated_power = int(node["base_load"] * variation)
        
        # Determine action based on priority
        if node["priority_tier"] == 1:
            action = "maintain"
        elif node["priority_tier"] == 2:
            action = random.choice(["maintain", "reduce"])
        else:
            action = random.choice(["maintain", "reduce", "cutoff"])
        
        # Adjust power based on action
        if action == "cutoff":
            allocated_power = 0
        elif action == "reduce":
            allocated_power = int(allocated_power * 0.7)
        
        allocation = {
            "node_id": node["node_id"],
            "allocated_power": allocated_power,
            "source_mix": {node["source_type"].lower(): allocated_power},
            "action": action,
            "latency_ms": random.randint(3, 9),
            "timestamp": timestamp
        }
        allocations.append(allocation)
    
    return {
        "type": "allocation_update",
        "allocations": allocations,
        "timestamp": timestamp,
        "summary": {
            "total_nodes": len(allocations),
            "total_allocated": sum(a["allocated_power"] for a in allocations),
            "avg_latency": sum(a["latency_ms"] for a in allocations) / len(allocations)
        }
    }

async def data_broadcaster():
    """Background task to broadcast data periodically"""
    while True:
        try:
            if active_connections:
                # Generate and broadcast allocation data
                allocation_data = generate_allocation_data()
                await broadcast_json(allocation_data)
                
                # Broadcast latency metric
                await broadcast_json({
                    "type": "latency",
                    "value": random.randint(3, 9),
                    "timestamp": int(time.time() * 1000)
                })
                
                logger.info(f"Broadcasted data to {len(active_connections)} connections")
            
            await asyncio.sleep(3)  # Broadcast every 3 seconds
            
        except Exception as e:
            logger.error(f"Error in broadcaster: {e}")
            await asyncio.sleep(1)

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "websocket_connections": len(active_connections)
    }

@app.post("/simulate_failure")
async def simulate_grid_failure(request: dict):
    """Simulate grid failure"""
    failure_percentage = request.get("failure_percentage", 0.5)
    
    await broadcast_json({
        "type": "grid_failure",
        "failure_percentage": failure_percentage,
        "timestamp": time.time(),
        "message": f"Grid failure simulation: {failure_percentage*100}% capacity reduction"
    })
    
    return {
        "status": "success",
        "failure_percentage": failure_percentage,
        "timestamp": time.time()
    }

@app.get("/insights")
async def get_insights():
    """Get AI insights"""
    insights = [
        "Grid operating at optimal efficiency",
        "Hospital loads prioritized during peak demand",
        "Solar generation exceeding forecast by 15%",
        "Recommended: Increase battery storage capacity",
        "Peak demand expected in next 2 hours"
    ]
    
    return {
        "insights": random.choice(insights),
        "timestamp": time.time(),
        "response_time_ms": random.randint(800, 2000)
    }

# WebSocket endpoint
@app.websocket("/ws/allocations")
async def websocket_allocations(websocket: WebSocket):
    """WebSocket endpoint for real-time allocation updates"""
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket connected. Total: {len(active_connections)}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": time.time(),
            "message": "Connected to Bharat-Grid AI",
            "total_connections": len(active_connections)
        })
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                if data.strip().lower() == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(active_connections)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Start background broadcaster on startup"""
    logger.info("🚀 Starting Bharat-Grid AI Backend")
    asyncio.create_task(data_broadcaster())

def main():
    """Run the server"""
    print("🚀 Bharat-Grid AI Ultra Simple Backend")
    print("=" * 50)
    print("Server URLs:")
    print("  • API: http://localhost:8000")
    print("  • WebSocket: ws://localhost:8000/ws/allocations")
    print("  • Health: http://localhost:8000/health")
    print("  • Docs: http://localhost:8000/docs")
    print()
    print("Features:")
    print("  ✓ Auto data generation every 3 seconds")
    print("  ✓ WebSocket broadcasting")
    print("  ✓ Grid failure simulation")
    print("  ✓ No threading - pure asyncio")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    uvicorn.run(
        "ultra_simple_backend:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()