import React from 'react'
import { ResponsiveContainer, Treemap, Tooltip } from 'recharts'
import type { PortfolioData, StressResult } from '../types'
import { formatCurrency, formatPct, humanizeAssetType } from '../utils'
import { ArrowDown, ArrowUp } from 'lucide-react'

interface ExposureHeatmapProps {
  portfolio: PortfolioData | null
  result: StressResult | null
}

interface TilePayload {
  name: string
  sector: string
  assetType: string
  size: number
  pnl: number
  pnlPct: number
  [key: string]: any
}

export const ExposureHeatmap: React.FC<ExposureHeatmapProps> = ({ portfolio, result }) => {

  if (!portfolio) {
    return (
      <div className="bg-white border border-[#E3E6EB] rounded-lg p-6 text-center text-[#5B6676] text-xs">
        Loading portfolio exposure data...
      </div>
    )
  }

  // Pre-index stressed PnL by position_id
  const pnlByPos = new Map<string, { pnl: number; pnlPct: number }>()
  if (result?.positions) {
    for (const p of result.positions) {
      pnlByPos.set(p.position_id, { pnl: p.pnl, pnlPct: p.pnl_pct })
    }
  }

  // Build aggregate nodes: sector -> asset_type
  const sectors = Object.keys(portfolio.by_sector || {})
  const assetTypes = ['loan', 'bond', 'derivative', 'equity']

  const treemapData: TilePayload[] = []
  for (const sec of sectors) {
    for (const at of assetTypes) {
      const posList = (portfolio.positions || []).filter(
        (p) => p.sector === sec && p.asset_type === at
      )
      if (posList.length > 0) {
        const mv = posList.reduce((acc, p) => acc + p.market_value, 0)
        let stressedPnl = 0
        for (const p of posList) {
          const impact = pnlByPos.get(p.position_id)
          if (impact) stressedPnl += impact.pnl
        }
        const stressedPct = mv > 0 ? (stressedPnl / mv) * 100 : 0

        treemapData.push({
          name: `${sec} ${at}`,
          sector: sec,
          assetType: at,
          size: mv,
          pnl: stressedPnl,
          pnlPct: stressedPct,
        })
      }
    }
  }

  // Helper to color tiles
  const getTileColor = (pnlPct: number, hasActiveResult: boolean) => {
    if (!hasActiveResult) {
      return '#E2E8F0' // neutral blue-grey at rest
    }
    if (pnlPct < -5.0) return '#B42318' // deep loss red
    if (pnlPct < -0.1) return '#FECDCA' // light loss red
    if (pnlPct > 5.0) return '#067647' // deep gain green
    if (pnlPct > 0.1) return '#A6F4C5' // light gain green
    return '#EAECF0' // neutral unchanged
  }

  const getTextColor = (pnlPct: number, hasActiveResult: boolean) => {
    if (!hasActiveResult) return '#0F1B2D'
    if (pnlPct < -5.0 || pnlPct > 5.0) return '#FFFFFF'
    if (pnlPct < -0.1) return '#912018'
    if (pnlPct > 0.1) return '#054F31'
    return '#0F1B2D'
  }

  // Custom Treemap Tile Content
  const CustomContent = (props: any) => {
    const { x, y, width, height, sector, assetType, pnlPct = 0, name } = props
    if (!width || !height || width <= 0 || height <= 0) return null

    const hasActiveResult = !!result
    const fill = getTileColor(pnlPct, hasActiveResult)
    const textColor = getTextColor(pnlPct, hasActiveResult)

    const canFitLabel = width >= 48 && height >= 24
    const canFitSubtext = width >= 65 && height >= 42
    const displaySector = (sector || name || '').slice(0, 8)
    const displayAsset = assetType ? humanizeAssetType(assetType).split(' ')[0] : ''

    return (
      <g className="cursor-pointer transition-opacity hover:opacity-90">
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          fill={fill}
          stroke="#FFFFFF"
          strokeWidth={1.5}
          rx={3}
        />
        {canFitLabel && displaySector && (
          <text
            x={x + 4}
            y={y + 14}
            fill={textColor}
            fontSize={10}
            fontWeight={600}
            fontFamily="Inter, sans-serif"
          >
            {displaySector}
          </text>
        )}
        {canFitSubtext && displayAsset && (
          <text
            x={x + 4}
            y={y + 26}
            fill={textColor}
            fontSize={9}
            fontFamily="Inter, sans-serif"
            opacity={0.85}
          >
            {displayAsset}
          </text>
        )}
        {canFitSubtext && hasActiveResult && (
          <text
            x={x + 4}
            y={y + 37}
            fill={textColor}
            fontSize={9}
            fontWeight={700}
            fontFamily="Inter, sans-serif"
          >
            {formatPct(pnlPct, 1)}
          </text>
        )}
      </g>
    )
  }

  // Top 5 losers and winners
  const topLosers = [...(result?.top_losers || [])].slice(0, 5)
  const topWinners = [...(result?.top_winners || [])]
    .filter((w) => w.pnl > 0)
    .slice(0, 5)

  return (
    <div className="bg-white border border-[#E3E6EB] rounded-lg p-4 space-y-4 text-left">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#E3E6EB] pb-2.5">
        <div>
          <h3 className="text-xs font-bold text-[#0F1B2D]">Portfolio Exposure Treemap</h3>
          <p className="text-[11px] text-[#5B6676] mt-0.5">
            Area proportional to market value ($1.32B wholesale book)
          </p>
        </div>
        <span className="text-[11px] text-[#8A94A6]">
          {result ? 'Shocked by scenario' : 'Resting state'}
        </span>
      </div>

      {/* Real Treemap Chart */}
      <div className="h-56 w-full bg-[#F9FAFB] border border-[#E3E6EB] rounded-lg p-1.5 relative">
        <ResponsiveContainer width="100%" height="100%">
          <Treemap
            data={treemapData as any}
            dataKey="size"
            aspectRatio={4 / 3}
            content={<CustomContent />}
          >
            <Tooltip
              content={({ active, payload }) => {
                const data = payload?.[0]?.payload
                if (!active || !data) return null
                return (
                  <div className="bg-white border border-[#E3E6EB] shadow-md rounded p-2 text-xs">
                    <div className="font-semibold text-[#0F1B2D] mb-0.5">
                      {data.sector} · {humanizeAssetType(data.assetType)}
                    </div>
                    <div className="text-[#5B6676]">
                      Market value: <strong className="text-[#0F1B2D]">{formatCurrency(data.size, 1)}</strong>
                    </div>
                    {result && (
                      <div className="text-[#5B6676] mt-0.5">
                        Stressed P&L:{' '}
                        <strong className={data.pnl < 0 ? 'text-[#B42318]' : data.pnl > 0 ? 'text-[#067647]' : 'text-[#0F1B2D]'}>
                          {formatCurrency(data.pnl, 1)} ({formatPct(data.pnlPct, 1)})
                        </strong>
                      </div>
                    )}
                  </div>
                )
              }}
            />
          </Treemap>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-between text-[10px] text-[#5B6676] px-1">
        <span>Legend:</span>
        <div className="flex items-center gap-1.5">
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-[#B42318]" />
            <span>&lt; −5%</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-[#FECDCA]" />
            <span>&lt; 0%</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-[#E2E8F0]" />
            <span>Neutral</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-[#A6F4C5]" />
            <span>&gt; 0%</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-[#067647]" />
            <span>&gt; +5%</span>
          </div>
        </div>
      </div>

      {/* Top 5 Losers and Top 5 Winners */}
      {result && (
        <div className="space-y-3 pt-2 border-t border-[#E3E6EB]">
          {/* Losers */}
          {topLosers.length > 0 && (
            <div>
              <div className="text-[11px] font-semibold text-[#B42318] mb-1.5 flex items-center gap-1">
                <ArrowDown className="w-3 h-3 text-[#B42318]" />
                <span>Largest scenario impairments</span>
              </div>
              <div className="space-y-1">
                {topLosers.map((pos) => (
                  <div
                    key={pos.position_id}
                    className="flex items-center justify-between text-[11px] py-1 px-1.5 rounded bg-[#FEF3F2] border border-[#FECDCA]"
                  >
                    <span className="font-medium text-[#0F1B2D] truncate max-w-[170px]">
                      {pos.counterparty}
                    </span>
                    <span className="font-semibold text-[#B42318] tabular-nums shrink-0">
                      {formatCurrency(pos.pnl, 1)} ({formatPct(pos.pnl_pct, 1)})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Winners */}
          {topWinners.length > 0 && (
            <div>
              <div className="text-[11px] font-semibold text-[#067647] mb-1.5 flex items-center gap-1">
                <ArrowUp className="w-3 h-3 text-[#067647]" />
                <span>Beneficiary offsets</span>
              </div>
              <div className="space-y-1">
                {topWinners.map((pos) => (
                  <div
                    key={pos.position_id}
                    className="flex items-center justify-between text-[11px] py-1 px-1.5 rounded bg-[#EDFDF5] border border-[#A6F4C5]"
                  >
                    <span className="font-medium text-[#0F1B2D] truncate max-w-[170px]">
                      {pos.counterparty}
                    </span>
                    <span className="font-semibold text-[#067647] tabular-nums shrink-0">
                      {formatCurrency(pos.pnl, 1)} ({formatPct(pos.pnl_pct, 1)})
                    </span>
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
