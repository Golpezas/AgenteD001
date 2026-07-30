import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { api } from '@/services/api';
import type { PriceListItem, Product, PaginatedResponse } from '@/types';

interface UsePriceListsReturn {
  items: PriceListItem[];
  products: Product[];
  total: number;
  loading: boolean;
  page: number;
  setPage: (p: number) => void;
  updatePrice: (itemId: string, price: number) => Promise<boolean>;
  refresh: () => void;
}

export default function usePriceLists(): UsePriceListsReturn {
  const [items, setItems] = useState<PriceListItem[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [refreshKey, setRefreshKey] = useState(0);

  const refresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      try {
        // Fetch products first
        const productRes = await api.get<PaginatedResponse<Product>>(
          `/api/v1/products?page=1&per_page=100`,
        );

        if (cancelled) return;
        setProducts(productRes.items);

        // Try fetching price-list-items if endpoint exists
        try {
          const itemRes = await api.get<PaginatedResponse<PriceListItem>>(
            `/api/v1/price-list-items?page=${page}&per_page=20`,
          );
          if (!cancelled) {
            setItems(itemRes.items);
            setTotal(itemRes.total);
          }
        } catch {
          // Endpoint not available — use empty items
          if (!cancelled) {
            setItems([]);
            setTotal(productRes.total);
          }
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const error = err as { detail?: string; message?: string };
          message.error(
            error.detail ?? error.message ?? 'Error al cargar listas de precios',
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchData();
    return () => {
      cancelled = true;
    };
  }, [page, refreshKey]);

  const updatePrice = useCallback(
    async (itemId: string, price: number): Promise<boolean> => {
      try {
        await api.put(`/api/v1/price-list-items/${itemId}`, { price });
        message.success('Precio actualizado correctamente');
        refresh();
        return true;
      } catch (err: unknown) {
        const error = err as { detail?: string; message?: string };
        message.error(
          error.detail ?? error.message ?? 'Error al actualizar precio',
        );
        return false;
      }
    },
    [refresh],
  );

  return {
    items,
    products,
    total,
    loading,
    page,
    setPage,
    updatePrice,
    refresh,
  };
}
