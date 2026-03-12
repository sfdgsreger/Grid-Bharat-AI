#!/usr/bin/env python3
"""
Comprehensive Load Testing for Bharat-Grid AI System

Tests all performance targets under various load conditions:
- Allocation latency under high node counts
- WebSocket latency under multiple connections
- RAG response time under concurrent requests
- System stability under sustained load

Requirements: 2.6, 4.1, 3.4, 4.4, 7.4, 7.5
"""

import asyncio
import aiohttp
import websockets
import time
import json
import statistics
import threading
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import numpy as np

from schemas import EnergyNode, SupplyEvent, AllocationResult
from performance_optimizer import performance_optimizer
from utils.latency_tracker import global_tracker


@dataclass
class LoadTestConfig:
    """Load test configuration"""
    duration_seconds: int = 60
    allocation_rps: int = 100  # Allocation requests per second
    websocket_connections: int = 50  # Concurrent WebSocket connections
    rag_rps: int = 10  # RAG requests per second
    node_count: int = 1000  # Number of nodes per allocation
    ramp_up_seconds: int = 10  # Gradual load increase


@dataclass
class LoadTestResults:
    """Load test results"""
    test_name: str
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    latency_stats: Dict[str, float]
    error_rate: float
    target_violations: int
    violation_rate: float
    system_metrics: Dict[str, Any]


