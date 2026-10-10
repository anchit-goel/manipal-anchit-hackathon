import React from 'react'
import type { HealthInfo } from '../types'
import { formatCurrency } from '../utils'

interface TopBarProps {
  totalMarketValue: number
  health: HealthInfo | null
  activeTab: 'stress' | 'whatif' | 'analyze' | 'calibration' | 'methodology'
  onSelectTab: (tab: 'stress' | 'whatif' | 'analyze' | 'calibration' | 'methodology') => void
  connectionState: 'connecting' | 'connected' | 'paused' | 'done' | 'error'
}

export const TopBar: React.FC<TopBarProps> = ({
  totalMarketValue,
  health,
  activeTab,
  onSelectTab,
  connectionState,
}) => {
  const isOffline = health ? health.offline_mode : true

  const navItems = [
    { id: 'stress', label: 'Monitor' },
    { id: 'whatif', label: 'Scenario lab' },
    { id: 'analyze', label: 'Analyze text' },
    { id: 'calibration', label: 'Calibration' },
    { id: 'methodology', label: 'Methodology' },
  ] as const

  return (
    <header className="bg-white border-b border-[#E3E6EB] px-6 py-0 flex items-center justify-between sticky top-0 z-40 h-14">
      {/* Brand & Tagline */}
      <div className="flex items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-[#0F1B2D] text-base tracking-tight">
              Signal-to-Shock
            </span>
            <span className="text-[11px] font-normal text-[#5B6676] pl-2 border-l border-[#E3E6EB] hidden sm:inline">
              Wholesale portfolio risk intelligence
            </span>
          </div>
        </div>
      </div>

      {/* Underlined Navigation Tabs */}
      <nav className="flex items-center gap-1 h-full" aria-label="Main navigation">
        {navItems.map((item) => {
          const isActive = activeTab === item.id
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`h-full px-3.5 text-sm font-medium transition-colors flex items-center border-b-2 -mb-[1px] ${
                isActive
                  ? 'border-[#1F4E9C] text-[#1F4E9C] font-semibold'
                  : 'border-transparent text-[#5B6676] hover:text-[#0F1B2D] hover:border-[#D0D5DD]'
              }`}
            >
              {item.label}
            </button>
          )
        })}
      </nav>

      {/* Status & Book Value */}
      <div className="flex items-center gap-3">
        {/* Mode Pill */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-[#F2F4F7] text-[#475467] border border-[#EAECF0]">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              connectionState === 'connected'
                ? 'bg-[#067647]'
                : connectionState === 'connecting'
                ? 'bg-[#B54708] animate-pulse'
                : 'bg-[#98A2B3]'
            }`}
          />
          <span>{isOffline ? 'Replay · offline' : 'Live stream'}</span>
        </div>

        {/* Wholesale Book Value */}
        <div className="text-right border-l border-[#E3E6EB] pl-3">
          <div className="text-[11px] text-[#5B6676] leading-none mb-0.5">Book value</div>
          <div className="text-xs font-semibold text-[#0F1B2D] tabular-nums leading-none">
            {formatCurrency(totalMarketValue, 2)}
          </div>
        </div>
      </div>
    </header>
  )
}
