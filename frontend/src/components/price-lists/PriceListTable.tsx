import { Table, Button, Space, Tag } from 'antd';
import { EditOutlined, HistoryOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Product, PriceListItem } from '@/types';
import PriceHistory from './PriceHistory';
import type { PriceHistoryEntry } from './PriceHistory';

interface PriceListTableProps {
  products: Product[];
  priceItems: PriceListItem[];
  loading: boolean;
  onEditPrice: (product: Product, currentItem?: PriceListItem) => void;
}

/** Construye entradas de histórico a partir de price_list_items */
function buildHistory(
  productId: string,
  items: PriceListItem[],
): PriceHistoryEntry[] {
  return items
    .filter((i) => i.product_id === productId)
    .map((i) => ({
      id: i.id,
      price: i.price,
      currency: i.currency,
      effective_from: i.effective_from,
      effective_to: i.effective_to ?? null,
    }))
    .sort(
      (a, b) =>
        new Date(b.effective_from).getTime() -
        new Date(a.effective_from).getTime(),
    );
}

/** Busca el item de precio vigente para un producto */
function findCurrentPrice(
  productId: string,
  items: PriceListItem[],
): PriceListItem | undefined {
  return items.find(
    (i) =>
      i.product_id === productId &&
      i.is_active &&
      (!i.effective_to || new Date(i.effective_to) >= new Date()),
  );
}

export default function PriceListTable({
  products,
  priceItems,
  loading,
  onEditPrice,
}: PriceListTableProps) {
  const columns: ColumnsType<Product> = [
    {
      title: 'Código',
      dataIndex: 'code',
      key: 'code',
      sorter: (a, b) => a.code.localeCompare(b.code),
    },
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: 'Familia',
      dataIndex: 'family',
      key: 'family',
      responsive: ['md' as const],
      render: (val: string | null) => val ?? '—',
    },
    {
      title: 'Categoría',
      dataIndex: 'category',
      key: 'category',
      responsive: ['lg' as const],
      render: (val: string | null) => val ?? '—',
    },
    {
      title: 'Precio Actual',
      key: 'currentPrice',
      render: (_, record) => {
        const item = findCurrentPrice(record.id, priceItems);
        return item ? (
          <span>
            {item.price.toLocaleString('es-AR', {
              style: 'currency',
              currency: item.currency,
            })}
          </span>
        ) : (
          <Tag color="default">Sin precio</Tag>
        );
      },
    },
    {
      title: 'Moneda',
      key: 'currency',
      render: (_, record) => {
        const item = findCurrentPrice(record.id, priceItems);
        return item ? (
          <Tag>{item.currency}</Tag>
        ) : (
          '—'
        );
      },
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 160,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() =>
              onEditPrice(record, findCurrentPrice(record.id, priceItems))
            }
          >
            Editar
          </Button>
        </Space>
      ),
    },
  ];

  const expandedRowRender = (record: Product) => {
    const history = buildHistory(record.id, priceItems);
    return <PriceHistory history={history} />;
  };

  return (
    <Table<Product>
      columns={columns}
      dataSource={products}
      rowKey="id"
      loading={loading}
      pagination={false}
      expandable={{
        expandedRowRender,
        expandIcon: ({ expanded, onExpand, record }) => (
          <Button
            type="text"
            size="small"
            icon={<HistoryOutlined />}
            onClick={(e) => onExpand(record, e)}
          >
            {expanded ? 'Ocultar historial' : 'Historial'}
          </Button>
        ),
      }}
      locale={{ emptyText: 'No hay productos registrados' }}
    />
  );
}
