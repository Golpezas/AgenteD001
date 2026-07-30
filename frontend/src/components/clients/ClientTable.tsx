import { Table, Button, Space, Popconfirm } from 'antd';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Company } from '@/types';

interface ClientTableProps {
  clients: Company[];
  total: number;
  loading: boolean;
  page: number;
  perPage: number;
  onPageChange: (page: number) => void;
  onPerPageChange: (perPage: number) => void;
  onEdit: (client: Company) => void;
  onDelete: (id: string) => void;
}

export default function ClientTable({
  clients,
  total,
  loading,
  page,
  perPage,
  onPageChange,
  onPerPageChange,
  onEdit,
  onDelete,
}: ClientTableProps) {
  const columns: ColumnsType<Company> = [
    {
      title: 'Razón Social',
      dataIndex: 'business_name',
      key: 'business_name',
      sorter: (a, b) => a.business_name.localeCompare(b.business_name),
    },
    {
      title: 'CUIT',
      dataIndex: 'cuit',
      key: 'cuit',
      render: (val: string | null) => val ?? '—',
    },
    {
      title: 'Rep. Legal',
      dataIndex: 'legal_rep',
      key: 'legal_rep',
      responsive: ['md' as const],
      render: (val: string | null) => val ?? '—',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      responsive: ['lg' as const],
      render: (val: string | null) => val ?? '—',
    },
    {
      title: 'Teléfono',
      dataIndex: 'phone',
      key: 'phone',
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
            title="Eliminar cliente"
            description="¿Está seguro de eliminar este cliente?"
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
    <Table<Company>
      columns={columns}
      dataSource={clients}
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
        showTotal: (totalItems) => `Total: ${totalItems} clientes`,
      }}
      locale={{ emptyText: 'No hay clientes registrados' }}
    />
  );
}
