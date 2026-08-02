import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  AppstoreOutlined,
  DollarOutlined,
  FileProtectOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import NotificationBadge from '@/components/notifications/NotificationBadge';
import styles from './AppLayout.module.css';

const { Header, Sider, Content } = Layout;

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
  },
  {
    key: '/clients',
    icon: <TeamOutlined />,
    label: 'Clientes',
  },
  {
    key: '/products',
    icon: <AppstoreOutlined />,
    label: 'Productos',
  },
  {
    key: '/price-lists',
    icon: <DollarOutlined />,
    label: 'Lista de Precios',
  },
  {
    key: '/business-rules',
    icon: <FileProtectOutlined />,
    label: 'Reglas de Negocio',
  },
  {
    key: '/analysis',
    icon: <SearchOutlined />,
    label: 'Análisis',
  },
];

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleMenuClick = (info: { key: string }) => {
    navigate(info.key);
  };

  return (
    <Layout className={styles.layout}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        className={styles.sider}
      >
        <div className={styles.logo}>{collapsed ? 'AD' : 'AgenteD'}</div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header className={styles.header}>
          <span className={styles.headerTitle}>AgenteD</span>
          <NotificationBadge />
        </Header>
        <Content className={styles.content}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
