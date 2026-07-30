import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { ConfigProvider } from 'antd';
import PolicyViewer from '@/components/business-rules/PolicyViewer';
import type { BusinessPolicy } from '@/types';

const mockPolicies: BusinessPolicy[] = [
  {
    id: 'pol-1',
    name: 'Descuento por Volumen',
    policy_type: 'discount',
    description: '10% off for large orders',
    value: 10,
    value_type: 'percentage',
    client_type: 'VIP',
    is_active: true,
    effective_from: '2026-01-01',
    effective_to: '2026-12-31',
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
  },
  {
    id: 'pol-2',
    name: 'Beneficio Implementación',
    policy_type: 'benefit',
    description: null,
    value: 50000,
    value_type: 'fixed_amount',
    client_type: null,
    is_active: false,
    effective_from: null,
    effective_to: null,
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
  },
];

describe('PolicyViewer', () => {
  it('renders policy names', () => {
    render(
      <ConfigProvider>
        <PolicyViewer policies={mockPolicies} loading={false} />
      </ConfigProvider>,
    );

    expect(screen.getByText('Descuento por Volumen')).toBeInTheDocument();
    expect(screen.getByText('Beneficio Implementación')).toBeInTheDocument();
  });

  it('renders formatted values (percentage)', () => {
    render(
      <ConfigProvider>
        <PolicyViewer policies={mockPolicies} loading={false} />
      </ConfigProvider>,
    );

    // Discount policy has 10% value
    expect(screen.getByText('10%')).toBeInTheDocument();
  });

  it('shows active/inactive status correctly', () => {
    render(
      <ConfigProvider>
        <PolicyViewer policies={mockPolicies} loading={false} />
      </ConfigProvider>,
    );

    const activeTags = screen.getAllByText('Activo');
    expect(activeTags).toHaveLength(1);

    const inactiveTags = screen.getAllByText('Inactivo');
    expect(inactiveTags).toHaveLength(1);
  });
});
