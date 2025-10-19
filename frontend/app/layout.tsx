// frontend/app/layout.tsx
import './globals.css'
import { AuthProvider } from '@/contexts/AuthContext'

export const metadata = {
  title: 'سیستم مدیریت یکپارچه - دیجی‌کالا',
  description: 'فروش و انبارداری',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fa" dir="rtl">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}

// frontend/components/Sidebar.tsx - نسخه به‌روزرسانی شده
'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import {
  LayoutDashboard,
  Package,
  Tag,
  MessageSquare,
  FileText,
  Warehouse,
  BarChart3,
  Users,
  Settings,
  LogOut,
  ChevronDown,
  Shield
} from 'lucide-react'
import { useState } from 'react'

interface MenuItem {
  name: string
  href: string
  icon: any
  permission?: string
  children?: MenuItem[]
}

const menuItems: { title: string; items: MenuItem[] }[] = [
  {
    title: 'داشبورد',
    items: [
      { name: 'صفحه اصلی', href: '/', icon: LayoutDashboard },
    ],
  },
  {
    title: '📦 فروش',
    items: [
      { name: 'سفارشات', href: '/orders', icon: Package, permission: 'sales_view' },
      { name: 'برچسب پستی', href: '/labels', icon: FileText, permission: 'labels_view' },
      { name: 'ثبت رهگیری', href: '/tracking', icon: Tag, permission: 'tracking_view' },
      { name: 'مدیریت پیامک', href: '/sms', icon: MessageSquare, permission: 'sms_view' },
      { name: 'گزارشات', href: '/reports', icon: BarChart3, permission: 'reports_view' },
    ],
  },
  {
    title: '🏭 انبارداری',
    items: [
      { name: 'موجودی کالا', href: '/warehouse/inventory', icon: Warehouse, permission: 'warehouse_view' },
      { name: 'ورود کالا', href: '/warehouse/receive', icon: Package, permission: 'warehouse_receive' },
      { name: 'خروج کالا', href: '/warehouse/dispatch', icon: Package, permission: 'warehouse_dispatch' },
      { name: 'موجودی‌گیری', href: '/warehouse/stock-take', icon: BarChart3, permission: 'warehouse_inventory' },
    ],
  },
  {
    title: '⚙️ مدیریت',
    items: [
      { name: 'کاربران', href: '/admin/users', icon: Users, permission: 'users_view' },
      { name: 'نقش‌ها', href: '/admin/roles', icon: Shield, permission: 'users_view' },
      { name: 'تنظیمات', href: '/settings', icon: Settings, permission: 'settings_view' },
    ],
  },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, logout, hasPermission } = useAuth()
  const [expandedSections, setExpandedSections] = useState<string[]>(['داشبورد', '📦 فروش'])

  const toggleSection = (title: string) => {
    setExpandedSections(prev =>
      prev.includes(title)
        ? prev.filter(t => t !== title)
        : [...prev, title]
    )
  }

  const handleLogout = () => {
    if (confirm('آیا مطمئن هستید که می‌خواهید خارج شوید؟')) {
      logout()
    }
  }

  if (!user) return null

  return (
    <aside className="w-64 bg-white border-l border-gray-200 flex flex-col h-screen">
      {/* Logo & User Info */}
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold text-blue-600">🛍️ دیجی‌کالا</h1>
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
              {user.full_name.charAt(0)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-900 truncate">{user.full_name}</p>
              <p className="text-xs text-gray-500 truncate">@{user.username}</p>
            </div>
          </div>
          {user.is_superuser && (
            <div className="mt-2 px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full text-center">
              ⭐ ادمین کل
            </div>
          )}
        </div>
      </div>

      {/* Menu */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-2">
        {menuItems.map((section) => {
          const isExpanded = expandedSections.includes(section.title)
          const visibleItems = section.items.filter(item => 
            !item.permission || hasPermission(item.permission)
          )

          if (visibleItems.length === 0) return null

          return (
            <div key={section.title}>
              <button
                onClick={() => toggleSection(section.title)}
                className="w-full flex items-center justify-between px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 rounded-lg transition"
              >
                <span>{section.title}</span>
                <ChevronDown 
                  size={16} 
                  className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                />
              </button>

              {isExpanded && (
                <div className="mt-1 space-y-1">
                  {visibleItems.map((item) => {
                    const Icon = item.icon
                    const isActive = pathname === item.href

                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={`flex items-center gap-3 px-4 py-2.5 text-sm rounded-lg transition ${
                          isActive
                            ? 'bg-blue-50 text-blue-700 font-medium'
                            : 'text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        <Icon size={18} />
                        {item.name}
                      </Link>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-gray-200">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition"
        >
          <LogOut size={18} />
          خروج از سیستم
        </button>
      </div>
    </aside>
  )
}

// frontend/app/page.tsx - به‌روزرسانی با Auth
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
      <h3 className="text-3xl font-bold mb-1">{value.toLocaleString('fa-IR')}</h3>
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