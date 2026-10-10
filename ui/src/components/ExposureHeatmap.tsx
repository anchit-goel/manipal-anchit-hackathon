import React from 'react'
import type { PortfolioData, StressResult } from '../types'
import { formatCurrency, formatPct } from '../utils'
import { TrendingDown, TrendingUp, Layers } from 'lucide-react'

interface ExposureHeatmapProps {
  portfolio: PortfolioData | null
  result: StressResult | null
}

export const ExposureHeatmap: React.FC<ExposureHeatmapProps> = ({ portfolio, result }) => {
  if (!portfolio) {
    return (
      <div className="glass-panel rounded-2xl p-4 h-full flex items-center justify-center text-slate-500 font-mono text-xs">
        Loading portfolio exposures...
      </div>
    )
  }

  // Aggregate positions by sector x asset_type
  const sectors = Object.keys(portfolio.by_sector || {})
  const assetTypes = ['loan', 'bond', 'derivative', 'equity']

  // Create lookup for stress result pnl per position
  const pnlByPos = new Map<string, number>()
  if (result) {
    for (const p of result.positions || []) {
      pnlByPos.set(p.position_id, p.pnl)
    }
  }

  // Calculate sector x asset_type metrics
  interface CellData {
    sector: string
    assetType: string
    marketValue: number
    stressedPnl: number
  }

  const cells: CellData[] = []
  for (const sec of sectors) {
    for (const at of assetTypes) {
      const posList = portfolio.positions.filter((p) => p.sector === sec && p.asset_type === at)
      if (posList.length > 0) {
        const mv = posList.reduce((acc, p) => acc + p.market_value, 0)
        const pnl = posList.reduce((acc, p) => acc + (pnlByPos.get(p.position_id) || 0), 0)
        cells.push({
          sector: sec,
          assetType: at,
          marketValue: mv,
          stressedPnl: pnl,
        })
      }
    }
  }

  // Top 5 losers & winners from the current stress result
  const topLosers = result?.top_losers?.slice(0, 5) || []
  const topWinners = result?.top_winners?.slice(0, 5) || []

  return (
    <div className="glass-panel rounded-2xl p-4 h-full flex flex-col space-y-4 overflow-y-auto">
      <div className="border-b border-slate-800 pb-2">
        <h3 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wide flex items-center gap-1.5">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span>Book Exposure Heatmap (Sector &times; Asset Type)</span>
        </h3>
        <span className="text-[11px] text-slate-400">
          Color indicates stressed shock intensity; cell size represents notional book exposure.
        </span>
      </div>

      {/* Grid of Sector x Asset Type Exposure Tiles */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {cells.map((cell) => {
          const hasStress = result !== null && cell.stressedPnl !== 0
          const isLoss = cell.stressedPnl < 0
          const isGain = cell.stressedPnl > 0
          const pnlPct = cell.marketValue > 0 ? (cell.stressedPnl / cell.marketValue) * 100 : 0

          let tileColor = 'bg-slate-900/60 border-slate-800 text-slate-200'
          if (hasStress) {
            if (isLoss) {
              tileColor = Math.abs(pnlPct) > 5
                ? 'bg-rose-950/70 border-rose-600/60 text-rose-200'
                : 'bg-rose-950/40 border-rose-800/40 text-rose-300'
            } else if (isGain) {
              tileColor = 'bg-emerald-950/60 border-emerald-600/60 text-emerald-200'
            }
          }

          return (
            <div
              key={`${cell.sector}-${cell.assetType}`}
              className={`p-2.5 rounded-xl border transition-all text-xs font-mono flex flex-col justify-between ${tileColor}`}
            >
              <div className="flex justify-between items-start gap-1 mb-1">
                <span className="font-semibold truncate text-[11px] text-slate-100">{cell.sector}</span>
                <span className="text-[10px] uppercase font-bold text-slate-400">{cell.assetType}</span>
              </div>

              <div className="text-[11px] tabular-nums font-mono text-slate-300">
                {formatCurrency(cell.marketValue, 1)}
              </div>

              {hasStress && (
                <div
                  className={`text-[10px] font-bold tabular-nums pt-1 mt-1 border-t border-slate-800/60 flex justify-between ${
                    isLoss ? 'text-rose-400' : 'text-emerald-400'
                  }`}
                >
                  <span>{formatCurrency(cell.stressedPnl, 1)}</span>
                  <span>{formatPct(pnlPct, 1)}</span>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Top 5 Losers and Winners Sub-table */}
      {result && (topLosers.length > 0 || topWinners.length > 0) && (
        <div className="space-y-3 pt-2 border-t border-slate-800">
          {topLosers.length > 0 && (
            <div>
              <h4 className="text-[11px] font-mono font-semibold text-rose-400 uppercase tracking-wide flex items-center gap-1 mb-1.5">
                <TrendingDown className="w-3.5 h-3.5" />
                <span>Top 5 Stressed Positions (Losses)</span>
              </h4>
              <div className="space-y-1 font-mono text-xs">
                {topLosers.map((pos) => (
                  <div
                    key={pos.position_id}
                    className="flex justify-between items-center p-1.5 rounded bg-rose-950/20 border border-rose-900/30"
                  >
                    <div className="truncate max-w-[130px]">
                      <span className="text-slate-200 text-[11px] font-medium block truncate">
                        {pos.counterparty}
                      </span>
                      <span className="text-[10px] text-slate-500 capitalize">{pos.asset_type}</span>
                    </div>
                    <div className="text-right tabular-nums">
                      <span className="text-rose-400 font-bold block text-[11px]">
                        {formatCurrency(pos.pnl)}
                      </span>
                      <span className="text-rose-500 text-[10px]">{formatPct(pos.pnl_pct, 1)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {topWinners.length > 0 && (
            <div>
              <h4 className="text-[11px] font-mono font-semibold text-emerald-400 uppercase tracking-wide flex items-center gap-1 mb-1.5">
                <TrendingUp className="w-3.5 h-3.5" />
                <span>Top Beneficiary Positions (Gains)</span>
              </h4>
              <div className="space-y-1 font-mono text-xs">
                {topWinners.map((pos) => (
                  <div
                    key={pos.position_id}
                    className="flex justify-between items-center p-1.5 rounded bg-emerald-950/20 border border-emerald-900/30"
                  >
                    <div className="truncate max-w-[130px]">
                      <span className="text-slate-200 text-[11px] font-medium block truncate">
                        {pos.counterparty}
                      </span>
                      <span className="text-[10px] text-slate-500 capitalize">{pos.asset_type}</span>
                    </div>
                    <div className="text-right tabular-nums">
                      <span className="text-emerald-400 font-bold block text-[11px]">
                        {formatCurrency(pos.pnl)}
                      </span>
                      <span className="text-emerald-500 text-[10px]">{formatPct(pos.pnl_pct, 1)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
