#!/usr/bin/env python3
"""
Startup script for the complete integrated Bharat-Grid AI system.

This script:
1. Initializes all system components
2. Sets up development data streams
3. Starts the FastAPI server with full integration
4. Provides system status monitoring

Usage:
    python start_integrated_system.py
"""

import asyncio
import logging
import signal
import sys
import time
from pathlib import Path

import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_data_directory():
    """Ensure data directory and required files exist"""
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    # Create required subdirectories
    (data_dir / "vector_store").mkdir(exist_ok=True)
    
    # Create empty stream files if they don't exist
    nodes_file = data_dir / "nodes_stream.csv"
    if not nodes_file.exists():
        with open(nodes_file, 'w') as f:
            f.write("node_id,current_load,priority_tier,source_type,status,lat,lng,timestamp\n")
    
    supply_file = data_dir / "supply_stream.jsonl"
    if not supply_file.exists():
        supply_file.touch()
    
    logger.info("✓ Data directory structure ready")


def check_dependencies():
    """Check that all required dependencies are available"""
    try:
        import pathway_engine
        import rag_system
        import api
        import system_integration
        import dev_stream_manager
        logger.info("✓ All required modules available")
        return True
    except ImportError as e:
        logger.error(f"✗ Missing required module: {e}")
        return False


def initialize_sample_data():
    """Initialize sample data for immediate demonstration"""
    try:
        from rag_system import EnergyRAG, create_sample_patterns
        
        # Initialize RAG system with sample data
        rag = EnergyRAG(vector_store_path="./data/vector_store")
        
        # Check if we already have patterns
        stats = rag.get_store_stats()
        if stats.get("total_patterns", 0) == 0:
            logger.info("Initializing sample consumption patterns...")
            sample_patterns = create_sample_patterns()
            added_count = rag.add_patterns_batch(sample_patterns)
            logger.info(f"✓ Added {added_count} sample patterns to RAG system")
        else:
            logger.info(f"✓ RAG system already has {stats['total_patterns']} patterns")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize sample data: {e}")
        return False


def start_development_streams():
    """Start development data streams for continuous operation"""
    try:
        from dev_stream_manager import DevStreamManager
        
        stream_manager = DevStreamManager("./data")
        stream_manager.start_streams()
        
        logger.info("✓ Development data streams started")
        return stream_manager
        
    except Exception as e:
        logger.error(f"Failed to start development streams: {e}")
        return None


class IntegratedSystemManager:
    """Manages the complete integrated system lifecycle"""
    
    def __init__(self):
        self.stream_manager = None
        self.server_task = None
        self.shutdown_event = asyncio.Event()
    
    async def startup(self):
        """Start all system components"""
        logger.info("Starting Bharat-Grid AI Integrated System...")
        logger.info("=" * 50)
        
        # Setup data directory
        setup_data_directory()
        
        # Check dependencies
        if not check_dependencies():
            logger.error("✗ Dependency check failed")
            return False
        
        # Initialize sample data
        if not initialize_sample_data():
            logger.warning("⚠ Sample data initialization failed, continuing...")
        
        # Start development streams
        self.stream_manager = start_development_streams()
        if not self.stream_manager:
            logger.warning("⚠ Development streams failed to start, continuing...")
        
        logger.info("✓ System initialization complete")
        logger.info("")
        logger.info("Starting FastAPI server with full integration...")
        
        return True
    
    async def shutdown(self):
        """Shutdown all system components"""
        logger.info("Shutting down integrated system...")
        
        # Stop development streams
        if self.stream_manager:
            try:
                self.stream_manager.stop_streams()
                logger.info("✓ Development streams stopped")
            except Exception as e:
                logger.error(f"Error stopping streams: {e}")
        
        # Stop system integration
        try:
            from system_integration import stop_integrated_system
            stop_integrated_system()
            logger.info("✓ System integration stopped")
        except Exception as e:
            logger.error(f"Error stopping integration: {e}")
        
        logger.info("✓ Shutdown complete")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run_server(self):
        """Run the FastAPI server"""
        config = uvicorn.Config(
            "api:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False  # Disable reload for integrated system
        )
        
        server = uvicorn.Server(config)
        
        # Start server in background
        server_task = asyncio.create_task(server.serve())
        
        # Wait for shutdown signal
        await self.shutdown_event.wait()
        
        # Graceful shutdown
        logger.info("Stopping server...")
        server.should_exit = True
        await server_task
    
    async def run(self):
        """Run the complete integrated system"""
        try:
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Startup
            if not await self.startup():
                logger.error("✗ System startup failed")
                return False
            
            # Display startup information
            self.display_startup_info()
            
            # Run server
            await self.run_server()
            
            return True
            
        except Exception as e:
            logger.error(f"System error: {e}")
            return False
        finally:
            await self.shutdown()
    
    def display_startup_info(self):
        """Display system startup information"""
        print()
        print("🚀 Bharat-Grid AI System Ready!")
        print("=" * 50)
        print("Server URLs:")
        print("  • API Server: http://localhost:8000")
        print("  • API Documentation: http://localhost:8000/docs")
        print("  • Health Check: http://localhost:8000/health")
        print("  • Integration Status: http://localhost:8000/integration/status")
        print()
        print("WebSocket Endpoints:")
        print("  • Real-time Allocations: ws://localhost:8000/ws/allocations")
        print()
        print("Key Features:")
        print("  ✓ Real-time energy allocation processing")
        print("  ✓ WebSocket broadcasting to dashboard")
        print("  ✓ AI-powered demand prediction (RAG system)")
        print("  ✓ Grid failure simulation")
        print("  ✓ Development data streams")
        print()
        print("Frontend Development:")
        print("  cd frontend && npm run dev")
        print("  Dashboard will be available at: http://localhost:5173")
        print()
        print("Press Ctrl+C to stop the system")
        print("=" * 50)
        print()


async def main():
    """Main entry point"""
    manager = IntegratedSystemManager()
    success = await manager.run()
    
    if success:
        logger.info("System shutdown complete")
        sys.exit(0)
    else:
        logger.error("System failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)