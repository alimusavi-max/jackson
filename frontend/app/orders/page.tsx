// frontend/app/orders/page.tsx - نسخه اصلاح شده
'use client'

import React, { useEffect, useState } from 'react'
import { ordersAPI } from '@/lib/api'
import { CheckCircle2 } from 'lucide-react'

interface OrderItem {
  id: number
  product_title: string
  product_code: string
  quantity: number
  price: number
  product_image: string | null
}

interface Order {
  id: number
  order_code: string
  shipment_id: string
  customer_name: string
  customer_phone: string
  status: string
  city: string
  province: string
  full_address: string
  postal_code: string
  tracking_code: string | null
  order_date_persian: string
  created_at: string
  updated_at: string
  items_count: number
  total_quantity: number
  total_amount: number
  items: OrderItem[]
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [filteredOrders, setFilteredOrders] = useState<Order[]>([])
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [confirming, setConfirming] = useState(false)
  
  const [filters, setFilters] = useState({
    search: '',
    city: 'all',
    province: 'all',
    status: 'all',
    has_tracking: 'all',
    has_address: 'all',
    has_phone: 'all',
    multi_item_only: false
  })

  useEffect(() => {
    loadOrders()
  }, [])

  useEffect(() => {
    applyFilters()
  }, [filters, orders])

  const loadOrders = async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('🔄 درخواست سفارشات...')
      
      const res = await ordersAPI.getAll({ limit: 1000 })
      
      console.log('✅ پاسخ دریافت شد:', res)
      
      // بررسی فرمت پاسخ
      let ordersData: Order[] = []
      
      if (Array.isArray(res.data)) {
        ordersData = res.data
      } else if (res.data && Array.isArray(res.data.orders)) {
        ordersData = res.data.orders
      } else if (Array.isArray(res)) {
        ordersData = res
      } else {
        console.error('❌ فرمت پاسخ نامعتبر:', res)
        throw new Error('فرمت پاسخ سرور نامعتبر است')
      }
      
      console.log(`✅ ${ordersData.length} سفارش دریافت شد`)
      
      // اطمینان از وجود items
      const processedOrders = ordersData.map(order => ({
        ...order,
        items: order.items || [],
        items_count: order.items_count || (order.items ? order.items.length : 0),
        total_quantity: order.total_quantity || 0,
        total_amount: order.total_amount || 0
      }))
      
