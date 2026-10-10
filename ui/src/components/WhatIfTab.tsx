import React, { useState } from 'react'
import { Sliders, Play, AlertCircle } from 'lucide-react'
import type { StressResult } from '../types'

interface WhatIfTabProps {
  onRunCustom: (theme: string, severity: number) => Promise<StressResult | null>
  loading?: boolean
}

const THEMES = [
  'shipping_disruption',
  'oil_price_up',
  'oil_price_down',
  'credit_downgrade',
  'credit_default',
  'banking_stress',
  'rate_hike',
  'rate_cut',
  'regulatory_action',
  'antitrust',
  'chip_supply_shock',
  'sanctions',
  'demand_shock',
  'merger_activity',
]

export const WhatIfTab: React.FC<WhatIfTabProps> = ({ onRunCustom, loading }) => {
  const [theme, setTheme] = useState<string>('shipping_disruption')
  const [severity, setSeverity] = useState<number>(8.0)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await onRunCustom(theme, severity)
    } catch (err: any) {
      setError(err?.message || 'Failed to execute custom stress shock')
    }
  }

  return (
    <div className="glass-panel rounded-2xl p-6 max-w-3xl mx-auto h-full overflow-y-auto">
      <div className="border-b border-slate-800 pb-3 mb-6">
        <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <Sliders className="w-5 h-5 text-cyan-400" />
          <span>Macro &amp; Sector What-If Stress Simulator</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Apply simulated macroeconomic, geopolitical, or sector-level shocks to the wholesale banking portfolio at arbitrary severity ratings.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Theme Selector */}
        <div>
          <label className="block text-xs font-mono font-medium text-slate-300 mb-2 uppercase tracking-wide">
            1. Select Controlled Risk Theme
          </label>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-slate-100 font-mono text-sm focus:outline-none focus:ring-1 focus:ring-cyan-400"
          >
            {THEMES.map((th) => (
              <option key={th} value={th}>
                #{th}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-slate-400 mt-1.5 block">
            Transmits via calibrated elasticity matrix indexed by asset type (equity, bond spread, loan PD uplift, derivative MTM).
          </span>
        </div>

        {/* Severity Slider */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-xs font-mono font-medium text-slate-300 uppercase tracking-wide">
              2. Impact Severity Rubric (1 - 10)
            </label>
            <span className="font-mono text-sm font-bold px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-800/40">
              {severity.toFixed(1)} / 10.0
            </span>
          </div>

          <input
            type="range"
            min="1.0"
            max="10.0"
            step="0.5"
            value={severity}
            onChange={(e) => setSeverity(parseFloat(e.target.value))}
            className="w-full accent-cyan-400 cursor-pointer h-2 bg-slate-800 rounded-lg"
          />

          <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-2">
            <span>1.0 (Calm / Routine)</span>
            <span>4.0 (Moderate)</span>
            <span>7.0 (Systemic Trigger)</span>
            <span>10.0 (Global Crisis)</span>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 px-4 rounded-xl font-mono text-xs font-bold uppercase tracking-wider bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 transition-all shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
        >
          <Play className="w-4 h-4 fill-slate-950" />
          <span>{loading ? 'Propagating Shocks...' : 'Propagate Stress Shock to Book'}</span>
        </button>
      </form>
    </div>
  )
}
