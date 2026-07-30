import { Card, Statistic } from 'antd';
import type { ReactNode } from 'react';

interface StatCardProps {
  icon: ReactNode;
  title: string;
  value: number;
  loading?: boolean;
}

export default function StatCard({ icon, title, value, loading }: StatCardProps) {
  return (
    <Card hoverable loading={loading}>
      <Statistic
        title={title}
        value={value}
        prefix={icon}
      />
    </Card>
  );
}
