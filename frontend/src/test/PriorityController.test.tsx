import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import PriorityController from '../components/PriorityController';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }: any) => children,
}));

// Mock dnd-kit
vi.mock('@dnd-kit/core', () => ({
  DndContext: ({ children }: any) => <div data-testid="dnd-context">{children}</div>,
  DragOverlay: ({ children }: any) => <div data-testid="drag-overlay">{children}</div>,
}));

vi.mock('@dnd-kit/sortable', () => ({
  SortableContext: ({ children }: any) => <div data-testid="sortable-context">{children}</div>,
  useSortable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: vi.fn(),
    transform: null,
    transition: null,
    isDragging: false,
  }),
  verticalListSortingStrategy: {},
}));

vi.mock('@dnd-kit/utilities', () => ({
  CSS: {
    Transform: {
      toString: () => '',
    },
  },
}));

describe('PriorityController', () => {
  it('renders the main title', () => {
    render(<PriorityController />);
    expect(screen.getByText('Priority Controller')).toBeInTheDocument();
  });

  it('renders all three priority tiers', () => {
    render(<PriorityController />);
    expect(screen.getByText('Tier 1 - Critical')).toBeInTheDocument();
    expect(screen.getByText('Tier 2 - Essential')).toBeInTheDocument();
    expect(screen.getByText('Tier 3 - Non-Essential')).toBeInTheDocument();
  });

  it('renders load items', () => {
    render(<PriorityController />);
    expect(screen.getByText('City Hospital')).toBeInTheDocument();
    expect(screen.getByText('Manufacturing Plant')).toBeInTheDocument();
    expect(screen.getByText('Primary School')).toBeInTheDocument();
  });

  it('shows save button as disabled initially', () => {
    render(<PriorityController />);
    const saveButton = screen.getByText('No Changes');
    expect(saveButton).toBeDisabled();
  });

  it('shows reset button', () => {
    render(<PriorityController />);
    expect(screen.getByText('Reset')).toBeInTheDocument();
  });

  it('renders priority legend', () => {
    render(<PriorityController />);
    expect(screen.getByText('Priority Levels')).toBeInTheDocument();
    expect(screen.getByText(/Critical loads that are never cut off/)).toBeInTheDocument();
  });

  it('handles reset button click', () => {
    render(<PriorityController />);
    const resetButton = screen.getByText('Reset');
    fireEvent.click(resetButton);
    // Component should reset to initial state
    expect(screen.getByText('No Changes')).toBeInTheDocument();
  });
});