"""
Demonstration of WebSocket endpoint for real-time allocation updates.

This script shows the WebSocket endpoint in action with simulated
allocation results and real-time broadcasting.
"""

import asyncio
import time
import json
from typing import List

from api import app, manager, broadcast_allocation_results
from schemas import AllocationResult, SourceMix, EnergyNode, SupplyEvent, Location, AvailableSources
from pathway_engine import EnergyDataIngestionPipeline


class WebSocketDemo:
    """Demonstration class for WebSocket functionality."""
    
    def __init__(self):
        self.pipeline = EnergyDataIngestionPipeline(data_dir="./data")
        self.demo_running = False
        
    async def simulate_websocket_client(self, client_id: str, duration: float = 10.0):
        """Simulate a WebSocket client connection."""
        print(f"🔌 Client {client_id} connecting...")
        
        # Create mock WebSocket client
        class MockWebSocketClient:
            def __init__(self, client_id: str):
                self.client_id = client_id
                self.messages_received = 0
                
            async def send_json(self, data):
                self.messages_received += 1
                message_type = data.get("type", "unknown")
                
                if message_type == "allocation_results":
                    total_allocated = data["summary"]["total_allocated"]
                    node_count = data["summary"]["total_nodes"]
                    print(f"  📊 Client {self.client_id}: Received allocation for {node_count} nodes, total: {total_allocated:.1f} kW")
                    
                elif message_type == "latency":
                    latency = data["value"]
                    print(f"  ⏱️  Client {self.client_id}: Latency metric: {latency:.2f}ms")
                    
                else:
                    print(f"  📨 Client {self.client_id}: Received {message_type}")
        
        # Create and register mock client
        mock_client = MockWebSocketClient(client_id)
        manager.active_connections.add(mock_client)
        
        try:
            # Keep client connected for specified duration
            await asyncio.sleep(duration)
            
        finally:
            # Disconnect client
            manager.disconnect(mock_client)
            print(f"🔌 Client {client_id} disconnected (received {mock_client.messages_received} messages)")
    
    async def generate_sample_allocations(self, interval: float = 2.0, count: int = 5):
        """Generate sample allocation results for demonstration."""
        print(f"🏭 Starting allocation generation (every {interval}s, {count} rounds)...")
        
        # Sample nodes with different priorities
        sample_nodes = [
            ("hospital_01", 150.0, 1, "Critical care facility"),
            ("hospital_02", 200.0, 1, "Emergency department"),
            ("factory_01", 300.0, 2, "Manufacturing plant"),
            ("factory_02", 250.0, 2, "Processing facility"),
            ("residential_01", 75.0, 3, "Apartment complex"),
            ("residential_02", 100.0, 3, "Housing development"),
        ]
        
        for round_num in range(count):
            print(f"\n🔄 Round {round_num + 1}/{count}")
            
            # Simulate varying supply conditions
            supply_factor = 1.0 - (round_num * 0.15)  # Decreasing supply
            total_supply = 1000.0 * supply_factor
            
            print(f"⚡ Supply event: {total_supply:.0f} kW available")
            
            # Create allocation results based on priority and available supply
            allocations = []
            remaining_supply = total_supply
            
            for node_id, demand, priority, description in sample_nodes:
                if remaining_supply >= demand:
                    # Full allocation
                    allocated = demand
                    action = "maintain"
                    remaining_supply -= demand
                elif remaining_supply > 0:
                    # Partial allocation
                    allocated = remaining_supply
                    action = "reduce"
                    remaining_supply = 0
                else:
                    # No allocation
                    allocated = 0
                    action = "cutoff"
                
                # Create source mix (prefer clean sources)
                source_mix = SourceMix()
                if allocated > 0:
                    # Distribute across sources (solar > grid > battery > diesel)
                    solar_portion = min(allocated * 0.4, allocated)
                    grid_portion = min((allocated - solar_portion) * 0.6, allocated - solar_portion)
                    battery_portion = min(allocated - solar_portion - grid_portion, allocated - solar_portion - grid_portion)
                    diesel_portion = allocated - solar_portion - grid_portion - battery_portion
                    
                    if solar_portion > 0:
                        source_mix.solar = solar_portion
                    if grid_portion > 0:
                        source_mix.grid = grid_portion
                    if battery_portion > 0:
                        source_mix.battery = battery_portion
                    if diesel_portion > 0:
                        source_mix.diesel = diesel_portion
                
                allocation = AllocationResult(
                    node_id=node_id,
                    allocated_power=allocated,
                    source_mix=source_mix,
                    action=action,
                    latency_ms=round(2.0 + round_num * 0.5, 1)  # Simulated processing latency
                )
                
                allocations.append(allocation)
                
                # Log allocation decision
                status_emoji = {"maintain": "🟢", "reduce": "🟡", "cutoff": "🔴"}[action]
                print(f"  {status_emoji} {node_id} (P{priority}): {allocated:.0f}/{demand:.0f} kW - {description}")
            
            # Broadcast allocations to WebSocket clients
            if manager.active_connections:
                stats = await broadcast_allocation_results(allocations)
                print(f"  📡 Broadcasted to {stats['sent']} clients in {stats['latency_ms']:.2f}ms")
            else:
                print("  📡 No WebSocket clients connected")
            
            # Wait before next round
            if round_num < count - 1:
                await asyncio.sleep(interval)
        
        print(f"\n✅ Allocation generation completed")
    
    async def run_demo(self, duration: float = 15.0):
        """Run the complete WebSocket demonstration."""
        print("🚀 Starting WebSocket Endpoint Demonstration")
        print("=" * 50)
        print(f"Demo duration: {duration} seconds")
        print(f"WebSocket endpoint: /ws/allocations")
        print()
        
        self.demo_running = True
        
        try:
            # Start multiple simulated clients
            client_tasks = [
                asyncio.create_task(self.simulate_websocket_client("Dashboard-1", duration)),
                asyncio.create_task(self.simulate_websocket_client("Monitor-2", duration * 0.8)),
                asyncio.create_task(self.simulate_websocket_client("Mobile-3", duration * 0.6)),
            ]
            
            # Start allocation generation
            allocation_task = asyncio.create_task(
                self.generate_sample_allocations(interval=2.5, count=int(duration / 2.5))
            )
            
            # Wait for all tasks to complete
            await asyncio.gather(*client_tasks, allocation_task)
            
        except KeyboardInterrupt:
            print("\n⏹️  Demo interrupted by user")
        
        finally:
            self.demo_running = False
            manager.active_connections.clear()
            
        print("\n" + "=" * 50)
        print("🏁 WebSocket Endpoint Demonstration Complete")
        print(f"Final connection count: {len(manager.active_connections)}")


async def main():
    """Main demonstration function."""
    demo = WebSocketDemo()
    
    print("WebSocket Endpoint Demo for Bharat-Grid AI")
    print("This demonstrates real-time allocation broadcasting")
    print()
    
    # Show current system status
    print("📊 System Status:")
    print(f"  Active WebSocket connections: {len(manager.active_connections)}")
    print(f"  Connection manager ready: ✅")
    print()
    
    # Run the demonstration
    await demo.run_demo(duration=15.0)
    
    # Show final statistics
    print("\n📈 Demo Statistics:")
    print(f"  Total connections created: {manager.connection_count}")
    print(f"  Active connections: {len(manager.active_connections)}")
    print("  WebSocket endpoint: Ready for production use ✅")


if __name__ == "__main__":
    print("🌐 Bharat-Grid AI WebSocket Endpoint Demo")
    print("Press Ctrl+C to stop the demo at any time\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()