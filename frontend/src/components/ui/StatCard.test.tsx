import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import StatCard from './StatCard';

describe('StatCard', () => {
  it('renders title and value', () => {
    render(<StatCard icon={<span data-testid="icon" />} title="Total Revenue" value={100} />);
    expect(screen.getByText('Total Revenue')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('renders in loading state with skeleton', () => {
    const { container } = render(<StatCard icon={<span />} title="Loading" value={0} loading />);
    // Ant Design Card with loading=true renders a skeleton placeholder
    expect(container.querySelector('.ant-card-loading')).toBeInTheDocument();
    // Statistic content should not be visible while loading
    expect(screen.queryByText('0')).not.toBeInTheDocument();
  });
});
