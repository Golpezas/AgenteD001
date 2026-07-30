import { Typography, Row, Col } from 'antd';
import {
  TeamOutlined,
  AppstoreOutlined,
  DollarOutlined,
} from '@ant-design/icons';
import StatCard from '@/components/ui/StatCard';
import useDashboard from '@/hooks/useDashboard';

const { Title, Paragraph } = Typography;

export default function Dashboard() {
  const { counts, loading } = useDashboard();

  return (
    <>
      <Title level={2}>Bienvenido a AgenteD</Title>
      <Paragraph>
        Sistema de gestión comercial y operativo. Seleccione una sección en el
        menú lateral para comenzar.
      </Paragraph>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            icon={<TeamOutlined />}
            title="Empresas"
            value={counts.companies}
            loading={loading}
          />
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            icon={<AppstoreOutlined />}
            title="Productos"
            value={counts.products}
            loading={loading}
          />
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            icon={<DollarOutlined />}
            title="Listas de Precio"
            value={counts.priceLists}
            loading={loading}
          />
        </Col>
      </Row>
    </>
  );
}
