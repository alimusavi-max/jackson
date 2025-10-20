'use client'

import { useState, useEffect } from 'react'
import { ordersAPI } from '@/lib/api'
import { Printer, Settings, CheckSquare, Square, Package, Loader2, AlertCircle, RefreshCw, Save, Trash2 } from 'lucide-react'

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
  status: string
  order_date_persian: string
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

export default function LabelsPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [selectedOrders, setSelectedOrders] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // تنظیمات
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait')
  const [includeDataMatrix, setIncludeDataMatrix] = useState(true)
  const [includeQRCode, setIncludeQRCode] = useState(true)
  const [fetchFromAPI, setFetchFromAPI] = useState(true)
  const [updateDB, setUpdateDB] = useState(true)
  
  // فیلترها
  const [filters, setFilters] = useState({
    search: '',
    city: 'all',
    province: 'all',
    status: 'all',
    multiItemOnly: false,
    hasAddress: 'all',
    dateFrom: '',
    dateTo: ''
  })

  // پروفایل‌های فرستنده
  const [senderProfiles, setSenderProfiles] = useState<Record<string, SenderProfile>>({})
  const [selectedProfile, setSelectedProfile] = useState<string>('default')
  const [currentSender, setCurrentSender] = useState<SenderProfile>({
    name: '',
    address: '',
    postal_code: '',
    phone: ''
  })
  const [newProfileName, setNewProfileName] = useState('')

  // بارگذاری اولیه
  useEffect(() => {
    loadOrders()
    loadProfilesFromStorage()
  }, [])

  // بارگذاری پروفایل‌ها از localStorage
  const loadProfilesFromStorage = () => {
    try {
      const saved = localStorage.getItem('sender_profiles')
      if (saved) {
        const profiles = JSON.parse(saved)
        setSenderProfiles(profiles)
        
        if (profiles.default) {
          setCurrentSender(profiles.default)
        }
      } else {
        const defaultProfiles = {
          'default': {
            name: '',
            address: '',
            postal_code: '',
            phone: ''
          }
        }
        setSenderProfiles(defaultProfiles)
        localStorage.setItem('sender_profiles', JSON.stringify(defaultProfiles))
      }
    } catch (error) {
      console.error('خطا در بارگذاری پروفایل‌ها:', error)
    }
  }

  // ذخیره پروفایل‌ها در localStorage
  const saveProfilesToStorage = (profiles: Record<string, SenderProfile>) => {
    try {
      localStorage.setItem('sender_profiles', JSON.stringify(profiles))
    } catch (error) {
      console.error('خطا در ذخیره پروفایل‌ها:', error)
    }
  }

  const loadOrders = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await ordersAPI.getAll({ limit: 1000 })
      
      // اطمینان از اینکه data یک آرایه است
      if (res && Array.isArray(res.data)) {
        setOrders(res.data)
      } else {
        console.error('پاسخ نامعتبر:', res)
        setOrders([])
        setError('فرمت داده نامعتبر است')
      }
    } catch (error) {
      console.error('خطا:', error)
      setOrders([])
      setError('خطا در دریافت سفارشات')
    } finally {
      setLoading(false)
    }
  }

  // ذخیره پروفایل جدید
  const saveProfile = () => {
    if (!newProfileName.trim()) {
      alert('⚠️ لطفاً نام پروفایل را وارد کنید')
      return
    }

    if (!currentSender.name || !currentSender.address) {
      alert('⚠️ لطفاً حداقل نام و آدرس فرستنده را وارد کنید')
      return
    }

    const updatedProfiles = {
      ...senderProfiles,
      [newProfileName]: { ...currentSender }
    }
    
    setSenderProfiles(updatedProfiles)
    saveProfilesToStorage(updatedProfiles)
    setSelectedProfile(newProfileName)
    setNewProfileName('')
    alert(`✅ پروفایل "${newProfileName}" ذخیره شد`)
  }

  // حذف پروفایل
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
    saveProfilesToStorage(updatedProfiles)
    
    if (selectedProfile === profileName) {
      setSelectedProfile('default')
      setCurrentSender(updatedProfiles.default || { name: '', address: '', postal_code: '', phone: '' })
    }
    
    alert(`✅ پروفایل "${profileName}" حذف شد`)
  }

  // انتخاب پروفایل
  const selectProfile = (profileName: string) => {
    setSelectedProfile(profileName)
    if (profileName && senderProfiles[profileName]) {
      setCurrentSender(senderProfiles[profileName])
    } else {
      setCurrentSender({ name: '', address: '', postal_code: '', phone: '' })
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

    try {
      const selectedOrdersList = orders.filter(o => selectedOrders.has(o.id))
      
      console.log('🚀 شروع تولید برچسب‌ها...')
      console.log(`📦 تعداد سفارشات: ${selectedOrdersList.length}`)
      console.log(`🔄 دریافت از API: ${fetchFromAPI}`)
      console.log(`💾 به‌روزرسانی دیتابیس: ${updateDB}`)

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
            fetch_from_api: fetchFromAPI,
            update_database: updateDB
          }
        })
      })

      console.log(`📡 پاسخ سرور: ${response.status} ${response.statusText}`)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('❌ خطای سرور:', errorText)
        throw new Error(`خطا در سرور: ${response.status}`)
      }

      const blob = await response.blob()
      console.log(`📄 حجم PDF: ${(blob.size / 1024).toFixed(2)} KB`)
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `labels_${new Date().getTime()}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      console.log('✅ دانلود موفق')
      
      if (updateDB) {
        alert(`✅ ${selectedOrders.size} برچسب با موفقیت ایجاد شد!\n\n💾 اطلاعات جدید در دیتابیس به‌روزرسانی شد.`)
        await loadOrders()
      } else {
        alert(`✅ ${selectedOrders.size} برچسب با موفقیت ایجاد و دانلود شد!`)
      }
      
    } catch (error: any) {
      console.error('❌ خطای کامل:', error)
      
      let errorMessage = 'خطای ناشناخته'
      
      if (error.message) {
        errorMessage = error.message
      }
      
      if (error.response) {
        errorMessage = `خطای سرور: ${error.response.status}`
      }
      
      alert(`❌ خطا در تولید برچسب‌ها:\n\n${errorMessage}\n\nلطفاً Console را بررسی کنید.`)
    } finally {
      setGenerating(false)
    }
  }

  // اطمینان از اینکه orders یک آرایه است قبل از filter
  const filteredOrders = Array.isArray(orders) ? orders.filter(order => {
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
    if (filters.status !== 'all' && order.status !== filters.status) return false
    if (filters.multiItemOnly && order.items_count <= 1) return false
    
    if (filters.hasAddress === 'yes' && (!order.full_address || order.full_address === 'نامشخص')) return false
    if (filters.hasAddress === 'no' && order.full_address && order.full_address !== 'نامشخص') return false

    if (filters.dateFrom && order.order_date_persian) {
      if (order.order_date_persian < filters.dateFrom) return false
    }
    if (filters.dateTo && order.order_date_persian) {
      if (order.order_date_persian > filters.dateTo) return false
    }

    return true
  }) : []

  const cities = Array.isArray(orders) ? Array.from(new Set(orders.map(o => o.city).filter(Boolean))).sort() : []
  const provinces = Array.isArray(orders) ? Array.from(new Set(orders.map(o => o.province).filter(Boolean))).sort() : []
  const statuses = Array.isArray(orders) ? Array.from(new Set(orders.map(o => o.status).filter(Boolean))).sort() : []

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

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
        <div className="text-center max-w-md">
          <div className="bg-red-50 border-2 border-red-200 rounded-xl p-8">
            <AlertCircle className="text-red-500 mx-auto mb-4" size={64} />
            <h2 className="text-2xl font-bold text-red-900 mb-2">خطا در بارگذاری</h2>
            <p className="text-red-700 mb-6">{error}</p>
            <button
              onClick={loadOrders}
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-medium flex items-center gap-2 mx-auto"
            >
              <RefreshCw size={20} />
              تلاش مجدد
            </button>
          </div>
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
                <span className="text-gray-400 mx-2">|</span>
                <span className="text-gray-500">کل: {orders.length}</span>
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={loadOrders}
                disabled={loading}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition disabled:opacity-50 flex items-center gap-2"
              >
                <RefreshCw size={18} />
                بارگذاری مجدد
              </button>
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

      {generating && (
        <div className="bg-blue-50 border-b border-blue-200">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center gap-3">
              <Loader2 className="animate-spin text-blue-600" size={24} />
              <div>
                <p className="font-medium text-blue-900">در حال تولید برچسب‌ها...</p>
                <p className="text-sm text-blue-700">
                  {fetchFromAPI && '🔄 دریافت اطلاعات از API دیجی‌کالا | '}
                  {updateDB && '💾 به‌روزرسانی دیتابیس | '}
                  لطفاً صبر کنید...
                </p>
              </div>
            </div>
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

          <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="text-yellow-600 flex-shrink-0 mt-0.5" size={20} />
            <div className="text-sm text-yellow-900">
              <p className="font-semibold mb-1">⚠️ مهم:</p>
              <p>اطلاعات فرستنده روی برچسب پستی چاپ می‌شود. می‌توانید پروفایل‌های مختلف ذخیره کنید.</p>
            </div>
          </div>

          {/* انتخاب پروفایل */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                انتخاب پروفایل ذخیره شده
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
                  className="w-full px-4 py-2.5 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition flex items-center justify-center gap-2"
                >
                  <Trash2 size={18} />
                  حذف پروفایل
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

          {/* ذخیره پروفایل جدید */}
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
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium flex items-center gap-2"
            >
              <Save size={18} />
              ذخیره پروفایل
            </button>
          </div>
        </div>

        {/* تنظیمات برچسب */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Settings className="text-purple-600" />
            تنظیمات برچسب و دریافت داده
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

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                دریافت و به‌روزرسانی داده
              </label>
              <div className="space-y-2 bg-blue-50 p-4 rounded-lg">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={fetchFromAPI}
                    onChange={(e) => setFetchFromAPI(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-sm">🔄 دریافت اطلاعات کامل از API دیجی‌کالا (آدرس، تلفن، کد پستی)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={updateDB}
                    onChange={(e) => setUpdateDB(e.target.checked)}
                    disabled={!fetchFromAPI}
                    className="w-4 h-4 text-blue-600 rounded disabled:opacity-50"
                  />
                  <span className="text-sm">💾 به‌روزرسانی دیتابیس با اطلاعات جدید (فقط موارد خالی یا نامشخص)</span>
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
          
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
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

            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">همه وضعیت‌ها</option>
              {statuses.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>

            <select
              value={filters.hasAddress}
              onChange={(e) => setFilters({...filters, hasAddress: e.target.value})}
              className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">همه (با/بدون آدرس)</option>
              <option value="yes">✓ دارای آدرس</option>
              <option value="no">✗ بدون آدرس</option>
            </select>

            <input
              type="text"
              placeholder="تاریخ از (مثال: 1403/01/01)"
              value={filters.dateFrom}
              onChange={(e) => setFilters({...filters, dateFrom: e.target.value})}
              className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />

            <input
              type="text"
              placeholder="تاریخ تا (مثال: 1403/12/29)"
              value={filters.dateTo}
              onChange={(e) => setFilters({...filters, dateTo: e.target.value})}
              className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />

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
              {filteredOrders.length} سفارش نمایش داده شده
            </span>
          </div>

          {filteredOrders.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <Package size={64} className="mx-auto mb-4 text-gray-300" />
              <p className="text-xl">هیچ سفارشی با این فیلترها یافت نشد</p>
              <p className="text-sm mt-2">فیلترها را تغییر دهید یا سفارشات جدید دریافت کنید</p>
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
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">وضعیت</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">آدرس</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">تعداد کالا</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-700">تاریخ</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOrders.map((order, index) => (
                    <tr
                      key={order.id}
                      className={`border-b hover:bg-blue-50 transition cursor-pointer ${
                        selectedOrders.has(order.id) ? 'bg-blue-50' : ''
                      } ${order.items_count > 1 ? 'bg-yellow-50' : ''} ${
                        !order.full_address || order.full_address === 'نامشخص' ? 'bg-red-50' : ''
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
                        <div>{order.city || '-'}</div>
                        <div className="text-xs text-gray-500">{order.province}</div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                          {order.status || 'نامشخص'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {order.full_address && order.full_address !== 'نامشخص' ? (
                          <span className="text-xs text-green-600 flex items-center gap-1">
                            ✓ دارد
                          </span>
                        ) : (
                          <span className="text-xs text-red-600 flex items-center gap-1">
                            ✗ ندارد
                            {fetchFromAPI && (
                              <span className="text-blue-600" title="با فعال بودن دریافت از API، اطلاعات کامل می‌شود">
                                🔄
                              </span>
                            )}
                          </span>
                        )}
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
                        <span className="text-xs text-gray-600">
                          {order.order_date_persian || '-'}
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