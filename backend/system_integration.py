#!/usr/bin/env python3
"""
System Integration Module for Bharat-Grid AI

This module connects all system components:
- Pathway engine to FastAPI server
- React dashboard to WebSocket endpoints  
- RAG system with API endpoints
- Development data streams for continuous operation

Requirements: 4.1, 8.1, 8.3, 8.5
"""

import asyncio
import logging
import time
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import system components
from api import app, manager, system_state
from pathway_engine import EnergyDataIngestionPipeline
from rag_system import EnergyRAG
from schemas import AllocationResult, EnergyNode, SupplyEvent
from dev_stream_manager import DevStreamManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemIntegrator:
    """
    Integrates all Bharat-Grid AI system components for end-to-end functionality.
    
    Handles:
    - Pathway engine connection to FastAPI
    - WebSocket broadcasting of allocation results
    - RAG system integration with API endpoints
    - Development data stream management
    """
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.pathway_engine: Optional[EnergyDataIngestionPipeline] = None
        self.rag_system: Optional[EnergyRAG] = None
        self.dev_stream_manager: Optional[DevStreamManager] = None
        self.is_running = False
        self.integration_thread: Optional[threading.Thread] = None
        
        logger.info("SystemIntegrator initialized")
    
    def initialize_components(self) -> bool:
        """Initialize all system components with proper connections"""
        try:
            logger.info("Initializing system components...")
            
            # Initialize Pathway engine
            self.pathway_engine = EnergyDataIngestionPipeline(str(self.data_dir))
            
            # Set up allocation callback to broadcast via WebSocket
            self.pathway_engine.add_allocation_callback(self._broadcast_allocations)
            
            # Initialize RAG system
            self.rag_system = EnergyRAG(
                vector_store_path=str(self.data_dir / "vector_store"),
                enable_pathway_llm=False  # Use standard for faster response
            )
            
            # Initialize development stream manager
            self.dev_stream_manager = DevStreamManager(str(self.data_dir))
            
            # Update global system state for API access
            system_state["pathway_engine"] = self.pathway_engine
            system_state["rag_system"] = self.rag_system
            
            logger.info("✓ All system components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            return False
    
    async def _broadcast_allocations(self, allocations: List[AllocationResult]):
        """
        Callback to broadcast allocation results via WebSocket.
        
        This connects the Pathway engine output to the FastAPI WebSocket system.
        """
        try:
            # Add timestamp to allocations for frontend display
            for allocation in allocations:
                allocation.timestamp = time.time()
            
            # Broadcast to all connected WebSocket clients
            broadcast_stats = await manager.broadcast_allocation_results(allocations)
            
            logger.info(f"Broadcasted {len(allocations)} allocations to "
                       f"{broadcast_stats['sent']} clients in "
                       f"{broadcast_stats['latency_ms']:.2f}ms")
            
        except Exception as e:
            logger.error(f"Failed to broadcast allocations: {e}")
    
    def start_data_streams(self) -> bool:
        """Start development data streams for continuous operation"""
        try:
            if not self.dev_stream_manager:
                logger.error("DevStreamManager not initialized")
                return False
            
            logger.info("Starting development data streams...")
            
            # Start the development streams
            self.dev_stream_manager.start(background=True)
            
            # Start the pathway pipeline
            if self.pathway_engine:
                self.pathway_engine.start_pipeline()
                self.pathway_engine.enable_real_time_allocation(True)
            
            logger.info("✓ Development data streams started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start data streams: {e}")
            return False
    
    def stop_data_streams(self):
        """Stop all data streams and processing"""
        try:
            logger.info("Stopping data streams...")
            
            if self.dev_stream_manager:
                self.dev_stream_manager.stop()
            
            if self.pathway_engine:
                self.pathway_engine.stop_pipeline()
            
            logger.info("✓ Data streams stopped")
            
        except Exception as e:
            logger.error(f"Error stopping data streams: {e}")
    
    def run_integration_loop(self):
        """
        Main integration loop that processes stream data and triggers allocations.
        
        This runs in a separate thread to avoid blocking the FastAPI server.
        """
        logger.info("Starting system integration loop...")
        
        while self.is_running:
            try:
                if self.pathway_engine:
                    # Process available stream data
                    stats = self.pathway_engine.process_stream_data()
                    
                    if stats['total_processed'] > 0:
                        logger.debug(f"Processed {stats['total_processed']} data items")
                    
                    if stats['allocation_triggered']:
                        logger.info("Real-time allocation triggered by supply event")
                
                # Small delay to prevent busy waiting
                time.sleep(0.01)  # 10ms delay for real-time processing
                
            except Exception as e:
                logger.error(f"Error in integration loop: {e}")
                time.sleep(1)  # Longer delay on error
        
        logger.info("Integration loop stopped")
    
    def start_integration(self) -> bool:
        """Start the complete system integration"""
        try:
            logger.info("Starting Bharat-Grid AI system integration...")
            
            # Initialize all components
            if not self.initialize_components():
                return False
            
            # Start data streams
            if not self.start_data_streams():
                return False
            
            # Start integration loop in separate thread
            self.is_running = True
            self.integration_thread = threading.Thread(
                target=self.run_integration_loop,
                daemon=True
            )
            self.integration_thread.start()
            
            logger.info("✓ System integration started successfully")
            logger.info("  - Pathway engine connected to FastAPI")
            logger.info("  - WebSocket broadcasting enabled")
            logger.info("  - RAG system integrated with API")
            logger.info("  - Development streams providing continuous data")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start system integration: {e}")
            return False
    
    def stop_integration(self):
        """Stop the complete system integration"""
        try:
            logger.info("Stopping system integration...")
            
            # Stop integration loop
            self.is_running = False
            if self.integration_thread:
                self.integration_thread.join(timeout=5)
            
            # Stop data streams
            self.stop_data_streams()
            
            logger.info("✓ System integration stopped")
            
        except Exception as e:
            logger.error(f"Error stopping integration: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "integration_running": self.is_running,
            "components": {
                "pathway_engine": self.pathway_engine is not None,
                "rag_system": self.rag_system is not None,
                "dev_stream_manager": self.dev_stream_manager is not None
            },
            "websocket_connections": len(manager.active_connections),
            "timestamp": time.time()
        }
        
        # Add component-specific status
        if self.pathway_engine:
            status["pathway_stats"] = self.pathway_engine.get_processing_stats()
            status["allocation_state"] = self.pathway_engine.get_current_allocation_state()
        
        if self.rag_system:
            status["rag_stats"] = self.rag_system.get_store_stats()
        
        if self.dev_stream_manager:
            status["stream_stats"] = self.dev_stream_manager.status()
        
        return status


# Global system integrator instance
system_integrator = SystemIntegrator()


def start_integrated_system() -> bool:
    """
    Start the complete integrated Bharat-Grid AI system.
    
    This function should be called during FastAPI startup to ensure
    all components are connected and running.
    """
    return system_integrator.start_integration()


def stop_integrated_system():
    """
    Stop the complete integrated system.
    
    This function should be called during FastAPI shutdown.
    """
    system_integrator.stop_integration()


def get_integration_status() -> Dict[str, Any]:
    """Get current integration status for monitoring"""
    return system_integrator.get_system_status()


# Integration validation functions
def validate_pathway_connection() -> bool:
    """Validate that Pathway engine is connected to FastAPI"""
    try:
        if not system_integrator.pathway_engine:
            return False
        
        # Check if allocation callback is registered
        return len(system_integrator.pathway_engine.allocation_callbacks) > 0
        
    except Exception as e:
        logger.error(f"Pathway connection validation failed: {e}")
        return False


def validate_websocket_connection() -> bool:
    """Validate WebSocket broadcasting capability"""
    try:
        # Check if WebSocket manager is available
        return manager is not None
        
    except Exception as e:
        logger.error(f"WebSocket connection validation failed: {e}")
        return False


def validate_rag_integration() -> bool:
    """Validate RAG system integration with API"""
    try:
        if not system_integrator.rag_system:
            return False
        
        # Test basic RAG functionality
        stats = system_integrator.rag_system.get_store_stats()
        return "total_patterns" in stats
        
    except Exception as e:
        logger.error(f"RAG integration validation failed: {e}")
        return False


async def run_integration_test() -> Dict[str, bool]:
    """
    Run comprehensive integration test.
    
    Returns:
        Dictionary with test results for each component
    """
    results = {
        "pathway_connection": validate_pathway_connection(),
        "websocket_connection": validate_websocket_connection(),
        "rag_integration": validate_rag_integration(),
        "system_running": system_integrator.is_running
    }
    
    logger.info("Integration test results:")
    for component, status in results.items():
        status_str = "✓ PASS" if status else "✗ FAIL"
        logger.info(f"  {component}: {status_str}")
    
    return results


if __name__ == "__main__":
    # Direct execution for testing
    import asyncio
    
    async def main():
        print("Starting Bharat-Grid AI System Integration Test")
        print("=" * 50)
        
        # Start integration
        if start_integrated_system():
            print("✓ System integration started")
            
            # Wait a moment for initialization
            await asyncio.sleep(2)
            
            # Run integration test
            test_results = await run_integration_test()
            
            # Show system status
            status = get_integration_status()
            print(f"\nSystem Status:")
            print(f"  Integration running: {status['integration_running']}")
            print(f"  WebSocket connections: {status['websocket_connections']}")
            
            # Keep running for a short test period
            print("\nRunning for 10 seconds...")
            await asyncio.sleep(10)
            
            # Stop integration
            stop_integrated_system()
            print("✓ System integration stopped")
            
        else:
            print("✗ Failed to start system integration")
    
    asyncio.run(main())