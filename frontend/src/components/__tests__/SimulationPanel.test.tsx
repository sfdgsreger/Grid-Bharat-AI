import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SimulationPanel from '../SimulationPanel';

// Mock fetch for testing
global.fetch = jest.fn();

describe('SimulationPanel Component', () => {
  const mockOnSimulate = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    (fetch as jest.Mock).mockClear();
  });

  it('renders simulation panel with default values', () => {
    render(<SimulationPanel onSimulate={mockOnSimulate} isSimulating={false} />);
    
    expect(screen.getByText('Grid Failure Simulation')).toBeInTheDocument();
    expect(screen.getByText('Ready to simulate')).toBeInTheDocument();
    expect(screen.getByText('25%')).toBeInTheDocument(); // Default percentage
    expect(screen.getByText('Simulate 25% Grid Failure')).toBeInTheDocument();
  });

  it('updates percentage when slider changes', () => {
    render(<SimulationPanel onSimulate={mockOnSimulate} isSimulating={false} />);
    
    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '50' } });
    
    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText('Simulate 50% Grid Failure')).toBeInTheDocument();
  });

  it('updates percentage when input field changes', () => {
    render(<SimulationPanel onSimulate={mockOnSimulate} isSimulating={false} />);
    
    const input = screen.getByDisplayValue('25');
    fireEvent.change(input, { target: { value: '75' } });
    
    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.getByText('Simulate 75% Grid Failure')).toBeInTheDocument();
  });

  it('disables controls when simulating', () => {
    render(<SimulationPanel onSimulate={mockOnSimulate} isSimulating={true} />);
    
    const slider = screen.getByRole('slider');
    const input = screen.getByDisplayValue('25');
    const button = screen.getByRole('button');
    
    expect(slider).toBeDisabled();
    expect(input).toBeDisabled();
    expect(button).toBeDisabled();
  });

  it('calls API and shows success result when simulation succeeds', async () => {
    const mockResponse = {
      status: 'simulated',
      reduction: 0.25,
      timestamp: 1234567890
    };
    
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    render(<SimulationPanel onSimulate={mockOnSimulate} isSimulating={false} />);
    
    const button = screen.getByText('Simulate 25% Grid Failure');
    fireEvent.click(button);

    // Should show loading state
    expect(screen.getByText('Simulating Grid Failure...')).toBeInTheDocument();

    // Wait for API call to complete
    await waitFor(() => {
      expect(screen.getByText('Simulation completed successfully')).toBeInTheDocument();
    });

    // Should show results
    expect(screen.getByText('Simulation Results')).toBeInTheDocument();
    expect(screen.getByText('simulated')).toBeInTheDocument();
    expect(screen.getByText('25.0%')).toBeInTheDocument();

    // Should call onSimulate callback
    expect(mockOnSimulate).toHaveBeenCalledWith(25);
  });

  it('shows error when API call fails', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<SimulationPanel onSimulate={mockOnSimulate} isSimulating={false} />);
    
    const button = screen.getByText('Simulate 25% Grid Failure');
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Simulation failed')).toBeInTheDocument();
    });

    expect(screen.getByText('Simulation Error')).toBeInTheDocument();
    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('clears error when clear button is clicked', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<SimulationPanel onSimulate={mockOnSimulate} isSimulating={false} />);
    
    const button = screen.getByText('Simulate 25% Grid Failure');
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Simulation Error')).toBeInTheDocument();
    });

    const clearButton = screen.getByText('Clear Error');
    fireEvent.click(clearButton);

    expect(screen.queryByText('Simulation Error')).not.toBeInTheDocument();
    expect(screen.getByText('Ready to simulate')).toBeInTheDocument();
  });

  it('constrains percentage input to valid range', () => {
    render(<SimulationPanel onSimulate={mockOnSimulate} isSimulating={false} />);
    
    const input = screen.getByDisplayValue('25');
    
    // Test upper bound
    fireEvent.change(input, { target: { value: '150' } });
    expect(screen.getByText('100%')).toBeInTheDocument();
    
    // Test lower bound
    fireEvent.change(input, { target: { value: '-10' } });
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('displays information panel with instructions', () => {
    render(<SimulationPanel onSimulate={mockOnSimulate} isSimulating={false} />);
    
    expect(screen.getByText('How It Works')).toBeInTheDocument();
    expect(screen.getByText(/Simulates grid failure by reducing total power supply/)).toBeInTheDocument();
    expect(screen.getByText(/Hospitals \(Tier 1\) get power first/)).toBeInTheDocument();
  });
});