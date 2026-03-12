import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

describe('App', () => {
  it('renders the main dashboard', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    // Check if the main title is rendered
    expect(screen.getByText('Bharat-Grid AI')).toBeInTheDocument();
    
    // Check if all main sections are present
    expect(screen.getByText('Power Connection Map')).toBeInTheDocument();
    expect(screen.getByText('System Metrics')).toBeInTheDocument();
    expect(screen.getByText('Live Allocation Stream')).toBeInTheDocument();
    expect(screen.getByText('Grid Failure Simulation')).toBeInTheDocument();
  });

  it('displays placeholder messages for future components', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    // Check placeholder messages
    expect(screen.getByText('Power map will be implemented in Task 9.1')).toBeInTheDocument();
    expect(screen.getByText('Live stream table will be implemented in Task 9.3')).toBeInTheDocument();
    expect(screen.getByText('Simulation controls will be implemented in Task 9.4')).toBeInTheDocument();
  });

  it('has disabled simulation controls', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    const slider = screen.getByRole('slider');
    const button = screen.getByRole('button', { name: /simulate grid failure/i });

    expect(slider).toBeDisabled();
    expect(button).toBeDisabled();
  });
});