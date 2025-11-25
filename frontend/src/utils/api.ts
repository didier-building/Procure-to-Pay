import axios from 'axios'

// Configure axios defaults
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'https://procure-to-pay-backend.onrender.com'

axios.defaults.baseURL = API_BASE_URL
axios.defaults.timeout = 30000

// Request interceptor to add auth token
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default axios