class LoadTestRunner:
    """
    Comprehensive load testing system for validating performance targets
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
        self.results: List[LoadTestResults] = []
        self.is_running = False
        
    async def run_allocation_load_test(self, config: LoadTestConfig) -> LoadTestResults:
        """
        Test allocation performance under high load
        """
        print(f"🚀 Running Allocation Load Test")
        print(f"   Duration: {config.duration_seconds}s")
        print(f"   Target RPS: {config.allocation_rps}")
        print(f"   Node Count: {config.node_count}")
        
        # Enable optimizations
        performance_optimizer.enable_all_optimizations()
        
        # Create test data
        nodes = self._create_test_nodes(config.node_count)
        supply_event = self._create_test_supply_event(
            sum(node.current_load for node in nodes) * 0.8
        )
        
        # Test metrics
        latencies = []
        errors = 0
        start_time = time.time()
        request_count = 0
        
        # Rate limiting
        request_interval = 1.0 / config.allocation_rps
        
        # Run test
        while time.time() - start_time < config.duration_seconds:
            request_start = time.perf_counter()
            
            try:
                # Perform allocation
                allocations = performance_optimizer.optimized_allocate_power(nodes, supply_event)
                
                # Record latency
                latency_ms = (time.perf_counter() - request_start) * 1000
                latencies.append(latency_ms)
                request_count += 1
                
                # Validate results
                if len(allocations) != len(nodes):
                    errors += 1
                
            except Exception as e:
                errors += 1
                print(f"Allocation error: {e}")
            
            # Rate limiting
            elapsed = time.time() - start_time
            expected_requests = int(elapsed * config.allocation_rps)
            if request_count >= expected_requests:
                await asyncio.sleep(0.001)
        
        # Calculate results
        actual_duration = time.time() - start_time
        actual_rps = request_count / actual_duration
        target_violations = len([l for l in latencies if l > 10.0])
        
        return LoadTestResults(
            test_name="Allocation Load Test",
            duration_seconds=actual_duration,
            total_requests=request_count,
            successful_requests=request_count - errors,
            failed_requests=errors,
            requests_per_second=actual_rps,
            latency_stats={
                'avg_ms': statistics.mean(latencies) if latencies else 0,
                'min_ms': min(latencies) if latencies else 0,
                'max_ms': max(latencies) if latencies else 0,
                'p95_ms': np.percentile(latencies, 95) if latencies else 0,
                'p99_ms': np.percentile(latencies, 99) if latencies else 0,
            },
            error_rate=(errors / request_count) * 100 if request_count > 0 else 0,
            target_violations=target_violations,
            violation_rate=(target_violations / len(latencies)) * 100 if latencies else 0,
            system_metrics=self._get_system_metrics()
        )
    
    async def run_websocket_load_test(self, config: LoadTestConfig) -> LoadTestResults:
        """
        Test WebSocket performance under multiple concurrent connections
        """
        print(f"🌐 Running WebSocket Load Test")
        print(f"   Duration: {config.duration_seconds}s")
        print(f"   Connections: {config.websocket_connections}")
        
        # WebSocket test metrics
        connection_latencies = []
        message_latencies = []
        connections_established = 0
        messages_received = 0
        errors = 0
        
        async def websocket_client(client_id: int):
            """Individual WebSocket client"""
            try:
                uri = f"{self.ws_url}/ws/allocations"
                
                # Measure connection time
                connect_start = time.perf_counter()
                async with websockets.connect(uri) as websocket:
                    connect_time = (time.perf_counter() - connect_start) * 1000
                    connection_latencies.append(connect_time)
                    nonlocal connections_established
                    connections_established += 1
                    
                    # Listen for messages
                    start_time = time.time()
                    while time.time() - start_time < config.duration_seconds:
                        try:
                            # Set timeout for message reception
                            message = await asyncio.wait_for(
                                websocket.recv(), 
                                timeout=1.0
                            )
                            
                            # Measure message latency (if timestamp available)
                            try:
                                data = json.loads(message)
                                if 'timestamp' in data:
                                    message_latency = (time.time() - data['timestamp']) * 1000
                                    message_latencies.append(message_latency)
                                
                                nonlocal messages_received
                                messages_received += 1
                                
                            except json.JSONDecodeError:
                                pass  # Ignore non-JSON messages
                                
                        except asyncio.TimeoutError:
                            # No message received, continue
                            continue
                        except Exception as e:
                            nonlocal errors
                            errors += 1
                            break
                            
            except Exception as e:
                errors += 1
                print(f"WebSocket client {client_id} error: {e}")
        
        # Start all WebSocket clients concurrently
        start_time = time.time()
        tasks = [
            websocket_client(i) 
            for i in range(config.websocket_connections)
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        actual_duration = time.time() - start_time
        
        # Calculate WebSocket-specific metrics
        avg_connection_latency = statistics.mean(connection_latencies) if connection_latencies else 0
        avg_message_latency = statistics.mean(message_latencies) if message_latencies else 0
        websocket_violations = len([l for l in message_latencies if l > 50.0])
        
        return LoadTestResults(
            test_name="WebSocket Load Test",
            duration_seconds=actual_duration,
            total_requests=connections_established + messages_received,
            successful_requests=connections_established + messages_received - errors,
            failed_requests=errors,
            requests_per_second=messages_received / actual_duration if actual_duration > 0 else 0,
            latency_stats={
                'connection_avg_ms': avg_connection_latency,
                'message_avg_ms': avg_message_latency,
                'message_min_ms': min(message_latencies) if message_latencies else 0,
                'message_max_ms': max(message_latencies) if message_latencies else 0,
                'message_p95_ms': np.percentile(message_latencies, 95) if message_latencies else 0,
            },
            error_rate=(errors / (connections_established + messages_received)) * 100 if (connections_established + messages_received) > 0 else 0,
            target_violations=websocket_violations,
            violation_rate=(websocket_violations / len(message_latencies)) * 100 if message_latencies else 0,
            system_metrics={
                'connections_established': connections_established,
                'messages_received': messages_received,
                **self._get_system_metrics()
            }
        )
    
    async def run_rag_load_test(self, config: LoadTestConfig) -> LoadTestResults:
        """
        Test RAG system performance under concurrent requests
        """
        print(f"🧠 Running RAG Load Test")
        print(f"   Duration: {config.duration_seconds}s")
        print(f"   Target RPS: {config.rag_rps}")
        
        # RAG test metrics
        latencies = []
        errors = 0
        request_count = 0
        
        async def rag_request(session: aiohttp.ClientSession):
            """Individual RAG request"""
            try:
                request_start = time.perf_counter()
                
                async with session.get(f"{self.base_url}/insights") as response:
                    if response.status == 200:
                        await response.json()
                        latency_ms = (time.perf_counter() - request_start) * 1000
                        latencies.append(latency_ms)
                    else:
                        nonlocal errors
                        errors += 1
                        
            except Exception as e:
                errors += 1
                print(f"RAG request error: {e}")
        
        # Run RAG requests
        start_time = time.time()
        request_interval = 1.0 / config.rag_rps
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < config.duration_seconds:
                # Send request
                await rag_request(session)
                request_count += 1
                
                # Rate limiting
                await asyncio.sleep(request_interval)
        
        actual_duration = time.time() - start_time
        actual_rps = request_count / actual_duration
        rag_violations = len([l for l in latencies if l > 2000.0])
        
        return LoadTestResults(
            test_name="RAG Load Test",
            duration_seconds=actual_duration,
            total_requests=request_count,
            successful_requests=request_count - errors,
            failed_requests=errors,
            requests_per_second=actual_rps,
            latency_stats={
                'avg_ms': statistics.mean(latencies) if latencies else 0,
                'min_ms': min(latencies) if latencies else 0,
                'max_ms': max(latencies) if latencies else 0,
                'p95_ms': np.percentile(latencies, 95) if latencies else 0,
                'p99_ms': np.percentile(latencies, 99) if latencies else 0,
            },
            error_rate=(errors / request_count) * 100 if request_count > 0 else 0,
            target_violations=rag_violations,
            violation_rate=(rag_violations / len(latencies)) * 100 if latencies else 0,
            system_metrics=self._get_system_metrics()
        )
    
    async def run_comprehensive_load_test(self, config: LoadTestConfig) -> List[LoadTestResults]:
        """
        Run comprehensive load test covering all performance targets
        """
        print("🎯 Running Comprehensive Load Test")
        print("=" * 50)
        
        results = []
        
        # Test 1: Allocation Performance
        allocation_result = await self.run_allocation_load_test(config)
        results.append(allocation_result)
        
        # Brief pause between tests
        await asyncio.sleep(2)
        
        # Test 2: WebSocket Performance
        websocket_result = await self.run_websocket_load_test(config)
        results.append(websocket_result)
        
        # Brief pause between tests
        await asyncio.sleep(2)
        
        # Test 3: RAG Performance
        rag_result = await self.run_rag_load_test(config)
        results.append(rag_result)
        
        self.results.extend(results)
        return results
    
    def _create_test_nodes(self, count: int) -> List[EnergyNode]:
        """Create test nodes for load testing"""
        nodes = []
        for i in range(count):
            priority = 1 if i % 10 < 3 else 2 if i % 10 < 7 else 3
            load = 50.0 + (i % 200)  # 50-250 kW range
            
            node = EnergyNode(
                node_id=f"load_test_node_{i:06d}",
                current_load=load,
                priority_tier=priority,
                source_type="Grid",
                status="active",
                location={"lat": 28.6139 + (i * 0.0001), "lng": 77.2090 + (i * 0.0001)},
                timestamp=time.time()
            )
            nodes.append(node)
        
        return nodes
    
    def _create_test_supply_event(self, total_supply: float) -> SupplyEvent:
        """Create test supply event"""
        return SupplyEvent(
            event_id=f"load_test_supply_{int(time.time())}",
            total_supply=total_supply,
            available_sources={
                "solar": total_supply * 0.4,
                "grid": total_supply * 0.3,
                "battery": total_supply * 0.2,
                "diesel": total_supply * 0.1
            },
            timestamp=time.time()
        )
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            import psutil
            process = psutil.Process()
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': process.memory_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'thread_count': process.num_threads(),
                'timestamp': time.time()
            }
        except ImportError:
            return {'timestamp': time.time()}
    
    def generate_load_test_report(self) -> str:
        """Generate comprehensive load test report"""
        if not self.results:
            return "No load test results available"
        
        report = []
        report.append("BHARAT-GRID AI LOAD TEST REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Overall summary
        total_requests = sum(r.total_requests for r in self.results)
        total_errors = sum(r.failed_requests for r in self.results)
        overall_error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0
        
        report.append("OVERALL SUMMARY")
        report.append("-" * 20)
        report.append(f"Total Requests: {total_requests:,}")
        report.append(f"Total Errors: {total_errors:,}")
        report.append(f"Overall Error Rate: {overall_error_rate:.2f}%")
        report.append("")
        
        # Individual test results
        for result in self.results:
            report.append(f"{result.test_name.upper()}")
            report.append("-" * len(result.test_name))
            report.append(f"Duration: {result.duration_seconds:.1f}s")
            report.append(f"Requests: {result.total_requests:,} ({result.requests_per_second:.1f} RPS)")
            report.append(f"Success Rate: {((result.successful_requests / result.total_requests) * 100):.1f}%")
            report.append(f"Error Rate: {result.error_rate:.2f}%")
            
            # Latency statistics
            report.append("Latency Statistics:")
            for metric, value in result.latency_stats.items():
                report.append(f"  {metric}: {value:.2f}ms")
            
            # Target compliance
            target_compliance = 100 - result.violation_rate
            status = "✓ PASS" if result.violation_rate < 5.0 else "✗ FAIL"
            report.append(f"Target Compliance: {target_compliance:.1f}% {status}")
            report.append(f"Target Violations: {result.target_violations} ({result.violation_rate:.1f}%)")
            
            # System metrics
            if result.system_metrics:
                report.append("System Metrics:")
                for metric, value in result.system_metrics.items():
                    if isinstance(value, float):
                        report.append(f"  {metric}: {value:.2f}")
                    else:
                        report.append(f"  {metric}: {value}")
            
            report.append("")
        
        # Performance targets summary
        report.append("PERFORMANCE TARGETS COMPLIANCE")
        report.append("-" * 35)
        
        # Check each target
        allocation_result = next((r for r in self.results if "Allocation" in r.test_name), None)
        websocket_result = next((r for r in self.results if "WebSocket" in r.test_name), None)
        rag_result = next((r for r in self.results if "RAG" in r.test_name), None)
        
        if allocation_result:
            status = "✓ PASS" if allocation_result.latency_stats['avg_ms'] < 10.0 else "✗ FAIL"
            report.append(f"Allocation Latency (<10ms): {allocation_result.latency_stats['avg_ms']:.2f}ms {status}")
        
        if websocket_result:
            avg_msg_latency = websocket_result.latency_stats.get('message_avg_ms', 0)
            status = "✓ PASS" if avg_msg_latency < 50.0 else "✗ FAIL"
            report.append(f"WebSocket Latency (<50ms): {avg_msg_latency:.2f}ms {status}")
        
        if rag_result:
            status = "✓ PASS" if rag_result.latency_stats['avg_ms'] < 2000.0 else "✗ FAIL"
            report.append(f"RAG Response Time (<2s): {rag_result.latency_stats['avg_ms']:.0f}ms {status}")
        
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 15)
        
        if allocation_result and allocation_result.violation_rate > 5.0:
            report.append("• Optimize allocation algorithm for large node counts")
            report.append("• Enable vectorized processing for >1000 nodes")
        
        if websocket_result and websocket_result.violation_rate > 5.0:
            report.append("• Implement WebSocket message batching")
            report.append("• Optimize JSON serialization")
        
        if rag_result and rag_result.violation_rate > 5.0:
            report.append("• Enable RAG response caching")
            report.append("• Optimize vector search parameters")
        
        if overall_error_rate > 1.0:
            report.append("• Investigate error causes and improve error handling")
        
        report.append("")
        report.append(f"Report generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(report)
    
    def save_results(self, filename: str = "load_test_results.json"):
        """Save load test results to JSON file"""
        results_data = []
        for result in self.results:
            results_data.append({
                'test_name': result.test_name,
                'duration_seconds': result.duration_seconds,
                'total_requests': result.total_requests,
                'successful_requests': result.successful_requests,
                'failed_requests': result.failed_requests,
                'requests_per_second': result.requests_per_second,
                'latency_stats': result.latency_stats,
                'error_rate': result.error_rate,
                'target_violations': result.target_violations,
                'violation_rate': result.violation_rate,
                'system_metrics': result.system_metrics
            })
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"Load test results saved to: {filename}")


async def run_performance_validation():
    """
    Run complete performance validation with load testing
    """
    print("🎯 Starting Performance Validation with Load Testing")
    print("=" * 60)
    
    # Configuration for load tests
    config = LoadTestConfig(
        duration_seconds=30,  # 30 second tests for validation
        allocation_rps=50,    # 50 allocation requests per second
        websocket_connections=20,  # 20 concurrent WebSocket connections
        rag_rps=5,           # 5 RAG requests per second
        node_count=1000,     # 1000 nodes per allocation
        ramp_up_seconds=5    # 5 second ramp up
    )
    
    # Run load tests
    runner = LoadTestRunner()
    
    try:
        results = await runner.run_comprehensive_load_test(config)
        
        # Generate and display report
        report = runner.generate_load_test_report()
        print("\n" + report)
        
        # Save results
        runner.save_results("performance_validation_results.json")
        
        # Save report
        with open("performance_validation_report.txt", "w") as f:
            f.write(report)
        
        # Check overall success
        all_tests_passed = all(
            result.violation_rate < 5.0 and result.error_rate < 1.0 
            for result in results
        )
        
        print(f"\n🎯 Performance Validation: {'✅ PASSED' if all_tests_passed else '❌ FAILED'}")
        
        return all_tests_passed
        
    except Exception as e:
        print(f"❌ Load testing failed: {e}")
        return False


if __name__ == "__main__":
    # Run performance validation
    success = asyncio.run(run_performance_validation())
    
    if success:
        print("\n🎉 All performance targets validated under load!")
    else:
        print("\n⚠️  Performance validation failed. Check report for details.")