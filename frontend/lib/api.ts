// lib/api.ts
const API_BASE_URL = 'http://localhost:8000/api'

// توکن را از localStorage بگیر
const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token')
  }
  return null
}

// هدرهای پیش‌فرض با authentication
const getHeaders = (): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  
  const token = getAuthToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  return headers
}

// تابع کمکی برای handle کردن response
const handleResponse = async (response: Response) => {
  if (response.status === 401) {
    // توکن منقضی شده - ریدایرکت به لاگین
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    throw new Error('Unauthorized')
  }

  if (!response.ok) {
    const error = await response.text()
    throw new Error(error || `HTTP ${response.status}`)
  }

  const data = await response.json()
  return data
}

export const ordersAPI = {
  // دریافت همه سفارشات
  async getAll(params?: { limit?: number; offset?: number; status?: string; has_tracking?: boolean; search?: string }) {
    const queryParams = new URLSearchParams()
    
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    if (params?.status) queryParams.append('status', params.status)
    if (params?.has_tracking !== undefined) queryParams.append('has_tracking', params.has_tracking.toString())
    if (params?.search) queryParams.append('search', params.search)

    const url = `${API_BASE_URL}/orders${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    
    console.log('🔍 Fetching orders from:', url)
    
    const response = await fetch(url, {
      method: 'GET',
      headers: getHeaders(),
    })

    const data = await handleResponse(response)
    
    console.log('📦 Response data:', data)
    
    // ✅ اینجا مهمه: چک کنیم data چه ساختاری داره
    if (data && typeof data === 'object') {
      // اگر data.data وجود داشت (فرمت: { data: [...], total: X })
      if (Array.isArray(data.data)) {
        console.log('✅ Format 1: { data: [...], total, ... }')
        return data
      }
      // اگر خود data یک آرایه بود
      else if (Array.isArray(data)) {
        console.log('✅ Format 2: [...]')
        return { data, total: data.length, page: 1, limit: data.length }
      }
    }
    
    // اگر هیچکدام نبود، خطا بده
    console.error('❌ Invalid response format:', data)
    throw new Error('Invalid response format')
  },

  // دریافت یک سفارش
  async getOne(id: number) {
    const response = await fetch(`${API_BASE_URL}/orders/${id}`, {
      method: 'GET',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },

  // همگام‌سازی سفارشات
  async sync(fetchFullDetails: boolean = false) {
    const response = await fetch(`${API_BASE_URL}/orders/sync`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ fetch_full_details: fetchFullDetails }),
    })

    return handleResponse(response)
  },

  // تایید سفارشات جدید
  async confirmNew() {
    const response = await fetch(`${API_BASE_URL}/orders/confirm-new`, {
      method: 'POST',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },

  // آمار سفارشات
  async getStats() {
    const response = await fetch(`${API_BASE_URL}/orders/stats/summary`, {
      method: 'GET',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },
}

export const trackingAPI = {
  // استخراج از PDF
  async extractPDF(file: File) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/tracking/extract-pdf`, {
      method: 'POST',
      body: formData,
      headers: {
        ...(getAuthToken() ? { 'Authorization': `Bearer ${getAuthToken()}` } : {}),
      },
    })

    return handleResponse(response)
  },

  // تطبیق با دیتابیس
  async matchDatabase(trackingData: any[]) {
    const response = await fetch(`${API_BASE_URL}/tracking/match-database`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ tracking_data: trackingData }),
    })

    return handleResponse(response)
  },

  // ثبت کد رهگیری
  async submit(orderId: number, trackingCode: string) {
    const formData = new FormData()
    formData.append('order_id', orderId.toString())
    formData.append('tracking_code', trackingCode)

    const response = await fetch(`${API_BASE_URL}/tracking/submit`, {
      method: 'POST',
      body: formData,
      headers: {
        ...(getAuthToken() ? { 'Authorization': `Bearer ${getAuthToken()}` } : {}),
      },
    })

    return handleResponse(response)
  },
}

export const smsAPI = {
  // وضعیت سرویس
  async getStatus() {
    const response = await fetch(`${API_BASE_URL}/sms/status`, {
      method: 'GET',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },

  // سفارشات آماده
  async getReadyOrders() {
    const response = await fetch(`${API_BASE_URL}/sms/ready-orders`, {
      method: 'GET',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },

  // ارسال پیامک
  async send(orderIds: number[], dryRun: boolean = false) {
    const response = await fetch(`${API_BASE_URL}/sms/send`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        order_ids: orderIds,
        dry_run: dryRun,
      }),
    })

    return handleResponse(response)
  },

  // تاریخچه
  async getLogs(limit: number = 100) {
    const response = await fetch(`${API_BASE_URL}/sms/logs?limit=${limit}`, {
      method: 'GET',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },
}

export const reportsAPI = {
  // آمار و گزارشات
  async getStats(days: number = 30) {
    const response = await fetch(`${API_BASE_URL}/reports/stats?days=${days}`, {
      method: 'GET',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },

  // مقایسه دوره‌های زمانی
  async getComparison() {
    const response = await fetch(`${API_BASE_URL}/reports/comparison`, {
      method: 'GET',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },
}

export const senderProfilesAPI = {
  // دریافت همه پروفایل‌ها
  async getAll() {
    const response = await fetch(`${API_BASE_URL}/sender-profiles/`, {
      method: 'GET',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },

  // دریافت پروفایل پیش‌فرض
  async getDefault() {
    const response = await fetch(`${API_BASE_URL}/sender-profiles/default/get`, {
      method: 'GET',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },

  // ایجاد پروفایل
  async create(profile: any) {
    const response = await fetch(`${API_BASE_URL}/sender-profiles/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(profile),
    })

    return handleResponse(response)
  },

  // به‌روزرسانی پروفایل
  async update(id: number, profile: any) {
    const response = await fetch(`${API_BASE_URL}/sender-profiles/${id}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(profile),
    })

    return handleResponse(response)
  },

  // حذف پروفایل
  async delete(id: number) {
    const response = await fetch(`${API_BASE_URL}/sender-profiles/${id}`, {
      method: 'DELETE',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },

  // تنظیم به عنوان پیش‌فرض
  async setDefault(id: number) {
    const response = await fetch(`${API_BASE_URL}/sender-profiles/${id}/set-default`, {
      method: 'POST',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },
}

export const warehouseAPI = {
  // محصولات
  async getProducts(lowStockOnly: boolean = false) {
    const response = await fetch(
      `${API_BASE_URL}/warehouse/products?low_stock_only=${lowStockOnly}`,
      {
        method: 'GET',
        headers: getHeaders(),
      }
    )

    return handleResponse(response)
  },

  // آمار انبار
  async getStats() {
    const response = await fetch(`${API_BASE_URL}/warehouse/stats`, {
      method: 'GET',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },
}

export const authAPI = {
  // لاگین
  async login(username: string, password: string) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      body: formData,
    })

    const data = await handleResponse(response)
    
    // ذخیره توکن
    if (data.access_token && typeof window !== 'undefined') {
      localStorage.setItem('auth_token', data.access_token)
    }
    
    return data
  },

  // دریافت اطلاعات کاربر فعلی
  async getCurrentUser() {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: getHeaders(),
    })

    return handleResponse(response)
  },

  // خروج
  async logout() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
    }
  },
}