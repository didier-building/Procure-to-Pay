import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  HomeIcon,
  DocumentTextIcon,
  PlusIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline'
import { useAuth } from '../hooks/useAuth'

const getNavigation = (userRole: string | undefined) => {
  const baseNav = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
    { name: 'Requests', href: '/requests', icon: DocumentTextIcon },
  ]
  
  // Only staff can create requests
  if (userRole === 'staff') {
    baseNav.push({ name: 'Create Request', href: '/requests/create', icon: PlusIcon })
  }
  

  
  return baseNav
}

export default function Navbar() {
  const location = useLocation()
  const { user, logout } = useAuth()

  return (
    <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 shrink-0 items-center border-b border-slate-200 px-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center"
          >
            <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-primary-700 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">P2P</span>
            </div>
            <span className="ml-3 text-lg font-semibold text-slate-900">
              Procurement
            </span>
          </motion.div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6">
          <ul className="space-y-2">
            {getNavigation(user?.role).map((item, index) => {
              const isActive = location.pathname === item.href
              
              return (
                <motion.li
                  key={item.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Link
                    to={item.href}
                    className={`
                      group flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200
                      ${isActive
                        ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                      }
                    `}
                  >
                    <item.icon
                      className={`
                        mr-3 h-5 w-5 transition-colors
                        ${isActive ? 'text-primary-600' : 'text-slate-400 group-hover:text-slate-600'}
                      `}
                    />
                    {item.name}
                  </Link>
                </motion.li>
              )
            })}
          </ul>
        </nav>

        {/* User Profile */}
        <div className="border-t border-slate-200 p-4">
          <div className="flex items-center">
            <UserCircleIcon className="h-8 w-8 text-slate-400" />
            <div className="ml-3">
              <p className="text-sm font-medium text-slate-900">
                {user?.username || 'User'}
              </p>
              <p className="text-xs text-slate-500">
                {user?.email || 'user@example.com'}
              </p>
            </div>
          </div>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={logout}
            className="mt-3 flex w-full items-center rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
          >
            <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5" />
            Sign out
          </motion.button>
        </div>
      </div>
    </div>
  )
}