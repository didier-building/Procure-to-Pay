import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import axios from '../utils/api'
import toast from 'react-hot-toast'

export default function Register() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    password_confirm: '',
    role: 'staff'
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await axios.post('/api/auth/register/', formData)
      toast.success('Registration successful!')
      
      // Store token and redirect
      localStorage.setItem('token', response.data.access)
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`
      
      navigate('/dashboard')
    } catch (error: any) {
      const errorMsg = error.response?.data?.username?.[0] || 
                      error.response?.data?.email?.[0] || 
                      'Registration failed'
      toast.error(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full space-y-8"
      >
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl flex items-center justify-center">
            <span className="text-white font-bold text-xl">P2P</span>
          </div>
          <h2 className="mt-6 text-3xl font-bold text-slate-900">Create Account</h2>
          <p className="mt-2 text-sm text-slate-600">Join the IST Africa Procurement System</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <input
              name="first_name"
              type="text"
              required
              value={formData.first_name}
              onChange={handleChange}
              className="input"
              placeholder="First Name"
            />
            <input
              name="last_name"
              type="text"
              required
              value={formData.last_name}
              onChange={handleChange}
              className="input"
              placeholder="Last Name"
            />
          </div>
          
          <input
            name="username"
            type="text"
            required
            value={formData.username}
            onChange={handleChange}
            className="input"
            placeholder="Username"
          />
          
          <input
            name="email"
            type="email"
            required
            value={formData.email}
            onChange={handleChange}
            className="input"
            placeholder="Email"
          />
          
          <select
            name="role"
            value={formData.role}
            onChange={handleChange}
            className="input"
          >
            <option value="staff">Staff</option>
            <option value="approver1">Level 1 Approver</option>
            <option value="approver2">Level 2 Approver</option>
            <option value="finance">Finance</option>
          </select>
          
          <input
            name="password"
            type="password"
            required
            value={formData.password}
            onChange={handleChange}
            className="input"
            placeholder="Password"
          />
          
          <input
            name="password_confirm"
            type="password"
            required
            value={formData.password_confirm}
            onChange={handleChange}
            className="input"
            placeholder="Confirm Password"
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white py-3 rounded-md hover:bg-primary-700 disabled:opacity-50"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="text-center">
          <Link to="/login" className="text-primary-600 hover:text-primary-700">
            Already have an account? Sign in
          </Link>
        </div>
      </motion.div>
    </div>
  )
}