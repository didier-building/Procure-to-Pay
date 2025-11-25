import { useState, useEffect, createContext, useContext, ReactNode } from 'react'
import axios from '../utils/api'

interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const isAuthenticated = !!user

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      // Set default authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      
      // Verify token and get user data
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchUser = async () => {
    try {
      const response = await axios.get('/api/auth/user/')
      setUser(response.data)
    } catch (error) {
      // Token is invalid, remove it
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
      console.error('Token validation failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await axios.post('/api/auth/login/', {
        username,
        password,
      })

      const { access, user: userData } = response.data
      
      // Store token
      localStorage.setItem('token', access)
      
      // Set authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${access}`
      
      // Set user data
      setUser(userData)
      
      return true
    } catch (error: any) {
      console.error('Login failed:', error)
      return false
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
    setUser(null)
  }

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}