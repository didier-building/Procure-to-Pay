import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import axios from '../utils/api'
import toast, { Toaster } from 'react-hot-toast'

interface RequestFormData {
  title: string
  description: string
  amount: number
}

export default function CreateRequest() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)

  const { register, handleSubmit, formState: { errors } } = useForm<RequestFormData>({
    defaultValues: {
      title: '',
      description: '',
      amount: 0
    }
  })

  const onSubmit = async (data: RequestFormData) => {
    try {
      setLoading(true)
      
      const formData = new FormData()
      formData.append('title', data.title)
      formData.append('description', data.description)
      formData.append('amount', data.amount.toString())
      
      if (uploadedFile) {
        formData.append('proforma', uploadedFile)
      }

      await axios.post('/api/procurement/requests/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      toast.success('Request created successfully!')
      navigate('/requests')
    } catch (error) {
      toast.error('Failed to create request. Please try again.')
      console.error('Error creating request:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadedFile(file)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="bg-white rounded-2xl shadow-xl p-8"
        >
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-800 mb-2">
              Create Purchase Request
            </h1>
            <p className="text-slate-600">
              Submit a new purchase request for approval
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Title */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Title *
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                placeholder="Brief title for your request"
                {...register('title', { required: 'Title is required' })}
              />
              {errors.title && (
                <p className="mt-1 text-sm text-danger-600">{errors.title.message}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Description
              </label>
              <textarea
                rows={4}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all resize-none"
                placeholder="Describe what you need to purchase..."
                {...register('description')}
              />
            </div>

            {/* Amount */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Amount ($) *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                placeholder="0.00"
                {...register('amount', { 
                  required: 'Amount is required',
                  min: { value: 0.01, message: 'Amount must be greater than 0' }
                })}
              />
              {errors.amount && (
                <p className="mt-1 text-sm text-danger-600">{errors.amount.message}</p>
              )}
            </div>

            {/* Proforma Upload */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Proforma Invoice (Optional)
              </label>
              <div className="flex items-center justify-center w-full">
                <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-300 border-dashed rounded-xl cursor-pointer bg-slate-50 hover:bg-slate-100 transition-colors">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <svg className="w-8 h-8 mb-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="mb-2 text-sm text-slate-500">
                      {uploadedFile ? uploadedFile.name : 'Click to upload proforma'}
                    </p>
                    <p className="text-xs text-slate-400">PDF, PNG, JPG up to 10MB</p>
                  </div>
                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={handleFileUpload}
                  />
                </label>
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-6">
              <motion.button
                type="submit"
                disabled={loading}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full bg-gradient-to-r from-primary-600 to-primary-700 text-white font-semibold py-3 px-6 rounded-xl hover:from-primary-700 hover:to-primary-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Creating Request...
                  </div>
                ) : (
                  'Submit Request'
                )}
              </motion.button>
            </div>
          </form>
        </motion.div>
      </div>
      <Toaster position="top-right" />
    </div>
  )
}