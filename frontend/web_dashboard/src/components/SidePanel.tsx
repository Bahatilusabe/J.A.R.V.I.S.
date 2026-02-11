import { useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  AlertTriangle,
  LineChart,
  FileCode,
  Brain,
  Network,
  Server,
  Hexagon,
  FileText,
  Settings,
  Shield,
  Zap,
} from 'lucide-react'
// authService removed — sidebar no longer needs auth checks here


// Minimal, standard sidebar for the dashboard. Keeps the API of previous SidePanel
// but uses a simple declarative navigation list and lightweight layout.

const navigationItems = [
  { title: 'Overview', icon: LayoutDashboard, url: '/dashboard' },
  { title: 'Incidents', icon: AlertTriangle, url: '/incidents' },
  { title: 'Predictions', icon: LineChart, url: '/pasm' },
  { title: 'Policies', icon: FileCode, url: '/policies' },
  { title: 'ModelOps', icon: Brain, url: '/modelops' },
  { title: 'Federation', icon: Network, url: '/federation' },
  { title: 'Edge Devices', icon: Server, url: '/edge' },
  { title: 'Deception Grid', icon: Hexagon, url: '/deception' },
  { title: 'Forensics', icon: FileText, url: '/forensics' },
  { title: 'Network Security', icon: Shield, url: '/network-security' },
]

const securityItems = [
  { title: 'Self-Healing', icon: Zap, url: '/self-healing' },
  { title: 'Settings', icon: Settings, url: '/settings' },
]

interface SidePanelProps {
  collapsed?: boolean
  onToggleCollapse?: () => void
}

export function SidePanel({ collapsed = false, onToggleCollapse = () => { } }: SidePanelProps) {
  const navigate = useNavigate()
  const location = typeof window !== 'undefined' ? window.location.pathname : '/'

  const isActive = (url: string) => location === url || (url !== '/' && location.startsWith(url))

  return (
    <div className={`flex flex-col h-screen bg-gradient-to-b from-slate-900/90 to-slate-900/70 border-r border-slate-800 ${collapsed ? 'w-20' : 'w-72'} transition-width duration-200`}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800/40">
        <a href="/" onClick={(e) => {
          e.preventDefault(); // SPA navigation via startTransition
          // eslint-disable-next-line @typescript-eslint/no-floating-promises
          import('react').then(({ startTransition }) => startTransition(() => navigate('/')))
        }} className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-cyan-400 shadow-md">
            <Shield className="h-5 w-5 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-base font-semibold tracking-tight text-white">JARVIS</span>
              <span className="text-xs text-slate-300">Security Ops</span>
            </div>
          )}
        </a>

        <div className="flex items-center gap-2">
          <button onClick={() => { onToggleCollapse(); }} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} className="p-2 rounded hover:bg-slate-800/40 transition-colors">
            <span className={`transform ${collapsed ? '' : 'rotate-180'} text-slate-300`}>{'❮'}</span>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-4">
        {/* Optional search for quick navigation */}
        {!collapsed && (
          <div className="mb-3">
            <input
              placeholder="Search…"
              className="w-full px-3 py-2 rounded bg-slate-800/40 border border-slate-700/30 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-cyan-400"
              aria-label="Search navigation"
            />
          </div>
        )}

        <div className="text-xs font-semibold text-slate-400 mb-2">Main</div>
        <div className="space-y-1">
          {navigationItems.map((item) => {
            const ActiveIcon = item.icon
            const active = isActive(item.url)
            return (
              <a
                key={item.title}
                href={item.url}
                title={item.title}
                onClick={(e) => { e.preventDefault(); import('react').then(({ startTransition }) => startTransition(() => navigate(item.url))) }}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${active ? 'bg-slate-800/60 text-white shadow-inner' : 'text-slate-300 hover:bg-slate-800/40'}`}>
                <ActiveIcon className={`h-5 w-5 ${active ? 'text-cyan-300' : 'text-slate-300'}`} />
                {!collapsed && <span className="text-sm">{item.title}</span>}
              </a>
            )
          })}
        </div>

        <div className="mt-6 text-xs font-semibold text-slate-400 mb-2">Security</div>
        <div className="space-y-1">
          {securityItems.map((item) => {
            const ActiveIcon = item.icon
            const active = isActive(item.url)
            return (
              <a
                key={item.title}
                href={item.url}
                title={item.title}
                onClick={(e) => { e.preventDefault(); import('react').then(({ startTransition }) => startTransition(() => navigate(item.url))) }}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${active ? 'bg-slate-800/60 text-white shadow-inner' : 'text-slate-300 hover:bg-slate-800/40'}`}>
                <ActiveIcon className={`h-5 w-5 ${active ? 'text-cyan-300' : 'text-slate-300'}`} />
                {!collapsed && <span className="text-sm">{item.title}</span>}
              </a>
            )
          })}
        </div>
      </div>

      {!collapsed && (
        <div className="px-4 py-3 border-t border-slate-800/40 text-xs text-slate-400">
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className="text-sm font-medium text-white">System Admin</div>
              <div className="text-xs text-slate-300">NODE-01</div>
            </div>
            <div className="text-right">
              <div className="text-xs">v1.0</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SidePanel
