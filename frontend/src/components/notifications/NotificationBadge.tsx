import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge, Dropdown, Typography, Tag } from 'antd';
import {
  BellOutlined,
  CheckOutlined,
  RightOutlined,
} from '@ant-design/icons';
import useNotifications from '@/hooks/useNotifications';
import type { MenuProps } from 'antd';
import type { Notification } from '@/types';

const { Text } = Typography;

/* ── Helpers ─────────────────────────────── */

function severityColor(severity: string): string {
  switch (severity) {
    case 'error':
      return '#f5222d';
    case 'warning':
      return '#fa8c16';
    case 'success':
      return '#52c41a';
    default:
      return '#1677ff';
  }
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'ahora';
  if (mins < 60) return `hace ${mins} min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `hace ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `hace ${days}d`;
  return `hace ${Math.floor(days / 30)} mes`;
}

function notificationLabel(n: Notification): React.ReactNode {
  return (
    <div
      style={{
        maxWidth: 300,
        padding: '6px 4px',
        borderBottom: '1px solid #303030',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 2,
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: severityColor(n.severity),
            display: 'inline-block',
            flexShrink: 0,
          }}
        />
        <Tag
          color={severityColor(n.severity)}
          style={{
            fontSize: 10,
            lineHeight: '16px',
            padding: '0 6px',
            margin: 0,
            textTransform: 'uppercase',
          }}
        >
          {n.type}
        </Tag>
        <Text
          strong
          style={{
            fontSize: 13,
            color: '#e8e8e8',
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {n.title}
        </Text>
      </div>
      <Text
        type="secondary"
        style={{ fontSize: 11, marginLeft: 16, color: '#8c8c8c' }}
      >
        {timeAgo(n.created_at)}
      </Text>
    </div>
  );
}

/* ── Componente ──────────────────────────── */

export default function NotificationBadge() {
  const navigate = useNavigate();
  const { unreadCount, unreadNotifications, markAllAsRead } =
    useNotifications();
  const [open, setOpen] = useState(false);

  const menuItems: MenuProps['items'] = [];

  if (unreadNotifications.length === 0) {
    menuItems.push({
      key: 'empty',
      label: (
        <Text type="secondary" style={{ display: 'block', textAlign: 'center', padding: '12px 16px' }}>
          No hay notificaciones
        </Text>
      ),
      disabled: true,
    });
  } else {
    unreadNotifications.forEach((n) => {
      menuItems.push({
        key: n.id,
        label: notificationLabel(n),
      });
    });

    menuItems.push({ type: 'divider' });

    menuItems.push({
      key: 'view-all',
      label: (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 4,
            color: '#1677ff',
          }}
        >
          <span>Ver todas</span>
          <RightOutlined style={{ fontSize: 11 }} />
        </div>
      ),
    });

    if (unreadCount > 0) {
      menuItems.push({
        key: 'mark-all-read',
        label: (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6,
              color: '#52c41a',
            }}
          >
            <CheckOutlined />
            <span>Marcar todas leídas</span>
          </div>
        ),
      });
    }
  }

  const navigateToResource = (resourceType?: string) => {
    switch (resourceType) {
      case 'product':
        navigate('/products');
        break;
      case 'company':
        navigate('/clients');
        break;
      case 'price_list':
        navigate('/price-lists');
        break;
      case 'business_policy':
        navigate('/business-rules');
        break;
      default:
        navigate('/notifications');
        break;
    }
  };

  const handleClick: MenuProps['onClick'] = ({ key }) => {
    setOpen(false);
    if (key === 'view-all') {
      navigate('/notifications');
    } else if (key === 'mark-all-read') {
      markAllAsRead();
    } else {
      const notif = unreadNotifications.find((n) => n.id === key);
      if (notif) navigateToResource(notif.resource_type ?? undefined);
    }
  };

  return (
    <Dropdown
      menu={{ items: menuItems, onClick: handleClick }}
      open={open}
      onOpenChange={setOpen}
      trigger={['click']}
    >
      <Badge
        count={unreadCount}
        size="small"
        showZero={false}
        style={{ backgroundColor: '#f5222d' }}
        offset={[0, 2]}
      >
        <BellOutlined
          style={{
            fontSize: 20,
            color: '#e8e8e8',
            cursor: 'pointer',
            padding: '8px',
          }}
        />
      </Badge>
    </Dropdown>
  );
}
