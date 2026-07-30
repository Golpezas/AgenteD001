/* ──────────────────────────────────────────────
   Types — interfaces que reflejan los schemas del backend
   ────────────────────────────────────────────── */

/** Empresa / Cliente */
export interface Company {
  id: string;
  business_name: string;
  cuit?: string | null;
  legal_rep?: string | null;
  email?: string | null;
  phone?: string | null;
  fiscal_address?: string | null;
  vertical?: string | null;
  tech_tier?: string | null;
  extra_data?: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CompanyCreate {
  business_name: string;
  cuit?: string;
  legal_rep?: string;
  email?: string;
  phone?: string;
  fiscal_address?: string;
  vertical?: string;
  tech_tier?: string;
  extra_data?: Record<string, unknown>;
}

export interface CompanyUpdate {
  business_name?: string;
  cuit?: string;
  legal_rep?: string;
  email?: string;
  phone?: string;
  fiscal_address?: string;
  vertical?: string;
  tech_tier?: string;
  extra_data?: Record<string, unknown>;
  is_active?: boolean;
}

/** Producto */
export interface Product {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  family?: string | null;
  category?: string | null;
  extra_data?: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  code: string;
  name: string;
  description?: string;
  family?: string;
  category?: string;
  extra_data?: Record<string, unknown>;
}

export interface ProductUpdate {
  code?: string;
  name?: string;
  description?: string;
  family?: string;
  category?: string;
  extra_data?: Record<string, unknown>;
  is_active?: boolean;
}

/** Lista de Precios */
export interface PriceList {
  id: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Item de lista de precios */
export interface PriceListItem {
  id: string;
  price_list_id: string;
  product_id: string;
  price: number;
  currency: string;
  effective_from: string;
  effective_to?: string | null;
  extra_data?: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Factor de licenciamiento */
export interface CalculationFactor {
  id: string;
  concept_key: string;
  concept_name: string;
  technology_tier: string;
  factor: number | null;
  is_available: boolean;
  extra_data?: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Política comercial */
export interface BusinessPolicy {
  id: string;
  name: string;
  policy_type: string;
  description?: string | null;
  value: number | null;
  value_type: string | null;
  conditions?: Record<string, unknown> | null;
  client_type?: string | null;
  is_active: boolean;
  effective_from?: string | null;
  effective_to?: string | null;
  created_at: string;
  updated_at: string;
}

/** Regla de precios */
export interface PricingRule {
  id: string;
  price_list_id: string;
  rule_type: string;
  params: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Respuesta paginada genérica */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

/** Severidad de notificación */
export type NotificationSeverity = 'info' | 'warning' | 'error' | 'success';

/** Tipo de notificación */
export type NotificationType = 'system' | 'business' | 'manual';

/** Notificación del sistema */
export interface Notification {
  id: string;
  type: NotificationType;
  category: string;
  title: string;
  description: string | null;
  severity: NotificationSeverity;
  resource_type: string | null;
  resource_id: string | null;
  is_read: boolean;
  is_dismissed: boolean;
  read_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Payload para crear notificación */
export interface NotificationCreate {
  type: NotificationType;
  category: string;
  title: string;
  description?: string;
  severity?: NotificationSeverity;
  resource_type?: string;
  resource_id?: string;
}

/** Respuesta del endpoint unread-count */
export interface UnreadCountResponse {
  count: number;
}

/** Alias para lista paginada de notificaciones */
export type NotificationList = PaginatedResponse<Notification>;
