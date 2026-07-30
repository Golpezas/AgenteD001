import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
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
        </Header>
        <Content className={styles.content}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
