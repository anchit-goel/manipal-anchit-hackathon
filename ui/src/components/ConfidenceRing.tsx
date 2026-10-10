import React, { useState } from 'react'
import type { ConfidenceParts } from '../types'

interface ConfidenceRingProps {
  score: number
  parts?: ConfidenceParts
}

export const ConfidenceRing: React.FC<ConfidenceRingProps> = ({ score, parts }) => {
  const [open, setOpen] = useState(false)
  const pct = Math.round(score * 100)
  const radius = 14
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (score * circumference)

  const strokeColor = score >= 0.75 ? '#10b981' : score >= 0.5 ? '#f59e0b' : '#ef4444'

  return (
    <div className="relative inline-flex items-center justify-center">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        className="relative flex items-center justify-center w-9 h-9 rounded-full focus:outline-none focus:ring-1 focus:ring-cyan-400 group cursor-pointer"
        aria-label={`Confidence score ${pct}%`}
      >
        <svg className="w-9 h-9 transform -rotate-90">
          <circle
            cx="18"
            cy="18"
            r={radius}
            stroke="#1e293b"
            strokeWidth="3"
            fill="transparent"
          />
          <circle
            cx="18"
            cy="18"
            r={radius}
            stroke={strokeColor}
            strokeWidth="3"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-300"
          />
        </svg>
        <span className="absolute text-[10px] font-mono font-bold text-slate-200">
          {pct}
        </span>
      </button>

      {open && parts && (
        <div
          role="tooltip"
          className="absolute left-1/2 bottom-full mb-2 -translate-x-1/2 w-64 p-3 rounded-lg bg-slate-900 border border-slate-700 shadow-2xl z-50 text-xs backdrop-blur-md pointer-events-none"
        >
          <div className="font-semibold text-slate-200 border-b border-slate-800 pb-1.5 mb-2 flex justify-between items-center">
            <span>Confidence Factors</span>
            <span className="font-mono text-cyan-400 font-bold">{(score * 100).toFixed(0)}%</span>
          </div>

          <div className="space-y-1.5 font-mono text-[11px]">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Source Reliability:</span>
              <span className="text-slate-200 font-semibold">{((parts.source_reliability ?? 0.75) * 100).toFixed(0)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Corroboration:</span>
              <span className="text-slate-200 font-semibold">{((parts.corroboration ?? 0.25) * 100).toFixed(0)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">FinBERT Agreement:</span>
              <span className="text-slate-200 font-semibold">{((parts.sentiment_agreement ?? 0.5) * 100).toFixed(0)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Self Consistency:</span>
              <span className="text-slate-200 font-semibold">{((parts.self_consistency ?? 1.0) * 100).toFixed(0)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Claim Certainty:</span>
              <span className="text-slate-200 font-semibold">{((parts.claim_certainty ?? 1.0) * 100).toFixed(0)}%</span>
            </div>
            {parts.hype_penalty_applied && parts.hype_penalty_applied > 0 ? (
              <div className="flex justify-between items-center text-rose-400 pt-1 border-t border-slate-800">
                <span>Social Hype Penalty:</span>
                <span>-{(parts.hype_penalty_applied * 100).toFixed(0)}%</span>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  )
}
