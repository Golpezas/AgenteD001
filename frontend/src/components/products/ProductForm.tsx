import { useEffect } from 'react';
import { Modal, Form, Input } from 'antd';
import type { Product, ProductCreate, ProductUpdate } from '@/types';

interface ProductFormProps {
  open: boolean;
  editingProduct: Product | null;
  onCancel: () => void;
  onSave: (values: ProductCreate | ProductUpdate) => Promise<boolean>;
}

export default function ProductForm({
  open,
  editingProduct,
  onCancel,
  onSave,
}: ProductFormProps) {
  const [form] = Form.useForm();
  const isEditing = !!editingProduct;

  useEffect(() => {
    if (open) {
      if (editingProduct) {
        form.setFieldsValue(editingProduct);
      } else {
        form.resetFields();
      }
    }
  }, [open, editingProduct, form]);

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
      title={isEditing ? 'Editar Producto' : 'Nuevo Producto'}
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
          name="code"
          label="SKU / Código"
          rules={[
            { required: true, message: 'El código es obligatorio' },
            { max: 50, message: 'Máximo 50 caracteres' },
          ]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          name="name"
          label="Nombre"
          rules={[
            { required: true, message: 'El nombre es obligatorio' },
            { max: 255, message: 'Máximo 255 caracteres' },
          ]}
        >
          <Input />
        </Form.Item>

        <Form.Item name="description" label="Descripción">
          <Input.TextArea rows={3} />
        </Form.Item>

        <Form.Item
          name="category"
          label="Categoría"
          rules={[{ max: 50, message: 'Máximo 50 caracteres' }]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          name="family"
          label="Familia"
          rules={[{ max: 100, message: 'Máximo 100 caracteres' }]}
        >
          <Input />
        </Form.Item>
      </Form>
    </Modal>
  );
}
