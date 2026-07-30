import { useState } from 'react';
import { Typography, Button } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import ClientTable from '@/components/clients/ClientTable';
import ClientForm from '@/components/clients/ClientForm';
import useClients from '@/hooks/useClients';
import type { Company, CompanyCreate, CompanyUpdate } from '@/types';

const { Title } = Typography;

export default function Clients() {
  const {
    clients,
    total,
    loading,
    page,
    setPage,
    createClient,
    updateClient,
    deleteClient,
  } = useClients();

  const [modalOpen, setModalOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<Company | null>(null);

  const handleEdit = (client: Company) => {
    setEditingClient(client);
    setModalOpen(true);
  };

  const handleCreate = () => {
    setEditingClient(null);
    setModalOpen(true);
  };

  const handleSave = async (values: CompanyCreate | CompanyUpdate) => {
    if (editingClient) {
      return await updateClient(editingClient.id, values);
    }
    return await createClient(values as CompanyCreate);
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setEditingClient(null);
  };

  return (
    <>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <Title level={2} style={{ margin: 0 }}>
          Clientes
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Nuevo Cliente
        </Button>
      </div>

      <ClientTable
        clients={clients}
        total={total}
        loading={loading}
        page={page}
        perPage={10}
        onPageChange={setPage}
        onPerPageChange={() => {}}
        onEdit={handleEdit}
        onDelete={deleteClient}
      />

      <ClientForm
        open={modalOpen}
        editingClient={editingClient}
        onCancel={handleModalClose}
        onSave={handleSave}
      />
    </>
  );
}
