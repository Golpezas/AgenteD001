import { Table, Tag, Badge } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { BusinessPolicy } from '@/types';

interface PolicyViewerProps {
  policies: BusinessPolicy[];
  loading: boolean;
}

const POLICY_TYPE_MAP: Record<string, { label: string; color: string }> = {
  discount: { label: 'Descuento', color: 'green' },
  benefit: { label: 'Beneficio', color: 'blue' },
  financing: { label: 'Financiamiento', color: 'purple' },
  policy: { label: 'Regla', color: 'orange' },
};

function formatValue(policy: BusinessPolicy): string {
  if (policy.value === null || policy.value === undefined) return '—';
  if (policy.value_type === 'percentage') {
    return `${policy.value}%`;
  }
  if (policy.value_type === 'fixed_amount') {
    return `$${policy.value.toLocaleString('es-AR')}`;
  }
  return String(policy.value);
}

export default function PolicyViewer({ policies, loading }: PolicyViewerProps) {
  const columns: ColumnsType<BusinessPolicy> = [
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: 'Tipo',
      dataIndex: 'policy_type',
      key: 'policy_type',
      render: (type: string) => {
        const info = POLICY_TYPE_MAP[type] ?? {
          label: type,
          color: 'default',
        };
        return <Badge color={info.color} text={info.label} />;
      },
    },
    {
      title: 'Valor',
      key: 'value',
      render: (_, record) => formatValue(record),
    },
    {
      title: 'Tipo de Valor',
      dataIndex: 'value_type',
      key: 'value_type',
      render: (val: string | null) => {
        if (!val) return '—';
        return val === 'percentage' ? (
          <Tag color="blue">Porcentaje</Tag>
        ) : (
          <Tag color="cyan">Monto Fijo</Tag>
        );
      },
    },
    {
      title: 'Cliente',
      dataIndex: 'client_type',
      key: 'client_type',
      render: (val: string | null) => val ?? 'Todos',
    },
    {
      title: 'Vigencia',
      key: 'effective',
      render: (_, record) => {
        if (!record.effective_from && !record.effective_to) return '—';
        const from = record.effective_from ?? '—';
        const to = record.effective_to ?? 'Indefinido';
        return `${from} → ${to}`;
      },
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) =>
        active ? (
          <Tag color="success">Activo</Tag>
        ) : (
          <Tag color="error">Inactivo</Tag>
        ),
    },
  ];

  return (
    <Table<BusinessPolicy>
      columns={columns}
      dataSource={policies}
      rowKey="id"
      loading={loading}
      pagination={false}
      locale={{ emptyText: 'No hay políticas comerciales registradas' }}
    />
  );
}
