import { useState } from 'react';
import { Typography, Button } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import ProductTable from '@/components/products/ProductTable';
import ProductForm from '@/components/products/ProductForm';
import useProducts from '@/hooks/useProducts';
import type { Product, ProductCreate, ProductUpdate } from '@/types';

const { Title } = Typography;

export default function ProductsPage() {
  const {
    products,
    total,
    loading,
    page,
    setPage,
    createProduct,
    updateProduct,
    deleteProduct,
  } = useProducts();

  const [modalOpen, setModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);

  const handleEdit = (product: Product) => {
    setEditingProduct(product);
    setModalOpen(true);
  };

  const handleCreate = () => {
    setEditingProduct(null);
    setModalOpen(true);
  };

  const handleSave = async (values: ProductCreate | ProductUpdate) => {
    if (editingProduct) {
      return await updateProduct(editingProduct.id, values);
    }
    return await createProduct(values as ProductCreate);
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setEditingProduct(null);
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
          Productos
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Nuevo Producto
        </Button>
      </div>

      <ProductTable
        products={products}
        total={total}
        loading={loading}
        page={page}
        perPage={10}
        onPageChange={setPage}
        onPerPageChange={() => {}}
        onEdit={handleEdit}
        onDelete={deleteProduct}
      />

      <ProductForm
        open={modalOpen}
        editingProduct={editingProduct}
        onCancel={handleModalClose}
        onSave={handleSave}
      />
    </>
  );
}
