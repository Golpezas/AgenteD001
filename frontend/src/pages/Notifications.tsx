import { useState, useMemo } from 'react';
import {
  Typography,
  Button,
  Table,
  Tag,
  Space,
  Select,
  Input,
  Modal,
  Form,
} from 'antd';
import {
  PlusOutlined,
  CheckOutlined,
  ThunderboltOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import useNotifications from '@/hooks/useNotifications';
import type { Notification, NotificationCreate } from '@/types';
import type { ColumnsType } from 'antd/es/table';

const { Title } = Typography;
const { Option } = Select;

/* ── Helpers ─────────────────────────────── */

const severityColors: Record<string, string> = {
  info: 'processing',
  warning: 'warning',
  error: 'error',
  success: 'success',
};

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

/* ── Página ───────────────────────────────── */

export default function NotificationsPage() {
  const {
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
    markAsRead,
    markAllAsRead,
    createNotification,
    forceCheck,
    refresh,
  } = useNotifications();

  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const handleCreate = async (values: NotificationCreate) => {
    const ok = await createNotification(values);
    if (ok) {
      setModalOpen(false);
      form.resetFields();
    }
  };

  const handleFilterChange = (patch: Partial<typeof filters>) => {
    setFilters({ ...filters, ...patch });
    setPage(1);
  };

  const columns: ColumnsType<Notification> = useMemo(
    () => [
      {
        title: 'Tipo',
        dataIndex: 'type',
        key: 'type',
        width: 100,
        render: (type: string) => <Tag>{type}</Tag>,
      },
      {
        title: 'Categoría',
        dataIndex: 'category',
        key: 'category',
        width: 120,
      },
      {
        title: 'Severidad',
        dataIndex: 'severity',
        key: 'severity',
        width: 100,
        render: (sev: string) => (
          <Tag color={severityColors[sev] ?? 'default'}>{sev}</Tag>
        ),
      },
      {
        title: 'Título',
        dataIndex: 'title',
        key: 'title',
        ellipsis: true,
      },
      {
        title: 'Descripción',
        dataIndex: 'description',
        key: 'description',
        ellipsis: true,
        render: (d: string | null) => d ?? '-',
      },
      {
        title: 'Recurso',
        key: 'resource',
        width: 150,
        render: (_: unknown, r: Notification) =>
          r.resource_type
            ? `${r.resource_type} #${r.resource_id?.slice(0, 8) ?? ''}`
            : '-',
      },
      {
        title: 'Fecha',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 120,
        render: (d: string) => timeAgo(d),
      },
      {
        title: 'Estado',
        dataIndex: 'is_read',
        key: 'is_read',
        width: 100,
        render: (read: boolean) => (
          <Tag color={read ? 'default' : 'processing'}>
            {read ? 'Leído' : 'No leído'}
          </Tag>
        ),
      },
      {
        title: 'Acciones',
        key: 'actions',
        width: 130,
        render: (_: unknown, record: Notification) =>
          !record.is_read ? (
            <Button
              type="link"
              size="small"
              onClick={() => markAsRead(record.id)}
            >
              Marcar leída
            </Button>
          ) : null,
      },
    ],
    [markAsRead],
  );

  return (
    <>
      {/* ── Header ── */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <Title level={2} style={{ margin: 0 }}>
          Notificaciones
        </Title>
        <Space wrap>
          <Button icon={<ReloadOutlined />} onClick={refresh}>
            Actualizar
          </Button>
          <Button icon={<CheckOutlined />} onClick={markAllAsRead}>
            Marcar todas leídas
          </Button>
          <Button icon={<ThunderboltOutlined />} onClick={forceCheck}>
            Forzar verificación
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalOpen(true)}
          >
            Nueva notificación
          </Button>
        </Space>
      </div>

      {/* ── Filtros ── */}
      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="Tipo"
          allowClear
          style={{ width: 140 }}
          value={filters.type}
          onChange={(val) => handleFilterChange({ type: val })}
        >
          <Option value="system">System</Option>
          <Option value="business">Business</Option>
          <Option value="manual">Manual</Option>
        </Select>
        <Input
          placeholder="Categoría"
          allowClear
          style={{ width: 160 }}
          value={filters.category}
          onChange={(e) =>
            handleFilterChange({
              category: e.target.value || undefined,
            })
          }
        />
        <Select
          placeholder="Estado"
          allowClear
          style={{ width: 140 }}
          value={
            filters.is_read !== undefined
              ? String(filters.is_read)
              : undefined
          }
          onChange={(val) =>
            handleFilterChange({
              is_read:
                val !== undefined ? val === 'true' : undefined,
            })
          }
        >
          <Option value="false">No leído</Option>
          <Option value="true">Leído</Option>
        </Select>
      </Space>

      {/* ── Tabla ── */}
      <Table<Notification>
        columns={columns}
        dataSource={notifications}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize: perPage,
          total,
          showSizeChanger: true,
          pageSizeOptions: ['10', '20', '50'],
          onChange: (p, ps) => {
            setPage(p);
            if (ps !== perPage) setPerPage(ps);
          },
        }}
        locale={{
          emptyText: error ?? 'No hay notificaciones',
        }}
      />

      {/* ── Modal: Nueva notificación ── */}
      <Modal
        title="Nueva notificación"
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        destroyOnHidden
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{ type: 'manual', severity: 'info' }}
        >
          <Form.Item
            name="title"
            label="Título"
            rules={[{ required: true, message: 'El título es obligatorio' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item name="type" label="Tipo" rules={[{ required: true }]}>
            <Select>
              <Option value="system">System</Option>
              <Option value="business">Business</Option>
              <Option value="manual">Manual</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="category"
            label="Categoría"
            rules={[{ required: true, message: 'La categoría es obligatoria' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item name="severity" label="Severidad">
            <Select>
              <Option value="info">Info</Option>
              <Option value="warning">Warning</Option>
              <Option value="error">Error</Option>
              <Option value="success">Success</Option>
            </Select>
          </Form.Item>

          <Form.Item name="description" label="Descripción">
            <Input.TextArea rows={3} />
          </Form.Item>

          <Form.Item name="resource_type" label="Tipo de recurso">
            <Input />
          </Form.Item>

          <Form.Item name="resource_id" label="ID de recurso">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
