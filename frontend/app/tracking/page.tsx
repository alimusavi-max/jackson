'use client'

import { useState } from 'react'
import { Upload, FileText, CheckCircle, XCircle, AlertCircle, Database } from 'lucide-react'

interface TrackingData {
  order_code: string
  tracking_code: string
  shipment_id?: string
}

interface MatchedOrder extends TrackingData {
  id?: number
  customer_name?: string
  city?: string
  status?: string
  matched?: boolean
}

export default function TrackingPage() {
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [extractedData, setExtractedData] = useState<TrackingData[]>([])
  const [matchedOrders, setMatchedOrders] = useState<MatchedOrder[]>([])
  const [processing, setProcessing] = useState(false)
  const [currentStep, setCurrentStep] = useState(1)
  const [submitResults, setSubmitResults] = useState<any[]>([])
  const [useDatabase, setUseDatabase] = useState(true) // پیش‌فرض: استفاده از دیتابیس

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // بررسی فرمت فایل
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('❌ لطفاً فقط فایل PDF انتخاب کنید')
      return
    }

    // بررسی حجم فایل (حداکثر 20MB)
    if (file.size > 20 * 1024 * 1024) {
      alert('❌ حجم فایل نباید بیشتر از 20MB باشد')
      return
    }

    setPdfFile(file)
    setProcessing(true)
    setExtractedData([])
    setMatchedOrders([])
    setSubmitResults([])

    try {
      console.log('📤 آپلود فایل:', file.name, 'حجم:', (file.size / 1024).toFixed(2), 'KB')
      
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost:8000/api/tracking/extract-pdf', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        const errorMessage = errorData?.detail || `خطای سرور: ${response.status}`
        throw new Error(errorMessage)
      }

      const data = await response.json()
      
      console.log('✅ داده دریافت شد:', data)
      
      if (!data || data.length === 0) {
        alert('⚠️ هیچ کد رهگیری در PDF یافت نشد!\n\nلطفاً اطمینان حاصل کنید:\n• فایل شامل جداول باشد\n• کدهای سفارش 9 رقمی باشند\n• کدهای رهگیری 24 رقمی باشند')
        setProcessing(false)
        return
      }
      
      setExtractedData(data)
      
      // 🔥 بعد از استخراج، اگر حالت دیتابیس فعال باشد، مستقیماً چک کن
      if (useDatabase && data.length > 0) {
        await matchWithDatabase(data)
      } else {
        setCurrentStep(2)
      }
      
      alert(`✅ ${data.length} سفارش از PDF استخراج شد`)
    } catch (error: any) {
      console.error('❌ خطا:', error)
      
      let errorMessage = 'خطای ناشناخته در استخراج PDF'
      
      if (error.message) {
        errorMessage = error.message
      }
      
      alert(`❌ خطا در استخراج PDF:\n\n${errorMessage}\n\nلطفاً:\n• فایل PDF را بررسی کنید\n• از فرمت صحیح اطمینان حاصل کنید\n• Console را برای جزئیات بیشتر چک کنید`)
    } finally {
      setProcessing(false)
    }
  }

  // 🔥 تابع جدید: تطبیق با دیتابیس
  const matchWithDatabase = async (trackingList: TrackingData[]) => {
    setProcessing(true)
    
    try {
      console.log('🔄 در حال تطبیق با دیتابیس...')
      
      // ارسال درخواست به backend برای تطبیق
      const response = await fetch('http://localhost:8000/api/tracking/match-database', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tracking_data: trackingList })
      })

      if (!response.ok) throw new Error('خطا در تطبیق با دیتابیس')

      const matched = await response.json()
      setMatchedOrders(matched.results || [])
      setCurrentStep(3)
      
      const matchedCount = matched.results?.filter((r: any) => r.matched).length || 0
      alert(`✅ ${matchedCount} سفارش از ${trackingList.length} تطبیق یافت`)
    } catch (error) {
      console.error('خطا در تطبیق:', error)
      alert('❌ خطا در تطبیق با دیتابیس')
    } finally {
      setProcessing(false)
    }
  }

  const handleExcelUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || extractedData.length === 0) return

    // بررسی فرمت فایل
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      alert('❌ لطفاً فقط فایل Excel (.xlsx یا .xls) انتخاب کنید')
      return
    }

    setProcessing(true)

    try {
      console.log('📤 آپلود Excel:', file.name)
      
      // خواندن Excel و ارسال به backend
      const formData = new FormData()
      formData.append('excel', file)
      formData.append('tracking_data', JSON.stringify(extractedData))

      const response = await fetch('http://localhost:8000/api/tracking/match-excel', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        throw new Error(errorData?.detail || 'خطا در پردازش Excel')
      }

      const matched = await response.json()
      
      console.log('✅ تطبیق کامل:', matched)
      
      if (!matched.results || matched.results.length === 0) {
        alert('⚠️ هیچ سفارشی تطبیق نیافت!\n\nلطفاً اطمینان حاصل کنید:\n• ستون اول: کد سفارش (9 رقمی)\n• ستون دوم: شناسه محموله')
        return
      }
      
      setMatchedOrders(matched.results || [])
      setCurrentStep(3)
      
      const matchedCount = matched.results?.filter((r: any) => r.matched).length || 0
      alert(`✅ ${matchedCount} سفارش از ${matched.results.length} تطبیق یافت`)
    } catch (error: any) {
      console.error('❌ خطا:', error)
      alert(`❌ خطا در پردازش Excel:\n\n${error.message}\n\nلطفاً فرمت فایل را بررسی کنید`)
    } finally {
      setProcessing(false)
    }
  }

  const handleSubmit = async () => {
    if (matchedOrders.length === 0) return

    setProcessing(true)
    const results: any[] = []

    for (const item of matchedOrders) {
      if (!item.matched) {
        results.push({
          order_code: item.order_code,
          tracking_code: item.tracking_code,
          success: false,
          message: 'سفارش در دیتابیس یافت نشد',
        })
        continue
      }

      try {
        const response = await fetch('http://localhost:8000/api/tracking/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            order_id: item.id,
            order_code: item.order_code,
            shipment_id: item.shipment_id,
            tracking_code: item.tracking_code,
          }),
        })

        const result = await response.json()
        results.push({
          order_code: item.order_code,
          tracking_code: item.tracking_code,
          success: response.ok,
          message: result.message || 'موفق',
        })
      } catch (error) {
        results.push({
          order_code: item.order_code,
          tracking_code: item.tracking_code,
          success: false,
          message: 'خطا در ارسال',
        })
      }
    }

    setSubmitResults(results)
    setProcessing(false)
    
    const successCount = results.filter(r => r.success).length
    alert(`✅ ${successCount} از ${results.length} کد رهگیری با موفقیت ثبت شد`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <a href="/" className="text-2xl hover:text-blue-600 transition">←</a>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">🏷️ ثبت کدهای رهگیری</h1>
              <p className="text-gray-600 mt-1">استخراج از PDF و ثبت خودکار در دیتابیس</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Progress Steps */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            {[
              { num: 1, title: 'آپلود PDF رسید', icon: '📄' },
              { num: 2, title: useDatabase ? 'تطبیق با دیتابیس' : 'آپلود Excel', icon: useDatabase ? '🔍' : '📊' },
              { num: 3, title: 'ارسال به API', icon: '🚀' },
            ].map((step, idx) => (
              <div key={step.num} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold transition ${
                      currentStep >= step.num
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {currentStep > step.num ? '✓' : step.icon}
                  </div>
                  <span className="text-sm mt-2 font-medium">{step.title}</span>
                </div>
                {idx < 2 && (
                  <div
                    className={`flex-1 h-1 mx-4 transition ${
                      currentStep > step.num ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step 1: PDF Upload */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <FileText className="text-blue-600" />
            مرحله ۱: آپلود PDF رسید پستی
          </h2>
          
          {/* 🔥 انتخاب روش */}
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="font-semibold text-blue-900 mb-3">روش تطبیق سفارشات:</h3>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={useDatabase}
                  onChange={() => setUseDatabase(true)}
                  className="w-5 h-5 text-blue-600"
                />
                <div>
                  <span className="font-medium text-blue-900">🔍 دیتابیس محلی</span>
                  <p className="text-sm text-blue-700">تطبیق خودکار با سفارشات موجود در دیتابیس</p>
                </div>
              </label>
              
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={!useDatabase}
                  onChange={() => setUseDatabase(false)}
                  className="w-5 h-5 text-blue-600"
                />
                <div>
                  <span className="font-medium text-blue-900">📊 فایل Excel</span>
                  <p className="text-sm text-blue-700">استفاده از فایل Excel (روش قدیمی)</p>
                </div>
              </label>
            </div>
          </div>

          <p className="text-gray-600 mb-4">
            فایل PDF رسید پست را که شامل کدهای رهگیری است آپلود کنید
          </p>

          {/* 🔥 راهنمای فرمت */}
          <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
            <details className="cursor-pointer">
              <summary className="font-medium text-gray-700 text-sm">
                📖 راهنمای فرمت فایل PDF
              </summary>
              <div className="mt-3 text-sm text-gray-600 space-y-2">
                <p className="font-medium">فایل PDF باید شامل موارد زیر باشد:</p>
                <ul className="list-disc list-inside space-y-1 mr-4">
                  <li><strong>کد سفارش</strong>: عدد 9 رقمی (مثال: 123456789)</li>
                  <li><strong>کد رهگیری</strong>: عدد 24 رقمی (مثال: 123456789012345678901234)</li>
                  <li>بهتر است اطلاعات به صورت <strong>جدول</strong> باشد</li>
                </ul>
                <div className="mt-2 p-2 bg-blue-50 rounded text-xs">
                  <strong>نکته:</strong> سیستم هم از جداول و هم از متن معمولی PDF استخراج می‌کند
                </div>
              </div>
            </details>
          </div>
          
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition">
            <input
              type="file"
              accept=".pdf"
              onChange={handlePdfUpload}
              className="hidden"
              id="pdf-upload"
              disabled={processing}
            />
            <label
              htmlFor="pdf-upload"
              className={`cursor-pointer flex flex-col items-center ${processing ? 'opacity-50' : ''}`}
            >
              {processing ? (
                <>
                  <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mb-2"></div>
                  <span className="text-lg font-medium text-gray-700">در حال پردازش...</span>
                  <span className="text-sm text-gray-500 mt-1">لطفاً صبر کنید</span>
                </>
              ) : (
                <>
                  <Upload className="text-gray-400 mb-2" size={48} />
                  <span className="text-lg font-medium text-gray-700">
                    {pdfFile ? pdfFile.name : 'کلیک کنید یا فایل PDF را بکشید'}
                  </span>
                  <span className="text-sm text-gray-500 mt-1">
                    {pdfFile ? `${(pdfFile.size / 1024).toFixed(2)} KB` : 'PDF تا 20MB'}
                  </span>
                </>
              )}
            </label>
          </div>

          {extractedData.length > 0 && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 text-green-700">
                <CheckCircle size={20} />
                <span className="font-medium">
                  {extractedData.length} سفارش استخراج شد
                </span>
              </div>
              
              <div className="mt-3 max-h-60 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-green-100">
                    <tr>
                      <th className="p-2 text-right">کد سفارش</th>
                      <th className="p-2 text-right">کد رهگیری</th>
                    </tr>
                  </thead>
                  <tbody>
                    {extractedData.slice(0, 5).map((item, idx) => (
                      <tr key={idx} className="border-b border-green-100">
                        <td className="p-2 font-mono text-xs">{item.order_code}</td>
                        <td className="p-2 font-mono text-xs">{item.tracking_code}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {extractedData.length > 5 && (
                  <p className="text-center text-gray-500 text-xs mt-2">
                    ... و {extractedData.length - 5} سفارش دیگر
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Step 2: Database Match or Excel Upload */}
        {currentStep >= 2 && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            {useDatabase ? (
              // 🔥 نمایش نتایج تطبیق با دیتابیس
              <>
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Database className="text-green-600" />
                  مرحله ۲: نتایج تطبیق با دیتابیس
                </h2>
                
                {matchedOrders.length > 0 && (
                  <div className="space-y-4">
                    {/* آمار */}
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                        <div className="text-3xl font-bold text-blue-700">
                          {matchedOrders.length}
                        </div>
                        <div className="text-sm text-blue-600">کل سفارشات</div>
                      </div>
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                        <div className="text-3xl font-bold text-green-700">
                          {matchedOrders.filter(o => o.matched).length}
                        </div>
                        <div className="text-sm text-green-600">✓ تطبیق یافت</div>
                      </div>
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                        <div className="text-3xl font-bold text-red-700">
                          {matchedOrders.filter(o => !o.matched).length}
                        </div>
                        <div className="text-sm text-red-600">✗ یافت نشد</div>
                      </div>
                    </div>

                    {/* جدول نتایج */}
                    <div className="mt-4 max-h-96 overflow-y-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 sticky top-0">
                          <tr>
                            <th className="p-3 text-right">ردیف</th>
                            <th className="p-3 text-right">کد سفارش</th>
                            <th className="p-3 text-right">کد رهگیری</th>
                            <th className="p-3 text-right">مشتری</th>
                            <th className="p-3 text-right">شهر</th>
                            <th className="p-3 text-right">وضعیت</th>
                          </tr>
                        </thead>
                        <tbody>
                          {matchedOrders.map((order, idx) => (
                            <tr 
                              key={idx} 
                              className={`border-b ${
                                order.matched 
                                  ? 'hover:bg-green-50' 
                                  : 'bg-red-50 hover:bg-red-100'
                              }`}
                            >
                              <td className="p-3 text-gray-600">{idx + 1}</td>
                              <td className="p-3 font-mono text-xs">{order.order_code}</td>
                              <td className="p-3 font-mono text-xs">{order.tracking_code}</td>
                              <td className="p-3">{order.customer_name || '-'}</td>
                              <td className="p-3">{order.city || '-'}</td>
                              <td className="p-3">
                                {order.matched ? (
                                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs flex items-center gap-1 w-fit">
                                    <CheckCircle size={14} />
                                    تطبیق یافت
                                  </span>
                                ) : (
                                  <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs flex items-center gap-1 w-fit">
                                    <XCircle size={14} />
                                    یافت نشد
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            ) : (
              // روش قدیمی: Excel
              <>
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <FileText className="text-green-600" />
                  مرحله ۲: آپلود فایل Excel
                </h2>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="text-blue-600 flex-shrink-0 mt-0.5" size={20} />
                    <div className="text-sm text-blue-900">
                      <p className="font-semibold mb-1">فرمت Excel:</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>ستون A: کد سفارش (9 رقمی)</li>
                        <li>ستون B: شناسه محموله</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-green-400 transition">
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleExcelUpload}
                    className="hidden"
                    id="excel-upload"
                    disabled={processing || extractedData.length === 0}
                  />
                  <label
                    htmlFor="excel-upload"
                    className={`cursor-pointer flex flex-col items-center ${extractedData.length === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <Upload className="text-gray-400 mb-2" size={48} />
                    <span className="text-lg font-medium text-gray-700">
                      کلیک کنید یا فایل Excel را بکشید
                    </span>
                  </label>
                </div>

                {matchedOrders.length > 0 && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-2 text-green-700">
                      <CheckCircle size={20} />
                      <span className="font-medium">
                        {matchedOrders.length} سفارش آماده ارسال است
                      </span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Step 3: Submit */}
        {currentStep >= 3 && matchedOrders.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <CheckCircle className="text-purple-600" />
              مرحله ۳: ارسال به API دیجی‌کالا
            </h2>

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
              <p className="text-purple-900">
                <strong>{matchedOrders.filter(o => o.matched).length}</strong> کد رهگیری آماده ارسال به سرور دیجی‌کالا و ذخیره در دیتابیس است
              </p>
              {matchedOrders.filter(o => !o.matched).length > 0 && (
                <p className="text-red-700 mt-2">
                  ⚠️ <strong>{matchedOrders.filter(o => !o.matched).length}</strong> سفارش تطبیق نیافت و ارسال نمی‌شود
                </p>
              )}
            </div>

            <button
              onClick={handleSubmit}
              disabled={processing || matchedOrders.filter(o => o.matched).length === 0}
              className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium text-lg"
            >
              {processing ? (
                <>
                  <div className="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  در حال ارسال...
                </>
              ) : (
                `🚀 ارسال ${matchedOrders.filter(o => o.matched).length} کد رهگیری به دیجی‌کالا`
              )}
            </button>

            {/* Results */}
            {submitResults.length > 0 && (
              <div className="mt-6">
                <h3 className="font-bold text-gray-900 mb-3">نتایج ارسال:</h3>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-green-700">
                      {submitResults.filter(r => r.success).length}
                    </div>
                    <div className="text-sm text-green-600">موفق</div>
                  </div>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-red-700">
                      {submitResults.filter(r => !r.success).length}
                    </div>
                    <div className="text-sm text-red-600">ناموفق</div>
                  </div>
                </div>

                <div className="max-h-96 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="p-3 text-right">کد سفارش</th>
                        <th className="p-3 text-right">کد رهگیری</th>
                        <th className="p-3 text-right">وضعیت</th>
                        <th className="p-3 text-right">پیام</th>
                      </tr>
                    </thead>
                    <tbody>
                      {submitResults.map((result, idx) => (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="p-3 font-mono text-xs">{result.order_code}</td>
                          <td className="p-3 font-mono text-xs">{result.tracking_code}</td>
                          <td className="p-3">
                            {result.success ? (
                              <span className="flex items-center gap-1 text-green-600">
                                <CheckCircle size={16} />
                                موفق
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-red-600">
                                <XCircle size={16} />
                                ناموفق
                              </span>
                            )}
                          </td>
                          <td className="p-3 text-xs text-gray-600">{result.message}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}