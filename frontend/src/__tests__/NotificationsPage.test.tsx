import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom/vitest';
import { ConfigProvider } from 'antd';
import { BrowserRouter } from 'react-router-dom';
import NotificationsPage from '@/pages/Notifications';
import useNotifications from '@/hooks/useNotifications';
import type { Mock } from 'vitest';

/* ── Mock del hook ── */
vi.mock('@/hooks/useNotifications', () => ({
  default: vi.fn(),
}));

const mockUseNotifications = useNotifications as unknown as Mock;

/* ── Fixtures dinámicas (created_at fresco) ── */

function buildMockNotifications() {
  return [
    {
      id: 'n1',
      type: 'system',
      category: 'product',
      title: 'Producto ABC creado',
      description: 'Nuevo producto',
      severity: 'info',
      resource_type: 'product',
      resource_id: 'prod-1',
      is_read: false,
      is_dismissed: false,
      read_at: null,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 'n2',
      type: 'business',
      category: 'policy',
      title: 'Política vencida',
      description: 'Vencimiento próximo',
      severity: 'warning',
      resource_type: null,
      resource_id: null,
      is_read: true,
      is_dismissed: false,
      read_at: new Date().toISOString(),
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];
}

const defaultHookState = {
  notifications: [],
  total: 0,
  loading: false,
  error: null,
  page: 1,
  perPage: 20,
  setPage: vi.fn(),
  setPerPage: vi.fn(),
  filters: {},
  setFilters: vi.fn(),
  unreadCount: 0,
  unreadNotifications: [],
  markAsRead: vi.fn(),
  markAllAsRead: vi.fn(),
  createNotification: vi.fn(),
  forceCheck: vi.fn(),
  refresh: vi.fn(),
};

/* ── Helpers ── */

function renderPage() {
  return render(
    <BrowserRouter>
      <ConfigProvider>
        <NotificationsPage />
      </ConfigProvider>
    </BrowserRouter>,
  );
}

/* ── Tests ── */

describe('NotificationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseNotifications.mockReturnValue(defaultHookState);
  });

  it('renderiza título de la página', () => {
    renderPage();
    expect(screen.getByText('Notificaciones')).toBeInTheDocument();
  });

  it('renderiza botones de acción', () => {
    renderPage();
    expect(screen.getByText('Actualizar')).toBeInTheDocument();
    expect(screen.getByText('Marcar todas leídas')).toBeInTheDocument();
    expect(screen.getByText('Forzar verificación')).toBeInTheDocument();
    expect(screen.getByText('Nueva notificación')).toBeInTheDocument();
  });

  it('renderiza filtro de categoría (Input)', () => {
    renderPage();
    const catInput = screen.getByPlaceholderText('Categoría');
    expect(catInput).toBeInTheDocument();
  });

  it('muestra notificaciones en la tabla', () => {
    mockUseNotifications.mockReturnValue({
      ...defaultHookState,
      notifications: buildMockNotifications(),
      total: 2,
    });

    renderPage();
    expect(screen.getByText('Producto ABC creado')).toBeInTheDocument();
    expect(screen.getByText('Política vencida')).toBeInTheDocument();
    expect(screen.getByText('No leído')).toBeInTheDocument();
    expect(screen.getByText('Leído')).toBeInTheDocument();
  });

  it('muestra botón "Marcar leída" solo para no leídas', () => {
    mockUseNotifications.mockReturnValue({
      ...defaultHookState,
      notifications: buildMockNotifications(),
      total: 2,
    });

    renderPage();
    const markButtons = screen.getAllByText('Marcar leída');
    expect(markButtons).toHaveLength(1);
  });

  it('llama a markAllAsRead al hacer clic', async () => {
    const user = userEvent.setup();
    const markAllAsRead = vi.fn();
    mockUseNotifications.mockReturnValue({
      ...defaultHookState,
      markAllAsRead,
    });

    renderPage();
    await user.click(screen.getByText('Marcar todas leídas'));
    expect(markAllAsRead).toHaveBeenCalledOnce();
  });

  it('llama a createNotification al enviar modal', async () => {
    const user = userEvent.setup();
    const createNotification = vi.fn().mockResolvedValue(true);
    mockUseNotifications.mockReturnValue({
      ...defaultHookState,
      createNotification,
    });

    renderPage();

    // Abrir modal
    await user.click(screen.getByText('Nueva notificación'));

    // Llenar formulario — usar getByRole para inputs sin label directo
    const titleInput = screen.getByLabelText('Título');
    await user.type(titleInput, 'Test notif');

    const catInput = screen.getByLabelText('Categoría');
    await user.type(catInput, 'test-cat');

    // Enviar formulario via OK button
    await user.click(screen.getByRole('button', { name: 'OK' }));

    expect(createNotification).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Test notif',
        category: 'test-cat',
      }),
    );
  });

  it('llama a forceCheck al hacer clic', async () => {
    const user = userEvent.setup();
    const forceCheck = vi.fn();
    mockUseNotifications.mockReturnValue({
      ...defaultHookState,
      forceCheck,
    });

    renderPage();
    await user.click(screen.getByText('Forzar verificación'));
    expect(forceCheck).toHaveBeenCalledOnce();
  });

  it('muestra estado vacío cuando no hay datos', () => {
    mockUseNotifications.mockReturnValue({
      ...defaultHookState,
      notifications: [],
      total: 0,
    });

    renderPage();
    expect(screen.getByText('No hay notificaciones')).toBeInTheDocument();
  });

  it('muestra error cuando hay error', () => {
    mockUseNotifications.mockReturnValue({
      ...defaultHookState,
      notifications: [],
      total: 0,
      error: 'Error de conexión',
    });

    renderPage();
    expect(screen.getByText('Error de conexión')).toBeInTheDocument();
  });
});
