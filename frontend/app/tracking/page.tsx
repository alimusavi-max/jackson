'use client'

import { useState } from 'react'
import { Printer, Download, FileText, AlertCircle } from 'lucide-react'

export default function LabelsPage() {
  const [selectedOrders, setSelectedOrders] = useState<number[]>([])
  const [isGenerating, setIsGenerating] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <a href="/" className="text-2xl hover:text-blue-600 transition">←</a>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">🏷️ ساخت برچسب پستی</h1>
              <p className="text-gray-600 mt-1">ایجاد برچسب‌های پستی برای سفارشات</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Coming Soon Notice */}
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-200 rounded-2xl shadow-lg p-12 text-center">
          <div className="flex flex-col items-center gap-6">
            <div className="w-32 h-32 bg-amber-100 rounded-full flex items-center justify-center">
              <Printer size={64} className="text-amber-600" />
            </div>
            
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                قابلیت ساخت برچسب پستی
              </h2>
              <p className="text-lg text-gray-600 mb-2">
                این قابلیت در نسخه بعدی اضافه خواهد شد
              </p>
              <p className="text-gray-500">
                شامل: QR Code، Barcode، Data Matrix، اطلاعات فرستنده و گیرنده
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-md w-full max-w-2xl text-right">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <FileText className="text-blue-600" />
                امکانات در دست توسعه:
              </h3>
              <ul className="space-y-3 text-gray-700">
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 font-bold">•</span>
                  <span>ساخت برچسب با QR Code و Barcode</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 font-bold">•</span>
                  <span>پشتیبانی از Data Matrix برای اطلاعات کامل</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 font-bold">•</span>
                  <span>انتخاب پروفایل فرستنده</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 font-bold">•</span>
                  <span>چاپ چندتایی (2 برچسب در هر صفحه A4)</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 font-bold">•</span>
                  <span>دانلود PDF برچسب‌ها</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-600 font-bold">•</span>
                  <span>حالت عمودی و افقی</span>
                </li>
              </ul>
            </div>

            <div className="flex gap-4">
              <a
                href="/orders"
                className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
              >
                📋 مشاهده سفارشات
              </a>
              <a
                href="/"
                className="px-8 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
              >
                🏠 بازگشت به داشبورد
              </a>
            </div>
          </div>
        </div>

        {/* Preview */}
        <div className="mt-8 bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">پیش‌نمایش برچسب</h3>
          <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center">
            <div className="text-gray-400 text-6xl mb-4">🏷️</div>
            <p className="text-gray-500">پیش‌نمایش برچسب در این قسمت نمایش داده خواهد شد</p>
          </div>
        </div>
      </main>
    </div>
  )
}