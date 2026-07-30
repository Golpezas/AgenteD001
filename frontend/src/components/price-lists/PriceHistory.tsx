import { Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';

export interface PriceHistoryEntry {
  id: string;
  price: number;
  currency: string;
  effective_from: string;
  effective_to: string | null;
}

interface PriceHistoryProps {
  history: PriceHistoryEntry[];
}

export default function PriceHistory({ history }: PriceHistoryProps) {
  const columns: ColumnsType<PriceHistoryEntry> = [
    {
      title: 'Precio',
      dataIndex: 'price',
      key: 'price',
      render: (val: number, record) =>
        val.toLocaleString('es-AR', {
          style: 'currency',
          currency: record.currency,
        }),
    },
    {
      title: 'Moneda',
      dataIndex: 'currency',
      key: 'currency',
      render: (val: string) => <Tag>{val}</Tag>,
    },
    {
      title: 'Vigente Desde',
      dataIndex: 'effective_from',
      key: 'effective_from',
    },
    {
      title: 'Vigente Hasta',
      dataIndex: 'effective_to',
      key: 'effective_to',
      render: (val: string | null) => val ?? '—',
    },
  ];

  if (history.length === 0) {
    return (
      <div style={{ padding: '12px 0', color: '#888' }}>
        Sin historial de precios para este producto.
      </div>
    );
  }

  return (
    <Table<PriceHistoryEntry>
      columns={columns}
      dataSource={history}
      rowKey="id"
      pagination={false}
      size="small"
      locale={{ emptyText: 'Sin historial de precios' }}
    />
  );
}
