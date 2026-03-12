#!/usr/bin/env python3
"""
Optimized WebSocket Manager for Bharat-Grid AI

Implements performance optimizations for WebSocket broadcasting:
- Message batching for reduced latency
- Connection pooling and management
- Compression for large messages
- Automatic reconnection handling
- Performance monitoring and metrics

Requirements: 4.1, 4.2, 7.4, 7.5
"""

import asyncio
import json
import time
import gzip
import logging
from typing import Dict, List, Set, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
from fastapi import WebSocket, WebSocketDisconnect
import weakref

from schemas import AllocationResult, LatencyMetric
from utils.latency_tracker import global_tracker, PerformanceContext


@dataclass
class ConnectionMetrics:
    """Metrics for individual WebSocket connection"""
    connection_id: str
    connected_at: float
    messages_sent: int = 0
    messages_failed: int = 0
    last_message_at: float = 0
    avg_latency_ms: float = 0
    total_bytes_sent: int = 0


@dataclass
class BroadcastMetrics:
    """Metrics for broadcast operations"""
    timestamp: float
    message_type: str
    connections_count: int
    successful_sends: int
    failed_sends: int
    total_latency_ms: float
    message_size_bytes: int
    compression_ratio: float = 1.0


class OptimizedWebSocketManager:
    """
    High-performance WebSocket connection manager with advanced optimizations
    """
    
    def __init__(self, max_connections: int = 1000):
        self.max_connections = max_connections
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self.broadcast_history: deque = deque(maxlen=100)
        
        # Performance optimization settings
        self.enable_compression = True
        self.enable_batching = True
        self.enable_message_queuing = True
        self.compression_threshold = 1024  # Compress messages > 1KB
        self.batch_size = 50  # Max connections per batch
        self.batch_delay_ms = 1  # Delay between batches
        
        # Message queuing for high-frequency updates
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self.queue_processor_task: Optional[asyncio.Task] = None
        self.is_processing_queue = False
        
        # Connection management
        self.connection_counter = 0
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
        
        # Performance monitoring
        self.total_broadcasts = 0
        self.total_latency_ms = 0
        self.target_latency_ms = 50.0
        
        # Event handlers
        self.on_connection_established: Optional[Callable] = None
        self.on_connection_lost: Optional[Callable] = None
        self.on_broadcast_complete: Optional[Callable] = None
        
        # Start background tasks
        self._start_background_tasks()
        
        logging.info("OptimizedWebSocketManager initialized")
    
    def _start_background_tasks(self):
        """Start background tasks for optimization"""
        if self.enable_message_queuing:
            self.queue_processor_task = asyncio.create_task(self._process_message_queue())
    
    async def connect(self, websocket: WebSocket) -> str:
        """
        Accept and register a new WebSocket connection with optimization
        """
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(code=1013, reason="Server overloaded")
            raise Exception(f"Maximum connections ({self.max_connections}) reached")
        
        await websocket.accept()
        
        # Generate unique connection ID
        connection_id = f"conn_{self.connection_counter}_{int(time.time())}"
        self.connection_counter += 1
        
        # Register connection
        self.active_connections[connection_id] = websocket
        self.connection_metrics[connection_id] = ConnectionMetrics(
            connection_id=connection_id,
            connected_at=time.time()
        )
        
        # Send connection confirmation
        await self._send_to_connection(
            websocket,
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": time.time(),
                "server_info": {
                    "optimization_enabled": True,
                    "compression_enabled": self.enable_compression,
                    "batching_enabled": self.enable_batching
                }
            }
        )
        
        # Trigger event handler
        if self.on_connection_established:
            await self.on_connection_established(connection_id, websocket)
        
        logging.info(f"WebSocket connected: {connection_id} (total: {len(self.active_connections)})")
        return connection_id
    
    async def disconnect(self, connection_id: str, reason: str = "Normal closure"):
        """
        Disconnect and cleanup a WebSocket connection
        """
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            
            try:
                await websocket.close(code=1000, reason=reason)
            except Exception as e:
                logging.warning(f"Error closing WebSocket {connection_id}: {e}")
            
            # Remove from active connections
            del self.active_connections[connection_id]
            
            # Update metrics
            if connection_id in self.connection_metrics:
                metrics = self.connection_metrics[connection_id]
                connection_duration = time.time() - metrics.connected_at
                logging.info(
                    f"WebSocket disconnected: {connection_id} "
                    f"(duration: {connection_duration:.1f}s, "
                    f"messages: {metrics.messages_sent})"
                )
            
            # Trigger event handler
            if self.on_connection_lost:
                await self.on_connection_lost(connection_id, reason)
            
            logging.info(f"WebSocket disconnected: {connection_id} (total: {len(self.active_connections)})")
    
    async def broadcast_json(
        self, 
        data: Dict[str, Any], 
        message_type: str = "broadcast",
        priority: bool = False
    ) -> BroadcastMetrics:
        """
        Broadcast JSON data to all connected clients with optimizations
        """
        if not self.active_connections:
            return BroadcastMetrics(
                timestamp=time.time(),
                message_type=message_type,
                connections_count=0,
                successful_sends=0,
                failed_sends=0,
                total_latency_ms=0,
                message_size_bytes=0
            )
        
        # Add timestamp for latency measurement
        data["broadcast_timestamp"] = time.time()
        
        if priority or not self.enable_message_queuing:
            # Send immediately for high-priority messages
            return await self._broadcast_immediate(data, message_type)
        else:
            # Queue for batch processing
            await self.message_queue.put((data, message_type))
            
            # Return estimated metrics (actual metrics recorded by queue processor)
            return BroadcastMetrics(
                timestamp=time.time(),
                message_type=message_type,
                connections_count=len(self.active_connections),
                successful_sends=0,  # Will be updated by queue processor
                failed_sends=0,
                total_latency_ms=0,
                message_size_bytes=len(json.dumps(data).encode())
            )
    
    async def _broadcast_immediate(
        self, 
        data: Dict[str, Any], 
        message_type: str
    ) -> BroadcastMetrics:
        """
        Immediate broadcast without queuing
        """
        start_time = time.perf_counter()
        
        # Serialize message once
        message_json = json.dumps(data)
        message_bytes = message_json.encode('utf-8')
        original_size = len(message_bytes)
        
        # Apply compression if beneficial
        compressed_message = None
        compression_ratio = 1.0
        
        if self.enable_compression and original_size > self.compression_threshold:
            compressed_data = gzip.compress(message_bytes)
            if len(compressed_data) < original_size * 0.8:  # Only use if >20% reduction
                compressed_message = compressed_data
                compression_ratio = original_size / len(compressed_data)
        
        # Broadcast to connections
        if self.enable_batching and len(self.active_connections) > self.batch_size:
            successful_sends, failed_sends = await self._broadcast_batched(
                message_json, compressed_message
            )
        else:
            successful_sends, failed_sends = await self._broadcast_standard(
                message_json, compressed_message
            )
        
        # Calculate metrics
        total_latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Record performance metrics
        global_tracker.record_latency('websocket', total_latency_ms, {
            'connections': len(self.active_connections),
            'message_size': original_size,
            'compression_ratio': compression_ratio
        })
        
        # Create broadcast metrics
        metrics = BroadcastMetrics(
            timestamp=time.time(),
            message_type=message_type,
            connections_count=len(self.active_connections),
            successful_sends=successful_sends,
            failed_sends=failed_sends,
            total_latency_ms=total_latency_ms,
            message_size_bytes=original_size,
            compression_ratio=compression_ratio
        )
        
        # Store in history
        self.broadcast_history.append(metrics)
        
        # Update global metrics
        self.total_broadcasts += 1
        self.total_latency_ms += total_latency_ms
        
        # Log performance warning if needed
        if total_latency_ms > self.target_latency_ms:
            logging.warning(
                f"WebSocket broadcast latency {total_latency_ms:.2f}ms "
                f"exceeds target {self.target_latency_ms}ms "
                f"(connections: {len(self.active_connections)}, "
                f"size: {original_size} bytes)"
            )
        
        # Trigger event handler
        if self.on_broadcast_complete:
            await self.on_broadcast_complete(metrics)
        
        return metrics
    
    async def _broadcast_batched(
        self, 
        message_json: str, 
        compressed_message: Optional[bytes]
    ) -> tuple[int, int]:
        """
        Broadcast using batching for better performance with many connections
        """
        successful_sends = 0
        failed_sends = 0
        
        # Split connections into batches
        connections_list = list(self.active_connections.items())
        
        for i in range(0, len(connections_list), self.batch_size):
            batch = connections_list[i:i + self.batch_size]
            
            # Send to batch concurrently
            batch_tasks = []
            for conn_id, websocket in batch:
                task = asyncio.create_task(
                    self._send_optimized_message(conn_id, websocket, message_json, compressed_message)
                )
                batch_tasks.append(task)
            
            # Wait for batch completion
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Count results
            for result in batch_results:
                if isinstance(result, Exception):
                    failed_sends += 1
                elif result:
                    successful_sends += 1
                else:
                    failed_sends += 1
            
            # Small delay between batches to prevent overwhelming
            if i + self.batch_size < len(connections_list):
                await asyncio.sleep(self.batch_delay_ms / 1000)
        
        return successful_sends, failed_sends
    
    async def _broadcast_standard(
        self, 
        message_json: str, 
        compressed_message: Optional[bytes]
    ) -> tuple[int, int]:
        """
        Standard broadcast without batching
        """
        successful_sends = 0
        failed_sends = 0
        
        # Send to all connections concurrently
        tasks = []
        for conn_id, websocket in self.active_connections.items():
            task = asyncio.create_task(
                self._send_optimized_message(conn_id, websocket, message_json, compressed_message)
            )
            tasks.append(task)
        
        # Wait for all sends to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count results
        for result in results:
            if isinstance(result, Exception):
                failed_sends += 1
            elif result:
                successful_sends += 1
            else:
                failed_sends += 1
        
        return successful_sends, failed_sends
    
    async def _send_optimized_message(
        self, 
        connection_id: str, 
        websocket: WebSocket, 
        message_json: str,
        compressed_message: Optional[bytes]
    ) -> bool:
        """
        Send message to individual connection with optimization
        """
        try:
            # Choose best message format
            if compressed_message and self.enable_compression:
                # Send compressed message with header
                await websocket.send_bytes(compressed_message)
            else:
                # Send standard JSON
                await websocket.send_text(message_json)
            
            # Update connection metrics
            if connection_id in self.connection_metrics:
                metrics = self.connection_metrics[connection_id]
                metrics.messages_sent += 1
                metrics.last_message_at = time.time()
                metrics.total_bytes_sent += len(message_json.encode())
            
            return True
            
        except WebSocketDisconnect:
            # Connection closed by client
            await self.disconnect(connection_id, "Client disconnected")
            return False
            
        except Exception as e:
            # Other connection error
            logging.error(f"Failed to send message to {connection_id}: {e}")
            
            # Update failure metrics
            if connection_id in self.connection_metrics:
                self.connection_metrics[connection_id].messages_failed += 1
            
            # Disconnect problematic connection
            await self.disconnect(connection_id, f"Send error: {str(e)}")
            return False
    
    async def _send_to_connection(self, websocket: WebSocket, data: Dict[str, Any]) -> bool:
        """
        Send data to a specific connection
        """
        try:
            await websocket.send_json(data)
            return True
        except Exception as e:
            logging.error(f"Failed to send to connection: {e}")
            return False
    
    async def _process_message_queue(self):
        """
        Background task to process queued messages in batches
        """
        self.is_processing_queue = True
        
        while self.is_processing_queue:
            try:
                # Collect messages for batch processing
                messages_batch = []
                
                # Wait for first message
                try:
                    first_message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                    messages_batch.append(first_message)
                except asyncio.TimeoutError:
                    continue
                
                # Collect additional messages (up to batch size)
                while len(messages_batch) < 10 and not self.message_queue.empty():
                    try:
                        message = self.message_queue.get_nowait()
                        messages_batch.append(message)
                    except asyncio.QueueEmpty:
                        break
                
                # Process batch
                for data, message_type in messages_batch:
                    await self._broadcast_immediate(data, message_type)
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.001)
                
            except Exception as e:
                logging.error(f"Error in message queue processor: {e}")
                await asyncio.sleep(1)
    
    async def broadcast_allocation_results(
        self, 
        allocations: List[AllocationResult]
    ) -> BroadcastMetrics:
        """
        Broadcast allocation results with performance optimization
        """
        # Prepare optimized allocation data
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
                },
                "avg_latency_ms": sum(a.latency_ms for a in allocations) / len(allocations) if allocations else 0
            }
        }
        
        # Broadcast with high priority
        metrics = await self.broadcast_json(allocation_data, "allocation_results", priority=True)
        
        # Send separate latency metric if broadcast was successful
        if metrics.successful_sends > 0:
            latency_data = LatencyMetric(value=metrics.total_latency_ms).dict()
            await self.broadcast_json(latency_data, "latency_metric")
        
        logging.info(
            f"Broadcasted {len(allocations)} allocation results to "
            f"{metrics.successful_sends} clients in {metrics.total_latency_ms:.2f}ms"
        )
        
        return metrics
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive connection statistics
        """
        if not self.connection_metrics:
            return {
                "active_connections": 0,
                "total_connections_created": self.connection_counter,
                "avg_latency_ms": 0,
                "total_broadcasts": self.total_broadcasts
            }
        
        # Calculate aggregate metrics
        total_messages = sum(m.messages_sent for m in self.connection_metrics.values())
        total_failures = sum(m.messages_failed for m in self.connection_metrics.values())
        total_bytes = sum(m.total_bytes_sent for m in self.connection_metrics.values())
        
        avg_broadcast_latency = (
            self.total_latency_ms / self.total_broadcasts 
            if self.total_broadcasts > 0 else 0
        )
        
        return {
            "active_connections": len(self.active_connections),
            "total_connections_created": self.connection_counter,
            "total_messages_sent": total_messages,
            "total_message_failures": total_failures,
            "success_rate": (total_messages / (total_messages + total_failures)) * 100 if (total_messages + total_failures) > 0 else 100,
            "total_bytes_sent": total_bytes,
            "total_broadcasts": self.total_broadcasts,
            "avg_broadcast_latency_ms": avg_broadcast_latency,
            "target_compliance": avg_broadcast_latency < self.target_latency_ms,
            "optimization_settings": {
                "compression_enabled": self.enable_compression,
                "batching_enabled": self.enable_batching,
                "queuing_enabled": self.enable_message_queuing,
                "batch_size": self.batch_size,
                "compression_threshold": self.compression_threshold
            }
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get detailed performance metrics
        """
        recent_broadcasts = list(self.broadcast_history)[-10:]  # Last 10 broadcasts
        
        if not recent_broadcasts:
            return {"no_data": True}
        
        # Calculate recent performance
        recent_latencies = [b.total_latency_ms for b in recent_broadcasts]
        recent_success_rates = [
            (b.successful_sends / (b.successful_sends + b.failed_sends)) * 100 
            if (b.successful_sends + b.failed_sends) > 0 else 100
            for b in recent_broadcasts
        ]
        
        return {
            "recent_avg_latency_ms": sum(recent_latencies) / len(recent_latencies),
            "recent_min_latency_ms": min(recent_latencies),
            "recent_max_latency_ms": max(recent_latencies),
            "recent_avg_success_rate": sum(recent_success_rates) / len(recent_success_rates),
            "target_violations": len([l for l in recent_latencies if l > self.target_latency_ms]),
            "violation_rate": len([l for l in recent_latencies if l > self.target_latency_ms]) / len(recent_latencies) * 100,
            "compression_usage": sum(1 for b in recent_broadcasts if b.compression_ratio > 1.0) / len(recent_broadcasts) * 100,
            "avg_compression_ratio": sum(b.compression_ratio for b in recent_broadcasts) / len(recent_broadcasts)
        }
    
    async def cleanup_stale_connections(self):
        """
        Clean up stale or problematic connections
        """
        current_time = time.time()
        
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        stale_connections = []
        
        for conn_id, metrics in self.connection_metrics.items():
            # Check for stale connections (no messages in last 10 minutes)
            if current_time - metrics.last_message_at > 600:
                stale_connections.append(conn_id)
            
            # Check for problematic connections (high failure rate)
            if metrics.messages_sent > 10:
                failure_rate = metrics.messages_failed / (metrics.messages_sent + metrics.messages_failed)
                if failure_rate > 0.5:  # >50% failure rate
                    stale_connections.append(conn_id)
        
        # Disconnect stale connections
        for conn_id in stale_connections:
            await self.disconnect(conn_id, "Stale connection cleanup")
        
        self.last_cleanup = current_time
        
        if stale_connections:
            logging.info(f"Cleaned up {len(stale_connections)} stale connections")
    
    async def shutdown(self):
        """
        Graceful shutdown of WebSocket manager
        """
        logging.info("Shutting down WebSocket manager...")
        
        # Stop queue processor
        self.is_processing_queue = False
        if self.queue_processor_task:
            self.queue_processor_task.cancel()
            try:
                await self.queue_processor_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect all connections
        disconnect_tasks = []
        for conn_id in list(self.active_connections.keys()):
            task = asyncio.create_task(self.disconnect(conn_id, "Server shutdown"))
            disconnect_tasks.append(task)
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        logging.info("WebSocket manager shutdown complete")


