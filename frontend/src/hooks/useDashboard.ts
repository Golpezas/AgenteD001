import { useState, useEffect } from 'react';
import { message } from 'antd';
import { api } from '@/services/api';
import type { PaginatedResponse, Company, Product } from '@/types';

interface DashboardCounts {
  companies: number;
  products: number;
  priceLists: number;
}

export default function useDashboard() {
  const [counts, setCounts] = useState<DashboardCounts>({
    companies: 0,
    products: 0,
    priceLists: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function fetchCounts() {
      setLoading(true);
      try {
        const [companiesRes, productsRes] = await Promise.all([
          api.get<PaginatedResponse<Company>>('/api/v1/companies?page=1&per_page=1'),
          api.get<PaginatedResponse<Product>>('/api/v1/products?page=1&per_page=1'),
        ]);

        // Price lists endpoint may not exist yet; try gracefully
        let priceListsCount = 0;
        try {
          const plRes = await api.get<PaginatedResponse<unknown>>(
            '/api/v1/price-list-items?page=1&per_page=1',
          );
          priceListsCount = plRes.total;
        } catch {
          // Endpoint not available yet — keep 0
        }

        if (!cancelled) {
          setCounts({
            companies: companiesRes.total,
            products: productsRes.total,
            priceLists: priceListsCount,
          });
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const error = err as { detail?: string; message?: string };
          message.error(error.detail ?? error.message ?? 'Error al cargar estadísticas');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchCounts();
    return () => { cancelled = true; };
  }, []);

  return { counts, loading };
}
