'use client'

import { useState, useEffect } from 'react'
import { ordersAPI } from '@/lib/api'

interface Order {
  id: number
  order_code: string
  shipment_id: string
  customer_name: string
  city: string
  province: string
  full_address: string
  postal_code: string
  customer_phone: string
  tracking_code: string | null
  items_count: number
}

export default function LabelsPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [selectedOrders, setSelectedOrders] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    loadOrders()
  }, [])

  const loadOrders = async () => {
    try {
      setLoading(true)
      // فقط سفارشاتی که آدرس کامل دارند
      const res = await ordersAPI.getAll({ limit: 1000 })
      const ordersWithAddress = res.data.filter((o: Order) => 
        o.full_address && 
        o.full_address !== 'نامشخص' && 
        o.customer_name &&
        o.city
      )
      setOrders(ordersWithAddress)
    } catch (error) {
      console.error('خطا:', error)
      alert('خطا در دریافت سفارشات')
    } finally {
      setLoading(false)
    }
  }

  const toggleOrder = (orderId: number) => {
    const newSelected = new Set(selectedOrders)
    if (newSelected.has(orderId)) {
      newSelected.delete(orderId)
    } else {
      newSelected.add(orderId)
    }
    setSelectedOrders(newSelected)
  }

  const toggleAll = () => {
    if (selectedOrders.size === orders.length) {
      setSelectedOrders(new Set())
    } else {
      setSelectedOrders(new Set(orders.map(o => o.id)))
    }
  }

  const generateLabels = async () => {
    if (selectedOrders.size === 0) {
      alert('⚠️ لطفاً حداقل یک سفارش انتخاب کنید')
      return
    }

    setGenerating(true)
    try {
      // TODO: اینجا API برای تولید PDF برچسب‌ها صدا زده میشه
      alert(`🎉 در حال تولید ${selectedOrders.size} برچسب...\n\nاین قابلیت به زودی اضافه می‌شود!`)
    } catch (error) {
      console.error('خطا:', error)
      alert('خطا در تولید برچسب‌ها')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">در حال بارگذاری...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <a href="/" className="text-2xl hover:text-blue-600 transition">←</a>
                <h1 className="text-2xl font-bold text-gray-900">🏷️ تولید برچسب پستی</h1>
              </div>
              <p className="text-gray-600 mt-1">
                <span className="font-bold text-blue-600">{selectedOrders.size}</span> از{' '}
                <span className="font-bold">{orders.length}</span> سفارش انتخاب شده
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={generateLabels}
                disabled={selectedOrders.size === 0 || generating}
                className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:bg-gray-300 disabled:cursor-not-allowed font-medium"
              >
                {generating ? '⏳ در حال تولید...' : `📄 تولید ${selectedOrders.size} برچسب`}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Controls */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-gray-900 mb-2">⚙️ تنظیمات</h3>
              <p className="text-sm text-gray-600">
                سفارشاتی که آدرس کامل دارند در لیست نمایش داده می‌شوند
              </p>
            </div>
            <button
              onClick={toggleAll}
              className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition font-medium"
            >
              {selectedOrders.size === orders.length ? '❌ لغو انتخاب همه' : '✅ انتخاب همه'}
            </button>
          </div>
        </div>

        {/* Orders List */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          {orders.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <p className="text-6xl mb-4">📦</p>
              <p className="text-xl">هیچ سفارشی با آدرس کامل یافت نشد</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b-2 border-blue-200">
                  <tr>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700 w-10">
                      <input
                        type="checkbox"
                        checked={selectedOrders.size === orders.length && orders.length > 0}
                        onChange={toggleAll}
                        className="w-4 h-4"
                      />
                    </th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">ردیف</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">کد سفارش</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">نام مشتری</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">شهر</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">آدرس</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">کد پستی</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">تعداد کالا</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order, index) => (
                    <tr
                      key={order.id}
                      className={`border-b hover:bg-blue-50 transition cursor-pointer ${
                        selectedOrders.has(order.id) ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => toggleOrder(order.id)}
                    >
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedOrders.has(order.id)}
                          onChange={() => toggleOrder(order.id)}
                          className="w-4 h-4"
                          onClick={(e) => e.stopPropagation()}
                        />
                      </td>
                      <td className="px-4 py-3 text-gray-600 font-medium">{index + 1}</td>
                      <td className="px-4 py-3">
                        <div className="font-mono text-xs font-bold text-blue-600">
                          {order.order_code}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">{order.customer_name}</div>
                        {order.customer_phone && (
                          <div className="text-xs text-gray-500 font-mono">{order.customer_phone}</div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        <div>{order.city}</div>
                        <div className="text-xs text-gray-500">{order.province}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-600 text-xs max-w-xs truncate">
                        {order.full_address}
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                          {order.postal_code || '-'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="inline-block px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-bold">
                          {order.items_count} عدد
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}