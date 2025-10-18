// lib/api.ts
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const ordersAPI = {
  getAll: (params?: any) => api.get('/orders', { params }),
  getById: (id: number) => api.get(`/orders/${id}`),
  getStats: () => api.get('/stats'),
  sync: (fetchDetails: boolean) => 
    api.post('/orders/sync', { fetch_full_details: fetchDetails }),
  confirmNew: (shipmentIds?: number[]) =>
    api.post('/orders/confirm-new', { shipment_ids: shipmentIds }),
}

export const smsAPI = {
  send: (orderIds: number[], dryRun: boolean) => 
    api.post('/sms/send', { order_ids: orderIds, dry_run: dryRun }),
}