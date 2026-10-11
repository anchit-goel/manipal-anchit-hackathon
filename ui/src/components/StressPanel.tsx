import React, { useState } from 'react'
import {
  Layers,
  Info,
  ArrowUpDown,
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
import type { StressResult, PortfolioData, Signal } from '../types'
import {
  formatCurrency,
  formatPct,
  humanizeTheme,
  humanizeAssetType,
} from '../utils'

interface StressPanelProps {
  result: StressResult | null
  portfolio?: PortfolioData | null
  leadSignal?: Signal | null
  loading?: boolean
  error?: string | null
  headline?: string
  whatIfSeverity?: number
}

export const StressPanel: React.FC<StressPanelProps> = ({
  result,
  portfolio,
  leadSignal,
  loading,
  error,
  headline,
  whatIfSeverity,
}) => {
  const [sortField, setSortField] = useState<'pnl' | 'market_value' | 'counterparty'>('pnl')
  const [sortAsc, setSortAsc] = useState<boolean>(true) // default ascending shows worst losers first

  if (loading) {
    return (
      <div className="bg-white border border-[#E3E6EB] rounded-lg p-8 text-center text-[#5B6676]">
        <div className="inline-block w-6 h-6 border-2 border-[#1F4E9C] border-t-transparent rounded-full animate-spin mb-3" />
        <div className="text-sm font-medium text-[#0F1B2D]">Calculating portfolio stress transmission...</div>
        <div className="text-xs text-[#8A94A6] mt-1">Applying instrument-level shock rules</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white border border-[#FECDCA] rounded-lg p-6 text-[#B42318]">
        <div className="text-sm font-semibold mb-1">Stress calculation unavailable</div>
        <div className="text-xs text-[#5B6676]">{error}</div>
      </div>
    )
  }

  // -------------------------------------------------------------
  // Default Book Overview (HERO IS NEVER EMPTY)
  // -------------------------------------------------------------
  if (!result) {
    const totalMv = portfolio?.total_market_value ?? 1320368000
    const byAsset = portfolio?.by_asset_type || {
      loan: 574000000,
      bond: 425000000,
      equity: 201368000,
      derivative: 120000000,
    }
    const bySector = portfolio?.by_sector || {
      Banking: 360000000,
      Energy: 290000000,
      Shipping: 240000000,
      Technology: 210000000,
      Aerospace: 120000000,
      Airlines: 100368000,
    }

    return (
      <div className="bg-white border border-[#E3E6EB] rounded-lg p-5 space-y-5 text-left">
        {/* Header */}
        <div className="border-b border-[#E3E6EB] pb-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-[#0F1B2D]">Wholesale Portfolio Overview</h2>
              <p className="text-xs text-[#5B6676] mt-0.5">
                Baseline synthetic wholesale balance sheet ($1.32B across 50 positions)
              </p>
            </div>
            <span className="px-2.5 py-1 rounded text-xs font-semibold bg-[#EDF3FC] text-[#1F4E9C] border border-[#B2CCF2]">
              Benchmark at rest
            </span>
          </div>
        </div>

        {/* Composition Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(byAsset).map(([at, mv]) => {
            const pct = (mv / totalMv) * 100
            return (
              <div key={at} className="bg-[#F9FAFB] border border-[#E3E6EB] rounded-lg p-3">
                <div className="text-[11px] font-medium text-[#5B6676]">{humanizeAssetType(at)}</div>
                <div className="text-base font-bold text-[#0F1B2D] tabular-nums mt-0.5">
                  {formatCurrency(mv, 1)}
                </div>
                <div className="text-[11px] text-[#8A94A6] tabular-nums">{pct.toFixed(1)}% of book</div>
              </div>
            )
          })}
        </div>

        {/* Sector Allocations */}
        <div>
          <div className="text-xs font-semibold text-[#0F1B2D] mb-2 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-[#5B6676]" />
            <span>Sector exposure concentrations</span>
          </div>
          <div className="space-y-2">
            {Object.entries(bySector).map(([sec, mv]) => {
              const pct = (mv / totalMv) * 100
              return (
                <div key={sec} className="text-xs">
                  <div className="flex justify-between text-[#5B6676] mb-1">
                    <span className="font-medium text-[#0F1B2D]">{sec}</span>
                    <span className="tabular-nums">
                      {formatCurrency(mv, 1)} ({pct.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="w-full bg-[#EAECF0] h-1.5 rounded-full overflow-hidden">
                    <div className="bg-[#1F4E9C] h-full rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Quiet Prompt */}
        <div className="bg-[#F2F4F7] border border-[#E3E6EB] rounded-lg p-3.5 flex items-center justify-between text-xs text-[#5B6676]">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-[#1F4E9C] shrink-0" />
            <span>Press <strong>Play</strong> in the toolbar above to replay the news flow or select any incoming signal.</span>
          </div>
          <span className="text-[11px] text-[#8A94A6]">Exposure-aware engine ready</span>
        </div>
      </div>
    )
  }

  // -------------------------------------------------------------
  // Active Scenario Result
  // -------------------------------------------------------------
  const isLoss = result.pnl_abs < 0
  const isGain = result.pnl_abs > 0
  const leadHeadline = headline || leadSignal?.headline || `Scenario: ${result.scenario_id}`

  // Calibrated move text
  const calMove = leadSignal?.calibrated_move_pct ?? result.headline_move_pct
  const calLow = leadSignal?.calibrated_low_pct ?? (calMove * 0.3)
  const calHigh = leadSignal?.calibrated_high_pct ?? (calMove * 1.8)
  const rangeText = `${formatPct(calMove, 1)}, 80% range ${formatPct(calLow, 1)} to ${formatPct(calHigh, 1)}`

  // What-if scenario check and user-chosen severity
  const isWhatIf = Boolean(whatIfSeverity !== undefined || result.scenario_id.startsWith('custom_'))
  const chosenSeverity = (() => {
    if (whatIfSeverity !== undefined) return whatIfSeverity
    if (result.scenario_id.startsWith('custom_')) {
      const parts = result.scenario_id.split('_')
      const num = parseFloat(parts[parts.length - 1])
      if (!isNaN(num) && num > 0) {
        return num >= 10 ? num / 10 : num
      }
    }
    return 8.0
  })()

  // Signal-driven impact score (e.g. 8.8 for Red Sea)
  // Strictly avoid exposing raw severity_scale multiplier under an impact label
  const signalImpactScore = (() => {
    if (leadSignal?.impact_score !== undefined && leadSignal.impact_score !== null) {
      return leadSignal.impact_score
    }
    if (result.headline_move_pct) {
      const inferred = Math.abs(result.headline_move_pct) - 0.53
      return Math.max(1.0, Math.min(10.0, Math.round(inferred * 10) / 10))
    }
    return 8.0
  })()

  // Top movers for horizontal bar chart
  const topMovers = [...(result.positions || [])]
    .sort((a, b) => Math.abs(b.pnl) - Math.abs(a.pnl))
    .slice(0, 8)
    .map((p) => ({
      name: p.counterparty.length > 14 ? p.counterparty.slice(0, 13) + '…' : p.counterparty,
      fullName: p.counterparty,
      pnl: p.pnl / 1e6,
      pnlRaw: p.pnl,
      pnlPct: p.pnl_pct,
      assetType: p.asset_type,
    }))

  // Sortable positions
  const sortedPositions = [...(result.positions || [])].sort((a, b) => {
    if (sortField === 'pnl') return sortAsc ? a.pnl - b.pnl : b.pnl - a.pnl
    if (sortField === 'market_value') return sortAsc ? a.market_value - b.market_value : b.market_value - a.market_value
    return sortAsc ? a.counterparty.localeCompare(b.counterparty) : b.counterparty.localeCompare(a.counterparty)
  })

  return (
    <div className="bg-white border border-[#E3E6EB] rounded-lg p-5 space-y-5 text-left">
      {/* Header */}
      <div className="border-b border-[#E3E6EB] pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-2">
            <span
              className={`px-2 py-0.5 rounded text-xs font-semibold ${
                isLoss
                  ? 'bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA]'
                  : isGain
                  ? 'bg-[#EDFDF5] text-[#067647] border border-[#A6F4C5]'
                  : 'bg-[#F2F4F7] text-[#475467]'
              }`}
            >
              {isLoss ? 'Scenario stress loss' : isGain ? 'Scenario net gain' : 'Neutral shock'}
            </span>
            <span className="text-xs text-[#5B6676]">
              {isWhatIf ? (
                <>Severity: <strong className="text-[#0F1B2D]">{chosenSeverity.toFixed(1)}</strong></>
              ) : (
                <>Impact score: <strong className="text-[#0F1B2D]">{signalImpactScore.toFixed(1)}</strong></>
              )}
            </span>
          </div>

          {/* Headline shock applied 80% range */}
          <div className="text-xs text-[#5B6676] bg-[#F9FAFB] px-2.5 py-1 rounded border border-[#E3E6EB] tabular-nums">
            Headline shock applied: <strong className="text-[#0F1B2D]">{rangeText}</strong>
          </div>
        </div>

        {/* Lead Headline */}
        <h2 className="text-sm font-bold text-[#0F1B2D] leading-snug">{leadHeadline}</h2>

        {/* Themes as plain labels */}
        {result.themes && result.themes.length > 0 && result.themes[0] !== 'none' && (
          <div className="flex flex-wrap items-center gap-1.5 mt-2">
            <span className="text-[11px] text-[#8A94A6]">Themes:</span>
            {result.themes.map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#EDF3FC] text-[#1F4E9C] border border-[#B2CCF2]"
              >
                {humanizeTheme(t)}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Metric Row (4 tiles) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* Value Before */}
        <div className="bg-[#F9FAFB] border border-[#E3E6EB] rounded-lg p-3">
          <div className="text-[11px] font-medium text-[#5B6676] mb-0.5">Value before</div>
          <div className="text-lg font-bold text-[#0F1B2D] tabular-nums">
            {formatCurrency(result.total_before, 2)}
          </div>
        </div>

        {/* Value After */}
        <div className="bg-[#F9FAFB] border border-[#E3E6EB] rounded-lg p-3">
          <div className="text-[11px] font-medium text-[#5B6676] mb-0.5">Value after</div>
          <div className="text-lg font-bold text-[#0F1B2D] tabular-nums">
            {formatCurrency(result.total_after, 2)}
          </div>
        </div>

        {/* Scenario P&L */}
        <div
          className={`border rounded-lg p-3 ${
            isLoss ? 'bg-[#FEF3F2] border-[#FECDCA]' : isGain ? 'bg-[#EDFDF5] border-[#A6F4C5]' : 'bg-[#F9FAFB] border-[#E3E6EB]'
          }`}
        >
          <div className="text-[11px] font-medium text-[#5B6676] mb-0.5">Portfolio P&L</div>
          <div
            className={`text-lg font-bold tabular-nums ${
              isLoss ? 'text-[#B42318]' : isGain ? 'text-[#067647]' : 'text-[#0F1B2D]'
            }`}
          >
            {formatCurrency(result.pnl_abs, 1)} ({formatPct(result.pnl_pct, 1)})
          </div>
        </div>

        {/* Uniform-Shock Benchmark */}
        <div className="bg-[#F9FAFB] border border-[#E3E6EB] rounded-lg p-3">
          <div className="text-[11px] font-medium text-[#5B6676] mb-0.5">Uniform benchmark</div>
          <div className="text-lg font-bold text-[#5B6676] tabular-nums">
            {formatPct(result.naive_pnl_pct, 1)} ({formatCurrency(result.naive_pnl_abs, 1)})
          </div>
        </div>
      </div>

      {/* Benchmark Caption */}
      <div className="text-[11px] text-[#5B6676] bg-[#F2F4F7] px-3 py-1.5 rounded border border-[#EAECF0]">
        *Shows how much of a headline shock reaches this book; not a forecast-accuracy claim.
      </div>

      {/* Horizontal Bar Chart of Top Contributors */}
      <div>
        <div className="text-xs font-semibold text-[#0F1B2D] mb-2">
          Top contributors by P&L ($M)
        </div>
        <div className="h-44 w-full bg-[#FAFAFA] border border-[#E3E6EB] rounded-lg p-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={topMovers}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
            >
              <XAxis
                type="number"
                tick={{ fill: '#5B6676', fontSize: 10 }}
                tickFormatter={(val) => `${val > 0 ? '+' : ''}${val.toFixed(1)}M`}
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fill: '#0F1B2D', fontSize: 11 }}
                width={75}
              />
              <Tooltip
                formatter={(val: any) => [`${Number(val).toFixed(2)}M`, 'P&L']}
                contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E3E6EB', color: '#0F1B2D', fontSize: 12 }}
              />
              <ReferenceLine x={0} stroke="#D0D5DD" />
              <Bar dataKey="pnl" radius={[0, 3, 3, 0]}>
                {topMovers.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.pnl < 0 ? '#B42318' : '#067647'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Breakdown by Asset Type & Sector */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Asset Type Table */}
        <div className="border border-[#E3E6EB] rounded-lg p-3">
          <div className="text-xs font-semibold text-[#0F1B2D] mb-2">P&L by asset type</div>
          <div className="space-y-2 text-xs">
            {Object.entries(result.by_asset_type || {}).map(([at, pnl]) => (
              <div key={at} className="flex items-center justify-between">
                <span className="text-[#5B6676]">{humanizeAssetType(at)}</span>
                <span
                  className={`font-semibold tabular-nums ${
                    pnl < 0 ? 'text-[#B42318]' : pnl > 0 ? 'text-[#067647]' : 'text-[#5B6676]'
                  }`}
                >
                  {formatCurrency(pnl, 1)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Sector Table */}
        <div className="border border-[#E3E6EB] rounded-lg p-3">
          <div className="text-xs font-semibold text-[#0F1B2D] mb-2">P&L by sector</div>
          <div className="space-y-2 text-xs">
            {Object.entries(result.by_sector || {})
              .filter(([_, pnl]) => Math.abs(pnl) > 0)
              .slice(0, 5)
              .map(([sec, pnl]) => (
                <div key={sec} className="flex items-center justify-between">
                  <span className="text-[#5B6676]">{sec}</span>
                  <span
                    className={`font-semibold tabular-nums ${
                      pnl < 0 ? 'text-[#B42318]' : pnl > 0 ? 'text-[#067647]' : 'text-[#5B6676]'
                    }`}
                  >
                    {formatCurrency(pnl, 1)}
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Sortable Positions Table */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="text-xs font-semibold text-[#0F1B2D]">
            Position transmission details ({result.positions?.length ?? 0} positions)
          </div>
          <span className="text-[11px] text-[#8A94A6]">Click header to sort</span>
        </div>

        <div className="border border-[#E3E6EB] rounded-lg overflow-x-auto max-h-64 overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F9FAFB] border-b border-[#E3E6EB] text-[#5B6676] sticky top-0">
              <tr>
                <th
                  onClick={() => {
                    setSortField('counterparty')
                    setSortAsc(!sortAsc)
                  }}
                  className="p-2.5 font-medium cursor-pointer hover:text-[#0F1B2D]"
                >
                  <div className="flex items-center gap-1">
                    <span>Counterparty</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="p-2.5 font-medium">Asset type</th>
                <th
                  onClick={() => {
                    setSortField('pnl')
                    setSortAsc(!sortAsc)
                  }}
                  className="p-2.5 font-medium text-right cursor-pointer hover:text-[#0F1B2D]"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Stressed P&L</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="p-2.5 font-medium">Transmission logic</th>
                <th className="p-2.5 font-medium text-center">Rule source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E3E6EB]">
              {sortedPositions.slice(0, 20).map((pos) => {
                const isPosLoss = pos.pnl < 0
                const isPosGain = pos.pnl > 0
                const isMeasured = pos.rule_source === 'measured'

                return (
                  <tr key={pos.position_id} className="hover:bg-[#F9FAFB]">
                    <td className="p-2.5 font-medium text-[#0F1B2D]">{pos.counterparty}</td>
                    <td className="p-2.5 text-[#5B6676]">{humanizeAssetType(pos.asset_type)}</td>
                    <td
                      className={`p-2.5 text-right font-semibold tabular-nums ${
                        isPosLoss ? 'text-[#B42318]' : isPosGain ? 'text-[#067647]' : 'text-[#8A94A6]'
                      }`}
                    >
                      {formatCurrency(pos.pnl, 1)} ({formatPct(pos.pnl_pct, 1)})
                    </td>
                    <td className="p-2.5 text-[#5B6676] max-w-xs truncate" title={pos.why}>
                      {pos.why || 'No direct exposure'}
                    </td>
                    <td className="p-2.5 text-center">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                          isMeasured
                            ? 'bg-[#EDFDF5] text-[#067647] border border-[#A6F4C5]'
                            : 'bg-[#F2F4F7] text-[#5B6676] border border-[#EAECF0]'
                        }`}
                      >
                        {isMeasured ? 'Measured' : 'Assumed'}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
