import { useEffect } from 'react';
import { Modal, Form, InputNumber, Select, DatePicker, message } from 'antd';
import dayjs from 'dayjs';
import type { Product, PriceListItem } from '@/types';

interface PriceEditModalProps {
  open: boolean;
  product: Product | null;
  currentItem?: PriceListItem | null;
  onSave: (itemId: string | null, values: {
    price: number;
    currency: string;
    effective_from: string;
  }) => Promise<boolean>;
  onCancel: () => void;
}

export default function PriceEditModal({
  open,
  product,
  currentItem,
  onSave,
  onCancel,
}: PriceEditModalProps) {
  const [form] = Form.useForm();

  useEffect(() => {
    if (open) {
      form.resetFields();
      if (currentItem) {
        form.setFieldsValue({
          price: currentItem.price,
          currency: currentItem.currency,
          effective_from: dayjs(currentItem.effective_from),
        });
      } else {
        form.setFieldsValue({
          price: undefined,
          currency: 'ARS',
          effective_from: dayjs(),
        });
      }
    }
  }, [open, currentItem, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      const success = await onSave(currentItem?.id ?? null, {
        price: values.price,
        currency: values.currency,
        effective_from: values.effective_from.format('YYYY-MM-DD'),
      });
      if (success) {
        onCancel();
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        // Validation errors — form handles the display
        return;
      }
      message.error('Error al guardar el precio');
    }
  };

  return (
    <Modal
      title={
        product
          ? `Editar Precio — ${product.code} ${product.name}`
          : 'Editar Precio'
      }
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
        initialValues={{
          price: undefined,
          currency: 'ARS',
          effective_from: dayjs(),
        }}
      >
        <Form.Item
          name="price"
          label="Precio"
          rules={[
            { required: true, message: 'Ingrese el precio' },
            {
              type: 'number',
              min: 0.01,
              message: 'El precio debe ser mayor a 0',
            },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={0.01}
            step={0.01}
            precision={2}
            placeholder="0.00"
          />
        </Form.Item>

        <Form.Item
          name="currency"
          label="Moneda"
          rules={[{ required: true, message: 'Seleccione una moneda' }]}
        >
          <Select>
            <Select.Option value="ARS">ARS — Peso Argentino</Select.Option>
            <Select.Option value="USD">USD — Dólar Americano</Select.Option>
            <Select.Option value="EUR">EUR — Euro</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="effective_from"
          label="Vigente Desde"
          rules={[
            { required: true, message: 'Seleccione la fecha de vigencia' },
          ]}
        >
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
