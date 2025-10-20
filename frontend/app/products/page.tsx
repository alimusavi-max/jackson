// frontend/app/warehouse/products/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import { 
  Package, Plus, Search, Filter, AlertTriangle, 
  Edit, Trash2, ShoppingCart, DollarSign, Layers
} from 'lucide-react'

interface MarketplaceSKU {
  id: number
  marketplace_id: number
  marketplace_name: string
  marketplace_code: string
  marketplace_sku: string
  marketplace_url: string | null
  price_in_marketplace: number | null
  is_active: boolean
}

interface Product {
  id: number
  sku: string
  title: string
  description: string | null
  category_name: string | null
  brand: string | null
  stock_quantity: number
  available_quantity: number
  reserved_quantity: number
  min_stock_alert: number
  cost_price: number
  sell_price: number
  warehouse_id: number
  warehouse_name: string
  is_active: boolean
  is_low_stock: boolean
  needs_reorder: boolean
  marketplace_skus: MarketplaceSKU[]
}

interface Warehouse {
  id: number
  name: string
}

export default function ProductsPage() {
  const { user } = useAuth()
  const [products, setProducts] = useState<Product[]>([])
  const [warehouses, setWarehouses] = useState<Warehouse[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedWarehouse, setSelectedWarehouse] = useState<number | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [showLowStockOnly, setShowLowStockOnly] = useState(false)
  const [expandedProduct, setExpandedProduct] = useState<number | null>(null)

  useEffect(() => {
    loadData()
  }, [selectedWarehouse, showLowStockOnly, searchTerm])

  const loadData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      
      // دریافت انبارها
      const whResponse = await fetch('http://localhost:8000/api/warehouse/warehouses', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (whResponse.ok) {
        setWarehouses(await whResponse.json())
      }

      // دریافت محصولات
      const params = new URLSearchParams()
      if (selectedWarehouse) params.append('warehouse_id', selectedWarehouse.toString())
      if (showLowStockOnly) params.append('low_stock_only', 'true')
      if (searchTerm) params.append('search', searchTerm)
      params.append('limit', '100')

      const productsResponse = await fetch(
        `http://localhost:8000/api/warehouse/products?${params}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )
      
      if (productsResponse.ok) {
        setProducts(await productsResponse.json())
      }
    } catch (error) {
      console.error('خطا:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (productId: number) => {
    if (!confirm('آیا مطمئن هستید؟')) return

    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch(
        `http://localhost:8000/api/warehouse/products/${productId}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      if (response.ok) {
        alert('✅ محصول حذف شد')
        loadData()
      }
    } catch (error) {
      alert('❌ خطا در حذف محصول')
    }
  }

  const lowStockCount = products.filter(p => p.is_low_stock).length
  const totalValue = products.reduce((sum, p) => sum + (p.stock_quantity * p.cost_price), 0)

  return (
    <ProtectedRoute requiredPermission="warehouse_view">
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
        {/* Header */}
        <header className="bg-white shadow-sm border-b sticky top-0 z-10">
          <div className="max-w-[1800px] mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <a href="/warehouse/inventory" className="text-2xl hover:text-blue-600 transition">←</a>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <Package className="text-blue-600" />
                    مدیریت محصولات
                  </h1>
                  <p className="text-gray-600 mt-1">
                    {products.length} محصول | {lowStockCount} موجودی کم
                  </p>
                </div>
              </div>

              {user?.permissions.includes('warehouse_create') && (
                <a
                  href="/warehouse/products/new"
                  className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
                >
                  <Plus size={20} />
                  محصول جدید
                </a>
              )}
            </div>
          </div>
        </header>

        <main className="max-w-[1800px] mx-auto px-6 py-8">
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl shadow-lg p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <Package size={32} />
              </div>
              <h3 className="text-3xl font-bold mb-1">{products.length}</h3>
              <p className="text-sm opacity-90">کل محصولات</p>
            </div>

            <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl shadow-lg p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <AlertTriangle size={32} />
              </div>
              <h3 className="text-3xl font-bold mb-1">{lowStockCount}</h3>
              <p className="text-sm opacity-90">موجودی کم</p>
            </div>

            <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl shadow-lg p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <Layers size={32} />
              </div>
              <h3 className="text-3xl font-bold mb-1">
                {products.reduce((sum, p) => sum + p.stock_quantity, 0)}
              </h3>
              <p className="text-sm opacity-90">مجموع موجودی</p>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl shadow-lg p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <DollarSign size={32} />
              </div>
              <h3 className="text-3xl font-bold mb-1">
                {(totalValue / 1000000).toFixed(1)}M
              </h3>
              <p className="text-sm opacity-90">ارزش انبار</p>
            </div>
          </div>

          {/* Filters */}
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div className="md:col-span-2">
                <div className="relative">
                  <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                  <input
                    type="text"
                    placeholder="جستجو (SKU، نام، بارکد...)"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pr-10 pl-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Warehouse Filter */}
              <div>
                <select
                  value={selectedWarehouse || ''}
                  onChange={(e) => setSelectedWarehouse(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">همه انبارها</option>
                  {warehouses.map(wh => (
                    <option key={wh.id} value={wh.id}>{wh.name}</option>
                  ))}
                </select>
              </div>

              {/* Low Stock Filter */}
              <div className="flex items-center">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showLowStockOnly}
                    onChange={(e) => setShowLowStockOnly(e.target.checked)}
                    className="w-5 h-5 text-orange-600 rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    فقط موجودی کم
                  </span>
                </label>
              </div>
            </div>
          </div>

          {/* Products Table */}
          <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto"></div>
              </div>
            ) : products.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <Package size={64} className="mx-auto mb-4 text-gray-300" />
                <p className="text-xl">محصولی یافت نشد</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b-2 border-blue-200">
                    <tr>
                      <th className="px-4 py-3 text-right w-10"></th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">SKU</th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">نام محصول</th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">انبار</th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">موجودی</th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">قابل فروش</th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">قیمت خرید</th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">قیمت فروش</th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">پلتفرم‌ها</th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">وضعیت</th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">عملیات</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.map((product) => (
                      <>
                        <tr
                          key={product.id}
                          className={`border-b hover:bg-blue-50 transition cursor-pointer ${
                            product.is_low_stock ? 'bg-orange-50' : ''
                          }`}
                          onClick={() => setExpandedProduct(
                            expandedProduct === product.id ? null : product.id
                          )}
                        >
                          <td className="px-4 py-3">
                            <button className="text-gray-600 hover:text-blue-600">
                              {expandedProduct === product.id ? '▼' : '◀'}
                            </button>
                          </td>
                          <td className="px-4 py-3">
                            <span className="font-mono text-xs font-bold text-blue-600">
                              {product.sku}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="font-medium text-gray-900">{product.title}</div>
                            {product.brand && (
                              <div className="text-xs text-gray-500">{product.brand}</div>
                            )}
                          </td>
                          <td className="px-4 py-3 text-gray-700">
                            {product.warehouse_name}
                          </td>
                          <td className="px-4 py-3">
                            <span className="font-bold text-gray-900">
                              {product.stock_quantity}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`font-bold ${
                              product.is_low_stock ? 'text-orange-600' : 'text-green-600'
                            }`}>
                              {product.available_quantity}
                            </span>
                            {product.reserved_quantity > 0 && (
                              <span className="text-xs text-gray-500 mr-1">
                                ({product.reserved_quantity} رزرو)
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-gray-700">
                            {product.cost_price.toLocaleString('fa-IR')} ت
                          </td>
                          <td className="px-4 py-3 font-bold text-green-700">
                            {product.sell_price.toLocaleString('fa-IR')} ت
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex gap-1">
                              {product.marketplace_skus.slice(0, 3).map((mp) => (
                                <span
                                  key={mp.id}
                                  className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium"
                                  title={mp.marketplace_name}
                                >
                                  {mp.marketplace_code}
                                </span>
                              ))}
                              {product.marketplace_skus.length > 3 && (
                                <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                  +{product.marketplace_skus.length - 3}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            {product.is_low_stock ? (
                              <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-xs flex items-center gap-1 w-fit">
                                <AlertTriangle size={12} />
                                موجودی کم
                              </span>
                            ) : (
                              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs w-fit">
                                ✓ موجود
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <a
                                href={`/warehouse/products/${product.id}/edit`}
                                className="p-2 text-blue-600 hover:bg-blue-50 rounded transition"
                                title="ویرایش"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <Edit size={16} />
                              </a>
                              
                              {user?.permissions.includes('warehouse_delete') && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleDelete(product.id)
                                  }}
                                  className="p-2 text-red-600 hover:bg-red-50 rounded transition"
                                  title="حذف"
                                >
                                  <Trash2 size={16} />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>

                        {/* Expanded Details */}
                        {expandedProduct === product.id && (
                          <tr className="bg-gradient-to-r from-blue-50 to-indigo-50">
                            <td colSpan={11} className="px-4 py-6">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Basic Info */}
                                <div>
                                  <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                                    📦 اطلاعات پایه
                                  </h4>
                                  <div className="space-y-2 bg-white p-4 rounded-lg">
                                    {product.description && (
                                      <div>
                                        <span className="text-xs text-gray-500">توضیحات:</span>
                                        <p className="text-sm text-gray-700 mt-1">{product.description}</p>
                                      </div>
                                    )}
                                    {product.category_name && (
                                      <div>
                                        <span className="text-xs text-gray-500">دسته‌بندی:</span>
                                        <p className="text-sm font-medium text-gray-900">{product.category_name}</p>
                                      </div>
                                    )}
                                    <div className="grid grid-cols-2 gap-3 pt-2">
                                      <div>
                                        <span className="text-xs text-gray-500">حد هشدار:</span>
                                        <p className="text-sm font-medium text-orange-600">
                                          {product.min_stock_alert}
                                        </p>
                                      </div>
                                      <div>
                                        <span className="text-xs text-gray-500">نقطه سفارش:</span>
                                        <p className="text-sm font-medium text-blue-600">
                                          {product.min_stock_alert}
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                </div>

                                {/* Marketplace SKUs */}
                                <div>
                                  <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                                    🌐 SKU در پلتفرم‌ها ({product.marketplace_skus.length})
                                  </h4>
                                  {product.marketplace_skus.length === 0 ? (
                                    <div className="bg-white p-4 rounded-lg text-center text-gray-500 text-sm">
                                      هیچ پلتفرمی ثبت نشده
                                    </div>
                                  ) : (
                                    <div className="space-y-2">
                                      {product.marketplace_skus.map((mp) => (
                                        <div
                                          key={mp.id}
                                          className="bg-white p-3 rounded-lg shadow-sm"
                                        >
                                          <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-bold">
                                                {mp.marketplace_code}
                                              </span>
                                              <span className="font-medium text-gray-900 text-sm">
                                                {mp.marketplace_name}
                                              </span>
                                            </div>
                                            {mp.is_active ? (
                                              <span className="text-green-600 text-xs">✓ فعال</span>
                                            ) : (
                                              <span className="text-gray-400 text-xs">✗ غیرفعال</span>
                                            )}
                                          </div>
                                          <div className="grid grid-cols-2 gap-2 text-xs">
                                            <div>
                                              <span className="text-gray-500">SKU:</span>
                                              <p className="font-mono font-bold text-gray-900 mt-0.5">
                                                {mp.marketplace_sku}
                                              </p>
                                            </div>
                                            {mp.price_in_marketplace && (
                                              <div>
                                                <span className="text-gray-500">قیمت:</span>
                                                <p className="font-bold text-green-600 mt-0.5">
                                                  {mp.price_in_marketplace.toLocaleString('fa-IR')} ت
                                                </p>
                                              </div>
                                            )}
                                          </div>
                                          {mp.marketplace_url && (
                                            <a
                                              href={mp.marketplace_url}
                                              target="_blank"
                                              rel="noopener noreferrer"
                                              className="text-blue-600 hover:text-blue-700 text-xs mt-2 inline-block"
                                            >
                                              🔗 مشاهده در {mp.marketplace_name}
                                            </a>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>

                              {/* Actions */}
                              <div className="mt-4 flex gap-3">
                                <a
                                  href={`/warehouse/products/${product.id}/edit`}
                                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm"
                                >
                                  ویرایش جزئیات
                                </a>
                                <button
                                  onClick={() => {/* TODO: Add transaction modal */}}
                                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm"
                                >
                                  افزودن تراکنش
                                </button>
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}