import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { message } from 'antd';
import useNotifications from '@/hooks/useNotifications';
import { api } from '@/services/api';
import type { PaginatedResponse, Notification, UnreadCountResponse } from '@/types';

/* ── Mock de api ── */
vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    del: vi.fn(),
  },
}));

vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...(actual as object),
    message: {
      success: vi.fn(),
      error: vi.fn(),
    },
  };
});

/* ── Fixtures ── */

const mockNotification: Notification = {
  id: 'notif-1',
  type: 'system',
  category: 'product',
  title: 'Producto creado',
  description: 'Se creó el producto ABC',
  severity: 'info',
  resource_type: 'product',
  resource_id: 'prod-123',
  is_read: false,
  is_dismissed: false,
  read_at: null,
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockUnreadCount: UnreadCountResponse = { count: 3 };

const mockPaginated: PaginatedResponse<Notification> = {
  items: [mockNotification],
  total: 1,
  page: 1,
  per_page: 20,
};

/* ── Tests ── */

describe('useNotifications', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('carga notificaciones al montar', async () => {
    vi.mocked(api.get).mockResolvedValue(mockPaginated);

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.notifications).toHaveLength(1);
    expect(result.current.total).toBe(1);
    expect(result.current.notifications[0].title).toBe('Producto creado');
    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/notifications?page=1&per_page=20'),
    );
  });

  it('setea error cuando la API falla', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Network Error'));

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBeTruthy();
    expect(message.error).toHaveBeenCalled();
  });

  it('actualiza pagina al llamar setPage', async () => {
    vi.mocked(api.get).mockResolvedValue(mockPaginated);

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(result.current.loading).toBe(false));
    vi.mocked(api.get).mockClear();

    act(() => {
      result.current.setPage(2);
    });

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining('page=2'),
      );
    });
  });

  it('marca notificacion como leida', async () => {
    vi.mocked(api.get).mockResolvedValue(mockPaginated);
    vi.mocked(api.patch).mockResolvedValue({
      ...mockNotification,
      is_read: true,
    });

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(result.current.loading).toBe(false));

    let success = false;
    await act(async () => {
      success = await result.current.markAsRead('notif-1');
    });

    expect(success).toBe(true);
    expect(api.patch).toHaveBeenCalledWith(
      '/api/v1/notifications/notif-1/read',
    );
    expect(message.success).toHaveBeenCalled();
  });

  it('marca todas como leidas', async () => {
    vi.mocked(api.get).mockResolvedValue(mockPaginated);
    vi.mocked(api.patch).mockResolvedValue({ updated: 5 });

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(result.current.loading).toBe(false));

    let success = false;
    await act(async () => {
      success = await result.current.markAllAsRead();
    });

    expect(success).toBe(true);
    expect(api.patch).toHaveBeenCalledWith(
      '/api/v1/notifications/read-all',
    );
  });

  it('crea notificacion manual', async () => {
    vi.mocked(api.get).mockResolvedValue(mockPaginated);
    vi.mocked(api.post).mockResolvedValue(mockNotification);

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(result.current.loading).toBe(false));

    let success = false;
    await act(async () => {
      success = await result.current.createNotification({
        type: 'manual',
        category: 'test',
        title: 'Test notif',
      });
    });

    expect(success).toBe(true);
    expect(api.post).toHaveBeenCalledWith(
      '/api/v1/notifications',
      expect.objectContaining({ type: 'manual', title: 'Test notif' }),
    );
  });

  it('ejecuta forceCheck y retorna cantidad creada', async () => {
    vi.mocked(api.get).mockResolvedValue(mockPaginated);
    vi.mocked(api.post).mockResolvedValue({ created: 2 });

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(result.current.loading).toBe(false));

    let success = false;
    await act(async () => {
      success = await result.current.forceCheck();
    });

    expect(success).toBe(true);
    expect(api.post).toHaveBeenCalledWith(
      '/api/v1/notifications/force-check',
      undefined,
    );
    expect(message.success).toHaveBeenCalledWith(
      expect.stringContaining('2'),
    );
  });

  it('aplica filtros y reinicia pagina a 1', async () => {
    vi.mocked(api.get).mockResolvedValue(mockPaginated);

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(result.current.loading).toBe(false));
    vi.mocked(api.get).mockClear();

    act(() => {
      result.current.setFilters({ type: 'system' });
    });

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining('type=system'),
      );
    });
    // Siempre debe incluir page=1 al cambiar filtros
    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining('page=1'),
    );
  });

  it('refresca al llamar refresh', async () => {
    vi.mocked(api.get).mockResolvedValue(mockPaginated);

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(result.current.loading).toBe(false));
    vi.mocked(api.get).mockClear();

    act(() => {
      result.current.refresh();
    });

    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(1));
  });

  it('inicia polling de unread-count al montar', async () => {
    // Orden: primera llamada = carga tabla, segunda = unread-count, tercera = unread notifs
    vi.mocked(api.get)
      .mockResolvedValueOnce(mockPaginated)
      .mockResolvedValueOnce(mockUnreadCount)
      .mockResolvedValueOnce(mockPaginated);

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => {
      expect(result.current.unreadCount).toBe(3);
    });
  });

  it('el polling se ejecuta cada 30s', async () => {
    vi.useFakeTimers();
    vi.mocked(api.get).mockResolvedValue(mockPaginated);

    renderHook(() => useNotifications());

    // Esperar carga inicial
    await vi.waitFor(() => {
      expect(api.get).toHaveBeenCalled();
    });

    const callsBefore = vi.mocked(api.get).mock.calls.length;

    // Avanzar 30s
    await act(async () => {
      await vi.advanceTimersByTimeAsync(30000);
    });

    // Debería haber más llamadas (2 por cada ciclo de polling)
    expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThan(
      callsBefore,
    );

    vi.useRealTimers();
  });

  it('limpia polling al desmontar', async () => {
    vi.useFakeTimers();
    vi.mocked(api.get).mockResolvedValue(mockPaginated);

    const { unmount } = renderHook(() => useNotifications());

    // Esperar carga inicial
    await vi.waitFor(() => {
      expect(api.get).toHaveBeenCalled();
    });

    vi.mocked(api.get).mockClear();
    unmount();

    // Avanzar 30s — no deberia llamar mas
    await vi.advanceTimersByTimeAsync(30000);
    expect(api.get).not.toHaveBeenCalled();

    vi.useRealTimers();
  });
});