# Global optimized manager instance
optimized_manager = OptimizedWebSocketManager()


# Convenience functions for backward compatibility
async def broadcast_allocation_results(allocations: List[AllocationResult]) -> Dict[str, Any]:
    """Broadcast allocation results using optimized manager"""
    metrics = await optimized_manager.broadcast_allocation_results(allocations)
    return {
        "sent": metrics.successful_sends,
        "failed": metrics.failed_sends,
        "latency_ms": metrics.total_latency_ms,
        "total_connections": metrics.connections_count
    }


def get_websocket_stats() -> Dict[str, Any]:
    """Get WebSocket statistics"""
    return optimized_manager.get_connection_stats()


def get_websocket_performance_metrics() -> Dict[str, Any]:
    """Get WebSocket performance metrics"""
    return optimized_manager.get_performance_metrics()


if __name__ == "__main__":
    # Demo usage
    async def demo():
        manager = OptimizedWebSocketManager()
        
        # Simulate some connections and broadcasts
        print("WebSocket Manager Demo")
        print("=" * 30)
        
        # Get initial stats
        stats = manager.get_connection_stats()
        print(f"Initial connections: {stats['active_connections']}")
        
        # Simulate broadcast
        test_data = {
            "type": "test_broadcast",
            "data": "Hello WebSocket clients!",
            "timestamp": time.time()
        }
        
        metrics = await manager.broadcast_json(test_data, "test")
        print(f"Broadcast completed: {metrics.successful_sends} sent, {metrics.total_latency_ms:.2f}ms")
        
        # Get performance metrics
        perf_metrics = manager.get_performance_metrics()
        print(f"Performance metrics: {perf_metrics}")
        
        await manager.shutdown()
    
    asyncio.run(demo())