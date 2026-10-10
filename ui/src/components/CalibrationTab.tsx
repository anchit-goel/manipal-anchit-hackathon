import React from 'react'
import {
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
  Area,
} from 'recharts'
import { LineChart, AlertTriangle } from 'lucide-react'
import type { CalibrationData } from '../types'

interface CalibrationTabProps {
  data: CalibrationData | null
  loading?: boolean
}

export const CalibrationTab: React.FC<CalibrationTabProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="glass-panel rounded-2xl p-6 max-w-4xl mx-auto h-full flex items-center justify-center font-mono text-xs text-slate-400">
        Loading empirical calibration model...
      </div>
    )
  }

  if (!data || !data.fit) {
    return (
      <div className="glass-panel rounded-2xl p-6 max-w-4xl mx-auto h-full flex flex-col items-center justify-center text-center text-slate-400">
        <AlertTriangle className="w-10 h-10 text-amber-400 mb-2" />
        <h3 className="font-semibold text-slate-200">Calibration Model Not Available</h3>
        <p className="text-xs text-slate-500 mt-1">Run calibration pipeline via backend.</p>
      </div>
    )
  }

  const { fit, buckets, curve } = data

  return (
    <div className="glass-panel rounded-2xl p-6 max-w-4xl mx-auto h-full overflow-y-auto space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-3">
        <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <LineChart className="w-5 h-5 text-cyan-400" />
          <span>Empirical Event-Study Calibration Model</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Grounds LLM impact scores (1-10) in historical abnormal market returns (&Delta;%) using beta-adjusted benchmark event studies.
        </p>
      </div>

      {/* Honest Framing Alert Banner */}
      <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-800/40 text-amber-300 text-xs leading-relaxed flex items-start gap-2">
        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-400" />
        <div>
          <strong className="block text-amber-200 font-mono mb-0.5">Empirical Rigor &amp; Sample Disclaimer:</strong>
          Fitted on n={fit.n_events} verified historical events with Spearman rank correlation &rho;={fit.spearman_rho.toFixed(2)} (p={fit.spearman_pvalue.toExponential(2)}) and Leave-One-Out MAE of {fit.loo_mae_linear.toFixed(2)}%. Predictive 80% intervals are intentionally wide to reflect true market fat tails and prevent false precision on small empirical samples.
        </div>
      </div>

      {/* Key Metric Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] text-slate-400 block mb-1">Sample Size (n)</span>
          <span className="text-lg font-bold text-slate-100">{fit.n_events} Events</span>
          <span className="text-[10px] text-slate-500 block mt-0.5">2016 - 2024 Shocks</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] text-slate-400 block mb-1">Spearman &rho;</span>
          <span className="text-lg font-bold text-cyan-400">+{fit.spearman_rho.toFixed(3)}</span>
          <span className="text-[10px] text-slate-500 block mt-0.5">Monotonic ordering</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] text-slate-400 block mb-1">Leave-One-Out MAE</span>
          <span className="text-lg font-bold text-slate-100">{fit.loo_mae_linear.toFixed(2)}%</span>
          <span className="text-[10px] text-slate-500 block mt-0.5">Cross-validation error</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] text-slate-400 block mb-1">Model Equation</span>
          <span className="text-sm font-bold text-slate-100 block truncate">
            |CAR| = {fit.intercept.toFixed(2)}% + {fit.slope.toFixed(2)} &times; Imp
          </span>
          <span className="text-[10px] text-slate-500 block mt-0.5">Monotone OLS fit</span>
        </div>
      </div>

      {/* Calibration Curve Chart */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <h3 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wide mb-2">
          Engine Impact Score vs Realized |CAR| [0, +1] Event Horizon
        </h3>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={curve} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
              <XAxis
                dataKey="impact"
                type="number"
                domain={[1, 10]}
                stroke="#64748b"
                fontSize={11}
                tickFormatter={(val) => `Imp ${val}`}
              />
              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickFormatter={(val) => `${val}%`}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload
                    return (
                      <div className="bg-slate-900 border border-slate-700 p-2.5 rounded shadow-xl text-xs font-mono">
                        <p className="font-bold text-cyan-300">Impact: {d.impact}</p>
                        <p className="text-slate-200">Expected Move: {d.move_pct?.toFixed(2)}%</p>
                        <p className="text-slate-400 text-[10px]">
                          80% Range: {d.low_pct?.toFixed(2)}% to {d.high_pct?.toFixed(2)}%
                        </p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              {/* 80% Confidence Band */}
              <Area
                dataKey="high_pct"
                stroke="transparent"
                fill="#06b6d4"
                fillOpacity={0.15}
              />
              {/* Fitted Expectation Line */}
              <Line
                type="monotone"
                dataKey="move_pct"
                stroke="#06b6d4"
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="flex justify-between items-center text-[11px] font-mono text-slate-500 mt-2">
          <span>&bull; Teal line = OLS Monotone Fit</span>
          <span>&bull; Shaded region = 80% Confidence Interval</span>
        </div>
      </div>

      {/* Severity Bucket Table */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <h3 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wide mb-3">
          Severity Tier Empirical Distribution Breakdown
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                <th className="py-2 px-3">Severity Bucket</th>
                <th className="py-2 px-3">Impact Range</th>
                <th className="py-2 px-3 text-right">Events (n)</th>
                <th className="py-2 px-3 text-right">Median |CAR|</th>
                <th className="py-2 px-3 text-right">25th Pct</th>
                <th className="py-2 px-3 text-right">75th Pct</th>
                <th className="py-2 px-3 text-right">IQR Band</th>
              </tr>
            </thead>
            <tbody>
              {buckets.map((b) => (
                <tr key={b.bucket} className="border-b border-slate-800/60">
                  <td className="py-2 px-3 font-semibold text-slate-200">{b.bucket}</td>
                  <td className="py-2 px-3 text-slate-400">{b.impact_range}</td>
                  <td className="py-2 px-3 text-right text-slate-300 tabular-nums">{b.n}</td>
                  <td className="py-2 px-3 text-right text-cyan-300 font-bold tabular-nums">
                    {b.median_car_pct > 0 ? `+${b.median_car_pct.toFixed(2)}%` : `${b.median_car_pct.toFixed(2)}%`}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-400 tabular-nums">{b.p25_pct.toFixed(2)}%</td>
                  <td className="py-2 px-3 text-right text-slate-400 tabular-nums">{b.p75_pct.toFixed(2)}%</td>
                  <td className="py-2 px-3 text-right text-slate-500 tabular-nums">{b.iqr_pct.toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
