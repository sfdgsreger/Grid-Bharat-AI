#!/usr/bin/env python3
"""
Complete System Runner for Bharat-Grid AI
Runs backend with data generation and WebSocket streaming
"""

import asyncio
import logging
import signal
import sys
import time
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteSystemRunner:
    """Runs the complete backend system with data generation"""
    
    def __init__(self):
        self.running = False
        self.data_thread = None
        self.api_task = None
        
    def setup_directories(self):
        """Setup required directories and files"""
        logger.info("Setting up directories...")
        
        # Create data directories
        Path("./data").mkdir(exist_ok=True)
        Path("./data/streams").mkdir(exist_ok=True)
        Path("./data/vector_store").mkdir(exist_ok=True)
        
        # Create initial stream files
        nodes_file = Path("./data/streams/nodes_stream.csv")
        if not nodes_file.exists():
            with open(nodes_file, 'w') as f:
                f.write("node_id,current_load,priority_tier,source_type,status,lat,lng,timestamp\n")
        
        supply_file = Path("./data/streams/supply_events.jsonl")
        if not supply_file.exists():
            supply_file.touch()
            
        logger.info("✓ Directories setup complete")
    
    def generate_sample_data(self):
        """Generate continuous sample data for WebSocket streaming"""
        import json
        import random
        import time
        from datetime import datetime
        
        logger.info("Starting data generation thread...")
        
        # Sample nodes configuration
        nodes_config = [
            {"node_id": "hospital_001", "priority_tier": 1, "base_load": 150, "source_type": "Grid"},
            {"node_id": "hospital_002", "priority_tier": 1, "base_load": 200, "source_type": "Diesel"},
            {"node_id": "factory_001", "priority_tier": 2, "base_load": 300, "source_type": "Solar"},
            {"node_id": "factory_002", "priority_tier": 2, "base_load": 250, "source_type": "Grid"},
            {"node_id": "residential_001", "priority_tier": 3, "base_load": 75, "source_type": "Battery"},
            {"node_id": "residential_002", "priority_tier": 3, "base_load": 50, "source_type": "Solar"},
        ]
        
        while self.running:
            try:
                # Generate node data
                timestamp = int(time.time() * 1000)
                
                # Write to CSV file
                with open("./data/streams/nodes_stream.csv", "a") as f:
                    for node in nodes_config:
                        # Add some variation to load
                        variation = random.uniform(0.8, 1.2)
                        current_load = int(node["base_load"] * variation)
                        
                        # Random status
                        status = random.choice(["active", "active", "active", "degraded"])  # Mostly active
                        
                        # Random location around Delhi
                        lat = 28.6139 + random.uniform(-0.01, 0.01)
                        lng = 77.2090 + random.uniform(-0.01, 0.01)
                        
                        f.write(f"{node['node_id']},{current_load},{node['priority_tier']},{node['source_type']},{status},{lat},{lng},{timestamp}\n")
                
                # Generate supply events
                supply_event = {
                    "event_id": f"supply_{timestamp}",
                    "total_supply": random.randint(800, 1200),
                    "available_sources": {
                        "grid": random.randint(200, 400),
                        "solar": random.randint(150, 300),
                        "battery": random.randint(100, 200),
                        "diesel": random.randint(50, 150)
                    },
                    "timestamp": timestamp
                }
                
                with open("./data/streams/supply_events.jsonl", "a") as f:
                    f.write(json.dumps(supply_event) + "\n")
                
                logger.info(f"Generated data batch at {datetime.now().strftime('%H:%M:%S')}")
                
                # Wait before next generation
                time.sleep(5)  # Generate data every 5 seconds
                
            except Exception as e:
                logger.error(f"Error generating data: {e}")
                time.sleep(1)
    
    def start_data_generation(self):
        """Start data generation in background thread"""
        if self.data_thread and self.data_thread.is_alive():
            logger.info("Data generation already running")
            return
            
        self.running = True
        self.data_thread = threading.Thread(target=self.generate_sample_data, daemon=True)
        self.data_thread.start()
        logger.info("✓ Data generation started")
    
    def stop_data_generation(self):
        """Stop data generation"""
        self.running = False
        if self.data_thread:
            self.data_thread.join(timeout=2)
        logger.info("✓ Data generation stopped")
    
    async def start_api_server(self):
        """Start the FastAPI server"""
        import uvicorn
        
        logger.info("Starting FastAPI server...")
        
        config = uvicorn.Config(
            "api:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.running = False
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Run the complete system"""
        try:
            logger.info("🚀 Starting Bharat-Grid AI Complete System")
            logger.info("=" * 50)
            
            # Setup
            self.setup_signal_handlers()
            self.setup_directories()
            
            # Start data generation
            self.start_data_generation()
            
            # Display info
            self.display_info()
            
            # Start API server (this will block)
            await self.start_api_server()
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"System error: {e}")
        finally:
            self.stop_data_generation()
    
    def display_info(self):
        """Display system information"""
        print()
        print("🚀 Bharat-Grid AI System Ready!")
        print("=" * 50)
        print("Backend Services:")
        print("  • API Server: http://localhost:8000")
        print("  • API Docs: http://localhost:8000/docs")
        print("  • Health Check: http://localhost:8000/health")
        print()
        print("WebSocket Endpoints:")
        print("  • Allocations: ws://localhost:8000/ws/allocations")
        print()
        print("Data Generation:")
        print("  ✓ Continuous node data generation (every 5s)")
        print("  ✓ Supply event generation")
        print("  ✓ WebSocket broadcasting enabled")
        print()
        print("Frontend Setup:")
        print("  cd frontend")
        print("  npm run dev")
        print("  Open: http://localhost:3001")
        print()
        print("Features Available:")
        print("  ✓ Real-time dashboard")
        print("  ✓ Grid failure simulation (red/green button)")
        print("  ✓ Priority controller (drag & drop)")
        print("  ✓ Live WebSocket data")
        print()
        print("Press Ctrl+C to stop")
        print("=" * 50)
        print()

def main():
    """Main entry point"""
    runner = CompleteSystemRunner()
    asyncio.run(runner.run())

if __name__ == "__main__":
    main()