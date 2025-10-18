'use client'

import { useState } from 'react'
import { Upload, FileText, CheckCircle, XCircle, AlertCircle, Database, AlertTriangle } from 'lucide-react'

interface TrackingData {
  order_code: string
  tracking_code: string
}

interface MatchedOrder extends TrackingData {
  id?: number
  customer_name?: string
  city?: string
  status?: string
  shipment_id?: string
  matched?: boolean
  reason?: string
}

export default function TrackingPage() {
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [extractedData, setExtractedData] = useState<TrackingData[]>([])
  const [matchedOrders, setMatchedOrders] = useState<MatchedOrder[]>([])
  const [processing, setProcessing] = useState(false)
  const [currentStep, setCurrentStep] = useState(1)
  const [useDatabase, setUseDatabase] = useState(true)

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('❌ لطفاً فقط فایل PDF انتخاب کنید')
      return
    }

    setPdfFile(file)
    setProcessing(true)
    setExtractedData([])
    setMatchedOrders([])

    try {
      console.log('📤 آپلود PDF:', file.name)
      
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost:8000/api/tracking/extract-pdf', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`خطای سرور: ${response.status}`)
      }

      const data = await response.json()
      
      console.log('✅ داده دریافت شد:', data)
      
      if (!data || data.length === 0) {
        alert('⚠️ هیچ کد رهگیری در PDF یافت نشد!')
        setProcessing(false)
        return
      }
      
      setExtractedData(data)
      
      // اگر دیتابیس فعاله، مستقیماً تطبیق بده
      if (useDatabase && data.length > 0) {
        await matchWithDatabase(data)
      } else {
        setCurrentStep(2)
      }
      
      alert(`✅ ${data.length} سفارش از PDF استخراج شد`)
    } catch (error: any) {
      console.error('❌ خطا:', error)
      alert(`❌ خطا در استخراج PDF:\n\n${error.message}`)
    } finally {
      setProcessing(false)
    }
  }

  const matchWithDatabase = async (trackingList: TrackingData[]) => {
    setProcessing(true)
    
    try {
      console.log('🔄 تطبیق با دیتابیس...')
      
      const response = await fetch('http://localhost:8000/api/tracking/match-database', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tracking_data: trackingList })
      })

      if (!response.ok) throw new Error('خطا در تطبیق')

      const data = await response.json()
      setMatchedOrders(data.results || [])
      setCurrentStep(3)
      
      alert(`✅ ${data.matched} سفارش تطبیق یافت\n⚠️ ${data.unmatched} سفارش یافت نشد`)
    } catch (error) {
      console.error('خطا:', error)
      alert('❌ خطا در تطبیق با دیتابیس')
    } finally {
      setProcessing(false)
    }
  }

  const handleExcelUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || extractedData.length === 0) return

    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      alert('❌ لطفاً فقط فایل Excel انتخاب کنید')
      return
    }

    setProcessing(true)

    try {
      console.log('📤 آپلود Excel:', file.name)
      
      const formData = new FormData()
      formData.append('excel', file)
      formData.append('tracking_data', JSON.stringify(extractedData))

      const response = await fetch('http://localhost:8000/api/tracking/match-excel', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) throw new Error('خطا در پردازش Excel')

      const data = await response.json()
      
      console.log('✅ تطبیق کامل:', data)
      
      setMatchedOrders(data.results || [])
      setCurrentStep(3)
      
      alert(`✅ ${data.matched} سفارش تطبیق یافت\n⚠️ ${data.unmatched} سفارش یافت نشد`)
    } catch (error: any) {
      console.error('❌ خطا:', error)
      alert(`❌ خطا:\n\n${error.message}`)
    } finally {
      setProcessing(false)
    }
  }

  const handleSubmit = async (orderId: number, trackingCode: string) => {
    try {
      const formData = new FormData()
      formData.append('order_id', orderId.toString())
      formData.append('tracking_code', trackingCode)

      const response = await fetch('http://localhost:8000/api/tracking/submit', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) throw new Error('خطا در ثبت')

      alert('✅ کد رهگیری ثبت شد')
      
      // به‌روزرسانی لیست
      setMatchedOrders(prev => prev.map(o => 
        o.id === orderId ? { ...o, submitted: true } : o
      ))
    } catch (error) {
      alert('❌ خطا در ثبت کد رهگیری')
    }
  }

  const matchedCount = matchedOrders.filter(o => o.matched).length
  const unmatchedCount = matchedOrders.length - matchedCount

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <a href="/" className="text-2xl hover:text-blue-600 transition">←</a>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">🏷️ ثبت کدهای رهگیری</h1>
              <p className="text-gray-600 mt-1">استخراج از PDF و ثبت خودکار</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Progress */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            {[
              { num: 1, title: 'آپلود PDF', icon: '📄' },
              { num: 2, title: useDatabase ? 'تطبیق دیتابیس' : 'آپلود Excel', icon: useDatabase ? '🔍' : '📊' },
              { num: 3, title: 'ثبت نهایی', icon: '✅' },
            ].map((step, idx) => (
              <div key={step.num} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold ${
                    currentStep >= step.num ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
                  }`}>
                    {currentStep > step.num ? '✓' : step.icon}
                  </div>
                  <span className="text-sm mt-2 font-medium">{step.title}</span>
                </div>
                {idx < 2 && (
                  <div className={`flex-1 h-1 mx-4 ${currentStep > step.num ? 'bg-blue-600' : 'bg-gray-200'}`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step 1: PDF */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <FileText className="text-blue-600" />
            مرحله ۱: آپلود PDF رسید پستی
          </h2>
          
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="font-semibold text-blue-900 mb-3">روش تطبیق:</h3>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={useDatabase}
                  onChange={() => setUseDatabase(true)}
                  className="w-5 h-5 text-blue-600"
                />
                <div>
                  <span className="font-medium text-blue-900">🔍 دیتابیس</span>
                  <p className="text-sm text-blue-700">تطبیق خودکار</p>
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
                  <span className="font-medium text-blue-900">📊 Excel</span>
                  <p className="text-sm text-blue-700">روش قدیمی</p>
                </div>
              </label>
            </div>
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
            <label htmlFor="pdf-upload" className={`cursor-pointer flex flex-col items-center ${processing ? 'opacity-50' : ''}`}>
              {processing ? (
                <>
                  <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mb-2"></div>
                  <span className="text-lg font-medium text-gray-700">در حال پردازش...</span>
                </>
              ) : (
                <>
                  <Upload className="text-gray-400 mb-2" size={48} />
                  <span className="text-lg font-medium text-gray-700">
                    {pdfFile ? pdfFile.name : 'کلیک کنید یا PDF بکشید'}
                  </span>
                </>
              )}
            </label>
          </div>

          {extractedData.length > 0 && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 text-green-700 mb-3">
                <CheckCircle size={20} />
                <span className="font-medium">{extractedData.length} سفارش استخراج شد</span>
              </div>
              <div className="max-h-40 overflow-y-auto">
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

        {/* Step 2: Excel (اگر دیتابیس فعال نباشه) */}
        {currentStep >= 2 && !useDatabase && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <h2 className="text-xl font-bold mb-4">📊 مرحله ۲: آپلود Excel</h2>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-yellow-900">
                <strong>فرمت:</strong> ستون A = کد سفارش، ستون B = شناسه محموله
              </p>
            </div>
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleExcelUpload}
              className="w-full px-4 py-3 border-2 border-dashed rounded-lg cursor-pointer hover:border-green-400"
            />
          </div>
        )}

        {/* Step 3: Results */}
        {currentStep >= 3 && matchedOrders.length > 0 && (
          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-blue-700">{matchedOrders.length}</div>
                <div className="text-sm text-blue-600">کل</div>
              </div>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-green-700">{matchedCount}</div>
                <div className="text-sm text-green-600">✓ تطبیق یافت</div>
              </div>
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-red-700">{unmatchedCount}</div>
                <div className="text-sm text-red-600">✗ یافت نشد</div>
              </div>
            </div>

            {/* سفارشات تطبیق یافته */}
            {matchedCount > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-bold text-green-700 mb-4 flex items-center gap-2">
                  <CheckCircle size={20} />
                  سفارشات تطبیق یافته ({matchedCount})
                </h3>
                <div className="overflow-x-auto max-h-96">
                  <table className="w-full text-sm">
                    <thead className="bg-green-50 sticky top-0">
                      <tr>
                        <th className="p-3 text-right">ردیف</th>
                        <th className="p-3 text-right">کد سفارش</th>
                        <th className="p-3 text-right">کد رهگیری</th>
                        <th className="p-3 text-right">مشتری</th>
                        <th className="p-3 text-right">شهر</th>
                        <th className="p-3 text-right">عملیات</th>
                      </tr>
                    </thead>
                    <tbody>
                      {matchedOrders
                        .filter(o => o.matched)
                        .map((order, idx) => (
                          <tr key={idx} className="border-b hover:bg-green-50">
                            <td className="p-3 text-gray-600">{idx + 1}</td>
                            <td className="p-3 font-mono text-xs">{order.order_code}</td>
                            <td className="p-3 font-mono text-xs">{order.tracking_code}</td>
                            <td className="p-3">{order.customer_name}</td>
                            <td className="p-3">{order.city}</td>
                            <td className="p-3">
                              <button
                                onClick={() => handleSubmit(order.id!, order.tracking_code)}
                                className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                              >
                                ثبت
                              </button>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* سفارشات یافت نشده */}
            {unmatchedCount > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-bold text-red-700 mb-4 flex items-center gap-2">
                  <AlertTriangle size={20} />
                  سفارشات یافت نشده ({unmatchedCount})
                </h3>
                <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="text-yellow-600 flex-shrink-0 mt-0.5" size={20} />
                    <div className="text-sm text-yellow-900">
                      <p className="font-semibold mb-1">⚠️ توجه:</p>
                      <p>این سفارشات در {useDatabase ? 'دیتابیس' : 'Excel'} یافت نشدند. می‌توانید اطلاعات آنها را به صورت دستی بررسی کنید.</p>
                    </div>
                  </div>
                </div>
                <div className="overflow-x-auto max-h-96">
                  <table className="w-full text-sm">
                    <thead className="bg-red-50 sticky top-0">
                      <tr>
                        <th className="p-3 text-right">ردیف</th>
                        <th className="p-3 text-right">کد سفارش</th>
                        <th className="p-3 text-right">کد رهگیری</th>
                        <th className="p-3 text-right">دلیل</th>
                      </tr>
                    </thead>
                    <tbody>
                      {matchedOrders
                        .filter(o => !o.matched)
                        .map((order, idx) => (
                          <tr key={idx} className="border-b hover:bg-red-50">
                            <td className="p-3 text-gray-600">{idx + 1}</td>
                            <td className="p-3 font-mono text-xs font-bold text-red-700">
                              {order.order_code}
                            </td>
                            <td className="p-3 font-mono text-xs">{order.tracking_code}</td>
                            <td className="p-3">
                              <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">
                                {order.reason === 'not_in_excel' 
                                  ? 'در Excel نبود' 
                                  : 'در دیتابیس نبود'}
                              </span>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* دکمه ثبت همه */}
            {matchedCount > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <button
                  onClick={() => {
                    matchedOrders
                      .filter(o => o.matched && o.id)
                      .forEach(o => handleSubmit(o.id!, o.tracking_code))
                  }}
                  className="w-full px-6 py-3 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg hover:from-green-700 hover:to-blue-700 transition font-medium text-lg"
                >
                  🚀 ثبت همه کدهای رهگیری ({matchedCount})
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}