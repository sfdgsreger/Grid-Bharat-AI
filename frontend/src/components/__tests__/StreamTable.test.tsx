import { render, screen } from '@testing-library/react';
import StreamTable from '../StreamTable';
import type { AllocationResult } from '../../types';

// Mock data for testing
const mockAllocations: AllocationResult[] = [
  {
    node_id: 'hospital_001',
    allocated_power: 150,
    source_mix: { grid: 150 },
    action: 'maintain',
    latency_ms: 5,
    timestamp: Date.now()
  },
  {
    node_id: 'factory_001',
    allocated_power: 250,
    source_mix: { solar: 250 },
    action: 'reduce',
    latency_ms: 7,
    timestamp: Date.now() - 1000
  },
  {
    node_id: 'residential_001',
    allocated_power: 0,
    source_mix: {},
    action: 'cutoff',
    latency_ms: 3,
    timestamp: Date.now() - 2000
  }
];

describe('StreamTable Component', () => {
  it('renders table with allocation data', () => {
    render(<StreamTable allocations={mockAllocations} />);
    
    // Check if table headers are present
    expect(screen.getByText('Node ID')).toBeInTheDocument();
    expect(screen.getByText('Power')).toBeInTheDocument();
    expect(screen.getByText('Action')).toBeInTheDocument();
    expect(screen.getByText('Latency')).toBeInTheDocument();
    expect(screen.getByText('Time')).toBeInTheDocument();
    
    // Check if data is displayed
    expect(screen.getByText('hospital_001')).toBeInTheDocument();
    expect(screen.getByText('factory_001')).toBeInTheDocument();
    expect(screen.getByText('residential_001')).toBeInTheDocument();
  });

  it('displays correct action colors and badges', () => {
    render(<StreamTable allocations={mockAllocations} />);
    
    // Check if action badges are present
    expect(screen.getByText('maintain')).toBeInTheDocument();
    expect(screen.getByText('reduce')).toBeInTheDocument();
    expect(screen.getByText('cutoff')).toBeInTheDocument();
  });

  it('formats power values correctly', () => {
    const highPowerAllocation: AllocationResult[] = [
      {
        node_id: 'test_node',
        allocated_power: 1500, // Should display as MW
        source_mix: { grid: 1500 },
        action: 'maintain',
        latency_ms: 5,
        timestamp: Date.now()
      }
    ];

    render(<StreamTable allocations={highPowerAllocation} />);
    expect(screen.getByText('1.5 MW')).toBeInTheDocument();
  });

  it('shows empty state when no allocations', () => {
    render(<StreamTable allocations={[]} />);
    
    expect(screen.getByText('Waiting for allocation data...')).toBeInTheDocument();
    expect(screen.getByText('Real-time updates will appear here')).toBeInTheDocument();
  });

  it('respects maxRows prop', () => {
    const manyAllocations = Array.from({ length: 20 }, (_, i) => ({
      node_id: `node_${i}`,
      allocated_power: 100,
      source_mix: { grid: 100 },
      action: 'maintain' as const,
      latency_ms: 5,
      timestamp: Date.now() - i * 1000
    }));

    render(<StreamTable allocations={manyAllocations} maxRows={5} />);
    
    // Should only show 5 entries
    expect(screen.getByText('Showing 5 of 5 entries')).toBeInTheDocument();
  });

  it('calculates and displays average latency', () => {
    render(<StreamTable allocations={mockAllocations} />);
    
    // Average of 5, 7, 3 should be 5.0
    expect(screen.getByText('5.0ms')).toBeInTheDocument();
  });

  it('displays summary statistics', () => {
    render(<StreamTable allocations={mockAllocations} />);
    
    // Check summary stats
    expect(screen.getByText('Maintain: 1')).toBeInTheDocument();
    expect(screen.getByText('Reduce: 1')).toBeInTheDocument();
    expect(screen.getByText('Cutoff: 1')).toBeInTheDocument();
  });
});