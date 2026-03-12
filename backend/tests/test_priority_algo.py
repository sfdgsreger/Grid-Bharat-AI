# Unit tests for priority allocation algorithm
import pytest
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import EnergyNode, SupplyEvent, AvailableSources, Location
from utils.priority_algo import PriorityAllocator, allocate_power_priority


class TestPriorityAllocator:
    """Test suite for priority allocation algorithm"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.allocator = PriorityAllocator()
        
        # Sample nodes with different priorities
        self.hospital = EnergyNode(
            node_id="hospital_1",
            current_load=100.0,
            priority_tier=1,
            source_type="Grid",
            status="active",
            location=Location(lat=28.6139, lng=77.2090),
            timestamp=time.time()
        )
        
        self.factory = EnergyNode(
            node_id="factory_1", 
            current_load=200.0,
            priority_tier=2,
            source_type="Grid",
            status="active",
            location=Location(lat=28.6139, lng=77.2090),
            timestamp=time.time()
        )
        
        self.residential = EnergyNode(
            node_id="residential_1",
            current_load=50.0,
            priority_tier=3,
            source_type="Grid", 
            status="active",
            location=Location(lat=28.6139, lng=77.2090),
            timestamp=time.time()
        )
        
        # Sample supply event
        self.supply_event = SupplyEvent(
            event_id="supply_1",
            total_supply=400.0,
            available_sources=AvailableSources(
                solar=150.0,
                grid=100.0,
                battery=100.0,
                diesel=50.0
            ),
            timestamp=time.time()
        )
    
    def test_full_supply_allocation(self):
        """Test allocation when supply exceeds demand"""
        nodes = [self.hospital, self.factory, self.residential]
        allocations = self.allocator.allocate_power(nodes, self.supply_event)
        
        # All nodes should get full power (maintain action)
        assert len(allocations) == 3
        assert all(a.action == 'maintain' for a in allocations)
        assert all(a.allocated_power == node.current_load for a, node in zip(allocations, sorted(nodes, key=lambda n: n.priority_tier)))
        
        # Verify power conservation
        total_allocated = sum(a.allocated_power for a in allocations)
        assert total_allocated == 350.0  # 100 + 200 + 50
        assert self.allocator.validate_power_conservation(allocations, self.supply_event.total_supply)
    
    def test_priority_ordering(self):
        """Test that higher priority nodes get power first"""
        # Create supply shortage scenario
        shortage_supply = SupplyEvent(
            event_id="shortage_1",
            total_supply=250.0,  # Less than total demand (350)
            available_sources=AvailableSources(
                solar=100.0,
                grid=100.0,
                battery=50.0,
                diesel=0.0
            ),
            timestamp=time.time()
        )
        
        nodes = [self.residential, self.factory, self.hospital]  # Mixed order
        allocations = self.allocator.allocate_power(nodes, shortage_supply)
        
        # Find allocations by node type
        hospital_alloc = next(a for a in allocations if a.node_id == "hospital_1")
        factory_alloc = next(a for a in allocations if a.node_id == "factory_1") 
        residential_alloc = next(a for a in allocations if a.node_id == "residential_1")
        
        # Hospital (tier 1) should get full power (100kW from 250kW available)
        assert hospital_alloc.action == 'maintain'
        assert hospital_alloc.allocated_power == 100.0
        
        # Factory (tier 2) should get partial power (150kW remaining, needs 200kW)
        assert factory_alloc.action == 'reduce'
        assert factory_alloc.allocated_power == 150.0
        
        # Residential (tier 3) should get no power (0kW remaining)
        assert residential_alloc.action == 'cutoff'
        assert residential_alloc.allocated_power == 0.0
        
        # Verify total allocation doesn't exceed supply
        total_allocated = sum(a.allocated_power for a in allocations)
        assert total_allocated == 250.0
        assert self.allocator.validate_power_conservation(allocations, shortage_supply.total_supply)
    
    def test_source_mix_optimization(self):
        """Test that source mix follows preference order: Solar > Grid > Battery > Diesel"""
        nodes = [self.hospital]  # Single node for clear source tracking
        allocations = self.allocator.allocate_power(nodes, self.supply_event)
        
        allocation = allocations[0]
        source_mix = allocation.source_mix
        
        # Should prefer solar first (100kW needed, 150kW solar available)
        assert source_mix.solar == 100.0
        assert source_mix.grid is None or source_mix.grid == 0
        assert source_mix.battery is None or source_mix.battery == 0
        assert source_mix.diesel is None or source_mix.diesel == 0
    
    def test_partial_allocation(self):
        """Test partial allocation when supply is insufficient"""
        # Create severe shortage
        shortage_supply = SupplyEvent(
            event_id="severe_shortage",
            total_supply=80.0,  # Much less than hospital demand (100)
            available_sources=AvailableSources(
                solar=50.0,
                grid=30.0,
                battery=0.0,
                diesel=0.0
            ),
            timestamp=time.time()
        )
        
        nodes = [self.hospital]
        allocations = self.allocator.allocate_power(nodes, shortage_supply)
        
        allocation = allocations[0]
        assert allocation.action == 'reduce'
        assert allocation.allocated_power == 80.0
        assert allocation.source_mix.solar == 50.0
        assert allocation.source_mix.grid == 30.0
    
    def test_zero_supply_cutoff(self):
        """Test cutoff action when no supply available"""
        zero_supply = SupplyEvent(
            event_id="zero_supply",
            total_supply=0.0,
            available_sources=AvailableSources(
                solar=0.0,
                grid=0.0,
                battery=0.0,
                diesel=0.0
            ),
            timestamp=time.time()
        )
        
        nodes = [self.hospital]
        allocations = self.allocator.allocate_power(nodes, zero_supply)
        
        allocation = allocations[0]
        assert allocation.action == 'cutoff'
        assert allocation.allocated_power == 0.0
    
    def test_latency_tracking(self):
        """Test that latency is tracked for each allocation"""
        nodes = [self.hospital, self.factory, self.residential]
        allocations = self.allocator.allocate_power(nodes, self.supply_event)
        
        # All allocations should have latency measurements
        assert all(a.latency_ms >= 0 for a in allocations)
        
        # Latency should be reasonable (< 10ms for this simple case)
        assert all(a.latency_ms < 10.0 for a in allocations)
    
    def test_diesel_usage_tracking(self):
        """Test diesel usage tracking for carbon footprint monitoring"""
        # Create scenario that requires diesel
        diesel_supply = SupplyEvent(
            event_id="diesel_needed",
            total_supply=100.0,
            available_sources=AvailableSources(
                solar=20.0,
                grid=30.0,
                battery=0.0,
                diesel=50.0
            ),
            timestamp=time.time()
        )
        
        nodes = [self.hospital]  # Needs 100kW
        allocations = self.allocator.allocate_power(nodes, diesel_supply)
        
        # Should use all clean sources first, then diesel
        allocation = allocations[0]
        assert allocation.source_mix.solar == 20.0
        assert allocation.source_mix.grid == 30.0
        assert allocation.source_mix.diesel == 50.0
        
        # Track total diesel usage
        total_diesel = self.allocator.get_total_diesel_usage(allocations)
        assert total_diesel == 50.0
    
    def test_allocation_summary(self):
        """Test allocation summary statistics"""
        nodes = [self.hospital, self.factory, self.residential]
        allocations = self.allocator.allocate_power(nodes, self.supply_event)
        
        summary = self.allocator.get_allocation_summary(allocations)
        
        assert summary['total_nodes'] == 3
        assert summary['total_allocated'] == 350.0
        assert summary['actions']['maintain'] == 3
        assert summary['actions']['reduce'] == 0
        assert summary['actions']['cutoff'] == 0
        assert summary['avg_latency_ms'] >= 0
    
    def test_convenience_function(self):
        """Test the convenience function works correctly"""
        nodes = [self.hospital]
        allocations = allocate_power_priority(nodes, self.supply_event)
        
        assert len(allocations) == 1
        assert allocations[0].node_id == "hospital_1"
        assert allocations[0].action == 'maintain'
    
    def test_empty_nodes_list(self):
        """Test handling of empty nodes list"""
        allocations = self.allocator.allocate_power([], self.supply_event)
        assert len(allocations) == 0
        
        summary = self.allocator.get_allocation_summary(allocations)
        assert summary['total_nodes'] == 0
        assert summary['total_allocated'] == 0.0
    
    def test_single_node_scenarios(self):
        """Test various single node scenarios"""
        # Test with exact supply match
        exact_supply = SupplyEvent(
            event_id="exact_match",
            total_supply=100.0,
            available_sources=AvailableSources(solar=100.0, grid=0.0, battery=0.0, diesel=0.0),
            timestamp=time.time()
        )
        
        allocations = self.allocator.allocate_power([self.hospital], exact_supply)
        assert len(allocations) == 1
        assert allocations[0].action == 'maintain'
        assert allocations[0].allocated_power == 100.0
    
    def test_equal_priority_nodes(self):
        """Test allocation among nodes with equal priority"""
        hospital2 = EnergyNode(
            node_id="hospital_2",
            current_load=80.0,
            priority_tier=1,  # Same priority as hospital_1
            source_type="Grid",
            status="active",
            location=Location(lat=28.6139, lng=77.2090),
            timestamp=time.time()
        )
        
        # Limited supply scenario
        limited_supply = SupplyEvent(
            event_id="limited",
            total_supply=150.0,  # Less than both hospitals need (180 total)
            available_sources=AvailableSources(solar=150.0, grid=0.0, battery=0.0, diesel=0.0),
            timestamp=time.time()
        )
        
        nodes = [hospital2, self.hospital]  # Both tier 1
        allocations = self.allocator.allocate_power(nodes, limited_supply)
        
        # First hospital in sorted order should get full power, second gets remainder
        sorted_allocations = sorted(allocations, key=lambda a: a.node_id)
        
        # Total allocation should not exceed supply
        total_allocated = sum(a.allocated_power for a in allocations)
        assert total_allocated <= 150.0
        assert self.allocator.validate_power_conservation(allocations, limited_supply.total_supply)
    
    def test_performance_with_many_nodes(self):
        """Test performance with larger number of nodes"""
        import time
        
        # Create 100 nodes with mixed priorities
        many_nodes = []
        for i in range(100):
            node = EnergyNode(
                node_id=f"node_{i}",
                current_load=10.0,  # 10kW each
                priority_tier=(i % 3) + 1,  # Mix of priorities 1, 2, 3
                source_type="Grid",
                status="active",
                location=Location(lat=28.6139, lng=77.2090),
                timestamp=time.time()
            )
            many_nodes.append(node)
        
        # Large supply event
        large_supply = SupplyEvent(
            event_id="large_supply",
            total_supply=500.0,  # Less than total demand (1000kW)
            available_sources=AvailableSources(
                solar=200.0,
                grid=200.0,
                battery=100.0,
                diesel=0.0
            ),
            timestamp=time.time()
        )
        
        start_time = time.perf_counter()
        allocations = self.allocator.allocate_power(many_nodes, large_supply)
        total_time = (time.perf_counter() - start_time) * 1000
        
        # Should complete within performance target
        assert total_time < 10.0, f"Allocation took {total_time:.2f}ms, exceeds 10ms target"
        
        # Should allocate to all nodes
        assert len(allocations) == 100
        
        # Should respect power conservation
        assert self.allocator.validate_power_conservation(allocations, large_supply.total_supply)
        
        # Check that priority ordering is respected
        # Group allocations by the original node priority
        tier1_allocations = []
        tier2_allocations = []
        tier3_allocations = []
        
        for allocation in allocations:
            node_index = int(allocation.node_id.split('_')[1])
            tier = (node_index % 3) + 1
            
            if tier == 1:
                tier1_allocations.append(allocation)
            elif tier == 2:
                tier2_allocations.append(allocation)
            else:
                tier3_allocations.append(allocation)
        
        # If any tier 1 node is cut off, all tier 2 and 3 should be cut off
        tier1_cutoffs = [a for a in tier1_allocations if a.action == 'cutoff']
        if tier1_cutoffs:
            tier2_cutoffs = [a for a in tier2_allocations if a.action == 'cutoff']
            tier3_cutoffs = [a for a in tier3_allocations if a.action == 'cutoff']
            
            # All tier 2 and 3 should be cut off if tier 1 nodes are cut off
            assert len(tier2_cutoffs) == len(tier2_allocations), "All tier 2 nodes should be cut off if tier 1 nodes are cut off"
            assert len(tier3_cutoffs) == len(tier3_allocations), "All tier 3 nodes should be cut off if tier 1 nodes are cut off"
        
        # Similarly, if any tier 2 node is cut off, all tier 3 should be cut off
        tier2_cutoffs = [a for a in tier2_allocations if a.action == 'cutoff']
        if tier2_cutoffs and not tier1_cutoffs:  # Only check if tier 1 is not cut off
            tier3_cutoffs = [a for a in tier3_allocations if a.action == 'cutoff']
            assert len(tier3_cutoffs) == len(tier3_allocations), "All tier 3 nodes should be cut off if tier 2 nodes are cut off"


if __name__ == "__main__":
    pytest.main([__file__])