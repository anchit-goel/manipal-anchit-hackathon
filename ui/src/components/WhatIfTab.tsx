import React, { useState, useEffect } from 'react'
import { Play, AlertCircle } from 'lucide-react'
import type { StressResult, PortfolioData } from '../types'
import { StressPanel } from './StressPanel'
import { humanizeTheme } from '../utils'

interface WhatIfTabProps {
  onRunCustom: (theme: string, severity: number) => Promise<StressResult | null>
  portfolio?: PortfolioData | null
  loading?: boolean
}

interface ThemeOption {
  id: string
  label: string
  description: string
}

const THEME_OPTIONS: ThemeOption[] = [
  {
    id: 'shipping_disruption',
    label: 'Shipping disruption',
    description: 'Chokepoint naval blockades, canal closures, or commercial fleet diversions.',
  },
  {
    id: 'oil_price_up',
    label: 'Oil price increase',
    description: 'Crude supply cuts or geopolitical supply constraints lifting oil benchmarks.',
  },
  {
    id: 'oil_price_down',
    label: 'Oil price drop',
    description: 'Demand contractions or supply gluts depressing energy revenues.',
  },
  {
    id: 'credit_downgrade',
    label: 'Credit downgrade',
    description: 'Rating agency notch cuts widening borrowing spreads and credit spreads.',
  },
  {
    id: 'credit_default',
    label: 'Credit default',
    description: 'Sovereign or counterparty debt distress triggering credit provisions.',
  },
  {
    id: 'banking_stress',
    label: 'Banking sector stress',
    description: 'Interbank liquidity crunches, deposit flight, or regional bank contagion.',
  },
  {
    id: 'rate_hike',
    label: 'Interest rate hike',
    description: 'Central bank policy rate tightening dampening bond valuations.',
  },
  {
    id: 'rate_cut',
    label: 'Interest rate cut',
    description: 'Emergency easing compressing wholesale net interest margins.',
  },
  {
    id: 'sovereign_risk',
    label: 'Sovereign risk',
    description: 'Emerging market debt moratoria and cross-border currency restrictions.',
  },
  {
    id: 'semiconductor_shortage',
    label: 'Semiconductor shortage',
    description: 'Foundry export curbs or packaging bottlenecks hitting tech supply chains.',
  },
]

export const WhatIfTab: React.FC<WhatIfTabProps> = ({ onRunCustom, portfolio, loading }) => {
  const [selectedTheme, setSelectedTheme] = useState<string>('shipping_disruption')
  const [severity, setSeverity] = useState<number>(8.0)
  const [result, setResult] = useState<StressResult | null>(null)
  const [localLoading, setLocalLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Execute scenario shock
  const executeScenario = async (t: string, s: number) => {
    setLocalLoading(true)
    setError(null)
    try {
      const res = await onRunCustom(t, s)
      setResult(res)
    } catch (err: any) {
      setError(err?.message || 'Failed to execute custom stress shock')
    } finally {
      setLocalLoading(false)
    }
  }

  // Auto-run once on mount so there is never an empty void
  useEffect(() => {
    executeScenario(selectedTheme, severity)
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    executeScenario(selectedTheme, severity)
  }

  const currentThemeObj = THEME_OPTIONS.find((t) => t.id === selectedTheme) || THEME_OPTIONS[0]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start text-left">
      {/* Left Column: Controls (4 cols) */}
      <div className="lg:col-span-5 bg-white border border-[#E3E6EB] rounded-lg p-5 space-y-5">
        <div>
          <h2 className="text-base font-bold text-[#0F1B2D]">Scenario Lab</h2>
          <p className="text-xs text-[#5B6676] mt-0.5">
            Formulate custom macroeconomic or sectoral stress scenarios and evaluate transmission.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Theme Selector */}
          <div>
            <label className="block text-xs font-semibold text-[#0F1B2D] mb-1.5">
              Risk theme
            </label>
            <select
              value={selectedTheme}
              onChange={(e) => {
                setSelectedTheme(e.target.value)
                executeScenario(e.target.value, severity)
              }}
              className="w-full bg-[#F9FAFB] border border-[#E3E6EB] rounded-md px-3 py-2 text-xs text-[#0F1B2D] focus:border-[#1F4E9C] focus:bg-white focus:outline-none transition-colors"
            >
              {THEME_OPTIONS.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-[#5B6676] mt-1.5 leading-relaxed bg-[#F9FAFB] p-2 rounded border border-[#EEF0F3]">
              {currentThemeObj.description}
            </p>
          </div>

          {/* Severity Slider with Labelled Stops */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-[#0F1B2D]">
                Severity scale (1–10)
              </label>
              <span className="text-sm font-bold text-[#1F4E9C] tabular-nums bg-[#EDF3FC] px-2 py-0.5 rounded border border-[#B2CCF2]">
                {severity.toFixed(1)}
              </span>
            </div>

            <input
              type="range"
              min="1"
              max="10"
              step="0.5"
              value={severity}
              onChange={(e) => {
                const val = parseFloat(e.target.value)
                setSeverity(val)
                executeScenario(selectedTheme, val)
              }}
              className="w-full accent-[#1F4E9C] cursor-pointer"
            />

            {/* Labelled stops */}
            <div className="flex justify-between text-[10px] text-[#8A94A6] mt-1.5 px-0.5">
              <span>1: Minor</span>
              <span>4: Moderate</span>
              <span>7: Major</span>
              <span>10: Extreme</span>
            </div>
          </div>

          {/* Error notice */}
          {error && (
            <div className="p-2.5 rounded bg-[#FEF3F2] border border-[#FECDCA] text-[#B42318] text-xs flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Run Scenario Button */}
          <button
            type="submit"
            disabled={loading || localLoading}
            className="w-full py-2 px-4 rounded-md font-medium text-xs bg-[#1F4E9C] text-white hover:bg-[#163A75] transition-colors flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{localLoading ? 'Evaluating scenario...' : 'Run scenario'}</span>
          </button>
        </form>
      </div>

      {/* Right Column: Live Stress Result (7 cols) */}
      <div className="lg:col-span-7">
        <StressPanel
          result={result}
          portfolio={portfolio}
          loading={localLoading || loading}
          headline={`Custom What-If: ${humanizeTheme(selectedTheme)} at Severity ${severity.toFixed(1)}`}
        />
      </div>
    </div>
  )
}
