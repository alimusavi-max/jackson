// ============= frontend/components/Sidebar.tsx =============
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Package,
  Tag,
  MessageSquare,
  FileText,
  Warehouse,
  DollarSign,
  Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const menuItems = [
  {
    title: 'فروش',
    items: [
      { name: 'داشبورد', href: '/', icon: LayoutDashboard },
      { name: 'سفارشات', href: '/orders', icon: Package },
      { name: 'ثبت رهگیری', href: '/tracking', icon: Tag },
      { name: 'مدیریت پیامک', href: '/sms', icon: MessageSquare },
      { name: 'برچسب پستی', href: '/labels', icon: FileText },
    ],
  },
  {
    title: 'انبار',
    items: [
      { name: 'موجودی', href: '/warehouse', icon: Warehouse, disabled: true },
    ],
  },
  {
    title: 'حسابداری',
    items: [
      { name: 'فاکتورها', href: '/accounting', icon: DollarSign, disabled: true },
    ],
  },
  {
    title: 'تنظیمات',
    items: [
      { name: 'تنظیمات', href: '/settings', icon: Settings },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white border-l border-slate-200 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-slate-200">
        <h1 className="text-2xl font-bold text-slate-900">
          🛍️ دیجی‌کالا
        </h1>
        <p className="text-sm text-slate-500 mt-1">سیستم مدیریت یکپارچه</p>
      </div>

      {/* Menu */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-6">
        {menuItems.map((section) => (
          <div key={section.title}>
            <h3 className="text-xs font-semibold text-slate-400 uppercase mb-3">
              {section.title}
            </h3>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                const isDisabled = item.disabled;

                return (
                  <li key={item.href}>
                    <Link
                      href={isDisabled ? '#' : item.href}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-blue-50 text-blue-700'
                          : isDisabled
                          ? 'text-slate-300 cursor-not-allowed'
                          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                      )}
                      onClick={(e) => isDisabled && e.preventDefault()}
                    >
                      <Icon size={18} />
                      {item.name}
                      {isDisabled && (
                        <span className="mr-auto text-xs bg-slate-100 px-2 py-0.5 rounded">
                          به زودی
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-200">
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-3 rounded-lg">
          <p className="text-xs font-medium text-slate-700">
            نسخه 2.0.0
          </p>
          <p className="text-xs text-slate-500 mt-1">
            ساخته شده با ❤️
          </p>
        </div>
      </div>
    </aside>
  );
}