import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom/vitest';
import { ConfigProvider } from 'antd';
import PriceEditModal from '@/components/price-lists/PriceEditModal';
import type { Product, PriceListItem } from '@/types';

const mockProduct: Product = {
  id: 'prod-1',
  code: 'ZEUS-001',
  name: 'Producto Test',
  family: 'Zeus',
  category: 'license',
  is_active: true,
  created_at: '2026-01-01',
  updated_at: '2026-01-01',
};

const mockItem: PriceListItem = {
  id: 'item-1',
  product_id: 'prod-1',
  price_list_id: 'list-1',
  price: 15000,
  currency: 'ARS',
  effective_from: '2026-01-01',
  effective_to: null,
  is_active: true,
  created_at: '2026-01-01',
  updated_at: '2026-01-01',
};

function renderModal(props: {
  open?: boolean;
  product?: Product | null;
  currentItem?: PriceListItem | null;
  onSave?: () => Promise<boolean>;
  onCancel?: () => void;
}) {
  const onSave = props.onSave ?? vi.fn().mockResolvedValue(true);
  const onCancel = props.onCancel ?? vi.fn();

  return {
    onSave,
    onCancel,
    ...render(
      <ConfigProvider>
        <PriceEditModal
          open={props.open ?? true}
          product={props.product ?? mockProduct}
          currentItem={props.currentItem ?? mockItem}
          onSave={onSave}
          onCancel={onCancel}
        />
      </ConfigProvider>,
    ),
  };
}

describe('PriceEditModal', () => {
  it('renders with product info in title', () => {
    renderModal({ open: true, product: mockProduct, currentItem: mockItem });

    expect(
      screen.getByText(`Editar Precio — ${mockProduct.code} ${mockProduct.name}`),
    ).toBeInTheDocument();
  });

  it('shows price input', () => {
    renderModal({ open: true, product: mockProduct, currentItem: mockItem });

    const priceInput = screen.getByRole('spinbutton');
    expect(priceInput).toBeInTheDocument();
  });

  it('validates price is required', async () => {
    const user = userEvent.setup();
    renderModal({ open: true, product: mockProduct, currentItem: null });

    // Clear the price input to trigger required validation
    const priceInput = screen.getByRole('spinbutton');
    await user.clear(priceInput);
    // Type a tab key to blur and trigger validation
    await user.tab();

    await waitFor(() => {
      expect(
        screen.getByText('Ingrese el precio'),
      ).toBeInTheDocument();
    });
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();

    renderModal({ open: true, product: mockProduct, currentItem: mockItem, onCancel });

    const cancelButton = screen.getByRole('button', { name: /cancelar/i });
    await user.click(cancelButton);

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('does not render when closed', () => {
    const { container } = renderModal({
      open: false,
      product: mockProduct,
      currentItem: mockItem,
    });

    // When closed, Ant Design removes modal content from DOM
    expect(container.querySelector('.ant-modal')).not.toBeInTheDocument();
  });
});
