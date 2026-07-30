import { useState, useEffect, useCallback, useRef } from 'react';
import { message } from 'antd';
import { api } from '@/services/api';
import type {
  Notification,
  NotificationCreate,
  PaginatedResponse,
  UnreadCountResponse,
} from '@/types';

const POLLING_INTERVAL = 30000; // 30s

interface NotificationFilters {
  type?: string;
  category?: string;
  is_read?: boolean;
}

interface UseNotificationsReturn {
  notifications: Notification[];
  total: number;
  loading: boolean;
  error: string | null;
  page: number;
  perPage: number;
  setPage: (page: number) => void;
  setPerPage: (perPage: number) => void;
  filters: NotificationFilters;
  setFilters: (filters: NotificationFilters) => void;
  unreadCount: number;
  unreadNotifications: Notification[];
  markAsRead: (id: string) => Promise<boolean>;
  markAllAsRead: () => Promise<boolean>;
  createNotification: (data: NotificationCreate) => Promise<boolean>;
  forceCheck: () => Promise<boolean>;
  refresh: () => void;
}

export default function useNotifications(): UseNotificationsReturn {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [filters, setFilters] = useState<NotificationFilters>({});
  const [unreadCount, setUnreadCount] = useState(0);
  const [unreadNotifications, setUnreadNotifications] = useState<Notification[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  // Fetch principal: lista paginada con filtros (para la tabla)
  useEffect(() => {
    let cancelled = false;

    async function fetchNotifications() {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        params.set('page', String(page));
        params.set('per_page', String(perPage));
        if (filters.type) params.set('type', filters.type);
        if (filters.category) params.set('category', filters.category);
        if (filters.is_read !== undefined) {
          params.set('is_read', String(filters.is_read));
        }

        const data = await api.get<PaginatedResponse<Notification>>(
          `/api/v1/notifications?${params.toString()}`,
        );
        if (!cancelled) {
          setNotifications(data.items);
          setTotal(data.total);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const errorObj = err as { detail?: string; message?: string };
          const msg =
            errorObj.detail ?? errorObj.message ?? 'Error al cargar notificaciones';
          setError(msg);
          message.error(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchNotifications();
    return () => {
      cancelled = true;
    };
  }, [page, perPage, filters, refreshKey]);

  // Polling automático cada 30s para unread-count y últimas 5 no leídas
  useEffect(() => {
    async function fetchUnreadData() {
      try {
        const [countData, unreadData] = await Promise.all([
          api.get<UnreadCountResponse>('/api/v1/notifications/unread-count'),
          api.get<PaginatedResponse<Notification>>(
            '/api/v1/notifications?is_read=false&per_page=5',
          ),
        ]);
        setUnreadCount(countData.count);
        setUnreadNotifications(unreadData.items);
      } catch {
        // Silencioso — mantener valores anteriores en caso de error de red
      }
    }

    fetchUnreadData();
    pollingRef.current = setInterval(fetchUnreadData, POLLING_INTERVAL);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  const markAsRead = useCallback(
    async (id: string): Promise<boolean> => {
      try {
        await api.patch<Notification>(`/api/v1/notifications/${id}/read`);
        message.success('Notificación marcada como leída');
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
        );
        refresh();
        return true;
      } catch (err: unknown) {
        const errorObj = err as { detail?: string; message?: string };
        message.error(
          errorObj.detail ?? errorObj.message ?? 'Error al marcar como leída',
        );
        return false;
      }
    },
    [refresh],
  );

  const markAllAsRead = useCallback(async (): Promise<boolean> => {
    try {
      await api.patch('/api/v1/notifications/read-all');
      message.success('Todas las notificaciones marcadas como leídas');
      setUnreadCount(0);
      refresh();
      return true;
    } catch (err: unknown) {
      const errorObj = err as { detail?: string; message?: string };
      message.error(
        errorObj.detail ??
          errorObj.message ??
          'Error al marcar todas como leídas',
      );
      return false;
    }
  }, [refresh]);

  const createNotification = useCallback(
    async (data: NotificationCreate): Promise<boolean> => {
      try {
        await api.post<Notification>('/api/v1/notifications', data);
        message.success('Notificación creada correctamente');
        refresh();
        return true;
      } catch (err: unknown) {
        const errorObj = err as { detail?: string; message?: string };
        message.error(
          errorObj.detail ?? errorObj.message ?? 'Error al crear notificación',
        );
        return false;
      }
    },
    [refresh],
  );

  const forceCheck = useCallback(async (): Promise<boolean> => {
    try {
      const result = await api.post<{ created: number }>(
        '/api/v1/notifications/force-check',
        undefined,
      );
      message.success(
        `Verificación completada: ${result.created} notificaciones creadas`,
      );
      refresh();
      return true;
    } catch (err: unknown) {
      const errorObj = err as { detail?: string; message?: string };
      message.error(
        errorObj.detail ?? errorObj.message ?? 'Error en verificación comercial',
      );
      return false;
    }
  }, [refresh]);

  return {
    notifications,
    total,
    loading,
    error,
    page,
    perPage,
    setPage,
    setPerPage,
    filters,
    setFilters,
    unreadCount,
    unreadNotifications,
    markAsRead,
    markAllAsRead,
    createNotification,
    forceCheck,
    refresh,
  };
}
