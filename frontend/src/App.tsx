import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from '@/components/layout/AppLayout';
import Dashboard from '@/pages/Dashboard';
import Clients from '@/pages/Clients';
import Products from '@/pages/Products';
import PriceLists from '@/pages/PriceLists';
import BusinessRules from '@/pages/BusinessRules';
import NotificationsPage from '@/pages/Notifications';
import Analysis from '@/pages/Analysis';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/clients" element={<Clients />} />
          <Route path="/products" element={<Products />} />
          <Route path="/price-lists" element={<PriceLists />} />
          <Route path="/business-rules" element={<BusinessRules />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
