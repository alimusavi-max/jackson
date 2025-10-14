// ============= frontend/types/index.ts =============
export interface Order {
  id: number;
  order_code: string;
  shipment_id: string;
  customer_name: string;
  customer_phone: string;
  status: string;
  city: string;
  province: string;
  full_address: string;
  postal_code: string;
  tracking_code: string | null;
  order_date_persian: string;
  items_count: number;
  total_amount: number;
}

export interface OrderItem {
  id: number;
  product_title: string;
  product_code: string;
  quantity: number;
  price: number;
  product_image: string | null;
}

export interface OrderDetail extends Order {
  items: OrderItem[];
}

export interface Stats {
  total_orders: number;
  orders_with_tracking: number;
  orders_without_tracking: number;
  total_sales: number;
  unique_cities: number;
  recent_orders_7d: number;
  completion_rate: number;
}

export interface SMSLog {
  id: number;
  order_id: number;
  tracking_code: string;
  phone_number: string;
  message: string;
  sent_at: string;
  is_successful: boolean;
  error_message: string | null;
}
