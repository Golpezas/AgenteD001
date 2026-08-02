/* ──────────────────────────────────────────────
   AnalysisJobTable — Tabla de jobs de análisis
   ────────────────────────────────────────────── */

import React, { useState } from 'react';
import { Table, Tag, Button, Space, Popconfirm, Empty, Spin } from 'antd';
import { ReloadOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons';
import type { AnalysisJob, AnalysisJobStatus } from '../../types';

interface AnalysisJobTableProps {
  jobs: AnalysisJob[];
  loading?: boolean;
  onRefresh: () => void;
  onViewDetails?: (job: AnalysisJob) => void;
  onDelete?: (jobId: string) => void;
}

const STATUS_COLORS: Record<AnalysisJobStatus, string> = {
  pending: 'blue',
  processing: 'orange',
  completed: 'green',
  failed: 'red',
};

const STATUS_LABELS: Record<AnalysisJobStatus, string> = {
  pending: 'Pendiente',
  processing: 'Procesando',
  completed: 'Completado',
  failed: 'Fallido',
};

export const AnalysisJobTable: React.FC<AnalysisJobTableProps> = ({
  jobs,
  loading = false,
  onRefresh,
  onViewDetails,
  onDelete,
}) => {
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([]);

  const handleExpand = (expanded: boolean, record: AnalysisJob) => {
    if (expanded) {
      setExpandedRowKeys((prev) => [...prev, record.id]);
    } else {
      setExpandedRowKeys((prev) => prev.filter((id) => id !== record.id));
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 200,
      render: (id: string) => <code>{id.slice(0, 8)}…</code>,
    },
    {
      title: 'Tipo',
      dataIndex: 'job_type',
      width: 100,
      render: (type: string) => (
        <Tag color={type === 'image' ? 'purple' : 'cyan'}>
          {type === 'image' ? 'Imagen' : 'URL'}
        </Tag>
      ),
    },
    {
      title: 'Entrada',
      dataIndex: 'input_data',
      width: 250,
      render: (input: Record<string, unknown>) => {
        if (input.url) return <span title={input.url as string}>{(input.url as string).slice(0, 50)}…</span>;
        if (input.image_bytes) return <span>📷 Imagen (base64)</span>;
        return '-';
      },
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      width: 120,
      render: (status: AnalysisJobStatus) => (
        <Tag color={STATUS_COLORS[status]}>
          {STATUS_LABELS[status]}
        </Tag>
      ),
    },
    {
      title: 'Creado',
      dataIndex: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 180,
      render: (_: unknown, record: AnalysisJob) => (
        <Space>
          {onViewDetails && (
            <Button type="link" icon={<EyeOutlined />} size="small" onClick={() => onViewDetails(record)}>
              Ver
            </Button>
          )}
          {onDelete && record.status !== 'processing' && (
            <Popconfirm
              title="¿Eliminar este job?"
              description="No se puede deshacer"
              okText="Sí"
              cancelText="No"
              onConfirm={() => onDelete?.(record.id)}
            >
              <Button type="link" danger icon={<DeleteOutlined />} size="small">
                Eliminar
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h3>Jobs de Análisis ({jobs.length})</h3>
        <Button icon={<ReloadOutlined />} onClick={onRefresh} loading={loading}>
          Actualizar
        </Button>
      </div>

      {jobs.length === 0 && !loading && (
        <Empty description="No hay jobs de análisis. Crea uno nuevo para empezar." />
      )}

      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={jobs}
          rowKey="id"
          expandable={{
            expandedRowKeys,
            onExpand: handleExpand,
            expandedRowRender: (record) => (
              <div style={{ padding: 16 }}>
                <strong>ID completo:</strong> <code>{record.id}</code>
                <br />
                <strong>Input data:</strong>
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginTop: 8 }}>
                  {JSON.stringify(record.input_data, null, 2)}
                </pre>
                {record.error_message && (
                  <>
                    <br />
                    <strong style={{ color: 'red' }}>Error:</strong>
                    <div style={{ color: 'red', marginTop: 4 }}>{record.error_message}</div>
                  </>
                )}
                {record.result_id && (
                  <>
                    <br />
                    <strong>Result ID:</strong> <code>{record.result_id}</code>
                  </>
                )}
              </div>
            ),
          }}
          pagination={{ pageSize: 10, showSizeChanger: true }}
        />
      </Spin>
    </div>
  );
};