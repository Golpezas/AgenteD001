import { Table, Button, Space, Popconfirm } from 'antd';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Product } from '@/types';

interface ProductTableProps {
  products: Product[];
  total: number;
  loading: boolean;
  page: number;
  perPage: number;
  onPageChange: (page: number) => void;
  onPerPageChange: (perPage: number) => void;
  onEdit: (product: Product) => void;
  onDelete: (id: string) => void;
}

export default function ProductTable({
  products,
  total,
  loading,
  page,
  perPage,
  onPageChange,
  onPerPageChange,
  onEdit,
  onDelete,
}: ProductTableProps) {
  const columns: ColumnsType<Product> = [
    {
      title: 'SKU / Código',
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
      title: 'Categoría',
      dataIndex: 'category',
      key: 'category',
      responsive: ['md' as const],
      render: (val: string | null) => val ?? '—',
    },
    {
      title: 'Familia',
      dataIndex: 'family',
      key: 'family',
      responsive: ['lg' as const],
      render: (val: string | null) => val ?? '—',
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => onEdit(record)}
          >
            Editar
          </Button>
          <Popconfirm
            title="Eliminar producto"
            description="¿Está seguro de eliminar este producto?"
            onConfirm={() => onDelete(record.id)}
            okText="Eliminar"
            cancelText="Cancelar"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              Eliminar
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Table<Product>
      columns={columns}
      dataSource={products}
      rowKey="id"
      loading={loading}
      pagination={{
        current: page,
        pageSize: perPage,
        total,
        showSizeChanger: true,
        pageSizeOptions: ['10', '20', '50'],
        onChange: onPageChange,
        onShowSizeChange: (_, size) => onPerPageChange(size),
        showTotal: (totalItems) => `Total: ${totalItems} productos`,
      }}
      locale={{ emptyText: 'No hay productos registrados' }}
    />
  );
}
