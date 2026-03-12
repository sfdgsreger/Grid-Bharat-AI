#!/usr/bin/env python3
"""
Simple Backend Runner with WebSocket Data Broadcasting
Fixes the WebSocket "no data" issue by generating and broadcasting sample data
"""

import asyncio
import json
import logging
import random
import time
import threading
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple FastAPI app with WebSocket
app = FastAPI(title="Bharat-Grid AI Backend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class SimpleConnectionManager:
    def __init__(self):
        self.active_connections = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast_json(self, data):
        if not self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Failed to send to WebSocket: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.active_connections.discard(conn)

manager = SimpleConnectionManager()

# Data generator class
class DataGenerator:
    def __init__(self):
        self.running = False
        self.thread = None
        
        # Sample nodes configuration
        self.nodes_config = [
            {"node_id": "hospital_001", "priority_tier": 1, "base_load": 150, "source_type": "Grid"},
            {"node_id": "hospital_002", "priority_tier": 1, "base_load": 200, "source_type": "Diesel"},
            {"node_id": "factory_001", "priority_tier": 2, "base_load": 300, "source_type": "Solar"},
            {"node_id": "factory_002", "priority_tier": 2, "base_load": 250, "source_type": "Grid"},
            {"node_id": "residential_001", "priority_tier": 3, "base_load": 75, "source_type": "Battery"},
            {"node_id": "residential_002", "priority_tier": 3, "base_load": 50, "source_type": "Solar"},
        ]
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._generate_data, daemon=True)
        self.thread.start()
        logger.info("✓ Data generation started")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("✓ Data generation stopped")
    
    def _generate_data(self):
        """Generate and broadcast allocation data continuously"""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while self.running:
            try:
                # Generate allocation results
                allocations = []
                timestamp = int(time.time() * 1000)
                
                for node in self.nodes_config:
                    # Add variation to load
                    variation = random.uniform(0.8, 1.2)
                    allocated_power = int(node["base_load"] * variation)
                    
                    # Determine action based on priority and random factors
                    if node["priority_tier"] == 1:
                        action = "maintain"  # Hospitals always maintained
                    elif node["priority_tier"] == 2:
                        action = random.choice(["maintain", "reduce"])
                    else:
                        action = random.choice(["maintain", "reduce", "cutoff"])
                    
                    # Adjust allocated power based on action
                    if action == "cutoff":
                        allocated_power = 0
                    elif action == "reduce":
                        allocated_power = int(allocated_power * 0.7)
                    
                    # Create source mix
                    source_mix = {node["source_type"].lower(): allocated_power}
                    
                    allocation = {
                        "node_id": node["node_id"],
                        "allocated_power": allocated_power,
                        "source_mix": source_mix,
                        "action": action,
                        "latency_ms": random.randint(3, 9),
                        "timestamp": timestamp
                    }
                    allocations.append(allocation)
                
                # Broadcast allocation data using the thread's event loop
                loop.run_until_complete(
                    manager.broadcast_json({
                        "type": "allocation_update",
                        "allocations": allocations,
                        "timestamp": timestamp,
                        "summary": {
                            "total_nodes": len(allocations),
                            "total_allocated": sum(a["allocated_power"] for a in allocations),
                            "avg_latency": sum(a["latency_ms"] for a in allocations) / len(allocations)
                        }
                    })
                )
                
                # Also broadcast latency metric
                loop.run_until_complete(
                    manager.broadcast_json({
                        "type": "latency",
                        "value": random.randint(3, 9),
                        "timestamp": timestamp
                    })
                )
                
                logger.info(f"Broadcasted data to {len(manager.active_connections)} connections")
                
                # Wait before next generation
                time.sleep(3)  # Generate every 3 seconds
                
            except Exception as e:
                logger.error(f"Error generating data: {e}")
                time.sleep(1)
        
        loop.close()

# Global data generator
data_generator = DataGenerator()

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "websocket_connections": len(manager.active_connections)
    }

@app.post("/simulate_failure")
async def simulate_grid_failure(request: dict):
    """Simulate grid failure"""
    failure_percentage = request.get("failure_percentage", 0.5)
    
    # Broadcast failure simulation
    await manager.broadcast_json({
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
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": time.time(),
            "message": "Connected to Bharat-Grid AI real-time updates",
            "total_connections": len(manager.active_connections)
        })
        
        # Keep connection alive
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                
                # Handle ping/pong
                if data.strip().lower() == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                    
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Start data generation on startup"""
    logger.info("🚀 Starting Bharat-Grid AI Backend")
    data_generator.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop data generation on shutdown"""
    logger.info("Shutting down Bharat-Grid AI Backend")
    data_generator.stop()

def main():
    """Run the server"""
    print("🚀 Bharat-Grid AI Simple Backend")
    print("=" * 40)
    print("Starting server with:")
    print("  • API Server: http://localhost:8000")
    print("  • WebSocket: ws://localhost:8000/ws/allocations")
    print("  • Health Check: http://localhost:8000/health")
    print("  • Auto data generation every 3 seconds")
    print()
    print("Frontend should connect to:")
    print("  VITE_API_URL=http://localhost:8000")
    print("  VITE_WS_URL=ws://localhost:8000")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 40)
    
    uvicorn.run(
        "simple_backend_runner:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()