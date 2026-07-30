import { useState, useMemo } from 'react';
import { Typography, Tabs, message } from 'antd';
import { api } from '@/services/api';
import usePriceLists from '@/hooks/usePriceLists';
import PriceListTable from '@/components/price-lists/PriceListTable';
import PriceEditModal from '@/components/price-lists/PriceEditModal';
import type { Product, PriceListItem } from '@/types';

const { Title } = Typography;

export default function PriceListsPage() {
  const { products, items: priceItems, loading, refresh } = usePriceLists();

  const [editProduct, setEditProduct] = useState<Product | null>(null);
  const [editItem, setEditItem] = useState<PriceListItem | null>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);

  /** Agrupa productos por familia */
  const families = useMemo(() => {
    const map = new Map<string, Product[]>();
    for (const p of products) {
      const family = p.family ?? 'Sin familia';
      if (!map.has(family)) map.set(family, []);
      map.get(family)!.push(p);
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [products]);

  const handleEditPrice = (product: Product, currentItem?: PriceListItem) => {
    setEditProduct(product);
    setEditItem(currentItem ?? null);
    setEditModalOpen(true);
  };

  const handleSavePrice = async (
    _itemId: string | null,
    values: { price: number; currency: string; effective_from: string },
  ): Promise<boolean> => {
    if (!editProduct) return false;
    try {
      // Try to call price-list-items endpoint; if it fails, show a message
      if (editItem?.id) {
        await api.put(`/api/v1/price-list-items/${editItem.id}`, {
          price: values.price,
          currency: values.currency,
          effective_from: values.effective_from,
        });
      } else {
        // Create new price-list-item
        const defaultListId = '00000000-0000-0000-0000-000000000001';
        await api.post('/api/v1/price-list-items', {
          product_id: editProduct.id,
          price_list_id: defaultListId,
          price: values.price,
          currency: values.currency,
          effective_from: values.effective_from,
        });
      }
      message.success('Precio guardado correctamente');
      refresh();
      return true;
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      message.error(
        error.detail ??
          error.message ??
          'Error al guardar precio. El endpoint de precios podría no estar disponible.',
      );
      return false;
    }
  };

  const handleCloseModal = () => {
    setEditModalOpen(false);
    setEditProduct(null);
    setEditItem(null);
  };

  return (
    <>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <Title level={2} style={{ margin: 0 }}>
          Lista de Precios
        </Title>
      </div>

      <Tabs
        defaultActiveKey={families[0]?.[0] ?? 'all'}
        items={[
          {
            key: 'all',
            label: 'Todos',
            children: (
              <PriceListTable
                products={products}
                priceItems={priceItems}
                loading={loading}
                onEditPrice={handleEditPrice}
              />
            ),
          },
          ...families.map(([family, familyProducts]) => ({
            key: family,
            label: family,
            children: (
              <PriceListTable
                products={familyProducts}
                priceItems={priceItems}
                loading={loading}
                onEditPrice={handleEditPrice}
              />
            ),
          })),
        ]}
      />

      <PriceEditModal
        open={editModalOpen}
        product={editProduct}
        currentItem={editItem}
        onSave={handleSavePrice}
        onCancel={handleCloseModal}
      />
    </>
  );
}
