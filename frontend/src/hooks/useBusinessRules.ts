import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { api } from '@/services/api';
import type { BusinessPolicy, PaginatedResponse } from '@/types';

interface UseBusinessRulesReturn {
  policies: BusinessPolicy[];
  total: number;
  loading: boolean;
  page: number;
  setPage: (p: number) => void;
  filterType: string | undefined;
  setFilterType: (t: string | undefined) => void;
  refresh: () => void;
}

export default function useBusinessRules(): UseBusinessRulesReturn {
  const [policies, setPolicies] = useState<BusinessPolicy[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [filterType, setFilterType] = useState<string | undefined>(undefined);
  const [refreshKey, setRefreshKey] = useState(0);

  const refresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function fetchPolicies() {
      setLoading(true);
      try {
        let url = `/api/v1/business-policies?page=${page}&per_page=20`;
        if (filterType) {
          url += `&policy_type=${filterType}`;
        }

        const data = await api.get<PaginatedResponse<BusinessPolicy>>(url);
        if (!cancelled) {
          setPolicies(data.items);
          setTotal(data.total);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const error = err as { detail?: string; message?: string };
          message.error(
            error.detail ?? error.message ?? 'Error al cargar reglas de negocio',
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchPolicies();
    return () => {
      cancelled = true;
    };
  }, [page, filterType, refreshKey]);

  return {
    policies,
    total,
    loading,
    page,
    setPage,
    filterType,
    setFilterType,
    refresh,
  };
}
