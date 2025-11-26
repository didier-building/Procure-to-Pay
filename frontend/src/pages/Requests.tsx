import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  DocumentTextIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline'
import axios from '../utils/api'
import RequestDetailsModal from '../components/RequestDetailsModal'
import toast, { Toaster } from 'react-hot-toast'

interface Request {
  id: number
  title: string
  description: string
  status: string
  created_at: string
  amount: number
  created_by: string
  approvals?: Array<{
    id: number
    level: number
    approved: boolean
    approved_by: string
    comment: string
    created_at: string
  }>
}

export default function Requests() {
  const { user } = useAuth()
  const [requests, setRequests] = useState<Request[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRequestId, setSelectedRequestId] = useState<number | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  

  
  const handleApprove = async (requestId: number) => {
    try {
      await axios.patch(`/api/procurement/requests/${requestId}/approve/`, {
        comment: 'Approved by ' + user?.role
      })
      toast.success('Request approved successfully')
      fetchRequests() // Refresh the list
    } catch (error: any) {
      console.error('Failed to approve request:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to approve request'
      toast.error('Error: ' + errorMessage)
    }
  }
  
  const handleReject = async (requestId: number) => {
    const reason = prompt('Please provide a reason for rejection:')
    if (!reason) return // User cancelled
    
    try {
      await axios.patch(`/api/procurement/requests/${requestId}/reject/`, {
        comment: reason
      })
      toast.success('Request rejected successfully')
      fetchRequests() // Refresh the list
    } catch (error: any) {
      console.error('Failed to reject request:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to reject request'
      toast.error('Error: ' + errorMessage)
    }
  }

  useEffect(() => {
    fetchRequests()
  }, [])

  const fetchRequests = async () => {
    try {
      const response = await axios.get('/api/procurement/requests/')
      setRequests(response.data.results || response.data)
    } catch (error) {
      console.error('Failed to fetch requests:', error)
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

  const filteredRequests = requests.filter(request =>
    request.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    request.created_by.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-200 rounded w-1/4"></div>
          <div className="h-32 bg-slate-200 rounded"></div>
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Purchase Requests</h1>
            <p className="text-slate-600">Manage and track all procurement requests</p>
          </div>
          {user?.role === 'staff' && (
            <Link
              to="/requests/create"
              className="btn-primary px-4 py-2"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              New Request
            </Link>
          )}
        </div>
      </motion.div>

      {/* Search and Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card p-6 mb-6"
      >
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search requests..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>
          <button className="btn-secondary px-4 py-2">
            <FunnelIcon className="h-5 w-5 mr-2" />
            Filter
          </button>
        </div>
      </motion.div>

      {/* Requests List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card overflow-hidden"
      >
        {filteredRequests.length > 0 ? (
          <div className="divide-y divide-slate-200">
            {filteredRequests.map((request, index) => (
              <motion.div
                key={request.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + index * 0.1 }}
                className="p-6 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <DocumentTextIcon className="h-5 w-5 text-slate-400" />
                      <h3 className="text-lg font-medium text-slate-900">
                        {request.title}
                      </h3>
                    </div>
                    <p className="mt-1 text-sm text-slate-600">
                      {request.description}
                    </p>
                    <div className="mt-2 flex items-center space-x-4 text-sm text-slate-500">
                      <span>Created by: {request.created_by}</span>
                      <span>•</span>
                      <span>Created: {new Date(request.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className="text-lg font-semibold text-slate-900">
                        ${request.amount?.toLocaleString() || 'N/A'}
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedRequestId(request.id)
                        setIsModalOpen(true)
                      }}
                      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(request.status)} hover:opacity-80 transition-opacity`}
                    >
                      {request.status}
                    </button>
                    
                    {/* Approval buttons for approvers */}
                    {(user?.role === 'approver1' || user?.role === 'approver2') && request.status === 'PENDING' && (
                      <div className="flex space-x-2 ml-4">
                        {/* Check if current user already approved */}
                        {request.approvals?.some(approval => 
                          approval.approved_by === user?.username && 
                          approval.level === (user?.role === 'approver1' ? 1 : 2) &&
                          approval.approved === true
                        ) ? (
                          <button
                            disabled
                            className="px-3 py-1 bg-gray-400 text-white text-sm rounded-md cursor-not-allowed"
                          >
                            ✓ Approved
                          </button>
                        ) : (
                          <>
                            <button
                              onClick={() => handleApprove(request.id)}
                              className="px-3 py-1 bg-green-600 text-white text-sm rounded-md hover:bg-green-700"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleReject(request.id)}
                              className="px-3 py-1 bg-red-600 text-white text-sm rounded-md hover:bg-red-700"
                            >
                              Reject
                            </button>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <DocumentTextIcon className="mx-auto h-12 w-12 text-slate-400" />
            <h3 className="mt-4 text-lg font-medium text-slate-900">No requests found</h3>
            <p className="mt-2 text-slate-600">
              {searchTerm ? 'Try adjusting your search criteria.' : 'Get started by creating your first request.'}
            </p>
            {!searchTerm && user?.role === 'staff' && (
              <Link
                to="/requests/create"
                className="mt-4 inline-flex btn-primary px-4 py-2"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Create Request
              </Link>
            )}
          </div>
        )}
      </motion.div>

      {/* Request Details Modal */}
      <RequestDetailsModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setSelectedRequestId(null)
          fetchRequests() // Refresh list when modal closes
        }}
        requestId={selectedRequestId}
      />
      <Toaster position="top-right" />
    </div>
  )
}