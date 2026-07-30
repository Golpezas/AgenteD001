import { Typography, Tabs } from 'antd';
import useBusinessRules from '@/hooks/useBusinessRules';
import PolicyViewer from '@/components/business-rules/PolicyViewer';

const { Title } = Typography;

const POLICY_TABS = [
  { key: undefined as string | undefined, label: 'Todas' },
  { key: 'discount', label: 'Descuentos' },
  { key: 'benefit', label: 'Beneficios' },
  { key: 'financing', label: 'Financiamiento' },
  { key: 'policy', label: 'Reglas' },
];

export default function BusinessRulesPage() {
  const { policies, loading, filterType, setFilterType } = useBusinessRules();

  const handleTabChange = (key: string) => {
    setFilterType(key === 'all' ? undefined : key);
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
          Reglas de Negocio
        </Title>
      </div>

      <Tabs
        activeKey={filterType ?? 'all'}
        onChange={handleTabChange}
        items={POLICY_TABS.map((tab) => ({
          key: tab.key ?? 'all',
          label: tab.label,
          children: (
            <PolicyViewer policies={policies} loading={loading} />
          ),
        }))}
      />
    </>
  );
}
