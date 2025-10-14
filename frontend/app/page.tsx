'use client'

import { useEffect, useState } from 'react'
import { ordersAPI } from '@/lib/api'

interface Stats {
  total_orders: number
  orders_with_tracking: number
  orders_without_tracking: number
  total_sales: number
}

interface Order {
  id: number
  order_code: string
  customer_name: string
  status: string
  tracking_code: string | null
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [recentOrders, setRecentOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  // دریافت داده‌ها
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      
      // دریافت آمار
      const statsRes = await ordersAPI.getStats()
      setStats(statsRes.data)
      
      // دریافت آخرین سفارشات
      const ordersRes = await ordersAPI.getAll({ limit: 5 })
      setRecentOrders(ordersRes.data)
    } catch (error) {
      console.error('خطا در دریافت داده‌ها:', error)
    } finally {
      setLoading(false)
    }
  }

  // همگام‌سازی با API دیجی‌کالا
  const handleSync = async () => {
    if (!confirm('⚠️ آیا مطمئن هستید؟\n\nاین عملیات ممکن است چند دقیقه طول بکشد و سفارشات جدید را از دیجی‌کالا دریافت می‌کند.')) {
      return
    }
    
    try {
      setSyncing(true)
      const response = await ordersAPI.sync(false)
      
      if (response.data.success) {
        alert(`✅ همگام‌سازی موفق!\n\n` +
          `📦 سفارشات جدید: ${response.data.new_orders}\n` +
          `🔄 به‌روزرسانی شده: ${response.data.updated_orders}\n` +
          `📊 مجموع: ${response.data.total}\n\n` +
          `در حال بارگذاری مجدد...`)
        await loadData()
      } else {
        alert(`❌ خطا در همگام‌سازی:\n\n${response.data.message}`)
      }
    } catch (error: any) {
      console.error('خطا:', error)
      alert(`❌ خطا در ارتباط با سرور:\n\n${error.response?.data?.message || error.message}`)
    } finally {
      setSyncing(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">در حال بارگذاری...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50" dir="rtl">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">🛍️ سیستم مدیریت دیجی‌کالا</h1>
              <p className="text-gray-600 mt-1">
                داشبورد مدیریت سفارشات - آخرین به‌روزرسانی: {new Date().toLocaleTimeString('fa-IR')}
              </p>
            </div>
            <div className="flex gap-3">
              <button 
                onClick={handleSync}
                disabled={syncing}
                className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <span className={syncing ? 'animate-spin' : ''}>🔄</span>
                {syncing ? 'در حال همگام‌سازی...' : 'همگام‌سازی با API'}
              </button>
              <a 
                href="/orders"
                className="px-5 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
              >
                📋 سفارشات
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* کل سفارشات */}
          <div className="bg-white rounded-2xl shadow-lg p-6 border-r-4 border-blue-500 hover:shadow-xl transition transform hover:-translate-y-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm font-medium">کل سفارشات</p>
                <h3 className="text-4xl font-bold text-gray-900 mt-2">
                  {stats?.total_orders.toLocaleString('fa-IR') || '0'}
                </h3>
                <p className="text-blue-600 text-sm mt-2">📦 تمام سفارشات</p>
              </div>
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center text-3xl">
                📦
              </div>
            </div>
          </div>

          {/* دارای کد رهگیری */}
          <div className="bg-white rounded-2xl shadow-lg p-6 border-r-4 border-green-500 hover:shadow-xl transition transform hover:-translate-y-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm font-medium">دارای کد رهگیری</p>
                <h3 className="text-4xl font-bold text-gray-900 mt-2">
                  {stats?.orders_with_tracking.toLocaleString('fa-IR') || '0'}
                </h3>
                <p className="text-gray-600 text-sm mt-2">
                  {stats ? Math.round((stats.orders_with_tracking / stats.total_orders) * 100) : 0}% از کل
                </p>
              </div>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center text-3xl">
                ✅
              </div>
            </div>
          </div>

          {/* بدون کد رهگیری */}
          <div className="bg-white rounded-2xl shadow-lg p-6 border-r-4 border-orange-500 hover:shadow-xl transition transform hover:-translate-y-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm font-medium">نیاز به رهگیری</p>
                <h3 className="text-4xl font-bold text-gray-900 mt-2">
                  {stats?.orders_without_tracking.toLocaleString('fa-IR') || '0'}
                </h3>
                <p className="text-orange-600 text-sm mt-2">⚠ نیاز به اقدام</p>
              </div>
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center text-3xl">
                ⏳
              </div>
            </div>
          </div>

          {/* مجموع فروش */}
          <div className="bg-white rounded-2xl shadow-lg p-6 border-r-4 border-purple-500 hover:shadow-xl transition transform hover:-translate-y-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm font-medium">مجموع فروش</p>
                <h3 className="text-3xl font-bold text-gray-900 mt-2">
                  {stats ? (stats.total_sales / 1000000).toFixed(1) : '0'} M
                </h3>
                <p className="text-purple-600 text-sm mt-2">
                  {stats?.total_sales.toLocaleString('fa-IR')} تومان
                </p>
              </div>
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center text-3xl">
                💰
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">⚡ دسترسی سریع</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <a href="/orders" className="p-4 border-2 border-blue-200 rounded-xl hover:bg-blue-50 hover:border-blue-400 transition text-center block">
              <div className="text-3xl mb-2">📋</div>
              <div className="font-medium text-gray-700">سفارشات</div>
            </a>
            <button className="p-4 border-2 border-green-200 rounded-xl hover:bg-green-50 hover:border-green-400 transition text-center">
              <div className="text-3xl mb-2">🏷️</div>
              <div className="font-medium text-gray-700">برچسب پستی</div>
            </button>
            <a href="/sms" className="p-4 border-2 border-purple-200 rounded-xl hover:bg-purple-50 hover:border-purple-400 transition text-center block">
              <div className="text-3xl mb-2">📱</div>
              <div className="font-medium text-gray-700">ارسال پیامک</div>
            </a>
            <button className="p-4 border-2 border-orange-200 rounded-xl hover:bg-orange-50 hover:border-orange-400 transition text-center">
              <div className="text-3xl mb-2">📊</div>
              <div className="font-medium text-gray-700">گزارشات</div>
            </button>
          </div>
        </div>

        {/* Recent Orders */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">📦 آخرین سفارشات</h2>
            <a href="/orders" className="text-blue-600 hover:text-blue-700 text-sm font-medium">
              مشاهده همه ←
            </a>
          </div>
          
          {recentOrders.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <p>هیچ سفارشی یافت نشد</p>
              <button 
                onClick={handleSync}
                className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
              >
                همگام‌سازی با دیجی‌کالا →
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {recentOrders.map((order, i) => (
                <div key={order.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
                      #{i + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">سفارش {order.order_code}</p>
                      <p className="text-sm text-gray-500">مشتری: {order.customer_name || 'نامشخص'}</p>
                    </div>
                  </div>
                  <div className="text-left">
                    {order.tracking_code ? (
                      <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                        ✓ {order.status || 'ارسال شده'}
                      </span>
                    ) : (
                      <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-medium">
                        ⏳ {order.status || 'در انتظار'}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}