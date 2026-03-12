#!/usr/bin/env python3
"""
Debug Backend - With extensive logging to see what's happening
"""

import asyncio
import json
import logging
import random
import time

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Bharat-Grid AI Debug Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections = set()
broadcaster_running = False

# Sample nodes
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
    logger.info(f"📡 Broadcasting to {len(active_connections)} connections")
    
    if not active_connections:
        logger.warning("⚠️  No active connections to broadcast to")
        return
    
    disconnected = set()
    success_count = 0
    
    for connection in active_connections:
        try:
            await connection.send_json(data)
            success_count += 1
            logger.debug(f"✓ Sent to connection")
        except Exception as e:
            logger.error(f"✗ Failed to send: {e}")
            disconnected.add(connection)
    
    # Remove disconnected
    for conn in disconnected:
        active_connections.discard(conn)
    
    logger.info(f"✓ Successfully broadcast to {success_count} connections")

def generate_allocation_data():
    """Generate allocation data"""
    logger.debug("Generating allocation data...")
    
    allocations = []
    timestamp = int(time.time() * 1000)
    
    for node in NODES_CONFIG:
        variation = random.uniform(0.8, 1.2)
        allocated_power = int(node["base_load"] * variation)
        
        if node["priority_tier"] == 1:
            action = "maintain"
        elif node["priority_tier"] == 2:
            action = random.choice(["maintain", "reduce"])
        else:
            action = random.choice(["maintain", "reduce", "cutoff"])
        
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
    
    logger.debug(f"Generated {len(allocations)} allocations")
    
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
    global broadcaster_running
    broadcaster_running = True
    
    logger.info("🚀 Data broadcaster started!")
    iteration = 0
    
    while broadcaster_running:
        try:
            iteration += 1
            logger.info(f"📊 Broadcast iteration #{iteration}")
            
            if active_connections:
                logger.info(f"👥 {len(active_connections)} active connections")
                
                # Generate and broadcast allocation data
                allocation_data = generate_allocation_data()
                await broadcast_json(allocation_data)
                
                # Broadcast latency metric
                await broadcast_json({
                    "type": "latency",
                    "value": random.randint(3, 9),
                    "timestamp": int(time.time() * 1000)
                })
                
                logger.info(f"✅ Iteration #{iteration} complete")
            else:
                logger.info("⏳ No connections yet, waiting...")
            
            await asyncio.sleep(3)  # Broadcast every 3 seconds
            
        except Exception as e:
            logger.error(f"❌ Error in broadcaster: {e}", exc_info=True)
            await asyncio.sleep(1)
    
    logger.info("🛑 Data broadcaster stopped")

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "websocket_connections": len(active_connections),
        "broadcaster_running": broadcaster_running
    }

@app.post("/simulate_failure")
async def simulate_grid_failure(request: dict):
    """Simulate grid failure"""
    failure_percentage = request.get("failure_percentage", 0.5)
    logger.info(f"🚨 Grid failure simulation: {failure_percentage*100}%")
    
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
    logger.info("🔌 New WebSocket connection attempt")
    
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"✅ WebSocket connected! Total connections: {len(active_connections)}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": time.time(),
            "message": "Connected to Bharat-Grid AI Debug Backend",
            "total_connections": len(active_connections),
            "broadcaster_running": broadcaster_running
        })
        logger.info("📤 Sent connection confirmation")
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                logger.debug(f"📥 Received from client: {data}")
                
                if data.strip().lower() == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                    logger.debug("📤 Sent pong")
                    
            except WebSocketDisconnect:
                logger.info("🔌 WebSocket disconnected normally")
                break
            except Exception as e:
                logger.error(f"❌ WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"❌ WebSocket connection error: {e}", exc_info=True)
    finally:
        active_connections.discard(websocket)
        logger.info(f"🔌 WebSocket removed. Remaining connections: {len(active_connections)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Start background broadcaster on startup"""
    logger.info("=" * 60)
    logger.info("🚀 STARTING BHARAT-GRID AI DEBUG BACKEND")
    logger.info("=" * 60)
    logger.info("📡 Starting data broadcaster...")
    
    # Start broadcaster as background task
    asyncio.create_task(data_broadcaster())
    
    logger.info("✅ Startup complete!")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global broadcaster_running
    broadcaster_running = False
    logger.info("🛑 Shutting down...")

def main():
    """Run the server"""
    print()
    print("=" * 60)
    print("🚀 Bharat-Grid AI DEBUG Backend")
    print("=" * 60)
    print("This version has extensive logging to debug issues")
    print()
    print("Server URLs:")
    print("  • API: http://localhost:8000")
    print("  • WebSocket: ws://localhost:8000/ws/allocations")
    print("  • Health: http://localhost:8000/health")
    print()
    print("Watch the logs below to see what's happening:")
    print("=" * 60)
    print()
    
    uvicorn.run(
        "debug_backend:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()