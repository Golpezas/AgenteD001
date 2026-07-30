import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom/vitest';
import { ConfigProvider } from 'antd';
import { BrowserRouter } from 'react-router-dom';
import NotificationBadge from '@/components/notifications/NotificationBadge';
import useNotifications from '@/hooks/useNotifications';
import type { Notification } from '@/types';
import type { Mock } from 'vitest';

/* ── Mock del hook ── */
vi.mock('@/hooks/useNotifications', () => ({
  default: vi.fn(),
}));

const mockUseNotifications = useNotifications as unknown as Mock;

/* ── Fixtures ── */

const mockUnreadNotifs: Notification[] = [
  {
    id: 'n1',
    type: 'system',
    category: 'product',
    title: 'Producto creado',
    description: null,
    severity: 'info',
    resource_type: null,
    resource_id: null,
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
    description: null,
    severity: 'warning',
    resource_type: null,
    resource_id: null,
    is_read: false,
    is_dismissed: false,
    read_at: null,
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

/* ── Helpers ── */

function renderBadge() {
  return render(
    <BrowserRouter>
      <ConfigProvider>
        <NotificationBadge />
      </ConfigProvider>
    </BrowserRouter>,
  );
}

/* ── Tests ── */

describe('NotificationBadge', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renderiza el icono BellOutlined', () => {
    mockUseNotifications.mockReturnValue({
      unreadCount: 0,
      unreadNotifications: [],
      markAllAsRead: vi.fn(),
    });

    renderBadge();
    // El icono BellOutlined se renderiza como un span con rol img o svg
    const bellIcon = document.querySelector('.anticon-bell');
    expect(bellIcon).toBeInTheDocument();
  });

  it('muestra contador cuando hay no leídas', () => {
    mockUseNotifications.mockReturnValue({
      unreadCount: 3,
      unreadNotifications: mockUnreadNotifs,
      markAllAsRead: vi.fn(),
    });

    renderBadge();
    // Badge de Ant Design muestra el count como span
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('no muestra contador cuando es 0', () => {
    mockUseNotifications.mockReturnValue({
      unreadCount: 0,
      unreadNotifications: [],
      markAllAsRead: vi.fn(),
    });

    renderBadge();
    // Sin número visible cuando el contador es 0
    expect(screen.queryByText('0')).not.toBeInTheDocument();
  });

  it('abre dropdown al hacer clic y muestra notificaciones', async () => {
    const user = userEvent.setup();
    mockUseNotifications.mockReturnValue({
      unreadCount: 2,
      unreadNotifications: mockUnreadNotifs,
      markAllAsRead: vi.fn(),
    });

    renderBadge();
    const bell = document.querySelector('.anticon-bell')!;
    await user.click(bell);

    expect(screen.getByText('Producto creado')).toBeInTheDocument();
    expect(screen.getByText('Política vencida')).toBeInTheDocument();
  });

  it('dropdown muestra "Ver todas" cuando hay notificaciones', async () => {
    const user = userEvent.setup();
    mockUseNotifications.mockReturnValue({
      unreadCount: 2,
      unreadNotifications: mockUnreadNotifs,
      markAllAsRead: vi.fn(),
    });

    renderBadge();
    const bell = document.querySelector('.anticon-bell')!;
    await user.click(bell);

    expect(screen.getByText('Ver todas')).toBeInTheDocument();
  });

  it('dropdown muestra "Marcar todas leídas" cuando hay no leídas', async () => {
    const user = userEvent.setup();
    mockUseNotifications.mockReturnValue({
      unreadCount: 2,
      unreadNotifications: mockUnreadNotifs,
      markAllAsRead: vi.fn(),
    });

    renderBadge();
    const bell = document.querySelector('.anticon-bell')!;
    await user.click(bell);

    expect(screen.getByText('Marcar todas leídas')).toBeInTheDocument();
  });

  it('dropdown muestra "No hay notificaciones" cuando está vacío', async () => {
    const user = userEvent.setup();
    mockUseNotifications.mockReturnValue({
      unreadCount: 0,
      unreadNotifications: [],
      markAllAsRead: vi.fn(),
    });

    renderBadge();
    const bell = document.querySelector('.anticon-bell')!;
    await user.click(bell);

    expect(screen.getByText('No hay notificaciones')).toBeInTheDocument();
  });

  it('dropdown NO muestra "Ver todas" cuando está vacío', async () => {
    const user = userEvent.setup();
    mockUseNotifications.mockReturnValue({
      unreadCount: 0,
      unreadNotifications: [],
      markAllAsRead: vi.fn(),
    });

    renderBadge();
    const bell = document.querySelector('.anticon-bell')!;
    await user.click(bell);

    expect(screen.queryByText('Ver todas')).not.toBeInTheDocument();
  });
});
