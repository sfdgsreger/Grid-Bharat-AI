import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PowerMap from '../components/PowerMap';
import type { EnergyNode, AllocationResult } from '../types';

// Sample test data
const sampleNodes: EnergyNode[] = [
  {
    node_id: 'hospital_001',
    current_load: 150,
    priority_tier: 1,
    source_type: 'Grid',
    status: 'active',
    location: { lat: 28.6139, lng: 77.2090 },
    timestamp: Date.now(),
  },
  {
    node_id: 'factory_001',
    current_load: 300,
    priority_tier: 2,
    source_type: 'Solar',
    status: 'active',
    location: { lat: 28.6200, lng: 77.2100 },
    timestamp: Date.now(),
  },
  {
    node_id: 'residential_001',
    current_load: 75,
    priority_tier: 3,
    source_type: 'Battery',
    status: 'active',
    location: { lat: 28.6100, lng: 77.2050 },
    timestamp: Date.now(),
  },
];

const sampleAllocations: AllocationResult[] = [
  {
    node_id: 'hospital_001',
    allocated_power: 150,
    source_mix: { grid: 150 },
    action: 'maintain',
    latency_ms: 5,
  },
  {
    node_id: 'factory_001',
    allocated_power: 250,
    source_mix: { solar: 250 },
    action: 'reduce',
    latency_ms: 7,
  },
  {
    node_id: 'residential_001',
    allocated_power: 0,
    source_mix: {},
    action: 'cutoff',
    latency_ms: 3,
  },
];

describe('PowerMap Component', () => {
  it('renders the power connection map title', () => {
    render(<PowerMap nodes={sampleNodes} allocations={sampleAllocations} />);
    expect(screen.getByText('Power Connection Map')).toBeInTheDocument();
  });

  it('renders the central grid hub', () => {
    render(<PowerMap nodes={sampleNodes} allocations={sampleAllocations} />);
    expect(screen.getByText('Grid Hub')).toBeInTheDocument();
  });

  it('displays correct status counts in legend', () => {
    render(<PowerMap nodes={sampleNodes} allocations={sampleAllocations} />);
    
    // Check status counts
    expect(screen.getByText('Maintain (1)')).toBeInTheDocument();
    expect(screen.getByText('Reduce (1)')).toBeInTheDocument();
    expect(screen.getByText('Cutoff (1)')).toBeInTheDocument();
  });

  it('displays total nodes and active allocations', () => {
    render(<PowerMap nodes={sampleNodes} allocations={sampleAllocations} />);
    
    expect(screen.getByText('Total Nodes: 3')).toBeInTheDocument();
    expect(screen.getByText('Active Allocations: 3')).toBeInTheDocument();
  });

  it('shows priority tier legend', () => {
    render(<PowerMap nodes={sampleNodes} allocations={sampleAllocations} />);
    
    expect(screen.getByText('Priority 1 (Hospital)')).toBeInTheDocument();
    expect(screen.getByText('Priority 2 (Factory)')).toBeInTheDocument();
    expect(screen.getByText('Priority 3 (Residential)')).toBeInTheDocument();
  });

  it('renders nodes with correct positioning', () => {
    render(<PowerMap nodes={sampleNodes} allocations={sampleAllocations} />);
    
    // Check that nodes are rendered (they should have priority tier indicators)
    const priorityIndicators = screen.getAllByText('1');
    expect(priorityIndicators.length).toBeGreaterThan(0);
    
    const priority2Indicators = screen.getAllByText('2');
    expect(priority2Indicators.length).toBeGreaterThan(0);
    
    const priority3Indicators = screen.getAllByText('3');
    expect(priority3Indicators.length).toBeGreaterThan(0);
  });

  it('handles empty nodes gracefully', () => {
    render(<PowerMap nodes={[]} allocations={[]} />);
    
    expect(screen.getByText('No Energy Nodes')).toBeInTheDocument();
    expect(screen.getByText('Waiting for real-time data...')).toBeInTheDocument();
  });

  it('displays correct statistics with empty data', () => {
    render(<PowerMap nodes={[]} allocations={[]} />);
    
    expect(screen.getByText('Total Nodes: 0')).toBeInTheDocument();
    expect(screen.getByText('Active Allocations: 0')).toBeInTheDocument();
    expect(screen.getByText('Maintain (0)')).toBeInTheDocument();
    expect(screen.getByText('Reduce (0)')).toBeInTheDocument();
    expect(screen.getByText('Cutoff (0)')).toBeInTheDocument();
  });
});