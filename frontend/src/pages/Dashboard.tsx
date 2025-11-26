import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  DocumentTextIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  PlusIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import axios from '../utils/api'

interface DashboardStats {
  total_requests: number
  pending_requests: number
  approved_requests: number
  rejected_requests: number
}

interface RecentRequest {
  id: number
  title: string
  status: string
  created_at: string
  amount: number
  created_by: string
}

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentRequests, setRecentRequests] = useState<RecentRequest[]>([])
  const [loading, setLoading] = useState(true)
  
  const getRoleTitle = (role: string) => {
    switch (role) {
      case 'staff': return 'Staff Dashboard'
      case 'approver1': return 'Level 1 Approver Dashboard'
      case 'approver2': return 'Level 2 Approver Dashboard'
      case 'finance': return 'Finance Dashboard'
      default: return 'Dashboard'
    }
  }
  
  const getRoleDescription = (role: string) => {
    switch (role) {
      case 'staff': return 'Create and manage your purchase requests'
      case 'approver1': return 'Review and approve purchase requests (Level 1)'
      case 'approver2': return 'Final approval for purchase requests (Level 2)'
      case 'finance': return 'Monitor approved requests and financial overview'
      default: return 'Welcome to the system'
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [statsResponse, requestsResponse] = await Promise.all([
        axios.get('/api/procurement/dashboard/stats/'),
        axios.get('/api/procurement/requests/?limit=5')
      ])
      
      setStats(statsResponse.data)
      setRecentRequests(requestsResponse.data.results || requestsResponse.data)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
        return 'text-success-600 bg-success-50'
      case 'rejected':
        return 'text-danger-600 bg-danger-50'
      case 'pending':
        return 'text-warning-600 bg-warning-50'
      default:
        return 'text-slate-600 bg-slate-50'
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white p-6 rounded-lg shadow-sm h-24" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-2xl font-bold text-slate-900">
          {user ? getRoleTitle(user.role) : 'Dashboard'}
        </h1>
        <p className="text-slate-600">
          {user ? getRoleDescription(user.role) : 'Welcome back! Here\'s an overview of your procurement activities.'}
        </p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-6"
        >
          <div className="flex items-center">
            <DocumentTextIcon className="h-8 w-8 text-primary-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600">Total Requests</p>
              <p className="text-2xl font-bold text-slate-900">{stats?.total_requests || 0}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card p-6"
        >
          <div className="flex items-center">
            <ClockIcon className="h-8 w-8 text-warning-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600">Pending</p>
              <p className="text-2xl font-bold text-slate-900">{stats?.pending_requests || 0}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card p-6"
        >
          <div className="flex items-center">
            <CheckCircleIcon className="h-8 w-8 text-success-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600">Approved</p>
              <p className="text-2xl font-bold text-slate-900">{stats?.approved_requests || 0}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card p-6"
        >
          <div className="flex items-center">
            <XCircleIcon className="h-8 w-8 text-danger-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600">Rejected</p>
              <p className="text-2xl font-bold text-slate-900">{stats?.rejected_requests || 0}</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="card"
          >
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900">Recent Requests</h2>
            </div>
            
            <div className="divide-y divide-slate-200">
              {recentRequests.length > 0 ? (
                recentRequests.map((request, index) => (
                  <motion.div
                    key={request.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 + index * 0.1 }}
                    className="p-6 hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="text-sm font-medium text-slate-900">
                          {request.title}
                        </h3>
                        <p className="text-sm text-slate-500">
                          Created {new Date(request.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className="text-sm font-medium text-slate-900">
                          ${request.amount?.toLocaleString() || 'N/A'}
                        </span>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                          {request.status}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="p-6 text-center text-slate-500">
                  No recent requests found
                </div>
              )}
            </div>
          </motion.div>
        </div>

        <div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="card p-6"
          >
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Quick Actions</h2>
            
            <div className="space-y-3">
              {user?.role === 'staff' && (
                <Link
                  to="/requests/create"
                  className="flex items-center p-3 rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100 transition-colors group"
                >
                  <PlusIcon className="h-5 w-5 mr-3" />
                  <span className="font-medium">Create New Request</span>
                </Link>
              )}
              
              <Link
                to="/requests"
                className="flex items-center p-3 rounded-lg bg-slate-50 text-slate-700 hover:bg-slate-100 transition-colors group"
              >
                <DocumentTextIcon className="h-5 w-5 mr-3" />
                <span className="font-medium">View All Requests</span>
              </Link>
              
              <button className="flex items-center p-3 rounded-lg bg-slate-50 text-slate-700 hover:bg-slate-100 transition-colors group w-full">
                <ChartBarIcon className="h-5 w-5 mr-3" />
                <span className="font-medium">Generate Report</span>
              </button>
            </div>
          </motion.div>
        </div>
      </div>

    </div>
  )
}