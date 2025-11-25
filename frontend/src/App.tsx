import { Routes, Route, Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Requests from './pages/Requests'
import CreateRequest from './pages/CreateRequest'
import Login from './pages/Login'
import Register from './pages/Register'
import { useAuth } from './hooks/useAuth'
import { Toaster } from 'react-hot-toast'
import './utils/api' // Initialize API configuration

function App() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full"
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {isAuthenticated && <Navbar />}
      
      <main className={`${isAuthenticated ? 'pl-64' : ''} transition-all duration-300`}>
        <Routes>
          <Route 
            path="/login" 
            element={!isAuthenticated ? <Login /> : <Navigate to="/dashboard" />} 
          />
          
          <Route 
            path="/register" 
            element={!isAuthenticated ? <Register /> : <Navigate to="/dashboard" />} 
          />
          
          <Route 
            path="/dashboard" 
            element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} 
          />
          
          <Route 
            path="/requests" 
            element={isAuthenticated ? <Requests /> : <Navigate to="/login" />} 
          />
          
          <Route 
            path="/requests/create" 
            element={isAuthenticated ? <CreateRequest /> : <Navigate to="/login" />} 
          />
          
          <Route 
            path="/" 
            element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} 
          />
        </Routes>
      </main>
      <Toaster position="top-right" />
    </div>
  )
}

export default App