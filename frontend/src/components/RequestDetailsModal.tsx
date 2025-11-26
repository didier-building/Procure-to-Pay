import { Fragment, useState, useEffect } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { XMarkIcon, DocumentTextIcon, UserIcon, CalendarIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline'
import axios from '../utils/api'
import { useAuth } from '../hooks/useAuth'

interface RequestDetails {
  id: number
  title: string
  description: string
  status: string
  amount: number
  created_at: string
  created_by: string
  purchase_order_data?: string | null
  approvals: Array<{
    id: number
    level: number
    status: string
    approved_by: string
    comment: string
    created_at: string
  }>
}

interface RequestDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  requestId: number | null
}

export default function RequestDetailsModal({ isOpen, onClose, requestId }: RequestDetailsModalProps) {
  const { user } = useAuth()
  const [request, setRequest] = useState<RequestDetails | null>(null)
  const [loading, setLoading] = useState(false)
  const [approvalComment, setApprovalComment] = useState('')

  useEffect(() => {
    if (isOpen && requestId) {
      fetchRequestDetails()
    }
  }, [isOpen, requestId])

  const fetchRequestDetails = async () => {
    if (!requestId) return
    
    setLoading(true)
    try {
      const response = await axios.get(`/api/procurement/requests/${requestId}/`)
      setRequest(response.data)
    } catch (error) {
      console.error('Failed to fetch request details:', error)
    } finally {
      setLoading(false)
    }
  }

  const canApprove = (request: RequestDetails) => {
    if (!user || !request) return false
    console.log('Debug - User:', user)
    console.log('Debug - User role:', user.role)
    console.log('Debug - Request status:', request.status)
    const isApprover = user.role === 'approver1' || user.role === 'approver2'
    console.log('Debug - Is approver:', isApprover)
    const canApproveResult = isApprover && request.status === 'PENDING'
    console.log('Debug - Can approve:', canApproveResult)
    return canApproveResult
  }

  const handleApprove = async () => {
    if (!request) return
    
    try {
      await axios.patch(`/api/procurement/requests/${request.id}/approve/`, {
        comment: approvalComment || `Approved by ${user?.role}`
      })
      alert('Request approved successfully!')
      setApprovalComment('')
      fetchRequestDetails() // Refresh data
    } catch (error: any) {
      alert('Error: ' + (error.response?.data?.detail || 'Failed to approve request'))
    }
  }

  const handleReject = async () => {
    if (!request) return
    
    const reason = prompt('Please provide a reason for rejection:')
    if (!reason) return
    
    try {
      await axios.patch(`/api/procurement/requests/${request.id}/reject/`, {
        comment: reason
      })
      fetchRequestDetails() // Refresh data
    } catch (error: any) {
      alert('Error: ' + (error.response?.data?.detail || 'Failed to reject request'))
    }
  }

  const handleReceiptUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !request) return

    const formData = new FormData()
    formData.append('receipt', file)

    try {
      await axios.post(`/api/procurement/requests/${request.id}/submit-receipt/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      alert('Receipt uploaded and validated successfully!')
      fetchRequestDetails() // Refresh data
    } catch (error: any) {
      alert('Error: ' + (error.response?.data?.detail || 'Failed to upload receipt'))
    }
  }

  const handleGeneratePO = async () => {
    if (!request) return

    try {
      await axios.post(`/api/procurement/requests/${request.id}/generate-purchase-order/`)
      alert('Purchase Order generated successfully!')
      fetchRequestDetails() // Refresh data
    } catch (error: any) {
      alert('Error: ' + (error.response?.data?.error || 'Failed to generate PO'))
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved': return 'text-green-700 bg-green-100'
      case 'rejected': return 'text-red-700 bg-red-100'
      case 'pending': return 'text-yellow-700 bg-yellow-100'
      default: return 'text-gray-700 bg-gray-100'
    }
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-6 shadow-xl transition-all">
                <div className="flex items-center justify-between mb-6">
                  <Dialog.Title className="text-lg font-medium text-gray-900">
                    Request Details [UPDATED VERSION]
                  </Dialog.Title>
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-500"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                {loading ? (
                  <div className="flex justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                ) : request ? (
                  <div className="space-y-6">
                    {/* Request Info */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            {request.title}
                          </h3>
                          <p className="text-gray-600 mb-4">{request.description}</p>
                          
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="flex items-center">
                              <UserIcon className="h-4 w-4 text-gray-400 mr-2" />
                              <span>Created by: {request.created_by}</span>
                            </div>
                            <div className="flex items-center">
                              <CalendarIcon className="h-4 w-4 text-gray-400 mr-2" />
                              <span>{new Date(request.created_at).toLocaleDateString()}</span>
                            </div>
                            <div className="flex items-center">
                              <CurrencyDollarIcon className="h-4 w-4 text-gray-400 mr-2" />
                              <span>${request.amount.toLocaleString()}</span>
                            </div>
                            <div className="flex items-center">
                              <DocumentTextIcon className="h-4 w-4 text-gray-400 mr-2" />
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                                {request.status}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Approval History */}
                    <div>
                      <h4 className="text-md font-semibold text-gray-900 mb-3">Approval History</h4>
                      <div className="space-y-3">
                        {request.approvals && request.approvals.length > 0 ? (
                          request.approvals.map((approval) => (
                            <div key={approval.id} className="border rounded-lg p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium text-gray-900">
                                  Level {approval.level} - {approval.approved_by}
                                </span>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(approval.status)}`}>
                                  {approval.status}
                                </span>
                              </div>
                              {approval.comment && (
                                <p className="text-sm text-gray-600 mb-2">{approval.comment}</p>
                              )}
                              <p className="text-xs text-gray-500">
                                {new Date(approval.created_at).toLocaleString()}
                              </p>
                            </div>
                          ))
                        ) : (
                          <p className="text-gray-500 text-sm">No approvals yet</p>
                        )}
                      </div>
                    </div>

                    {/* PO Generation & Receipt Upload for Approved Requests */}
                    {request.status === 'APPROVED' && (
                      <div className="pt-4 border-t space-y-3">
                        {/* PO Status or Generate Button */}
                        <div>
                          {request.purchase_order_data ? (
                            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                              <p className="text-green-800 font-medium">✅ Purchase Order Generated</p>
                              <p className="text-green-600 text-sm mt-1">PO ready for receipt validation</p>
                            </div>
                          ) : (
                            <button
                              onClick={handleGeneratePO}
                              className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                              Generate Purchase Order
                            </button>
                          )}
                        </div>
                        
                        {/* Receipt Upload for Staff */}
                        {request.created_by === user?.username && request.purchase_order_data && (
                          <div>
                            <h5 className="font-medium text-gray-900 mb-2">Upload Receipt for Validation</h5>
                            <input
                              type="file"
                              accept=".pdf,.png,.jpg,.jpeg"
                              onChange={handleReceiptUpload}
                              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                            />
                            <p className="text-xs text-gray-500 mt-1">Upload receipt to validate against generated PO</p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Action Buttons */}
                    {canApprove(request) && (
                      <div className="pt-4 border-t space-y-3">
                        {/* Comment Field */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Approval Comment (Optional)
                          </label>
                          <textarea
                            value={approvalComment}
                            onChange={(e) => setApprovalComment(e.target.value)}
                            placeholder="Add your comment..."
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            rows={3}
                          />
                        </div>
                        
                        {/* Action Buttons */}
                        <div className="flex space-x-3">
                          <button
                            onClick={handleApprove}
                            className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                          >
                            Approve
                          </button>
                          <button
                            onClick={handleReject}
                            className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                          >
                            Reject
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    Failed to load request details
                  </div>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}