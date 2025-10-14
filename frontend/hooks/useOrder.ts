// ============= frontend/hooks/useOrders.ts =============
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ordersAPI } from '@/lib/api';
import { toast } from 'sonner';

export function useOrders(params?: any) {
  return useQuery({
    queryKey: ['orders', params],
    queryFn: async () => {
      const response = await ordersAPI.getAll(params);
      return response.data;
    },
  });
}

export function useOrderDetail(id: number) {
  return useQuery({
    queryKey: ['order', id],
    queryFn: async () => {
      const response = await ordersAPI.getById(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useOrderStats() {
  return useQuery({
    queryKey: ['order-stats'],
    queryFn: async () => {
      const response = await ordersAPI.getStats();
      return response.data;
    },
    refetchInterval: 30000, // هر 30 ثانیه
  });
}

export function useSyncOrders() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (fetchDetails: boolean) => {
      const response = await ordersAPI.sync(fetchDetails);
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(
        `${data.new_orders} سفارش جدید و ${data.updated_orders} سفارش به‌روزرسانی شد`
      );
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['order-stats'] });
    },
    onError: () => {
      toast.error('خطا در همگام‌سازی سفارشات');
    },
  });
}