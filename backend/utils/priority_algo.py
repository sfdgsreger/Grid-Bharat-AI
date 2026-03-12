# Priority-based power allocation algorithm for Bharat-Grid AI
# Implements O(n) allocation with source mix optimization and latency tracking

import time
from typing import List, Dict, Tuple
try:
    from ..schemas import EnergyNode, SupplyEvent, AllocationResult, SourceMix, AvailableSources
    from .latency_tracker import global_tracker, PerformanceContext
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from schemas import EnergyNode, SupplyEvent, AllocationResult, SourceMix, AvailableSources
    from utils.latency_tracker import global_tracker, PerformanceContext


class PriorityAllocator:
    """
    O(n) priority-based power allocation engine with source mix optimization.
    
    Allocates power to nodes based on priority tiers:
    - Tier 1 (Hospitals): Highest priority
    - Tier 2 (Factories): Medium priority  
    - Tier 3 (Residential): Lowest priority
    
    Source preference order (for carbon footprint minimization):
    Solar > Grid > Battery > Diesel
    """
    
    def __init__(self):
        self.source_preference = ['solar', 'grid', 'battery', 'diesel']
    
    def allocate_power(
        self, 
        nodes: List[EnergyNode], 
        supply_event: SupplyEvent
    ) -> List[AllocationResult]:
        """
        Allocate available power to nodes based on priority tiers.
        
        Args:
            nodes: List of energy nodes requiring power
            supply_event: Current power supply availability
            
        Returns:
            List of allocation results for each node
            
        Performance: O(n log n) for sorting + O(n) for allocation = O(n log n)
        Target latency: <10ms
        """
        with PerformanceContext(global_tracker, 'allocation', {'node_count': len(nodes)}):
            start_time = time.perf_counter()
            
            # Sort nodes by priority tier (O(n log n))
            # Tier 1 (hospitals) first, then tier 2 (factories), then tier 3 (residential)
            sorted_nodes = sorted(nodes, key=lambda node: node.priority_tier)
            
            # Initialize remaining supply sources
            remaining_sources = {
                'solar': supply_event.available_sources.solar,
                'grid': supply_event.available_sources.grid,
                'battery': supply_event.available_sources.battery,
                'diesel': supply_event.available_sources.diesel
            }
            
            allocations = []
            
            # Single pass allocation (O(n))
            for node in sorted_nodes:
                allocation_start = time.perf_counter()
                
                # Calculate optimal source mix for this node
                allocated_power, source_mix, action = self._allocate_to_node(
                    node, remaining_sources
                )
                
                # Update remaining sources
                for source, amount in source_mix.items():
                    if amount and amount > 0:
                        remaining_sources[source] -= amount
                
                # Calculate processing latency for this allocation
                allocation_latency = (time.perf_counter() - allocation_start) * 1000
                
                # Create allocation result
                allocation = AllocationResult(
                    node_id=node.node_id,
                    allocated_power=allocated_power,
                    source_mix=SourceMix(
                        solar=source_mix.get('solar'),
                        grid=source_mix.get('grid'),
                        battery=source_mix.get('battery'),
                        diesel=source_mix.get('diesel')
                    ),
                    action=action,
                    latency_ms=allocation_latency
                )
                
                allocations.append(allocation)
            
            # Calculate total processing time
            total_latency = (time.perf_counter() - start_time) * 1000
            
            # Log performance warning if target exceeded (handled by PerformanceContext)
            return allocations
    
    def _allocate_to_node(
        self, 
        node: EnergyNode, 
        remaining_sources: Dict[str, float]
    ) -> Tuple[float, Dict[str, float], str]:
        """
        Allocate power to a single node using source mix optimization.
        
        Args:
            node: Energy node requiring power
            remaining_sources: Available power from each source
            
        Returns:
            Tuple of (allocated_power, source_mix, action)
        """
        required_power = node.current_load
        total_available = sum(remaining_sources.values())
        
        # If no power available, cutoff
        if total_available <= 0:
            return 0.0, {}, 'cutoff'
        
        # If full power available, maintain with optimal source mix
        if total_available >= required_power:
            source_mix = self._optimize_source_mix(required_power, remaining_sources)
            return required_power, source_mix, 'maintain'
        
        # Partial power available, reduce with optimal source mix
        source_mix = self._optimize_source_mix(total_available, remaining_sources)
        return total_available, source_mix, 'reduce'
    
    def _optimize_source_mix(
        self, 
        target_power: float, 
        available_sources: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Optimize source mix to minimize carbon footprint.
        
        Preference order: Solar > Grid > Battery > Diesel
        
        Args:
            target_power: Amount of power to allocate
            available_sources: Available power from each source
            
        Returns:
            Dictionary mapping source to allocated amount
        """
        source_mix = {}
        remaining_power = target_power
        
        # Allocate from sources in preference order
        for source in self.source_preference:
            if remaining_power <= 0:
                break
                
            available = available_sources.get(source, 0)
            if available <= 0:
                continue
            
            # Allocate as much as possible from this source
            allocated = min(remaining_power, available)
            if allocated > 0:
                source_mix[source] = allocated
                remaining_power -= allocated
        
        return source_mix
    
    def get_total_diesel_usage(self, allocations: List[AllocationResult]) -> float:
        """
        Calculate total diesel usage across all allocations.
        
        Args:
            allocations: List of allocation results
            
        Returns:
            Total diesel power allocated in kW
        """
        total_diesel = 0.0
        for allocation in allocations:
            if allocation.source_mix.diesel:
                total_diesel += allocation.source_mix.diesel
        return total_diesel
    
    def validate_power_conservation(
        self, 
        allocations: List[AllocationResult], 
        total_supply: float
    ) -> bool:
        """
        Validate that total allocated power does not exceed total supply.
        
        Args:
            allocations: List of allocation results
            total_supply: Total available power supply
            
        Returns:
            True if power conservation is maintained
        """
        total_allocated = sum(allocation.allocated_power for allocation in allocations)
        return total_allocated <= total_supply + 1e-6  # Allow for floating point precision
    
    def get_allocation_summary(self, allocations: List[AllocationResult]) -> Dict:
        """
        Generate summary statistics for allocation results.
        
        Args:
            allocations: List of allocation results
            
        Returns:
            Dictionary with allocation statistics
        """
        if not allocations:
            return {
                'total_nodes': 0,
                'total_allocated': 0.0,
                'actions': {'maintain': 0, 'reduce': 0, 'cutoff': 0},
                'source_breakdown': {'solar': 0.0, 'grid': 0.0, 'battery': 0.0, 'diesel': 0.0},
                'avg_latency_ms': 0.0
            }
        
        # Calculate statistics
        total_allocated = sum(a.allocated_power for a in allocations)
        actions = {'maintain': 0, 'reduce': 0, 'cutoff': 0}
        source_breakdown = {'solar': 0.0, 'grid': 0.0, 'battery': 0.0, 'diesel': 0.0}
        total_latency = sum(a.latency_ms for a in allocations)
        
        for allocation in allocations:
            actions[allocation.action] += 1
            
            # Sum up source usage
            if allocation.source_mix.solar:
                source_breakdown['solar'] += allocation.source_mix.solar
            if allocation.source_mix.grid:
                source_breakdown['grid'] += allocation.source_mix.grid
            if allocation.source_mix.battery:
                source_breakdown['battery'] += allocation.source_mix.battery
            if allocation.source_mix.diesel:
                source_breakdown['diesel'] += allocation.source_mix.diesel
        
        return {
            'total_nodes': len(allocations),
            'total_allocated': total_allocated,
            'actions': actions,
            'source_breakdown': source_breakdown,
            'avg_latency_ms': total_latency / len(allocations),
            'total_diesel_usage': source_breakdown['diesel']
        }


# Convenience function for direct usage
def allocate_power_priority(
    nodes: List[EnergyNode], 
    supply_event: SupplyEvent
) -> List[AllocationResult]:
    """
    Convenience function for priority-based power allocation.
    
    Args:
        nodes: List of energy nodes requiring power
        supply_event: Current power supply availability
        
    Returns:
        List of allocation results for each node
    """
    allocator = PriorityAllocator()
    return allocator.allocate_power(nodes, supply_event)