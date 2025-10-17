'use client'

import { useState, useEffect } from 'react'
import { ordersAPI } from '@/lib/api'
import { Printer, Settings, CheckSquare, Square, Package, Loader2 } from 'lucide-react'

interface Order {
  id: number
  order_code: string
  shipment_id: string
  customer_name: string
  customer_phone: string
  city: string
  province: string
  full_address: string
  postal_code: string
  tracking_code: string | null
  items_count: number
  total_quantity: number
  items: any[]
}

interface SenderProfile {
  name: string
  address: string
  postal_code: string
  phone: string
}

interface ProgressState {
  current: number
  total: number
  percentage: number
  currentOrder: string
  message: string
}

export default function LabelsPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [selectedOrders, setSelectedOrders] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [progress, setProgress] = useState<ProgressState | null>(null)
  
  // تنظیمات
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait')
  const [includeDataMatrix, setIncludeDataMatrix] = useState(true)
  const [includeQRCode, setIncludeQRCode] = useState(true)
  
  // فیلترها
  const [filters, setFilters] = useState({
    search: '',
    city: 'all',
    province: 'all',
    multiItemOnly: false
  })

  // پروفایل فرستنده
  const [senderProfiles, setSenderProfiles] = useState<Record<string, SenderProfile>>({
    'default': { name: '', address: '', postal_code: '', phone: '' }
  })
  const [selectedProfile, setSelectedProfile] = useState<string>('default')
  const [currentSender, setCurrentSender] = useState<SenderProfile>({
    name: '',
    address: '',
    postal_code: '',
    phone: ''
  })
  const [newProfileName, setNewProfileName] = useState('')

  useEffect(() => {
    loadOrders()
  }, [])

  const loadOrders = async () => {
    try {
      setLoading(true)
      const res = await ordersAPI.getAll({ limit: 1000 })
      
      const ordersWithAddress = res.data.filter((o: Order) => 
        o.full_address && 
        o.full_address !== 'نامشخص' && 
        o.customer_name
      )
      
      setOrders(ordersWithAddress)
    } catch (error) {
      console.error('خطا:', error)
      alert('خطا در دریافت سفارشات')
    } finally {
      setLoading(false)
    }
  }

  const saveProfile = () => {
    if (!newProfileName.trim()) {
      alert('⚠️ لطفاً نام پروفایل را وارد کنید')
      return
    }

    const updatedProfiles = {
      ...senderProfiles,
      [newProfileName]: { ...currentSender }
    }
    
    setSenderProfiles(updatedProfiles)
    setSelectedProfile(newProfileName)
    alert(`✅ پروفایل "${newProfileName}" ذخیره شد`)
    setNewProfileName('')
  }

  const deleteProfile = (profileName: string) => {
    if (profileName === 'default') {
      alert('⚠️ نمی‌توانید پروفایل پیش‌فرض را حذف کنید')
      return
    }

    if (!confirm(`آیا مطمئن هستید که می‌خواهید پروفایل "${profileName}" را حذف کنید؟`)) {
      return
    }

    const updatedProfiles = { ...senderProfiles }
    delete updatedProfiles[profileName]
    
    setSenderProfiles(updatedProfiles)
    
    if (selectedProfile === profileName) {
      setSelectedProfile('default')
      setCurrentSender(updatedProfiles.default || { name: '', address: '', postal_code: '', phone: '' })
    }
  }

  const selectProfile = (profileName: string) => {
    setSelectedProfile(profileName)
    setCurrentSender(senderProfiles[profileName] || { name: '', address: '', postal_code: '', phone: '' })
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
    if (selectedOrders.size === filteredOrders.length) {
      setSelectedOrders(new Set())
    } else {
      setSelectedOrders(new Set(filteredOrders.map(o => o.id)))
    }
  }

  const generateLabels = async () => {
    if (selectedOrders.size === 0) {
      alert('⚠️ لطفاً حداقل یک سفارش انتخاب کنید')
      return
    }

    if (!currentSender.name || !currentSender.address) {
      alert('⚠️ لطفاً اطلاعات فرستنده را تکمیل کنید')
      return
    }

    setGenerating(true)
    setProgress({
      current: 0,
      total: selectedOrders.size,
      percentage: 0,
      currentOrder: '',
      message: 'شروع تولید برچسب‌ها...'
    })

    try {
      const selectedOrdersList = orders.filter(o => selectedOrders.has(o.id))
      
      // نمایش پیشرفت شبیه‌سازی شده (چون SSE در مرورگر پیچیده است)
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (!prev) return null
          const newCurrent = Math.min(prev.current + 1, prev.total - 1)
          return {
            ...prev,
            current: newCurrent,
            percentage: Math.round((newCurrent / prev.total) * 100),
            currentOrder: selectedOrdersList[newCurrent]?.order_code || '',
            message: `در حال پردازش ${newCurrent + 1} از ${prev.total}...`
          }
        })
      }, 500)

      const response = await fetch('http://localhost:8000/api/labels/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          orders: selectedOrdersList.map(o => ({
            id: o.id,
            order_code: o.order_code,
            shipment_id: o.shipment_id,
            customer_name: o.customer_name,
            customer_phone: o.customer_phone,
            city: o.city,
            province: o.province,
            full_address: o.full_address,
            postal_code: o.postal_code,
            items: o.items
          })),
          sender: currentSender,
          settings: {
            orientation,
            include_datamatrix: includeDataMatrix,
            include_qrcode: includeQRCode,
            fetch_from_api: false
          }
        })
      })

      clearInterval(progressInterval)

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`خطا در سرور: ${errorText}`)
      }

      // بروزرسانی پیشرفت به 100%
      setProgress({
        current: selectedOrders.size,
        total: selectedOrders.size,
        percentage: 100,
        currentOrder: '',
        message: 'در حال آماده‌سازی دانلود...'
      })

      // دانلود PDF
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `labels_${new Date().getTime()}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      alert(`✅ ${selectedOrders.size} برچسب با موفقیت ایجاد شد!`)
    } catch (error: any) {
      console.error('خطا:', error)
      alert(`❌ خطا در تولید برچسب‌ها:\n\n${error.message}`)
    } finally {
      setGenerating(false)
      setProgress(null)
    }
  }

  // فیلتر کردن سفارشات
  const filteredOrders = orders.filter(order => {
    if (filters.search) {
      const search = filters.search.toLowerCase()
      if (
        !order.order_code?.toLowerCase().includes(search) &&
        !order.customer_name?.toLowerCase().includes(search) &&
        !order.city?.toLowerCase().includes(search)
      ) {
        return false
      }
    }

    if (filters.city !== 'all' && order.city !== filters.city) return false
    if (filters.province !== 'all' && order.province !== filters.province) return false
    if (filters.multiItemOnly && order.items_count <= 1) return false

    return true
  })

  const cities = Array.from(new Set(orders.map(o => o.city).filter(Boolean))).sort()
  const provinces = Array.from(new Set(orders.map(o => o.province).filter(Boolean))).sort()

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
                <span className="font-bold">{filteredOrders.length}</span> سفارش انتخاب شده
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={generateLabels}
                disabled={selectedOrders.size === 0 || generating}
                className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:bg-gray-300 disabled:cursor-not-allowed font-medium flex items-center gap-2"
              >
                {generating ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    در حال تولید...
                  </>
                ) : (
                  <>
                    <Printer size={20} />
                    تولید {selectedOrders.size} برچسب
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      {generating && progress && (
        <div className="bg-blue-50 border-b border-blue-200">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium text-blue-700">
                {progress.message}
              </span>
              <span className="text-sm font-bold text-blue-900">
                {progress.percentage}%
              </span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progress.percentage}%` }}
              />
            </div>
            {progress.currentOrder && (
              <p className="text-xs text-blue-600 mt-2">
                سفارش جاری: {progress.currentOrder}
              </p>
            )}
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* تنظیمات فرستنده */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Settings className="text-blue-600" />
            اطلاعات فرستنده
          </h2>

          {/* انتخاب پروفایل */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                انتخاب پروفایل
              </label>
              <select
                value={selectedProfile}
                onChange={(e) => selectProfile(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">پروفایل جدید</option>
                {Object.keys(senderProfiles).map(name => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
            </div>
            {selectedProfile && selectedProfile !== '' && (
              <div className="flex items-end">
                <button
                  onClick={() => deleteProfile(selectedProfile)}
                  className="w-full px-4 py-2.5 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition"
                >
                  🗑️ حذف پروفایل
                </button>
              </div>
            )}
          </div>

          {/* فرم اطلاعات */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                نام فرستنده *
              </label>
              <input
                type="text"
                value={currentSender.name}
                onChange={(e) => setCurrentSender({...currentSender, name: e.target.value})}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="مثال: فروشگاه تجارت دریای آرام"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                شماره تلفن *
              </label>
              <input
                type="text"
                value={currentSender.phone}
                onChange={(e) => setCurrentSender({...currentSender, phone: e.target.value})}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="021-12345678"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                کد پستی *
              </label>
              <input
                type="text"
                value={currentSender.postal_code}
                onChange={(e) => setCurrentSender({...currentSender, postal_code: e.target.value})}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="1234567890"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                آدرس کامل *
              </label>
              <input
                type="text"
                value={currentSender.address}
                onChange={(e) => setCurrentSender({...currentSender, address: e.target.value})}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="تهران، خیابان..."
              />
            </div>
          </div>

          {/* ذخیره پروفایل */}
          <div className="flex gap-3">
            <input
              type="text"
              value={newProfileName}
              onChange={(e) => setNewProfileName(e.target.value)}
              className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="نام پروفایل جدید (مثال: فروشگاه تهران)"
            />
            <button
              onClick={saveProfile}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              💾 ذخیره پروفایل
            </button>
          </div>
        </div>

        {/* تنظیمات برچسب */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Settings className="text-purple-600" />
            تنظیمات برچسب
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                حالت چاپ
              </label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={orientation === 'portrait'}
                    onChange={() => setOrientation('portrait')}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span>📄 عمودی (A5)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={orientation === 'landscape'}
                    onChange={() => setOrientation('landscape')}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span>📄 افقی (A5)</span>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                گزینه‌های اضافی
              </label>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeDataMatrix}
                    onChange={(e) => setIncludeDataMatrix(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span>📊 Data Matrix (پیشنهاد می‌شود)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeQRCode}
                    onChange={(e) => setIncludeQRCode(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span>🔲 QR Code</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* فیلترها */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            🔍 فیلتر سفارشات
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <input
              type="text"
              placeholder="جستجو..."
              value={filters.search}
              onChange={(e) => setFilters({...filters, search: e.target.value})}
              className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />

            <select
              value={filters.province}
              onChange={(e) => setFilters({...filters, province: e.target.value})}
              className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">همه استان‌ها</option>
              {provinces.map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>

            <select
              value={filters.city}
              onChange={(e) => setFilters({...filters, city: e.target.value})}
              className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">همه شهرها</option>
              {cities.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.multiItemOnly}
                  onChange={(e) => setFilters({...filters, multiItemOnly: e.target.checked})}
                  className="w-4 h-4 text-orange-600 rounded"
                />
                <span className="text-sm">🎁 فقط چندقلمی</span>
              </label>
            </div>
          </div>
        </div>

        {/* لیست سفارشات */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="p-4 bg-gray-50 border-b flex items-center justify-between">
            <button
              onClick={toggleAll}
              className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition font-medium flex items-center gap-2"
            >
              {selectedOrders.size === filteredOrders.length ? (
                <>
                  <CheckSquare size={18} />
                  لغو انتخاب همه
                </>
              ) : (
                <>
                  <Square size={18} />
                  انتخاب همه ({filteredOrders.length})
                </>
              )}
            </button>
            
            <span className="text-sm text-gray-600">
              {filteredOrders.length} سفارش آماده چاپ برچسب
            </span>
          </div>

          {filteredOrders.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <Package size={64} className="mx-auto mb-4 text-gray-300" />
              <p className="text-xl">هیچ سفارش آماده‌ای یافت نشد</p>
              <p className="text-sm mt-2">سفارشات باید دارای آدرس کامل باشند</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b-2 border-blue-200">
                  <tr>
                    <th className="px-4 py-3 text-right w-10">
                      <input
                        type="checkbox"
                        checked={selectedOrders.size === filteredOrders.length && filteredOrders.length > 0}
                        onChange={toggleAll}
                        className="w-4 h-4"
                      />
                    </th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">ردیف</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">کد سفارش</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">نام مشتری</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">شهر</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">تعداد کالا</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">کد پستی</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOrders.map((order, index) => (
                    <tr
                      key={order.id}
                      className={`border-b hover:bg-blue-50 transition cursor-pointer ${
                        selectedOrders.has(order.id) ? 'bg-blue-50' : ''
                      } ${order.items_count > 1 ? 'bg-yellow-50' : ''}`}
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
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <span className="inline-block px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-bold">
                            {order.total_quantity} عدد
                          </span>
                          {order.items_count > 1 && (
                            <span className="text-orange-600 text-lg" title="چندقلمی">🎁</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                          {order.postal_code || '-'}
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