// frontend/app/admin/users/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import { Users, UserPlus, Shield, Edit, Trash2, CheckCircle, XCircle } from 'lucide-react'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  phone: string | null
  is_active: boolean
  is_superuser: boolean
  roles: string[]
  permissions: string[]
  created_at: string
  last_login: string | null
}

interface Role {
  id: number
  name: string
  display_name: string
  description: string
  permissions: Array<{
    name: string
    display_name: string
    category: string
  }>
}

export default function UsersManagementPage() {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)

  useEffect(() => {
    loadUsers()
    loadRoles()
  }, [])

  const loadUsers = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch('http://localhost:8000/api/auth/users', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setUsers(data)
      }
    } catch (error) {
      console.error('خطا در دریافت کاربران:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadRoles = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch('http://localhost:8000/api/auth/roles', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setRoles(data)
      }
    } catch (error) {
      console.error('خطا در دریافت نقش‌ها:', error)
    }
  }

  const deleteUser = async (userId: number) => {
    if (!confirm('آیا مطمئن هستید؟')) return

    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch(`http://localhost:8000/api/auth/users/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        alert('✅ کاربر حذف شد')
        loadUsers()
      } else {
        const error = await response.json()
        alert(`❌ ${error.detail}`)
      }
    } catch (error) {
      alert('❌ خطا در حذف کاربر')
    }
  }

  return (
    <ProtectedRoute requiredPermission="users_view">
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
        {/* Header */}
        <header className="bg-white shadow-sm border-b sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <a href="/" className="text-2xl hover:text-blue-600 transition">←</a>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <Users className="text-blue-600" />
                    مدیریت کاربران
                  </h1>
                  <p className="text-gray-600 mt-1">
                    {users.length} کاربر | {users.filter(u => u.is_active).length} فعال
                  </p>
                </div>
              </div>

              {currentUser?.permissions.includes('users_create') && (
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
                >
                  <UserPlus size={20} />
                  کاربر جدید
                </button>
              )}
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-6 py-8">
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">کل کاربران</p>
                  <h3 className="text-3xl font-bold text-gray-900 mt-1">{users.length}</h3>
                </div>
                <Users className="text-blue-600" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">کاربران فعال</p>
                  <h3 className="text-3xl font-bold text-green-600 mt-1">
                    {users.filter(u => u.is_active).length}
                  </h3>
                </div>
                <CheckCircle className="text-green-600" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">غیرفعال</p>
                  <h3 className="text-3xl font-bold text-red-600 mt-1">
                    {users.filter(u => !u.is_active).length}
                  </h3>
                </div>
                <XCircle className="text-red-600" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">ادمین‌ها</p>
                  <h3 className="text-3xl font-bold text-purple-600 mt-1">
                    {users.filter(u => u.is_superuser).length}
                  </h3>
                </div>
                <Shield className="text-purple-600" size={32} />
              </div>
            </div>
          </div>

          {/* Users Table */}
          <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="p-6 border-b">
              <h2 className="text-xl font-bold text-gray-900">لیست کاربران</h2>
            </div>

            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto"></div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        کاربر
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        نقش‌ها
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        وضعیت
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        آخرین ورود
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        عملیات
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {users.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div>
                            <div className="font-medium text-gray-900">
                              {user.full_name}
                              {user.is_superuser && (
                                <span className="ml-2 px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                                  ادمین
                                </span>
                              )}
                            </div>
                            <div className="text-sm text-gray-500">@{user.username}</div>
                            <div className="text-sm text-gray-500">{user.email}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-wrap gap-1">
                            {user.roles.map((role, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                              >
                                {role}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          {user.is_active ? (
                            <span className="px-3 py-1 bg-green-100 text-green-800 text-xs rounded-full flex items-center gap-1 w-fit">
                              <CheckCircle size={14} />
                              فعال
                            </span>
                          ) : (
                            <span className="px-3 py-1 bg-red-100 text-red-800 text-xs rounded-full flex items-center gap-1 w-fit">
                              <XCircle size={14} />
                              غیرفعال
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {user.last_login 
                            ? new Date(user.last_login).toLocaleDateString('fa-IR')
                            : 'هرگز'
                          }
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            {currentUser?.permissions.includes('users_edit') && (
                              <button
                                onClick={() => setSelectedUser(user)}
                                className="p-2 text-blue-600 hover:bg-blue-50 rounded transition"
                                title="ویرایش"
                              >
                                <Edit size={18} />
                              </button>
                            )}
                            
                            {currentUser?.permissions.includes('users_delete') && 
                             !user.is_superuser && 
                             user.id !== currentUser?.id && (
                              <button
                                onClick={() => deleteUser(user.id)}
                                className="p-2 text-red-600 hover:bg-red-50 rounded transition"
                                title="حذف"
                              >
                                <Trash2 size={18} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Roles Summary */}
          <div className="mt-6 bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Shield className="text-purple-600" />
              نقش‌های سیستم
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {roles.map((role) => (
                <div key={role.id} className="border rounded-lg p-4">
                  <h3 className="font-bold text-gray-900">{role.display_name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{role.description}</p>
                  <div className="mt-3">
                    <span className="text-xs text-gray-500">
                      {role.permissions.length} مجوز
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}