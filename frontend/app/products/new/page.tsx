// frontend/app/warehouse/products/new/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import { Plus, X, Save, AlertCircle } from 'lucide-react'

interface Warehouse {
  id: number
  name: string
}

interface Marketplace {
  id: number
  name: string
  code: string
}

interface MarketplaceSKU {
  marketplace_id: number
  marketplace_sku: string
  marketplace_url: string
  price_in_marketplace: number | null
  sync_stock: boolean
}

export default function NewProductPage() {
  const router = useRouter()
  const { user } = useAuth()
  
  const [warehouses, setWarehouses] = useState<Warehouse[]>([])
  const [marketplaces, setMarketplaces] = useState<Marketplace[]>([])
  const [submitting, setSubmitting] = useState(false)
  
  const [formData, setFormData] = useState({
    sku: '',
    title: '',
    description: '',
    brand: '',
    warehouse_id: 0,
    cost_price: 0,
    sell_price: 0,
    min_stock_alert: 5,
    reorder_point: 10,
    barcode: '',
    weight: null as number | null
  })
  
  const [marketplaceSkus, setMarketplaceSkus] = useState<MarketplaceSKU[]>([])
  const [showAddMarketplace, setShowAddMarketplace] = useState(false)
  const [newMarketplaceSku, setNewMarketplaceSku] = useState<MarketplaceSKU>({
    marketplace_id: 0,
    marketplace_sku: '',
    marketplace_url: '',
    price_in_marketplace: null,
    sync_stock: false
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      
      // دریافت انبارها
      const whRes = await fetch('http://localhost:8000/api/warehouse/warehouses', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (whRes.ok) {
        const data = await whRes.json()
        setWarehouses(data)
        if (data.length > 0) {
          setFormData(prev => ({ ...prev, warehouse_id: data[0].id }))
        }
      }

      // دریافت مارکت‌ها
      const mpRes = await fetch('http://localhost:8000/api/warehouse/marketplaces', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (mpRes.ok) {
        setMarketplaces(await mpRes.json())
      }
    } catch (error) {
      console.error('خطا:', error)
    }
  }

  const handleAddMarketplaceSku = () => {
    if (!newMarketplaceSku.marketplace_id || !newMarketplaceSku.marketplace_sku) {
      alert('⚠️ لطفاً مارکت و SKU را وارد کنید')
      return
    }

    // چک تکراری
    if (marketplaceSkus.some(m => m.marketplace_id === newMarketplaceSku.marketplace_id)) {
      alert('⚠️ این مارکت قبلاً اضافه شده است')
      return
    }

    setMarketplaceSkus([...marketplaceSkus, newMarketplaceSku])
    setNewMarketplaceSku({
      marketplace_id: 0,
      marketplace_sku: '',
      marketplace_url: '',
      price_in_marketplace: null,
      sync_stock: false
    })
    setShowAddMarketplace(false)
  }

  const handleRemoveMarketplaceSku = (index: number) => {
    setMarketplaceSkus(marketplaceSkus.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validation
    if (!formData.sku || !formData.title || !formData.warehouse_id) {
      alert('⚠️ لطفاً فیلدهای ضروری را پر کنید')
      return
    }

    setSubmitting(true)

    try {
      const token = localStorage.getItem('auth_token')
      const payload = {
        ...formData,
        marketplace_skus: marketplaceSkus
      }

      const response = await fetch('http://localhost:8000/api/warehouse/products', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        alert('✅ محصول با موفقیت ایجاد شد!')
        router.push('/warehouse/products')
      } else {
        const error = await response.json()
        alert(`❌ ${error.detail}`)
      }
    } catch (error) {
      alert('❌ خطا در ایجاد محصول')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <ProtectedRoute requiredPermission="warehouse_create">
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
        {/* Header */}
        <header className="bg-white shadow-sm border-b sticky top-0 z-10">
          <div className="max-w-5xl mx-auto px-6 py-4">
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.back()}
                className="text-2xl hover:text-blue-600 transition"
              >
                ←
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">محصول جدید</h1>
                <p className="text-gray-600 mt-1">افزودن محصول به انبار</p>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-5xl mx-auto px-6 py-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Info */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                📦 اطلاعات پایه
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    SKU داخلی *
                  </label>
                  <input
                    type="text"
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                    className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="PROD-001"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    کد منحصر به فرد در سیستم شما
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    بارکد
                  </label>
                  <input
                    type="text"
                    value={formData.barcode}
                    onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                    className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="1234567890123"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    نام محصول *
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="گوشی موبایل سامسونگ Galaxy A54"
                    required
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    توضیحات
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="توضیحات کامل محصول..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    برند
                  </label>
                  <input
                    type="text"
                    value={formData.brand}
                    onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                    className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Samsung"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    انبار *
                  </label>
                  <select
                    value={formData.warehouse_id}
                    onChange={(e) => setFormData({ ...formData, warehouse_id: parseInt(e.target.value) })}
                    className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value={0}>انتخاب کنید</option>
                    {warehouses.map(wh => (
                      <option key={wh.id} value={wh.id}>{wh.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    وزن (گرم)
                  </label>
                  <input
                    type="number"
                    value={formData.weight || ''}
                    onChange={(e) => setFormData({ ...formData, weight: e.target.value ? parseFloat(e.target.value) : null })}
                    className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="200"
                  />
                </div>
              </div>
            </div>

            {/* Pricing & Stock */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                💰 قیمت و موجودی
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    قیمت خرید (تومان) *
                  </label>
                  <input
                    type="number"
                    value={formData.cost_price}
                    onChange={(e) => setFormData({ ...formData, cost_price: parseFloat(e.target.value) })}
                    className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="1000000"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    قیمت فروش (تومان) *
                  </label>
                  <input
                    type="number"
                    value={formData.sell_price}
                    onChange={(e) => setFormData({ ...formData, sell_price: parseFloat(e.target.value) })}
                    className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="1200000"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    حد هشدار موجودی
                  </label>
                  <input
                    type="number"
                    value={formData.min_stock_alert}
                    onChange={(e) => setFormData({ ...formData, min_stock_alert: parseInt(e.target.value) })}
                    className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="5"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    نقطه سفارش مجدد
                  </label>
                  <input
                    type="number"
                    value={formData.reorder_point}
                    onChange={(e) => setFormData({ ...formData, reorder_point: parseInt(e.target.value) })}
                    className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="10"
                  />
                </div>
              </div>
            </div>

            {/* Marketplace SKUs */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  🌐 SKU در پلتفرم‌های فروش ({marketplaceSkus.length})
                </h2>
                <button
                  type="button"
                  onClick={() => setShowAddMarketplace(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2 text-sm"
                >
                  <Plus size={16} />
                  افزودن پلتفرم
                </button>
              </div>

              <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertCircle className="text-blue-600 flex-shrink-0 mt-0.5" size={20} />
                  <div className="text-sm text-blue-900">
                    <p className="font-semibold mb-1">💡 نکته:</p>
                    <p>
                      این محصول در سایت‌های مختلف شماره محصول متفاوتی دارد؟ اینجا می‌تونید 
                      برای هر پلتفرم (دیجی‌کالا، باسلام، دیوار و...) SKU مخصوص اون رو ثبت کنید.
                    </p>
                  </div>
                </div>
              </div>

              {marketplaceSkus.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>هنوز هیچ پلتفرمی اضافه نشده</p>
                  <p className="text-sm mt-1">روی دکمه "افزودن پلتفرم" کلیک کنید</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {marketplaceSkus.map((mp, index) => {
                    const marketplace = marketplaces.find(m => m.id === mp.marketplace_id)
                    return (
                      <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm font-bold">
                              {marketplace?.code}
                            </span>
                            <span className="font-medium text-gray-900">
                              {marketplace?.name}
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleRemoveMarketplaceSku(index)}
                            className="p-1 text-red-600 hover:bg-red-50 rounded transition"
                          >
                            <X size={18} />
                          </button>
                        </div>

                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div>
                            <span className="text-gray-500">SKU:</span>
                            <p className="font-mono font-bold text-gray-900 mt-1">
                              {mp.marketplace_sku}
                            </p>
                          </div>
                          {mp.price_in_marketplace && (
                            <div>
                              <span className="text-gray-500">قیمت در این پلتفرم:</span>
                              <p className="font-bold text-green-600 mt-1">
                                {mp.price_in_marketplace.toLocaleString('fa-IR')} تومان
                              </p>
                            </div>
                          )}
                        </div>

                        {mp.marketplace_url && (
                          <div className="mt-2">
                            <a
                              href={mp.marketplace_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-700 text-xs"
                            >
                              🔗 {mp.marketplace_url}
                            </a>
                          </div>
                        )}

                        {mp.sync_stock && (
                          <div className="mt-2 flex items-center gap-1 text-xs text-green-600">
                            <span>✓</span>
                            <span>همگام‌سازی موجودی فعال</span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Add Marketplace Form */}
              {showAddMarketplace && (
                <div className="mt-4 p-4 bg-blue-50 border-2 border-blue-300 rounded-lg">
                  <h3 className="font-bold text-gray-900 mb-3">افزودن پلتفرم جدید</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        پلتفرم *
                      </label>
                      <select
                        value={newMarketplaceSku.marketplace_id}
                        onChange={(e) => setNewMarketplaceSku({
                          ...newMarketplaceSku,
                          marketplace_id: parseInt(e.target.value)
                        })}
                        className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        <option value={0}>انتخاب کنید</option>
                        {marketplaces
                          .filter(m => !marketplaceSkus.some(mp => mp.marketplace_id === m.id))
                          .map(m => (
                            <option key={m.id} value={m.id}>
                              {m.name} ({m.code})
                            </option>
                          ))
                        }
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        SKU در این پلتفرم *
                      </label>
                      <input
                        type="text"
                        value={newMarketplaceSku.marketplace_sku}
                        onChange={(e) => setNewMarketplaceSku({
                          ...newMarketplaceSku,
                          marketplace_sku: e.target.value
                        })}
                        className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="DKP-123456"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        لینک محصول
                      </label>
                      <input
                        type="url"
                        value={newMarketplaceSku.marketplace_url}
                        onChange={(e) => setNewMarketplaceSku({
                          ...newMarketplaceSku,
                          marketplace_url: e.target.value
                        })}
                        className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="https://www.digikala.com/product/..."
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        قیمت در این پلتفرم (تومان)
                      </label>
                      <input
                        type="number"
                        value={newMarketplaceSku.price_in_marketplace || ''}
                        onChange={(e) => setNewMarketplaceSku({
                          ...newMarketplaceSku,
                          price_in_marketplace: e.target.value ? parseFloat(e.target.value) : null
                        })}
                        className="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="1500000"
                      />
                    </div>

                    <div className="md:col-span-2">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={newMarketplaceSku.sync_stock}
                          onChange={(e) => setNewMarketplaceSku({
                            ...newMarketplaceSku,
                            sync_stock: e.target.checked
                          })}
                          className="w-5 h-5 text-blue-600 rounded"
                        />
                        <span className="text-sm font-medium text-gray-700">
                          همگام‌سازی خودکار موجودی با این پلتفرم
                        </span>
                      </label>
                    </div>
                  </div>

                  <div className="flex gap-3 mt-4">
                    <button
                      type="button"
                      onClick={() => setShowAddMarketplace(false)}
                      className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                    >
                      لغو
                    </button>
                    <button
                      type="button"
                      onClick={handleAddMarketplaceSku}
                      className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      افزودن
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => router.back()}
                className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
              >
                لغو
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition font-medium flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    در حال ذخیره...
                  </>
                ) : (
                  <>
                    <Save size={20} />
                    ذخیره محصول
                  </>
                )}
              </button>
            </div>
          </form>
        </main>
      </div>
    </ProtectedRoute>
  )
}