import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Newspaper,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  ArrowDown,
  ArrowUp,
  Minus,
} from 'lucide-react'
import type { Signal } from '../types'
import {
  cleanModelName,
  formatPct,
  formatConfidence,
  formatShortDate,
  humanizeTheme,
  humanizeEventClass,
} from '../utils'

interface SignalCardProps {
  signal: Signal
  isSelected?: boolean
  onSelect?: (signal: Signal) => void
}

export const SignalCard: React.FC<SignalCardProps> = ({ signal, isSelected, onSelect }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  const isSuppressed =
    signal.outcome_type === 'suppressed' ||
    (!signal.trigger_eligible && !!signal.suppression_reason)
  const isMerged = signal.outcome_type === 'merged'
  const isTriggered = signal.trigger_eligible && !isSuppressed && !isMerged

  const isSocial = signal.source_type === 'social'
  const modelClean = cleanModelName(signal.model_versions?.extractor)
  const isFallback = modelClean.includes('fallback')

  const sentiment = signal.sentiment_score ?? 0
  const isNegative = sentiment < -0.1
  const isPositive = sentiment > 0.1

  const handleCardClick = () => {
    onSelect?.(signal)
  }

  const handleToggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsExpanded((prev) => !prev)
  }

  return (
    <div
      onClick={handleCardClick}
      className={`border rounded-lg transition-colors cursor-pointer text-left overflow-hidden ${
        isSelected
          ? 'bg-[#F0F5FD] border-[#1F4E9C] border-l-4 border-l-[#1F4E9C]'
          : isTriggered
          ? 'bg-white border-[#E3E6EB] hover:bg-[#F9FAFB] border-l-4 border-l-[#B42318]'
          : isSuppressed
          ? 'bg-[#FAFAFA] border-[#E3E6EB] opacity-75 hover:opacity-100'
          : 'bg-white border-[#E3E6EB] hover:bg-[#F9FAFB]'
      }`}
    >
      {/* Compact Row Content */}
      <div className="p-3">
        {/* Line 1: Entity + Ticker + Time + Status Tag */}
        <div className="flex items-center justify-between gap-1.5 text-xs mb-1">
          <div className="flex items-center gap-1.5 min-w-0">
            {isSocial ? (
              <MessageSquare className="w-3.5 h-3.5 text-[#5B6676] shrink-0" aria-label="Social source" />
            ) : (
              <Newspaper className="w-3.5 h-3.5 text-[#5B6676] shrink-0" aria-label="News source" />
            )}
            <span className="font-semibold text-[#0F1B2D] truncate">{signal.entity}</span>
            {signal.ticker && (
              <span className="font-mono-id text-[11px] text-[#5B6676] px-1 py-0.2 bg-[#F2F4F7] rounded">
                {signal.ticker}
              </span>
            )}
            <span className="text-[11px] text-[#8A94A6] shrink-0">
              {formatShortDate(signal.timestamp)}
            </span>
          </div>

          {/* Status Tag (ONLY for Triggered, Suppressed, or Merged) */}
          <div className="shrink-0 flex items-center gap-1">
            {isTriggered && (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA]">
                Triggered
              </span>
            )}
            {isSuppressed && (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-[#F2F4F7] text-[#5B6676] border border-[#EAECF0]">
                Suppressed
              </span>
            )}
            {isMerged && (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-[#EDF3FC] text-[#1F4E9C] border border-[#B2CCF2]">
                Merged
              </span>
            )}

            {/* Toggle Drawer Button */}
            <button
              type="button"
              onClick={handleToggleExpand}
              className="p-0.5 text-[#8A94A6] hover:text-[#0F1B2D] rounded transition-colors"
              aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
            >
              {isExpanded ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        </div>

        {/* Line 2: Headline clamped to 2 lines */}
        <p className="text-xs text-[#0F1B2D] leading-snug line-clamp-2 my-1.5">
          {signal.headline}
        </p>

        {/* Line 3: Inline metrics & suppressed reason */}
        <div className="flex items-center justify-between gap-2 text-[11px] text-[#5B6676] pt-1 border-t border-[#F2F4F7]">
          <div className="flex items-center gap-3">
            {/* Sentiment */}
            <span className="flex items-center gap-0.5 tabular-nums">
              {isNegative ? (
                <ArrowDown className="w-3 h-3 text-[#B42318]" />
              ) : isPositive ? (
                <ArrowUp className="w-3 h-3 text-[#067647]" />
              ) : (
                <Minus className="w-3 h-3 text-[#5B6676]" />
              )}
              <span className={isNegative ? 'text-[#B42318] font-medium' : isPositive ? 'text-[#067647] font-medium' : ''}>
                {sentiment > 0 ? `+${sentiment.toFixed(2)}` : sentiment.toFixed(2)}
              </span>
            </span>

            {/* Impact Score */}
            <span className="tabular-nums">
              <span className="text-[#8A94A6] mr-1">Impact</span>
              <span className="font-semibold text-[#0F1B2D]">{signal.impact_score.toFixed(1)}</span>
            </span>

            {/* Confidence */}
            <span className="tabular-nums">
              <span className="text-[#8A94A6] mr-1">Conf</span>
              <span className="font-medium text-[#0F1B2D]">{formatConfidence(signal.confidence)}</span>
            </span>
          </div>

          {/* Short Reason on Suppressed Rows */}
          {isSuppressed && signal.suppression_reason && (
            <span
              className="text-[10px] text-[#8A94A6] truncate max-w-[130px]"
              title={signal.suppression_reason}
            >
              {signal.suppression_reason.replace(/^(suppressed:\s*)/i, '')}
            </span>
          )}
        </div>
      </div>

      {/* Expandable Details Drawer */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="border-t border-[#E3E6EB] bg-[#F9FAFB] p-3 text-xs space-y-2.5 overflow-hidden"
          >
            {/* Meta tags */}
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="px-1.5 py-0.5 rounded text-[10px] bg-white border border-[#E3E6EB] text-[#475467]">
                {humanizeEventClass(signal.event_class)}
              </span>
              <span
                className={`px-1.5 py-0.5 rounded text-[10px] border ${
                  isFallback
                    ? 'bg-[#FFFAEB] border-[#FEDF89] text-[#B54708]'
                    : 'bg-white border-[#E3E6EB] text-[#475467]'
                }`}
              >
                Extractor: {modelClean}
              </span>
              {signal.calibrated_move_pct !== null && signal.calibrated_move_pct !== undefined && (
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-white border border-[#E3E6EB] text-[#0F1B2D] tabular-nums font-medium">
                  Calibrated move: {formatPct(signal.calibrated_move_pct, 1)}
                </span>
              )}
            </div>

            {/* Themes */}
            {signal.themes && signal.themes.length > 0 && signal.themes[0] !== 'none' && (
              <div>
                <span className="text-[11px] text-[#5B6676] block mb-1">Themes:</span>
                <div className="flex flex-wrap gap-1">
                  {signal.themes.map((t) => (
                    <span
                      key={t}
                      className="px-2 py-0.5 rounded text-[11px] bg-[#EDF3FC] text-[#1F4E9C] border border-[#B2CCF2]"
                    >
                      {humanizeTheme(t)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Confidence Breakdown Bars */}
            {signal.confidence_parts && (
              <div className="space-y-1.5 pt-1 border-t border-[#EAECF0]">
                <div className="flex justify-between text-[11px] text-[#5B6676]">
                  <span>Confidence factors</span>
                  <span className="font-semibold text-[#0F1B2D]">{formatConfidence(signal.confidence)}</span>
                </div>
                {Object.entries(signal.confidence_parts).map(([k, v]) => {
                  if (v === undefined || v === null) return null
                  const label = k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
                  const valPct = Math.round(v * 100)
                  return (
                    <div key={k} className="text-[10px]">
                      <div className="flex justify-between text-[#8A94A6] mb-0.5">
                        <span>{label}</span>
                        <span className="tabular-nums font-medium text-[#0F1B2D]">{valPct}%</span>
                      </div>
                      <div className="w-full bg-[#EAECF0] h-1 rounded-full overflow-hidden">
                        <div
                          className="bg-[#1F4E9C] h-1 rounded-full"
                          style={{ width: `${Math.min(100, Math.max(0, valPct))}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Rationale */}
            {signal.rationale && (
              <div className="pt-1 border-t border-[#EAECF0] text-[11px] text-[#5B6676]">
                <span className="font-medium text-[#0F1B2D]">Analysis rationale: </span>
                {signal.rationale}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
