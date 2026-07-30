import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { api } from '@/services/api';
import type { Company, CompanyCreate, CompanyUpdate, PaginatedResponse } from '@/types';

interface UseClientsReturn {
  clients: Company[];
  total: number;
  loading: boolean;
  page: number;
  perPage: number;
  setPage: (page: number) => void;
  setPerPage: (perPage: number) => void;
  createClient: (data: CompanyCreate) => Promise<boolean>;
  updateClient: (id: string, data: CompanyUpdate) => Promise<boolean>;
  deleteClient: (id: string) => Promise<boolean>;
  refresh: () => void;
}

export default function useClients(): UseClientsReturn {
  const [clients, setClients] = useState<Company[]>([]);
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

    async function fetchClients() {
      setLoading(true);
      try {
        const data = await api.get<PaginatedResponse<Company>>(
          `/api/v1/companies?page=${page}&per_page=${perPage}`,
        );
        if (!cancelled) {
          setClients(data.items);
          setTotal(data.total);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const error = err as { detail?: string; message?: string };
          message.error(error.detail ?? error.message ?? 'Error al cargar clientes');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchClients();
    return () => { cancelled = true; };
  }, [page, perPage, refreshKey]);

  const createClient = useCallback(async (data: CompanyCreate): Promise<boolean> => {
    try {
      await api.post<Company>('/api/v1/companies', data);
      message.success('Cliente creado correctamente');
      refresh();
      return true;
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      message.error(error.detail ?? error.message ?? 'Error al crear cliente');
      return false;
    }
  }, [refresh]);

  const updateClient = useCallback(async (id: string, data: CompanyUpdate): Promise<boolean> => {
    try {
      await api.put<Company>(`/api/v1/companies/${id}`, data);
      message.success('Cliente actualizado correctamente');
      refresh();
      return true;
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      message.error(error.detail ?? error.message ?? 'Error al actualizar cliente');
      return false;
    }
  }, [refresh]);

  const deleteClient = useCallback(async (id: string): Promise<boolean> => {
    try {
      await api.del(`/api/v1/companies/${id}`);
      message.success('Cliente eliminado correctamente');
      refresh();
      return true;
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      message.error(error.detail ?? error.message ?? 'Error al eliminar cliente');
      return false;
    }
  }, [refresh]);

  return {
    clients,
    total,
    loading,
    page,
    perPage,
    setPage,
    setPerPage,
    createClient,
    updateClient,
    deleteClient,
    refresh,
  };
}
