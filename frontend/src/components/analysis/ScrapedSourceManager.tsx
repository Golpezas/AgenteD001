/* ──────────────────────────────────────────────
   ScrapedSourceManager — Gestión de fuentes scrapeadas
   ────────────────────────────────────────────── */

import React, { useState } from 'react';
import { Table, Tag, Button, Space, Modal, Form, Input, Popconfirm, Empty, Spin } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ScrapedSource, ScrapedSourceCreate } from '../../types';

interface ScrapedSourceManagerProps {
  sources: ScrapedSource[];
  loading?: boolean;
  onRefresh: () => void;
  onCreate: (payload: ScrapedSourceCreate) => Promise<boolean>;
  onDelete: (sourceId: string) => Promise<boolean>;
  onUpdate?: (source: ScrapedSource) => Promise<boolean>;
}

export const ScrapedSourceManager: React.FC<ScrapedSourceManagerProps> = ({
  sources,
  loading = false,
  onRefresh,
  onCreate,
  onDelete,
  onUpdate,
}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<ScrapedSource | null>(null);
  const [form] = Form.useForm();

  const showCreateModal = () => {
    setEditingSource(null);
    form.resetFields();
    setModalOpen(true);
  };

  const showEditModal = (source: ScrapedSource) => {
    setEditingSource(source);
    form.setFieldsValue({
      name: source.name || '',
      schedule_interval_minutes: source.schedule_interval_minutes || '',
    });
    setModalOpen(true);
  };

  const handleSubmit = async (values: ScrapedSourceCreate) => {
    const success = editingSource
      ? await onUpdate!({ ...editingSource, ...values })
      : await onCreate(values);
    if (success) {
      form.resetFields();
      setModalOpen(false);
      setEditingSource(null);
      onRefresh();
    }
  };

  const handleDelete = async (sourceId: string) => {
    const success = await onDelete(sourceId);
    if (success) onRefresh();
  };

  const columns = [
    {
      title: 'URL',
      dataIndex: 'url',
      width: '40%',
      ellipsis: true,
      tooltip: (url: string) => url,
    },
    {
      title: 'Nombre',
      dataIndex: 'name',
      width: '20%',
      render: (name: string | null) => name || <Tag color="default">Sin nombre</Tag>,
    },
    {
      title: 'Intervalo (min)',
      dataIndex: 'schedule_interval_minutes',
      width: '15%',
      render: (val: number | null) => (val ? `${val} min` : <Tag color="default">Manual</Tag>),
    },
    {
      title: 'Último análisis',
      dataIndex: 'last_analyzed_at',
      width: '15%',
      render: (date: string | null) => (date ? new Date(date).toLocaleString() : 'Nunca'),
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      width: '10%',
      render: (active: boolean) => (active ? <Tag color="success">Activo</Tag> : <Tag color="default">Inactivo</Tag>),
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: '100px',
      render: (_: unknown, record: ScrapedSource) => (
        <Space>
          {onUpdate && (
            <Button type="link" icon={<EditOutlined />} size="small" onClick={() => showEditModal(record)}>
              Editar
            </Button>
          )}
          <Popconfirm
            title="¿Eliminar esta fuente?"
            description="Se eliminará permanentemente"
            okText="Sí"
            cancelText="No"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />} size="small">
              Eliminar
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3>Fuentes Scrapeadas ({sources.length})</h3>
        <Space>
          <Button icon={<PlusOutlined />} onClick={showCreateModal} loading={loading}>
            Nueva fuente
          </Button>
          <Button icon={<ReloadOutlined />} onClick={onRefresh} loading={loading}>
            Actualizar
          </Button>
        </Space>
      </div>

      {sources.length === 0 && !loading && (
        <Empty
          description="No hay fuentes configuradas. Agrega una URL para monitorear."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button icon={<PlusOutlined />} onClick={showCreateModal} type="primary">
            Crear primera fuente
          </Button>
        </Empty>
      )}

      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={sources}
          rowKey="id"
          pagination={{ pageSize: 10, showSizeChanger: true }}
        />
      </Spin>

      {/* Create/Edit Modal */}
      <Modal
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          setEditingSource(null);
          form.resetFields();
        }}
        title={editingSource ? 'Editar fuente' : 'Nueva fuente scrapeada'}
        width={500}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {editingSource ? (
            <Form.Item label="URL" colon={false}>
              <Input disabled value={editingSource.url} style={{ background: '#f5f5f5' }} />
            </Form.Item>
          ) : (
            <Form.Item
              name="url"
              label="URL"
              rules={[{ required: true, message: 'La URL es obligatoria' }, { max: 2048 }]}
            >
              <Input placeholder="https://ejemplo.com/producto" />
            </Form.Item>
          )}

          <Form.Item name="name" label="Nombre (opcional)">
            <Input placeholder="Nombre descriptivo" />
          </Form.Item>

          <Form.Item
            name="schedule_interval_minutes"
            label="Intervalo de monitoreo (minutos, opcional)"
            rules={[{ type: 'number', min: 1, message: 'Mínimo 1 minuto' }]}
          >
            <Input type="number" min={1} placeholder="Ej: 60 para cada hora" />
          </Form.Item>

          <Space style={{ marginTop: 16, justifyContent: 'flex-end' }}>
            <Button onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              {editingSource ? 'Guardar' : 'Crear'}
            </Button>
          </Space>
        </Form>
      </Modal>
    </div>
  );
};