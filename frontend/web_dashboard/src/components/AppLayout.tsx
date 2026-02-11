import { ReactNode } from 'react'
import { SystemBar } from './SystemBar'

interface AppLayoutProps {
  children: ReactNode
  // Optional props used by pages for highlighting active nav or handling clicks
  activeLink?: string
  onNavLinkClick?: (path: string) => void
}

/**
 * Master App Layout Component
 * Integrates SystemBar (topbar) and SidePanel
 * Used across all views for consistent UI
 */
export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex flex-col h-screen bg-slate-950">
      {/* Top System Bar */}
      <SystemBar />

      {/* Main Content Area (SidePanel is provided by top-level Layout) */}
      <div className="flex flex-1 overflow-hidden">
        {/* Main Content */}
        <main className="flex-1 overflow-auto bg-slate-950">
          {children}
        </main>
      </div>
    </div>
  )
}

export default AppLayout
