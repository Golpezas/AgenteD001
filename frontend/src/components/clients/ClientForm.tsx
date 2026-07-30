import { useEffect } from 'react';
import { Modal, Form, Input } from 'antd';
import type { Company, CompanyCreate, CompanyUpdate } from '@/types';

interface ClientFormProps {
  open: boolean;
  editingClient: Company | null;
  onCancel: () => void;
  onSave: (values: CompanyCreate | CompanyUpdate) => Promise<boolean>;
}

export default function ClientForm({
  open,
  editingClient,
  onCancel,
  onSave,
}: ClientFormProps) {
  const [form] = Form.useForm();
  const isEditing = !!editingClient;

  useEffect(() => {
    if (open) {
      if (editingClient) {
        form.setFieldsValue(editingClient);
      } else {
        form.resetFields();
      }
    }
  }, [open, editingClient, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      const success = await onSave(values);
      if (success) {
        form.resetFields();
      }
    } catch {
      // validation failed — modal stays open
    }
  };

  return (
    <Modal
      title={isEditing ? 'Editar Cliente' : 'Nuevo Cliente'}
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      okText="Guardar"
      cancelText="Cancelar"
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ is_active: true }}
      >
        <Form.Item
          name="business_name"
          label="Razón Social"
          rules={[
            { required: true, message: 'La razón social es obligatoria' },
            { max: 255, message: 'Máximo 255 caracteres' },
          ]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          name="cuit"
          label="CUIT"
          rules={[{ max: 20, message: 'Máximo 20 caracteres' }]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          name="legal_rep"
          label="Representante Legal"
          rules={[{ max: 255, message: 'Máximo 255 caracteres' }]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          name="email"
          label="Email"
          rules={[
            { type: 'email', message: 'Email inválido' },
            { max: 255, message: 'Máximo 255 caracteres' },
          ]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          name="phone"
          label="Teléfono"
          rules={[{ max: 50, message: 'Máximo 50 caracteres' }]}
        >
          <Input />
        </Form.Item>

        <Form.Item name="fiscal_address" label="Dirección Fiscal">
          <Input.TextArea rows={2} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
