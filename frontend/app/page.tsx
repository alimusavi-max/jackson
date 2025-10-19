// frontend/app/page.tsx
'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import Sidebar from '@/components/Sidebar'
import { Package, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react'

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/stats')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('خطا:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-gray-50" dir="rtl">
        <Sidebar />
        
        <main className="flex-1 overflow-y-auto">
          {/* Header */}
          <header className="bg-white shadow-sm border-b">
            <div className="px-8 py-6">
              <h1 className="text-3xl font-bold text-gray-900">
                خوش آمدید، {user?.full_name}! 👋
              </h1>
              <p className="text-gray-600 mt-2">
                نمای کلی عملکرد سیستم
              </p>
            </div>
          </header>

          <div className="p-8">
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto"></div>
              </div>
            ) : (
              <>
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  <StatCard
                    title="کل سفارشات"
                    value={stats?.total_orders || 0}
                    icon={Package}
                    color="blue"
                  />
                  <StatCard
                    title="دارای کد رهگیری"
                    value={stats?.orders_with_tracking || 0}
                    icon={CheckCircle}
                    color="green"
                  />
                  <StatCard
                    title="بدون کد رهگیری"
                    value={stats?.orders_without_tracking || 0}
                    icon={AlertCircle}
                    color="orange"
                  />
                  <StatCard
                    title="مجموع فروش"
                    value={`${((stats?.total_sales || 0) / 1000000).toFixed(1)}M`}
                    icon={TrendingUp}
                    color="purple"
                  />
                </div>

                {/* Quick Actions */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">⚡ دسترسی سریع</h2>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {user?.permissions.includes('sales_view') && (
                      <QuickAction href="/orders" icon="📋" label="سفارشات" />
                    )}
                    {user?.permissions.includes('labels_view') && (
                      <QuickAction href="/labels" icon="🏷️" label="برچسب پستی" />
                    )}
                    {user?.permissions.includes('tracking_view') && (
                      <QuickAction href="/tracking" icon="📮" label="کد رهگیری" />
                    )}
                    {user?.permissions.includes('warehouse_view') && (
                      <QuickAction href="/warehouse/inventory" icon="🏭" label="موجودی انبار" />
                    )}
                    {user?.permissions.includes('users_view') && (
                      <QuickAction href="/admin/users" icon="👥" label="کاربران" />
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}

function StatCard({ title, value, icon: Icon, color }: any) {
  const colors = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600',
    purple: 'from-purple-500 to-purple-600',
  }

  return (
    <div className={`bg-gradient-to-br ${colors[color as keyof typeof colors]} rounded-2xl shadow-lg p-6 text-white`}>
      <div className="flex items-center justify-between mb-4">
        <Icon size={32} className="opacity-80" />
      </div>
      <h3 className="text-3xl font-bold mb-1">{typeof value === 'number' ? value.toLocaleString('fa-IR') : value}</h3>
      <p className="text-sm opacity-90">{title}</p>
    </div>
  )
}

function QuickAction({ href, icon, label }: any) {
  return (
    <a
      href={href}
      className="p-4 border-2 border-gray-200 rounded-xl hover:border-blue-400 hover:bg-blue-50 transition text-center block"
    >
      <div className="text-3xl mb-2">{icon}</div>
      <div className="font-medium text-gray-700 text-sm">{label}</div>
    </a>
  )
}