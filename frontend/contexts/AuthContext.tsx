// frontend/contexts/AuthContext.tsx
'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  is_superuser: boolean
  roles: string[]
  permissions: string[]
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  hasPermission: (permission: string) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // بارگذاری کاربر از localStorage
    const token = localStorage.getItem('auth_token')
    if (token) {
      loadUser(token)
    } else {
      setLoading(false)
    }
  }, [])

  const loadUser = async (token: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        // Token نامعتبر است
        localStorage.removeItem('auth_token')
      }
    } catch (error) {
      console.error('خطا در بارگذاری کاربر:', error)
      localStorage.removeItem('auth_token')
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    try {
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)

      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'نام کاربری یا رمز عبور اشتباه است')
      }

      const data = await response.json()
      localStorage.setItem('auth_token', data.access_token)
      await loadUser(data.access_token)
      router.push('/')
    } catch (error: any) {
      console.error('خطای لاگین:', error)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setUser(null)
    router.push('/login')
  }

  const hasPermission = (permission: string): boolean => {
    if (!user) return false
    if (user.is_superuser) return true
    return user.permissions.includes(permission)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, hasPermission }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}