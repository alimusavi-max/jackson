// frontend/app/warehouse/inventory/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import Sidebar from '@/components/Sidebar'
import { 
  Package, 
  Search, 
  Plus, 
  Edit, 
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Filter
} from 'lucide-react'

interface Product {
  id: number
  sku: string
  dkp_code: string
  title: string
  category: string
  stock_quantity: number
  reserved_quantity: number
  available_quantity: number
  min_stock_alert: number
  cost_price: number
  sell_price: number
  warehouse_name: string
  is_low_stock: boolean
}

export default function InventoryPage() {
  const { user } = useAuth()
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    search: '',
    category: 'all',
    stock_status: 'all'
  })

  useEffect(() => {
    loadProducts()
  }, [])

  const loadProducts = async () => {
    try {
      // فعلاً داده نمونه - بعداً با API واقعی جایگزین می‌شود
      const mockProducts: Product[] = [
        {
          id: 1,
          sku: 'SKU-001',
          dkp_code: 'DKP123456',
          title: 'گوشی موبایل سامسونگ Galaxy A54',
          category: 'موبایل',
          stock_quantity: 45,
          reserved_quantity: 5,
          available_quantity: 40,
          min_stock_alert: 10,
          cost_price: 15000000,
          sell_price: 18000000,
          warehouse_name: 'انبار مرکزی',
          is_low_stock: false
        },
        {
          id: 2,
          sku: 'SKU-002',
          dkp_code: 'DKP789012',
          title: 'لپ‌تاپ لنوو IdeaPad 3',
          category: 'لپ‌تاپ',
          stock_quantity: 8,
          reserved_quantity: 2,
          available_quantity: 6,
          min_stock_alert: 10,
          cost_price: 25000000,
          sell_price: 30000000,
          warehouse_name: 'انبار مرکزی',
          is_low_stock: true
        },
        {
          id: 3,
          sku: 'SKU-003',
          dkp_code: 'DKP345678',
          title: 'هدفون بی‌سیم سونی WH-1000XM5',
          category: 'لوازم جانبی',
          stock_quantity: 120,
          reserved_quantity: 15,
          available_quantity: 105,
          min_stock_alert: 20,
          cost_price: 12000000,
          sell_price: 15000000,
          warehouse_name: 'انبار مرکزی',
          is_low_stock: false
        }
      ]
      setProducts(mockProducts)
    } catch (error) {
      console.error('خطا:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredProducts = products.filter(product => {
    if (filters.search) {
      const search = filters.search.toLowerCase()
      if (
        !product.title.toLowerCase().includes(search) &&
        !product.sku.toLowerCase().includes(search) &&
        !product.dkp_code.toLowerCase().includes(search)
      ) {
        return false
      }
    }

    if (filters.category !== 'all' && product.category !== filters.category) {
      return false
    }

    if (filters.stock_status === 'low' && !product.is_low_stock) {
      return false
    }
    if (filters.stock_status === 'available' && product.available_quantity === 0) {
      return false
    }

    return true
  })

  const totalValue = products.reduce((sum, p) => sum + (p.stock_quantity * p.cost_price), 0)
  const lowStockCount = products.filter(p => p.is_low_stock).length
  const totalProducts = products.length
  const totalStock = products.reduce((sum, p) => sum + p.stock_quantity, 0)

  return (
    <ProtectedRoute requiredPermission="warehouse_view">
      <div className="flex h-screen bg-gray-50" dir="rtl">
        <Sidebar />
        
        <main className="flex-1 overflow-y-auto">
          {/* Header */}
          <header className="bg-white shadow-sm border-b sticky top-0 z-10">
            <div className="px-8 py-6">
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Package className="text-blue-600" />
                موجودی انبار
              </h1>
              <p className="text-gray-600 mt-2">
                مدیریت و پیگیری موجودی کالاها
              </p>
            </div>
          </header>

          <div className="p-8">
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl shadow-lg p-6 text-white">
                <Package size={32} className="mb-4 opacity-80" />
                <h3 className="text-3xl font-bold mb-1">{totalProducts}</h3>
                <p className="text-sm opacity-90">کل محصولات</p>
              </div>

              <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl shadow-lg p-6 text-white">
                <TrendingUp size={32} className="mb-4 opacity-80" />
                <h3 className="text-3xl font-bold mb-1">{totalStock.toLocaleString('fa-IR')}</h3>
                <p className="text-sm opacity-90">مجموع موجودی</p>
              </div>

              <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl shadow-lg p-6 text-white">
                <AlertTriangle size={32} className="mb-4 opacity-80" />
                <h3 className="text-3xl font-bold mb-1">{lowStockCount}</h3>
                <p className="text-sm opacity-90">موجودی کم</p>
              </div>

              <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl shadow-lg p-6 text-white">
                <TrendingDown size={32} className="mb-4 opacity-80" />
                <h3 className="text-3xl font-bold mb-1">
                  {(totalValue / 1000000000).toFixed(1)}B
                </h3>
                <p className="text-sm opacity-90">ارزش کل</p>
              </div>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
              <div className="flex items-center gap-2 mb-4">
                <Filter className="text-gray-600" size={20} />
                <h3 className="font-bold text-gray-900">فیلترها</h3>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="relative">
                  <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                  <input
                    type="text"
                    placeholder="جستجو (نام، SKU، DKP)..."
                    value={filters.search}
                    onChange={(e) => setFilters({...filters, search: e.target.value})}
                    className="w-full pr-10 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <select
                  value={filters.category}
                  onChange={(e) => setFilters({...filters, category: e.target.value})}
                  className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">همه دسته‌ها</option>
                  <option value="موبایل">موبایل</option>
                  <option value="لپ‌تاپ">لپ‌تاپ</option>
                  <option value="لوازم جانبی">لوازم جانبی</option>
                </select>

                <select
                  value={filters.stock_status}
                  onChange={(e) => setFilters({...filters, stock_status: e.target.value})}
                  className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">همه وضعیت‌ها</option>
                  <option value="available">موجود</option>
                  <option value="low">موجودی کم</option>
                </select>
              </div>
            </div>

            {/* Products Table */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="p-6 border-b flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-900">
                  لیست کالاها ({filteredProducts.length})
                </h2>
                
                {user?.permissions.includes('warehouse_create') && (
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2">
                    <Plus size={18} />
                    کالای جدید
                  </button>
                )}
              </div>

              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto"></div>
                </div>
              ) : filteredProducts.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Package size={64} className="mx-auto mb-4 text-gray-300" />
                  <p>هیچ کالایی یافت نشد</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          محصول
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          موجودی
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          رزرو شده
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          قابل فروش
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          قیمت
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
                      {filteredProducts.map((product) => (
                        <tr key={product.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4">
                            <div>
                              <div className="font-medium text-gray-900">{product.title}</div>
                              <div className="text-sm text-gray-500">
                                SKU: {product.sku} | DKP: {product.dkp_code}
                              </div>
                              <div className="text-xs text-gray-400 mt-1">
                                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                                  {product.category}
                                </span>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-lg font-bold text-gray-900">
                              {product.stock_quantity}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-orange-600 font-medium">
                              {product.reserved_quantity}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-green-600 font-bold">
                              {product.available_quantity}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="text-sm">
                              <div className="text-gray-900 font-medium">
                                {product.sell_price.toLocaleString('fa-IR')} تومان
                              </div>
                              <div className="text-gray-500">
                                خرید: {product.cost_price.toLocaleString('fa-IR')}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            {product.is_low_stock ? (
                              <span className="px-3 py-1 bg-red-100 text-red-800 text-xs rounded-full flex items-center gap-1 w-fit">
                                <AlertTriangle size={14} />
                                موجودی کم
                              </span>
                            ) : (
                              <span className="px-3 py-1 bg-green-100 text-green-800 text-xs rounded-full flex items-center gap-1 w-fit">
                                ✓ موجود
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            {user?.permissions.includes('warehouse_edit') && (
                              <button
                                className="p-2 text-blue-600 hover:bg-blue-50 rounded transition"
                                title="ویرایش"
                              >
                                <Edit size={18} />
                              </button>
                            )}
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