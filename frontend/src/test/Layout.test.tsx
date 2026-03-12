import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from '../components/Layout';

describe('Layout', () => {
  it('renders the header with title and version', () => {
    render(
      <MemoryRouter>
        <Layout>
          <div>Test content</div>
        </Layout>
      </MemoryRouter>
    );

    expect(screen.getByText('Bharat-Grid AI')).toBeInTheDocument();
    expect(screen.getByText('v1.0.0')).toBeInTheDocument();
    expect(screen.getByText('Real-time Energy Distribution')).toBeInTheDocument();
  });

  it('renders children content', () => {
    render(
      <MemoryRouter>
        <Layout>
          <div>Test content</div>
        </Layout>
      </MemoryRouter>
    );

    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('has proper styling classes', () => {
    const { container } = render(
      <MemoryRouter>
        <Layout>
          <div>Test content</div>
        </Layout>
      </MemoryRouter>
    );

    const mainDiv = container.firstChild as HTMLElement;
    expect(mainDiv).toHaveClass('min-h-screen', 'bg-slate-900');
  });
});