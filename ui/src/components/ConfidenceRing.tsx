import React, { useState } from 'react'
import type { ConfidenceParts } from '../types'
import { formatConfidence } from '../utils'

interface ConfidenceRingProps {
  score: number
  parts?: ConfidenceParts
}

export const ConfidenceRing: React.FC<ConfidenceRingProps> = ({ score, parts }) => {
  const [open, setOpen] = useState(false)
  const pct = Math.round(score * 100)
  const radius = 13
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - score * circumference

  const strokeColor = score >= 0.75 ? '#067647' : score >= 0.5 ? '#B54708' : '#B42318'

  return (
    <div className="relative inline-flex items-center justify-center">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        className="relative flex items-center justify-center w-8 h-8 rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1F4E9C] cursor-pointer"
        aria-label={`Confidence score ${pct}%`}
      >
        <svg className="w-8 h-8 transform -rotate-90">
          <circle
            cx="16"
            cy="16"
            r={radius}
            stroke="#EAECF0"
            strokeWidth="2.5"
            fill="transparent"
          />
          <circle
            cx="16"
            cy="16"
            r={radius}
            stroke={strokeColor}
            strokeWidth="2.5"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-300"
          />
        </svg>
        <span className="absolute text-[10px] font-semibold text-[#0F1B2D] tabular-nums">
          {pct}
        </span>
      </button>

      {open && parts && (
        <div
          role="tooltip"
          className="absolute left-1/2 bottom-full mb-2 -translate-x-1/2 w-64 p-3 rounded-lg bg-white border border-[#E3E6EB] shadow-lg z-50 text-xs pointer-events-none"
        >
          <div className="font-semibold text-[#0F1B2D] border-b border-[#E3E6EB] pb-1.5 mb-2 flex justify-between items-center">
            <span>Confidence breakdown</span>
            <span className="font-semibold text-[#1F4E9C] tabular-nums">{formatConfidence(score)}</span>
          </div>

          <div className="space-y-1.5 text-[11px]">
            {Object.entries(parts).map(([key, val]) => {
              if (val === undefined || val === null) return null
              const label = key
                .split('_')
                .filter(Boolean)
                .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                .join(' ')
              const pVal = Math.round(val * 100)

              return (
                <div key={key}>
                  <div className="flex justify-between text-[#5B6676] mb-0.5">
                    <span>{label}</span>
                    <span className="font-medium text-[#0F1B2D] tabular-nums">{pVal}%</span>
                  </div>
                  <div className="w-full bg-[#EAECF0] h-1 rounded-full overflow-hidden">
                    <div
                      className="bg-[#1F4E9C] h-1 rounded-full"
                      style={{ width: `${Math.min(100, Math.max(0, pVal))}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
