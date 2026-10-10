import React from 'react'
import type { StressResult, Signal } from '../types'
import { formatCurrency, formatPct, formatConfidence } from '../utils'

interface KpiStripProps {
  totalMarketValue: number
  activeResult: StressResult | null
  signals: Signal[]
  totalSignalsCount: number
}

export const KpiStrip: React.FC<KpiStripProps> = ({
  totalMarketValue,
  activeResult,
  signals,
  totalSignalsCount,
}) => {
  // Triggered vs suppressed
  const triggeredCount = signals.filter(
    (s) => s.trigger_eligible && s.outcome_type !== 'suppressed' && s.outcome_type !== 'merged'
  ).length
  const suppressedCount = signals.filter(
    (s) => s.outcome_type === 'suppressed' || (!s.trigger_eligible && !!s.suppression_reason)
  ).length

  // Median confidence
  let medianConf = 0.78
  if (signals.length > 0) {
    const confs = signals.map((s) => s.confidence).sort((a, b) => a - b)
    const mid = Math.floor(confs.length / 2)
    medianConf = confs.length % 2 !== 0 ? confs[mid] : (confs[mid - 1] + confs[mid]) / 2
  }

  // Active P&L
  const hasResult = !!activeResult
  const pnlAbs = activeResult?.pnl_abs ?? 0
  const pnlPct = activeResult?.pnl_pct ?? 0
  const isLoss = pnlAbs < 0
  const isGain = pnlAbs > 0

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {/* 1. Book Value */}
      <div className="bg-white border border-[#E3E6EB] rounded-lg p-3">
        <div className="text-[11px] font-medium text-[#5B6676] uppercase tracking-wider mb-1">
          Book value
        </div>
        <div className="text-xl font-bold text-[#0F1B2D] tabular-nums">
          {formatCurrency(totalMarketValue, 2)}
        </div>
        <div className="text-[11px] text-[#8A94A6] mt-0.5">50 wholesale positions</div>
      </div>

      {/* 2. Latest Scenario P&L */}
      <div className="bg-white border border-[#E3E6EB] rounded-lg p-3">
        <div className="text-[11px] font-medium text-[#5B6676] uppercase tracking-wider mb-1">
          Scenario P&L
        </div>
        <div className="flex items-baseline gap-2">
          <span
            className={`text-xl font-bold tabular-nums ${
              isLoss
                ? 'text-[#B42318]'
                : isGain
                ? 'text-[#067647]'
                : 'text-[#0F1B2D]'
            }`}
          >
            {hasResult ? formatCurrency(pnlAbs, 1) : '$0.0M'}
          </span>
          {hasResult && (
            <span
              className={`text-xs font-semibold tabular-nums px-1.5 py-0.5 rounded ${
                isLoss
                  ? 'bg-[#FEF3F2] text-[#B42318]'
                  : isGain
                  ? 'bg-[#EDFDF5] text-[#067647]'
                  : 'bg-[#F2F4F7] text-[#475467]'
              }`}
            >
              {formatPct(pnlPct, 1)}
            </span>
          )}
        </div>
        <div className="text-[11px] text-[#8A94A6] mt-0.5">
          {hasResult ? 'Active stress impact' : 'No active scenario'}
        </div>
      </div>

      {/* 3. Signals Processed */}
      <div className="bg-white border border-[#E3E6EB] rounded-lg p-3">
        <div className="text-[11px] font-medium text-[#5B6676] uppercase tracking-wider mb-1">
          Signals processed
        </div>
        <div className="text-xl font-bold text-[#0F1B2D] tabular-nums">
          {signals.length}{' '}
          <span className="text-xs font-normal text-[#8A94A6]">of {totalSignalsCount}</span>
        </div>
        <div className="text-[11px] text-[#8A94A6] mt-0.5">Multi-source feed</div>
      </div>

      {/* 4. Triggered vs Suppressed */}
      <div className="bg-white border border-[#E3E6EB] rounded-lg p-3">
        <div className="text-[11px] font-medium text-[#5B6676] uppercase tracking-wider mb-1">
          Gating status
        </div>
        <div className="text-xl font-bold text-[#0F1B2D] tabular-nums flex items-baseline gap-2">
          <span>{triggeredCount}</span>
          <span className="text-xs font-normal text-[#8A94A6]">trig</span>
          <span className="text-xs text-[#D0D5DD]">/</span>
          <span className="text-[#5B6676]">{suppressedCount}</span>
          <span className="text-xs font-normal text-[#8A94A6]">supp</span>
        </div>
        <div className="text-[11px] text-[#8A94A6] mt-0.5">Rumors filtered</div>
      </div>

      {/* 5. Median Confidence */}
      <div className="bg-white border border-[#E3E6EB] rounded-lg p-3">
        <div className="text-[11px] font-medium text-[#5B6676] uppercase tracking-wider mb-1">
          Median confidence
        </div>
        <div className="text-xl font-bold text-[#0F1B2D] tabular-nums">
          {formatConfidence(medianConf)}
        </div>
        <div className="text-[11px] text-[#8A94A6] mt-0.5">Multi-factor score</div>
      </div>
    </div>
  )
}