      setOrders(processedOrders)
      
    } catch (error: any) {
      console.error('❌ خطا در دریافت سفارشات:', error)
      
      let errorMessage = 'خطا در دریافت سفارشات'
      
      if (error.response) {
        errorMessage = `خطای سرور: ${error.response.status}`
        console.error('Response error:', error.response.data)
      } else if (error.request) {
        errorMessage = 'خطا در اتصال به سرور'
        console.error('Request error:', error.request)
      } else {
        errorMessage = error.message || 'خطای نامشخص'
      }
      
      setError(errorMessage)
      alert(`❌ ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async () => {
    if (!confirm('⚠️ آیا مطمئن هستید؟\n\nاین عملیات ممکن است چند دقیقه طول بکشد.')) {
      return
    }
    
    try {
      setSyncing(true)
      const response = await ordersAPI.sync(false)
      
      if (response.data.success) {
        alert(`✅ همگام‌سازی موفق!\n\n` +
          `📦 سفارشات جدید: ${response.data.new_orders}\n` +
          `🔄 به‌روزرسانی شده: ${response.data.updated_orders}\n` +
          `📊 مجموع: ${response.data.total}`)
        await loadOrders()
      } else {
        alert(`❌ خطا:\n\n${response.data.message}`)
      }
    } catch (error: any) {
      console.error('خطا:', error)
      alert(`❌ خطا:\n\n${error.response?.data?.message || error.message}`)
    } finally {
      setSyncing(false)
    }
  }

  const handleConfirmNewOrders = async () => {
    const newOrders = orders.filter(o => 
      o.status === 'سفارش جدید' || 
      o.status === 'new' || 
      o.status === 'New Order'
    )
    
    if (newOrders.length === 0) {
      alert('⚠️ هیچ سفارش جدیدی برای تایید وجود ندارد')
      return
    }
    
    if (!confirm(`⚠️ آیا مطمئن هستید؟\n\n${newOrders.length} سفارش جدید تایید خواهد شد.\nاین عملیات وضعیت سفارشات را در دیجی‌کالا تغییر می‌دهد.`)) {
      return
    }
    
    try {
      setConfirming(true)
      
      const response = await fetch('http://localhost:8000/api/orders/confirm-new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      
      const data = await response.json()
      
      if (data.success) {
        alert(`✅ تایید موفق!\n\n` +
          `✓ تایید شده: ${data.confirmed}\n` +
          `✗ ناموفق: ${data.failed}\n` +
          `📊 مجموع: ${data.total}`)
        await loadOrders()
      } else {
        alert(`❌ خطا:\n\n${data.message}`)
      }
    } catch (error: any) {
      console.error('خطا:', error)
      alert(`❌ خطا در تایید سفارشات:\n\n${error.message}`)
    } finally {
      setConfirming(false)
    }
  }

  const toggleRow = (orderId: number) => {
    const newExpanded = new Set(expandedRows)
    
    if (newExpanded.has(orderId)) {
      newExpanded.delete(orderId)
    } else {
      newExpanded.add(orderId)
    }
    
    setExpandedRows(newExpanded)
  }

  const applyFilters = () => {
    let result = [...orders]

    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      result = result.filter(order => 
        order.order_code?.toLowerCase().includes(searchLower) ||
        order.customer_name?.toLowerCase().includes(searchLower) ||
        order.tracking_code?.toLowerCase().includes(searchLower) ||
        order.customer_phone?.includes(filters.search) ||
        order.items?.some(item => item.product_title?.toLowerCase().includes(searchLower))
      )
    }

    if (filters.city !== 'all') {
      result = result.filter(order => order.city === filters.city)
    }

    if (filters.province !== 'all') {
      result = result.filter(order => order.province === filters.province)
    }

    if (filters.status !== 'all') {
      result = result.filter(order => order.status === filters.status)
    }

    if (filters.has_tracking === 'yes') {
      result = result.filter(order => order.tracking_code && order.tracking_code !== 'نامشخص')
    } else if (filters.has_tracking === 'no') {
      result = result.filter(order => !order.tracking_code || order.tracking_code === 'نامشخص')
    }

    if (filters.has_address === 'yes') {
      result = result.filter(order => order.full_address && order.full_address !== 'نامشخص')
    } else if (filters.has_address === 'no') {
      result = result.filter(order => !order.full_address || order.full_address === 'نامشخص')
    }

    if (filters.has_phone === 'yes') {
      result = result.filter(order => order.customer_phone && order.customer_phone !== 'نامشخص')
    } else if (filters.has_phone === 'no') {
      result = result.filter(order => !order.customer_phone || order.customer_phone === 'نامشخص')
    }

    if (filters.multi_item_only) {
      result = result.filter(order => order.items_count > 1)
    }

    setFilteredOrders(result)
  }

  const resetFilters = () => {
    setFilters({
      search: '',
      city: 'all',
      province: 'all',
      status: 'all',
      has_tracking: 'all',
      has_address: 'all',
      has_phone: 'all',
      multi_item_only: false
    })
  }

  const multiItemOrders = orders.filter(o => o.items_count > 1).length
  const totalItems = orders.reduce((sum, o) => sum + (o.total_quantity || 0), 0)
  const newOrdersCount = orders.filter(o => 
    o.status === 'سفارش جدید' || 
    o.status === 'new' || 
    o.status === 'New Order'
  ).length

  const cities = Array.from(new Set(orders.map(o => o.city).filter(Boolean))).sort()
  const provinces = Array.from(new Set(orders.map(o => o.province).filter(Boolean))).sort()
  const statuses = Array.from(new Set(orders.map(o => o.status).filter(Boolean))).sort()

  // نمایش خطا
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
        <div className="text-center max-w-md bg-white rounded-xl shadow-lg p-8">
          <div className="text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-red-600 mb-2">خطا در بارگذاری سفارشات</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={loadOrders}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              تلاش مجدد
            </button>
            <button
              onClick={() => window.location.href = '/'}
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
            >
              بازگشت به داشبورد
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">در حال بارگذاری سفارشات...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <a href="/" className="text-2xl hover:text-blue-600 transition">←</a>
                <h1 className="text-2xl font-bold text-gray-900">📋 مدیریت سفارشات</h1>
              </div>
              <div className="flex gap-4 mt-2 text-sm">
                <span className="text-gray-600">
                  <span className="font-bold text-blue-600">{filteredOrders.length}</span> سفارش 
                  {filteredOrders.length !== orders.length && (
                    <span className="text-gray-400"> از {orders.length}</span>
                  )}
                </span>
                <span className="text-gray-400">|</span>
                <span className="text-orange-600">
                  🎁 {multiItemOrders} سفارش چندقلمی
                </span>
                <span className="text-gray-400">|</span>
                <span className="text-purple-600">
                  📦 {totalItems} کالا
                </span>
                {newOrdersCount > 0 && (
                  <>
                    <span className="text-gray-400">|</span>
                    <span className="text-green-600">
                      🆕 {newOrdersCount} سفارش جدید
                    </span>
                  </>
                )}
              </div>
            </div>
            <div className="flex gap-3">
              <button 
                onClick={handleConfirmNewOrders}
                disabled={confirming || newOrdersCount === 0}
                className="px-5 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {confirming ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    در حال تایید...
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={20} />
                    تایید سفارشات جدید ({newOrdersCount})
                  </>
                )}
              </button>
              
              <button 
                onClick={handleSync}
                disabled={syncing}
                className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
              >
                {syncing ? '⏳ در حال همگام‌سازی...' : '🔄 همگام‌سازی'}
              </button>
              
              <button 
                onClick={resetFilters}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
              >
                ❌ پاک کردن فیلترها
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1800px] mx-auto px-6 py-6">
        {/* Filters */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            🔍 فیلترهای پیشرفته
            <span className="text-sm font-normal text-gray-500">
              ({filteredOrders.length} نتیجه)
            </span>
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">جستجو</label>
              <input
                type="text"
                placeholder="کد سفارش، نام مشتری، تلفن، محصول..."
                value={filters.search}
                onChange={(e) => setFilters({...filters, search: e.target.value})}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">استان</label>
              <select
                value={filters.province}
                onChange={(e) => setFilters({...filters, province: e.target.value})}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">همه استان‌ها ({provinces.length})</option>
                {provinces.map(province => (
                  <option key={province} value={province}>
                    {province} ({orders.filter(o => o.province === province).length})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">شهر</label>
              <select
                value={filters.city}
                onChange={(e) => setFilters({...filters, city: e.target.value})}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">همه شهرها ({cities.length})</option>
                {cities.map(city => (
                  <option key={city} value={city}>
                    {city} ({orders.filter(o => o.city === city).length})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">وضعیت</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({...filters, status: e.target.value})}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">همه وضعیت‌ها</option>
                {statuses.map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">کد رهگیری</label>
              <select
                value={filters.has_tracking}
                onChange={(e) => setFilters({...filters, has_tracking: e.target.value})}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">همه</option>
                <option value="yes">✓ دارای کد</option>
                <option value="no">✗ بدون کد</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">آدرس کامل</label>
              <select
                value={filters.has_address}
                onChange={(e) => setFilters({...filters, has_address: e.target.value})}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">همه</option>
                <option value="yes">✓ دارای آدرس</option>
                <option value="no">✗ بدون آدرس</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">شماره تلفن</label>
              <select
                value={filters.has_phone}
                onChange={(e) => setFilters({...filters, has_phone: e.target.value})}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">همه</option>
                <option value="yes">✓ دارای تلفن</option>
                <option value="no">✗ بدون تلفن</option>
              </select>
            </div>

            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.multi_item_only}
                  onChange={(e) => setFilters({...filters, multi_item_only: e.target.checked})}
                  className="w-5 h-5 text-orange-600 rounded focus:ring-2 focus:ring-orange-500"
                />
                <span className="text-sm font-medium text-orange-700">
                  🎁 فقط سفارشات چندقلمی ({multiItemOrders})
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Orders Table - ادامه در قسمت بعد... */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          {filteredOrders.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <p className="text-6xl mb-4">📦</p>
              <p className="text-xl">هیچ سفارشی با این فیلترها یافت نشد</p>
              <button 
                onClick={resetFilters}
                className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
              >
                پاک کردن فیلترها →
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b-2 border-blue-200">
                  <tr>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700 w-10"></th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">ردیف</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">کد سفارش</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">نام مشتری</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">شهر</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">وضعیت</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">کد رهگیری</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">محصولات</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">تعداد کل</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">تاریخ</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOrders.map((order, index) => {
                    const isExpanded = expandedRows.has(order.id)
                    const orderItems = order.items || []
                    const hasMultipleItems = orderItems.length > 1
                    const isNewOrder = order.status === 'سفارش جدید' || order.status === 'new' || order.status === 'New Order'
                    
                    return (
                      <React.Fragment key={order.id}>
                        <tr className={`border-b hover:bg-blue-50 transition cursor-pointer ${hasMultipleItems ? 'bg-yellow-50' : ''} ${isNewOrder ? 'bg-green-50' : ''}`} onClick={() => toggleRow(order.id)}>
                          <td className="px-4 py-3">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                toggleRow(order.id)
                              }}
                              className="text-gray-600 hover:text-blue-600 transition"
                            >
                              {isExpanded ? '▼' : '◀'}
                            </button>
                          </td>
                          <td className="px-4 py-3 text-gray-600 font-medium">
                            {index + 1}
                          </td>
                          <td className="px-4 py-3">
                            <div className="font-mono text-xs font-bold text-blue-600">
                              {order.order_code}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="font-medium text-gray-900">
                              {order.customer_name || <span className="text-red-500">نامشخص</span>}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-gray-700">
                            {order.city || '-'}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                              isNewOrder 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-blue-100 text-blue-800'
                            }`}>
                              {order.status || 'نامشخص'}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            {order.tracking_code && order.tracking_code !== 'نامشخص' ? (
                              <span className="px-2 py-1 text-xs font-mono bg-green-100 text-green-800 rounded block text-center">
                                {order.tracking_code}
                              </span>
                            ) : (
                              <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded block text-center">
                                بدون کد
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <div className="flex items-center justify-center gap-1">
                              <span className="inline-block px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-bold">
                                {order.items_count} قلم
                              </span>
                              {hasMultipleItems && (
                                <span className="text-orange-600 text-lg" title="سفارش چندقلمی">🎁</span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-bold">
                              {order.total_quantity || order.items_count} عدد
                            </span>
                          </td>
                          <td className="px-4 py-3 text-xs text-gray-600">
                            {order.order_date_persian || '-'}
                          </td>
                        </tr>

                        {isExpanded && (
                          <tr className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b-2">
                            <td colSpan={10} className="px-4 py-4">
                              {orderItems.length > 0 ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                  <div className="space-y-3">
                                    <h4 className="font-bold text-gray-900 flex items-center gap-2 mb-3">
                                      📞 اطلاعات تماس و آدرس
                                    </h4>
                                    
                                    <div className="bg-white p-3 rounded-lg shadow-sm">
                                      <div className="text-xs text-gray-500 mb-1">استان</div>
                                      <div className="font-medium text-gray-900">{order.province || 'نامشخص'}</div>
                                    </div>

                                    <div className="bg-white p-3 rounded-lg shadow-sm">
                                      <div className="text-xs text-gray-500 mb-1">شماره تلفن</div>
                                      <div className="font-mono text-gray-900" dir="ltr">{order.customer_phone || 'نامشخص'}</div>
                                    </div>

                                    <div className="bg-white p-3 rounded-lg shadow-sm">
                                      <div className="text-xs text-gray-500 mb-1">کد پستی</div>
                                      <div className="font-mono text-gray-900">{order.postal_code || 'نامشخص'}</div>
                                    </div>

                                    <div className="bg-white p-3 rounded-lg shadow-sm">
                                      <div className="text-xs text-gray-500 mb-1">آدرس کامل</div>
                                      <div className="text-gray-900 leading-relaxed">{order.full_address || 'نامشخص'}</div>
                                    </div>
                                  </div>

                                  <div>
                                    <h4 className="font-bold text-gray-900 flex items-center gap-2 mb-3">
                                      🛒 محصولات سفارش ({orderItems.length} قلم)
                                      {hasMultipleItems && (
                                        <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded-full">
                                          چندقلمی
                                        </span>
                                      )}
                                    </h4>
                                    
                                    <div className="space-y-2 max-h-80 overflow-y-auto">
                                      {orderItems.map((item, idx) => (
                                        <div key={item.id} className="bg-white p-3 rounded-lg shadow-sm flex items-start gap-3">
                                          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold text-sm flex-shrink-0">
                                            {idx + 1}
                                          </div>
                                          <div className="flex-1 min-w-0">
                                            <div className="font-medium text-gray-900 text-sm leading-tight mb-1">
                                              {item.product_title}
                                            </div>
                                            <div className="flex items-center gap-4 text-xs text-gray-600 flex-wrap">
                                              <span className="font-mono">کد: {item.product_code}</span>
                                              <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded font-bold">
                                                {item.quantity} عدد
                                              </span>
                                              <span className="font-bold text-green-700">
                                                {item.price.toLocaleString('fa-IR')} تومان
                                              </span>
                                              <span className="text-gray-500">
                                                = {(item.price * item.quantity).toLocaleString('fa-IR')} تومان
                                              </span>
                                            </div>
                                          </div>
                                        </div>
                                      ))}
                                    </div>

                                    <div className="mt-3 bg-gradient-to-r from-green-100 to-emerald-100 p-4 rounded-lg">
                                      <div className="grid grid-cols-2 gap-4 text-sm mb-2">
                                        <div>
                                          <span className="text-gray-700">تعداد اقلام:</span>
                                          <span className="font-bold text-purple-700 mr-2">{orderItems.length} قلم</span>
                                        </div>
                                        <div>
                                          <span className="text-gray-700">تعداد کل:</span>
                                          <span className="font-bold text-blue-700 mr-2">{order.total_quantity} عدد</span>
                                        </div>
                                      </div>
                                      <div className="flex items-center justify-between border-t border-green-200 pt-2">
                                        <span className="font-bold text-gray-700">مجموع سفارش:</span>
                                        <span className="text-2xl font-bold text-green-700">
                                          {order.total_amount.toLocaleString('fa-IR')} تومان
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              ) : (
                                <div className="text-center py-4 text-red-500">
                                  خطا در بارگذاری جزئیات
                                </div>
                              )}
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}