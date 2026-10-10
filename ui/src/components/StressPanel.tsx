import React, { useState } from 'react'
import {
  TrendingDown,
  TrendingUp,
  Layers,
  HelpCircle,
  ShieldAlert,
  ArrowRight,
  Info,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts'
import type { StressResult, PositionImpact } from '../types'
import { formatCurrency, formatPct } from '../utils'

interface StressPanelProps {
  result: StressResult | null
  loading?: boolean
  error?: string | null
  headline?: string
}

export const StressPanel: React.FC<StressPanelProps> = ({
  result,
  loading,
  error,
  headline,
}) => {
  const [selectedPosition, setSelectedPosition] = useState<PositionImpact | null>(null)

  if (loading) {
    return (
      <div className="glass-panel rounded-2xl p-6 h-full flex flex-col justify-center items-center text-slate-400">
        <div className="w-10 h-10 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="font-mono text-sm tracking-wide">COMPUTING EXPOSURE SHOCKS...</p>
        <span className="text-xs text-slate-500 mt-1">Transmitting stress vectors through wholesale book</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass-panel rounded-2xl p-6 h-full flex flex-col justify-center items-center text-center">
        <ShieldAlert className="w-12 h-12 text-rose-400 mb-3" />
        <h3 className="font-semibold text-lg text-slate-100 mb-1">Stress Test Unqualified</h3>
        <p className="text-sm text-slate-400 max-w-md">{error}</p>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="glass-panel rounded-2xl p-6 h-full flex flex-col justify-center items-center text-center text-slate-400">
        <Layers className="w-12 h-12 text-slate-600 mb-3" />
        <h3 className="font-semibold text-lg text-slate-200 mb-1">Wholesale Stress Testing Engine</h3>
        <p className="text-xs text-slate-400 max-w-md">
          Awaiting risk trigger from live narrative feed or what-if scenario. Signals with severity &gt; 7.0 and confidence &ge; 60% automatically propagate shocks.
        </p>
      </div>
    )
  }

  const isNetGain = result.pnl_abs > 0
  const isNetZero = Math.abs(result.pnl_abs) < 1000

  // Prepare waterfall chart data
  const chartData = (result.waterfall || []).map((item) => ({
    name: item.label,
    pnl: item.pnl,
    displayPnl: item.pnl / 1e6, // In Millions for neat chart scale
  }))

  return (
    <div className="glass-panel rounded-2xl p-5 h-full flex flex-col overflow-y-auto space-y-5">
      {/* Scenario Header Banner */}
      <div className="border-b border-slate-800 pb-3">
        <div className="flex items-center justify-between gap-3 mb-1.5">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[11px] font-mono uppercase font-bold tracking-wider bg-rose-500/20 text-rose-300 border border-rose-500/40">
              {result.scenario_id}
            </span>
            {result.themes.map((th) => (
              <span
                key={th}
                className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300 border border-slate-700"
              >
                #{th}
              </span>
            ))}
          </div>

          <div className="text-xs font-mono text-slate-400">
            Severity Scale: <span className="text-slate-100 font-bold">{result.severity_scale.toFixed(2)}x</span>
          </div>
        </div>

        {headline && (
          <h2 className="text-base font-semibold text-slate-100 mt-2 line-clamp-2">
            {headline}
          </h2>
        )}

        {result.corroborating_signal_ids && result.corroborating_signal_ids.length > 0 && (
          <div className="text-xs text-slate-400 mt-1 flex items-center gap-1.5 font-mono">
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            <span>Debounced scenario merged {result.corroborating_signal_ids.length} corroborating signals within 48h</span>
          </div>
        )}
      </div>

      {/* Hero Metric: Portfolio Before -> After */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 shadow-inner">
        <div>
          <span className="text-xs font-mono text-slate-400 block mb-1">Portfolio Book Value</span>
          <div className="text-xl md:text-2xl font-mono font-bold text-slate-100 tabular-nums">
            {formatCurrency(result.total_before)}
          </div>
          <span className="text-[11px] text-slate-500">50 wholesale positions</span>
        </div>

        <div className="flex flex-col justify-center items-start md:items-center">
          <div className="flex items-center gap-2 text-slate-400 mb-1">
            <span className="text-xs font-mono">Portfolio Impact</span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
          </div>
          <div
            className={`text-xl md:text-2xl font-mono font-bold flex items-center gap-1.5 tabular-nums ${
              isNetGain ? 'text-emerald-400' : isNetZero ? 'text-slate-300' : 'text-rose-400'
            }`}
          >
            {isNetGain ? (
              <TrendingUp className="w-5 h-5 text-emerald-400" />
            ) : isNetZero ? null : (
              <TrendingDown className="w-5 h-5 text-rose-400" />
            )}
            <span>{formatCurrency(result.pnl_abs)}</span>
            <span className="text-sm font-normal">({formatPct(result.pnl_pct)})</span>
          </div>
          <span className="text-[11px] text-slate-400">
            {result.positions_hit} of {result.positions?.length || 50} positions impacted
          </span>
        </div>

        <div className="md:text-right">
          <span className="text-xs font-mono text-slate-400 block mb-1">Stressed Book Value</span>
          <div className="text-xl md:text-2xl font-mono font-bold text-slate-100 tabular-nums">
            {formatCurrency(result.total_after)}
          </div>
          <span className="text-[11px] text-slate-500">Post-shock repricing</span>
        </div>
      </div>

      {/* Comparison: Exposure-Aware vs Uniform Benchmark */}
      <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
        <div className="flex justify-between items-center mb-1.5">
          <h4 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wide flex items-center gap-1.5">
            <span>Exposure-Aware Model vs Uniform-Shock Benchmark</span>
            <span title="Shows how much of a headline shock actually reaches this book; not a forecast-accuracy claim.">
              <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            </span>
          </h4>
        </div>
        <p className="text-[11px] text-slate-400 mb-3">
          Uniform-shock benchmark shows how much of a headline shock actually reaches this book; not a forecast-accuracy claim.
        </p>

        <div className="space-y-2 font-mono text-xs">
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-slate-300">Uniform-Shock Benchmark (Flat {formatPct(result.headline_move_pct)}):</span>
              <span className="text-rose-400 font-bold tabular-nums">
                {formatCurrency(result.naive_pnl_abs)} ({formatPct(result.naive_pnl_pct)})
              </span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-rose-600/70 rounded-full"
                style={{ width: `${Math.min(100, Math.abs(result.naive_pnl_pct) * 8)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <span className="text-cyan-300 font-medium">Signal-to-Shock Exposure-Aware PnL:</span>
              <span
                className={`font-bold tabular-nums ${
                  isNetGain ? 'text-emerald-400' : isNetZero ? 'text-slate-300' : 'text-rose-400'
                }`}
              >
                {formatCurrency(result.pnl_abs)} ({formatPct(result.pnl_pct)})
              </span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${isNetGain ? 'bg-emerald-500' : 'bg-rose-500'}`}
                style={{ width: `${Math.min(100, Math.abs(result.pnl_pct) * 8)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Waterfall Contribution Chart */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex justify-between items-center mb-2">
          <h4 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wide">
            Loss & Gain Waterfall Decomposition ($ Millions)
          </h4>
        </div>
        <div className="h-44 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
              <XAxis
                dataKey="name"
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
                interval={0}
                angle={-25}
                textAnchor="end"
              />
              <YAxis
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
                tickFormatter={(val) => `${val > 0 ? '+' : ''}${val}M`}
              />
              <ReferenceLine y={0} stroke="#334155" />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload
                    return (
                      <div className="bg-slate-900 border border-slate-700 p-2 rounded shadow-xl text-xs font-mono">
                        <p className="font-semibold text-slate-100">{data.name}</p>
                        <p className={data.pnl >= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                          {formatCurrency(data.pnl)}
                        </p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Bar dataKey="displayPnl" radius={[3, 3, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.name === 'Total' ? (entry.pnl >= 0 ? '#10b981' : '#f43f5e') : entry.pnl >= 0 ? '#10b981' : '#ef4444'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Position Breakdown Table with "Why This Position" and Measured/Assumed Tags */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
        <h4 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wide mb-2.5">
          Top Impacted Positions &amp; Transmission Explanations
        </h4>
        <div className="overflow-x-auto max-h-56">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                <th className="py-1.5 px-2">ID</th>
                <th className="py-1.5 px-2">Counterparty</th>
                <th className="py-1.5 px-2">Asset Type</th>
                <th className="py-1.5 px-2 text-right">Market Value</th>
                <th className="py-1.5 px-2 text-right">Stress PnL</th>
                <th className="py-1.5 px-2 text-right">Move %</th>
                <th className="py-1.5 px-2">Transmission Mechanism</th>
              </tr>
            </thead>
            <tbody>
              {result.positions
                .filter((p) => p.pnl !== 0)
                .sort((a, b) => a.pnl - b.pnl)
                .map((pos) => {
                  const isPosLoss = pos.pnl < 0
                  return (
                    <tr
                      key={pos.position_id}
                      onClick={() => setSelectedPosition(pos)}
                      className="border-b border-slate-800/60 hover:bg-slate-800/50 cursor-pointer"
                    >
                      <td className="py-2 px-2 text-slate-400 text-[11px]">{pos.position_id}</td>
                      <td className="py-2 px-2 font-medium text-slate-200 truncate max-w-[140px]">
                        {pos.counterparty}
                      </td>
                      <td className="py-2 px-2 text-slate-300 capitalize">{pos.asset_type}</td>
                      <td className="py-2 px-2 text-right tabular-nums text-slate-300">
                        {formatCurrency(pos.market_value)}
                      </td>
                      <td
                        className={`py-2 px-2 text-right tabular-nums font-bold ${
                          isPosLoss ? 'text-rose-400' : 'text-emerald-400'
                        }`}
                      >
                        {formatCurrency(pos.pnl)}
                      </td>
                      <td
                        className={`py-2 px-2 text-right tabular-nums ${
                          isPosLoss ? 'text-rose-400' : 'text-emerald-400'
                        }`}
                      >
                        {formatPct(pos.pnl_pct)}
                      </td>
                      <td className="py-2 px-2 text-slate-400 text-[11px] max-w-[220px]">
                        <div className="flex items-center gap-1.5 truncate" title={pos.why}>
                          {pos.rule_source && (
                            <span
                              className={`px-1 py-0.2 rounded text-[9px] uppercase font-bold ${
                                pos.rule_source === 'measured'
                                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                                  : 'bg-amber-950 text-amber-300 border border-amber-800'
                              }`}
                            >
                              {pos.rule_source}
                            </span>
                          )}
                          <span className="truncate">{pos.why}</span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Position Detail Modal / Drawer */}
      {selectedPosition && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        >
          <div className="glass-panel p-5 rounded-2xl max-w-md w-full border border-slate-700 shadow-2xl">
            <div className="flex justify-between items-center mb-3 border-b border-slate-800 pb-2">
              <h3 className="font-semibold text-slate-100 flex items-center gap-2">
                <span>{selectedPosition.counterparty}</span>
                <span className="text-xs font-mono text-cyan-400">({selectedPosition.position_id})</span>
              </h3>
              <button
                type="button"
                onClick={() => setSelectedPosition(null)}
                className="text-slate-400 hover:text-slate-100 font-mono text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex justify-between text-slate-300">
                <span>Asset Type / Sector:</span>
                <span className="font-semibold text-slate-100 capitalize">
                  {selectedPosition.asset_type} · {selectedPosition.sector}
                </span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Book Value:</span>
                <span className="font-semibold text-slate-100">{formatCurrency(selectedPosition.market_value)}</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Stressed PnL:</span>
                <span
                  className={`font-bold ${
                    selectedPosition.pnl < 0 ? 'text-rose-400' : 'text-emerald-400'
                  }`}
                >
                  {formatCurrency(selectedPosition.pnl)} ({formatPct(selectedPosition.pnl_pct)})
                </span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Exposure Tag Matched:</span>
                <span className="text-cyan-300">#{selectedPosition.tag || 'none'}</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Shock Rule Origin:</span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ${
                    selectedPosition.rule_source === 'measured'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                      : 'bg-amber-950 text-amber-300 border border-amber-800'
                  }`}
                >
                  {selectedPosition.rule_source || 'assumed'}
                </span>
              </div>

              <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-300 leading-relaxed">
                <span className="text-slate-400 block mb-1">Transmission Rationale:</span>
                {selectedPosition.why}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
