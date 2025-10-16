'use client'

import { useState, useEffect } from 'react'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, Package, MapPin, DollarSign, Calendar, Download } from 'lucide-react'

interface Stats {
  totalOrders: number
  totalRevenue: number
  uniqueCustomers: number
  uniqueProducts: number
  topCities: { name: string; count: number }[]
  topProducts: { name: string; quantity: number; revenue: number }[]
  statusDistribution: { name: string; value: number }[]
  dailySales: { date: string; amount: number; orders: number }[]
}

export default function ReportsPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [dateRange, setDateRange] = useState('30') // days

  useEffect(() => {
    loadStats()
  }, [dateRange])

  const loadStats = async () => {
    try {
      setLoading(true)
      const response = await fetch(`http://localhost:8000/api/reports/stats?days=${dateRange}`)
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('خطا در دریافت آمار:', error)
    } finally {
      setLoading(false)
    }
  }

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">در حال بارگذاری آمار...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <a href="/" className="text-2xl hover:text-blue-600 transition">←</a>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">📊 گزارشات و آمار</h1>
                <p className="text-gray-600 mt-1">تحلیل جامع فروش و عملکرد</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="7">7 روز اخیر</option>
                <option value="30">30 روز اخیر</option>
                <option value="90">3 ماه اخیر</option>
                <option value="365">یک سال اخیر</option>
              </select>
              <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center gap-2">
                <Download size={18} />
                دانلود گزارش
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1800px] mx-auto px-6 py-8">
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <Package size={32} />
              <div className="text-right">
                <p className="text-blue-100 text-sm">کل سفارشات</p>
                <h3 className="text-3xl font-bold mt-1">
                  {stats?.totalOrders.toLocaleString('fa-IR')}
                </h3>
              </div>
            </div>
            <div className="flex items-center gap-2 text-blue-100 text-sm">
              <TrendingUp size={16} />
              <span>12% افزایش نسبت به ماه قبل</span>
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <DollarSign size={32} />
              <div className="text-right">
                <p className="text-green-100 text-sm">مجموع فروش</p>
                <h3 className="text-3xl font-bold mt-1">
                  {((stats?.totalRevenue || 0) / 1000000).toFixed(1)}M
                </h3>
              </div>
            </div>
            <div className="flex items-center gap-2 text-green-100 text-sm">
              <TrendingUp size={16} />
              <span>{stats?.totalRevenue.toLocaleString('fa-IR')} تومان</span>
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <Package size={32} />
              <div className="text-right">
                <p className="text-purple-100 text-sm">مشتریان منحصر به فرد</p>
                <h3 className="text-3xl font-bold mt-1">
                  {stats?.uniqueCustomers.toLocaleString('fa-IR')}
                </h3>
              </div>
            </div>
            <div className="flex items-center gap-2 text-purple-100 text-sm">
              <TrendingUp size={16} />
              <span>8% افزایش</span>
            </div>
          </div>

          <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <Package size={32} />
              <div className="text-right">
                <p className="text-orange-100 text-sm">تنوع محصولات</p>
                <h3 className="text-3xl font-bold mt-1">
                  {stats?.uniqueProducts.toLocaleString('fa-IR')}
                </h3>
              </div>
            </div>
            <div className="flex items-center gap-2 text-orange-100 text-sm">
              <Package size={16} />
              <span>محصولات فعال</span>
            </div>
          </div>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Daily Sales Chart */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Calendar className="text-blue-600" />
              روند فروش روزانه
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={stats?.dailySales || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="amount" stroke="#3b82f6" strokeWidth={2} name="مبلغ (تومان)" />
                <Line type="monotone" dataKey="orders" stroke="#10b981" strokeWidth={2} name="تعداد سفارش" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Status Distribution */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Package className="text-green-600" />
              توزیع وضعیت سفارشات
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={stats?.statusDistribution || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {stats?.statusDistribution?.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Top Cities */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <MapPin className="text-purple-600" />
              پرفروش‌ترین شهرها
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stats?.topCities || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8b5cf6" name="تعداد سفارش" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Top Products */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Package className="text-orange-600" />
              پرفروش‌ترین محصولات
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stats?.topProducts || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={150} />
                <Tooltip />
                <Bar dataKey="quantity" fill="#f59e0b" name="تعداد فروش" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Detailed Tables */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Products Table */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">محصولات پرفروش (جدول)</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-right">رتبه</th>
                    <th className="px-4 py-3 text-right">محصول</th>
                    <th className="px-4 py-3 text-right">تعداد</th>
                    <th className="px-4 py-3 text-right">فروش (تومان)</th>
                  </tr>
                </thead>
                <tbody>
                  {stats?.topProducts?.slice(0, 10).map((product, idx) => (
                    <tr key={idx} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3 font-bold text-gray-600">{idx + 1}</td>
                      <td className="px-4 py-3">{product.name}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-bold">
                          {product.quantity}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-bold text-green-600">
                        {product.revenue.toLocaleString('fa-IR')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Top Cities Table */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">شهرهای برتر (جدول)</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-right">رتبه</th>
                    <th className="px-4 py-3 text-right">شهر</th>
                    <th className="px-4 py-3 text-right">تعداد سفارش</th>
                    <th className="px-4 py-3 text-right">سهم (%)</th>
                  </tr>
                </thead>
                <tbody>
                  {stats?.topCities?.slice(0, 10).map((city, idx) => {
                    const percentage = ((city.count / (stats?.totalOrders || 1)) * 100).toFixed(1)
                    return (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="px-4 py-3 font-bold text-gray-600">{idx + 1}</td>
                        <td className="px-4 py-3 font-medium">{city.name}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-bold">
                            {city.count}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-purple-600 h-2 rounded-full"
                                style={{ width: `${percentage}%` }}
                              />
                            </div>
                            <span className="text-xs font-medium">{percentage}%</span>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}