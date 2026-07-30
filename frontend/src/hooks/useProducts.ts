import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { api } from '@/services/api';
import type { Product, ProductCreate, ProductUpdate, PaginatedResponse } from '@/types';

interface UseProductsReturn {
  products: Product[];
  total: number;
  loading: boolean;
  page: number;
  perPage: number;
  setPage: (page: number) => void;
  setPerPage: (perPage: number) => void;
  createProduct: (data: ProductCreate) => Promise<boolean>;
  updateProduct: (id: string, data: ProductUpdate) => Promise<boolean>;
  deleteProduct: (id: string) => Promise<boolean>;
  refresh: () => void;
}

export default function useProducts(): UseProductsReturn {
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [refreshKey, setRefreshKey] = useState(0);

  const refresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function fetchProducts() {
      setLoading(true);
      try {
        const data = await api.get<PaginatedResponse<Product>>(
          `/api/v1/products?page=${page}&per_page=${perPage}`,
        );
        if (!cancelled) {
          setProducts(data.items);
          setTotal(data.total);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const error = err as { detail?: string; message?: string };
          message.error(error.detail ?? error.message ?? 'Error al cargar productos');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchProducts();
    return () => { cancelled = true; };
  }, [page, perPage, refreshKey]);

  const createProduct = useCallback(async (data: ProductCreate): Promise<boolean> => {
    try {
      await api.post<Product>('/api/v1/products', data);
      message.success('Producto creado correctamente');
      refresh();
      return true;
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      message.error(error.detail ?? error.message ?? 'Error al crear producto');
      return false;
    }
  }, [refresh]);

  const updateProduct = useCallback(async (id: string, data: ProductUpdate): Promise<boolean> => {
    try {
      await api.put<Product>(`/api/v1/products/${id}`, data);
      message.success('Producto actualizado correctamente');
      refresh();
      return true;
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      message.error(error.detail ?? error.message ?? 'Error al actualizar producto');
      return false;
    }
  }, [refresh]);

  const deleteProduct = useCallback(async (id: string): Promise<boolean> => {
    try {
      await api.del(`/api/v1/products/${id}`);
      message.success('Producto eliminado correctamente');
      refresh();
      return true;
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      message.error(error.detail ?? error.message ?? 'Error al eliminar producto');
      return false;
    }
  }, [refresh]);

  return {
    products,
    total,
    loading,
    page,
    perPage,
    setPage,
    setPerPage,
    createProduct,
    updateProduct,
    deleteProduct,
    refresh,
  };
}
