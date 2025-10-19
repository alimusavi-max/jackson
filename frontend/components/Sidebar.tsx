// frontend/components/Sidebar.tsx
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