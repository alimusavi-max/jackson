// frontend/app/warehouse/inventory/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import Sidebar from '@/components/Sidebar'
import { Package, AlertTriangle, TrendingUp, DollarSign, Plus } from 'lucide-react'

interface Product {
  id: number
  sku: string
  title: string
  stock_quantity: number
  available_quantity: number
  min_stock_alert: number
  cost_price: number
  sell_price: number
  is_low_stock: boolean
}

interface Stats {
  total_products: number
  low_stock_items: number
  total_inventory_value: number
  today_transactions: number
}

export default function WarehouseInventoryPage() {
  const { user } = useAuth()
  const [products, setProducts] = useState<Product[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'low_stock'>('all')

  useEffect(() => {
    loadData()
  }, [filter])

  const loadData = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      
      // دریافت محصولات
      const productsRes = await fetch(
        `http://localhost:8000/api/warehouse/products?low_stock_only=${filter === 'low_stock'}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )
      if (productsRes.ok) {
        setProducts(await productsRes.json())
      }

      // دریافت آمار
      const statsRes = await fetch('http://localhost:8000/api/warehouse/stats', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (statsRes.ok) {
        setStats(await statsRes.json())
      }
    } catch (error) {
      console.error('خطا در دریافت داده‌ها:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <ProtectedRoute requiredPermission="warehouse_view">
      <div className="flex h-screen bg-gray-50" dir="rtl">
        <Sidebar />
        
        <main className="flex-1 overflow-y-auto">
          {/* Header */}
          <header className="bg-white shadow-sm border-b sticky top-0 z-10">
            <div className="px-8 py-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <Package className="text-blue-600" />
                    موجودی انبار
                  </h1>
                  <p className="text-gray-600 mt-2">
                    مدیریت موجودی و کالاهای انبار
                  </p>
                </div>

                {user?.permissions.includes('warehouse_create') && (
                  <button className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2">
                    <Plus size={20} />
                    محصول جدید
                  </button>
                )}
              </div>
            </div>
          </header>

          <div className="p-8">
            {/* Stats Cards */}
            {stats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <StatCard
                  title="کل محصولات"
                  value={stats.total_products}
                  icon={Package}
                  color="blue"
                />
                <StatCard
                  title="موجودی کم"
                  value={stats.low_stock_items}
                  icon={AlertTriangle}
                  color="orange"
                />
                <StatCard
                  title="ارزش انبار"
                  value={`${(stats.total_inventory_value / 1000000).toFixed(1)}M`}
                  icon={DollarSign}
                  color="green"
                />
                <StatCard
                  title="تراکنش امروز"
                  value={stats.today_transactions}
                  icon={TrendingUp}
                  color="purple"
                />
              </div>
            )}

            {/* Filters */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-4 py-2 rounded-lg transition ${
                    filter === 'all'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  همه محصولات ({stats?.total_products || 0})
                </button>
                <button
                  onClick={() => setFilter('low_stock')}
                  className={`px-4 py-2 rounded-lg transition flex items-center gap-2 ${
                    filter === 'low_stock'
                      ? 'bg-orange-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <AlertTriangle size={16} />
                  موجودی کم ({stats?.low_stock_items || 0})
                </button>
              </div>
            </div>

            {/* Products Table */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="p-6 border-b">
                <h2 className="text-xl font-bold text-gray-900">لیست محصولات</h2>
              </div>

              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto"></div>
                </div>
              ) : products.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Package size={48} className="mx-auto mb-4 opacity-50" />
                  <p className="text-lg">محصولی یافت نشد</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          SKU
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          نام محصول
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          موجودی کل
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          موجودی قابل فروش
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          قیمت خرید
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          قیمت فروش
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          وضعیت
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          عملیات
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {products.map((product) => (
                        <tr key={product.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4">
                            <span className="font-mono text-sm font-medium text-gray-900">
                              {product.sku}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="font-medium text-gray-900">
                              {product.title}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-gray-900 font-medium">
                              {product.stock_quantity}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`font-medium ${
                              product.is_low_stock ? 'text-orange-600' : 'text-green-600'
                            }`}>
                              {product.available_quantity}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600">
                            {product.cost_price.toLocaleString('fa-IR')} ت
                          </td>
                          <td className="px-6 py-4 text-sm font-medium text-gray-900">
                            {product.sell_price.toLocaleString('fa-IR')} ت
                          </td>
                          <td className="px-6 py-4">
                            {product.is_low_stock ? (
                              <span className="px-3 py-1 bg-orange-100 text-orange-800 text-xs rounded-full flex items-center gap-1 w-fit">
                                <AlertTriangle size={14} />
                                موجودی کم
                              </span>
                            ) : (
                              <span className="px-3 py-1 bg-green-100 text-green-800 text-xs rounded-full w-fit">
                                ✓ موجود
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                              جزئیات
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}

function StatCard({ title, value, icon: Icon, color }: any) {
  const colors = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600',
    purple: 'from-purple-500 to-purple-600',
  }

  return (
    <div className={`bg-gradient-to-br ${colors[color as keyof typeof colors]} rounded-2xl shadow-lg p-6 text-white`}>
      <div className="flex items-center justify-between mb-4">
        <Icon size={32} className="opacity-80" />
      </div>
      <h3 className="text-3xl font-bold mb-1">{typeof value === 'number' ? value.toLocaleString('fa-IR') : value}</h3>
      <p className="text-sm opacity-90">{title}</p>
    </div>
  )
}