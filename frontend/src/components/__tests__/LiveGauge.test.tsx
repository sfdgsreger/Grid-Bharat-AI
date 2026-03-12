import React from 'react';
import { render, screen } from '@testing-library/react';
import { LiveGauge } from '../LiveGauge';

describe('LiveGauge Component', () => {
  const defaultProps = {
    title: 'Test Gauge',
    value: 500,
    max: 1000,
    unit: 'kW',
    color: 'blue' as const
  };

  it('renders gauge with correct title and values', () => {
    render(<LiveGauge {...defaultProps} />);
    
    expect(screen.getByText('Test Gauge')).toBeInTheDocument();
    expect(screen.getByText('500')).toBeInTheDocument();
    expect(screen.getByText('kW')).toBeInTheDocument();
    expect(screen.getByText('Max:')).toBeInTheDocument();
    expect(screen.getByText('1,000 kW')).toBeInTheDocument();
  });

  it('calculates percentage correctly', () => {
    render(<LiveGauge {...defaultProps} />);
    
    // 500/1000 = 50%
    expect(screen.getByText('50.0%')).toBeInTheDocument();
  });

  it('shows correct status based on percentage', () => {
    // Normal status (< 75%)
    render(<LiveGauge {...defaultProps} value={700} />);
    expect(screen.getByText('Normal')).toBeInTheDocument();
    
    // High status (75-90%)
    render(<LiveGauge {...defaultProps} value={800} />);
    expect(screen.getByText('High')).toBeInTheDocument();
    
    // Critical status (> 90%)
    render(<LiveGauge {...defaultProps} value={950} />);
    expect(screen.getByText('Critical')).toBeInTheDocument();
  });

  it('handles different color variants', () => {
    const { rerender } = render(<LiveGauge {...defaultProps} color="red" />);
    
    // Test that component renders without errors for different colors
    rerender(<LiveGauge {...defaultProps} color="green" />);
    rerender(<LiveGauge {...defaultProps} color="yellow" />);
    rerender(<LiveGauge {...defaultProps} color="blue" />);
    
    expect(screen.getByText('Test Gauge')).toBeInTheDocument();
  });

  it('handles edge cases correctly', () => {
    // Zero value
    render(<LiveGauge {...defaultProps} value={0} />);
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('0.0%')).toBeInTheDocument();
    
    // Value exceeding max
    render(<LiveGauge {...defaultProps} value={1500} />);
    expect(screen.getByText('1,500')).toBeInTheDocument();
    expect(screen.getByText('100.0%')).toBeInTheDocument(); // Should cap at 100%
  });
});