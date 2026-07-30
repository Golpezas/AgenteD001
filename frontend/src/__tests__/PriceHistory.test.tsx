import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import PriceHistory from '@/components/price-lists/PriceHistory';
import type { PriceHistoryEntry } from '@/components/price-lists/PriceHistory';

describe('PriceHistory', () => {
  const mockHistory: PriceHistoryEntry[] = [
    {
      id: '1',
      price: 15000,
      currency: 'ARS',
      effective_from: '2026-01-01',
      effective_to: '2026-06-30',
    },
    {
      id: '2',
      price: 18000,
      currency: 'ARS',
      effective_from: '2026-07-01',
      effective_to: null,
    },
  ];

  it('renders price entries with formatted values', () => {
    render(<PriceHistory history={mockHistory} />);

    // Should show both entries — es-AR locale uses $ 15.000,00 format
    expect(screen.getByText((content) => content.includes('15.000'))).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes('18.000'))).toBeInTheDocument();
  });

  it('renders currency tags', () => {
    render(<PriceHistory history={mockHistory} />);

    const tags = screen.getAllByText('ARS');
    expect(tags).toHaveLength(2);
  });

  it('shows placeholder for null effective_to', () => {
    render(<PriceHistory history={mockHistory} />);

    // The entry with null effective_to should show em dash
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('shows empty message when no history', () => {
    render(<PriceHistory history={[]} />);

    expect(
      screen.getByText('Sin historial de precios para este producto.'),
    ).toBeInTheDocument();
  });
});
