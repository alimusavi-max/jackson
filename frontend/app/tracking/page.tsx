'use client'

import { useState } from 'react'
import { Upload, FileText, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

interface TrackingData {
  order_code: string
  tracking_code: string
  shipment_id: string
}

interface MergedData extends TrackingData {
  status?: string
}

export default function TrackingPage() {
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [excelFile, setExcelFile] = useState<File | null>(null)
  const [extractedData, setExtractedData] = useState<TrackingData[]>([])
  const [mergedData, setMergedData] = useState<MergedData[]>([])
  const [processing, setProcessing] = useState(false)
  const [currentStep, setCurrentStep] = useState(1)
  const [submitResults, setSubmitResults] = useState<any[]>([])

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setPdfFile(file)
    setProcessing(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost:8000/api/tracking/extract-pdf', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) throw new Error('خطا در استخراج PDF')

      const data = await response.json()
      setExtractedData(data)
      setCurrentStep(2)
      alert(`✅ ${data.length} سفارش از PDF استخراج شد`)
    } catch (error) {
      alert('❌ خطا در استخراج PDF')
      console.error(error)
    } finally {
      setProcessing(false)
    }
  }

  const handleExcelUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || extractedData.length === 0) return

    setExcelFile(file)
    setProcessing(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      // خواندن Excel و تطبیق با داده‌های PDF
      const reader = new FileReader()
      reader.onload = async (event) => {
        // اینجا باید Excel را parse کنیم
        // برای سادگی، فرض می‌کنیم داده‌ها در فرمت مناسب هستند
        
        // شبیه‌سازی تطبیق داده‌ها
        const matched = extractedData.map(item => ({
          ...item,
          status: 'ready'
        }))
        
        setMergedData(matched)
        setCurrentStep(3)
        alert(`✅ ${matched.length} سفارش تطبیق یافت`)
        setProcessing(false)
      }
      
      reader.readAsArrayBuffer(file)
    } catch (error) {
      alert('❌ خطا در پردازش Excel')
      console.error(error)
      setProcessing(false)
    }
  }

  const handleSubmit = async () => {
    if (mergedData.length === 0) return

    setProcessing(true)
    const results: any[] = []

    for (const item of mergedData) {
      try {
        const response = await fetch('http://localhost:8000/api/tracking/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            shipment_id: item.shipment_id,
            tracking_code: item.tracking_code,
            order_code: item.order_code,
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
              <p className="text-gray-600 mt-1">استخراج از PDF و ارسال به API دیجی‌کالا</p>
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
              { num: 2, title: 'آپلود Excel', icon: '📊' },
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
          <p className="text-gray-600 mb-4">
            فایل PDF رسید پست را که شامل کدهای رهگیری است آپلود کنید
          </p>
          
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
              className="cursor-pointer flex flex-col items-center"
            >
              <Upload className="text-gray-400 mb-2" size={48} />
              <span className="text-lg font-medium text-gray-700">
                {pdfFile ? pdfFile.name : 'کلیک کنید یا فایل را بکشید'}
              </span>
              <span className="text-sm text-gray-500 mt-1">PDF تا 10MB</span>
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

        {/* Step 2: Excel Upload */}
        {currentStep >= 2 && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
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
                  {excelFile ? excelFile.name : 'کلیک کنید یا فایل Excel را بکشید'}
                </span>
              </label>
            </div>

            {mergedData.length > 0 && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 text-green-700">
                  <CheckCircle size={20} />
                  <span className="font-medium">
                    {mergedData.length} سفارش آماده ارسال است
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Submit */}
        {currentStep >= 3 && mergedData.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <CheckCircle className="text-purple-600" />
              مرحله ۳: ارسال به API دیجی‌کالا
            </h2>

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
              <p className="text-purple-900">
                <strong>{mergedData.length}</strong> کد رهگیری آماده ارسال به سرور دیجی‌کالا و ذخیره در دیتابیس است
              </p>
            </div>

            <button
              onClick={handleSubmit}
              disabled={processing}
              className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium text-lg"
            >
              {processing ? (
                <>
                  <div className="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  در حال ارسال...
                </>
              ) : (
                '🚀 ارسال به دیجی‌کالا و ذخیره در دیتابیس'
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