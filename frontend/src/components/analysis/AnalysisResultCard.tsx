/* ──────────────────────────────────────────────
   AnalysisResultCard — Tarjeta de resultado con approve/reject
   ────────────────────────────────────────────── */

import React from 'react';
import { Card, Tag, Button, Space, Typography, Divider, Modal, Form, Input } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, EditOutlined } from '@ant-design/icons';
import type { AnalysisResult, AnalysisResultStatus } from '../../types';

interface AnalysisResultCardProps {
  result: AnalysisResult;
  onApprove: (id: string) => void;
  onReject: (id: string, reason?: string) => void;
  loading?: boolean;
}

const STATUS_CONFIG: Record<AnalysisResultStatus, { color: string; label: string; icon: React.ReactNode }> = {
  proposal: { color: 'orange', label: 'Propuesta', icon: <EditOutlined /> },
  accepted: { color: 'green', label: 'Aceptado', icon: <CheckCircleOutlined /> },
  rejected: { color: 'red', label: 'Rechazado', icon: <CloseCircleOutlined /> },
};

export const AnalysisResultCard: React.FC<AnalysisResultCardProps> = ({
  result,
  onApprove,
  onReject,
  loading = false,
}) => {
  const [rejectModalOpen, setRejectModalOpen] = React.useState(false);
  const [form] = Form.useForm();

  const config = STATUS_CONFIG[result.status];

  const handleRejectSubmit = async (values: { reason: string }) => {
    await onReject(result.id, values.reason);
    setRejectModalOpen(false);
    form.resetFields();
  };

  const handleApprove = () => {
    onApprove(result.id);
  };

  const handleReject = () => {
    setRejectModalOpen(true);
  };

  return (
    <Card
      style={{ marginBottom: 16 }}
      extra={
        result.status === 'proposal' && !loading && (
          <Space>
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={handleApprove}
              loading={loading}
            >
              Aprobar
            </Button>
            <Button
              danger
              icon={<CloseCircleOutlined />}
              onClick={handleReject}
              loading={loading}
            >
              Rechazar
            </Button>
          </Space>
        )
      }
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <Typography.Title level={4} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            {result.product_name || 'Producto sin nombre'}
            <Tag color={config.color} icon={config.icon}>
              {config.label}
            </Tag>
          </Typography.Title>
          <Typography.Text type="secondary" style={{ marginLeft: 4 }}>
            Job: {result.job_id.slice(0, 8)}… | Result: {result.id.slice(0, 8)}…
          </Typography.Text>
        </div>
        <Typography.Text type="secondary">
          {new Date(result.created_at).toLocaleString()}
        </Typography.Text>
      </div>

      <Divider />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        {result.extracted_price !== null && (
          <div>
            <Typography.Text type="secondary" strong>Precio extraído:</Typography.Text>
            <div style={{ fontSize: 18, fontWeight: 600, marginTop: 4 }}>
              {result.extracted_price.toLocaleString()} {result.currency || 'ARS'}
            </div>
          </div>
        )}

        {result.confidence_score !== null && (
          <div>
            <Typography.Text type="secondary" strong>Confianza:</Typography.Text>
            <div style={{ fontSize: 18, fontWeight: 600, marginTop: 4 }}>
              {(result.confidence_score * 100).toFixed(1)}%
            </div>
          </div>
        )}

        <div>
          <Typography.Text type="secondary" strong>Creado:</Typography.Text>
          <div style={{ marginTop: 4 }}>{new Date(result.created_at).toLocaleString()}</div>
        </div>
      </div>

      {result.proposal_data && (
        <>
          <Divider style={{ marginTop: 16 }} />
          <Typography.Text type="secondary" strong>Datos de la propuesta:</Typography.Text>
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginTop: 8, background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
            {JSON.stringify(result.proposal_data, null, 2)}
          </pre>
        </>
      )}

      {result.raw_data && (
        <>
          <Divider style={{ marginTop: 16 }} />
          <Typography.Text type="secondary" strong>Respuesta cruda (Gemini):</Typography.Text>
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginTop: 8, background: '#fafafa', padding: 12, borderRadius: 4, maxHeight: 200, overflow: 'auto' }}>
            {JSON.stringify(result.raw_data, null, 2)}
          </pre>
        </>
      )}

      {/* Reject Modal */}
      <Modal
        open={rejectModalOpen}
        onCancel={() => setRejectModalOpen(false)}
        title="Rechazar propuesta"
        width={500}
      >
        <Form form={form} layout="vertical" onFinish={handleRejectSubmit}>
          <Form.Item name="reason" label="Motivo (opcional)" rules={[{ max: 500 }]}>
            <Input.TextArea rows={4} placeholder="Razón para rechazar esta propuesta…" />
          </Form.Item>
          <Space style={{ marginTop: 16, justifyContent: 'flex-end' }}>
            <Button onClick={() => setRejectModalOpen(false)}>Cancelar</Button>
            <Button type="primary" danger htmlType="submit" loading={loading}>
              Confirmar rechazo
            </Button>
          </Space>
        </Form>
      </Modal>
    </Card>
  );
};