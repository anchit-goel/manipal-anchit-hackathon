import React from 'react'
import { motion } from 'framer-motion'
import { Newspaper, MessageSquare, AlertTriangle, ShieldCheck, Flame } from 'lucide-react'
import type { Signal } from '../types'
import { ConfidenceRing } from './ConfidenceRing'
import { cleanModelName, getSeverityColor } from '../utils'

interface SignalCardProps {
  signal: Signal
  isSelected?: boolean
  onSelect?: (signal: Signal) => void
}

export const SignalCard: React.FC<SignalCardProps> = ({ signal, isSelected, onSelect }) => {
  const isSuppressed = signal.outcome_type === 'suppressed' || (!signal.trigger_eligible && !!signal.suppression_reason)
  const isMerged = signal.outcome_type === 'merged'
  const isTriggered = signal.trigger_eligible && !isSuppressed && !isMerged
  const sev = getSeverityColor(signal.impact_score)

  const isSocial = signal.source_type === 'social'
  const modelClean = cleanModelName(signal.model_versions?.extractor)
  const isLlm = !modelClean.includes('fallback')

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: isSuppressed ? 0.6 : 1, x: 0 }}
      transition={{ duration: 0.3 }}
      onClick={() => onSelect?.(signal)}
      className={`relative p-3.5 rounded-xl border transition-all duration-200 cursor-pointer text-left ${
        isSelected
          ? 'border-cyan-400/80 bg-slate-900/95 shadow-lg shadow-cyan-950/40 ring-1 ring-cyan-400/30'
          : isTriggered
          ? 'border-rose-500/50 bg-slate-900/80 hover:border-rose-400/80 hover:bg-slate-900 shadow-md shadow-rose-950/30 animate-pulse-subtle'
          : isSuppressed
          ? 'border-slate-800/60 bg-slate-950/40 opacity-60 hover:opacity-90'
          : 'border-slate-800/80 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900/80'
      }`}
    >
      {/* Top row: Sources, Badges, Model */}
      <div className="flex items-center justify-between gap-2 mb-2 text-xs">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span
            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-medium ${
              isSocial
                ? 'bg-purple-950/60 text-purple-300 border border-purple-800/40'
                : 'bg-blue-950/60 text-blue-300 border border-blue-800/40'
            }`}
          >
            {isSocial ? <MessageSquare className="w-3 h-3" /> : <Newspaper className="w-3 h-3" />}
            {signal.source}
          </span>

          <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
            {signal.event_class}
          </span>

          <span
            className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
              isLlm
                ? 'bg-cyan-950/40 text-cyan-300 border border-cyan-800/40'
                : 'bg-amber-950/40 text-amber-300 border border-amber-800/40'
            }`}
          >
            {modelClean}
          </span>
        </div>

        {/* Trigger status chip */}
        <div>
          {isTriggered && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-sm shadow-rose-500/20">
              <Flame className="w-3 h-3 text-rose-400 fill-rose-400" />
              TRIGGER
            </span>
          )}
          {isMerged && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-indigo-950 text-indigo-300 border border-indigo-800">
              merged into {signal.merged_into || 'scenario'}
            </span>
          )}
          {isSuppressed && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono text-slate-400 bg-slate-900 border border-slate-800">
              <ShieldCheck className="w-3 h-3 text-slate-400" />
              SUPPRESSED
            </span>
          )}
        </div>
      </div>

      {/* Entity & Ticker Header */}
      <div className="flex items-baseline justify-between mb-1.5">
        <h4 className="font-semibold text-sm text-slate-100 truncate flex items-center gap-1.5">
          {signal.entity}
          {signal.ticker && (
            <span className="text-xs font-mono font-medium px-1.5 py-0.2 rounded bg-slate-800/90 text-cyan-300 border border-slate-700">
              ${signal.ticker}
            </span>
          )}
        </h4>
        <span className="text-[10px] font-mono text-slate-400">
          {new Date(signal.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      {/* Headline Snippet */}
      <p className="text-xs text-slate-300 line-clamp-2 mb-2.5 font-normal leading-relaxed">
        {signal.headline}
      </p>

      {/* Metrics Row: Sentiment Bar, Impact Gauge, Confidence Ring */}
      <div className="grid grid-cols-[1fr_auto_auto] items-center gap-3 pt-2 border-t border-slate-800/80 mb-2">
        {/* Sentiment Bar */}
        <div className="flex flex-col gap-1">
          <div className="flex justify-between text-[10px] font-mono text-slate-400">
            <span>Sentiment</span>
            <span
              className={
                signal.sentiment_score > 0.05
                  ? 'text-emerald-400 font-semibold'
                  : signal.sentiment_score < -0.05
                  ? 'text-rose-400 font-semibold'
                  : 'text-slate-400'
              }
            >
              {signal.sentiment_score > 0 ? `+${signal.sentiment_score.toFixed(2)}` : signal.sentiment_score.toFixed(2)}
            </span>
          </div>
          <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden flex">
            {signal.sentiment_score < 0 ? (
              <>
                <div
                  className="bg-rose-500 h-full ml-auto"
                  style={{ width: `${Math.min(100, Math.abs(signal.sentiment_score) * 100)}%` }}
                />
                <div className="w-1/2 h-full bg-transparent" />
              </>
            ) : (
              <>
                <div className="w-1/2 h-full bg-transparent" />
                <div
                  className="bg-emerald-500 h-full"
                  style={{ width: `${Math.min(100, signal.sentiment_score * 100)}%` }}
                />
              </>
            )}
          </div>
        </div>

        {/* Impact Gauge */}
        <div className="flex flex-col items-center">
          <span className="text-[10px] font-mono text-slate-400">Impact</span>
          <span className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${sev.badge}`}>
            {signal.impact_score.toFixed(1)}/10
          </span>
        </div>

        {/* Confidence Ring with popover */}
        <div className="flex flex-col items-center">
          <span className="text-[10px] font-mono text-slate-400">Conf</span>
          <ConfidenceRing score={signal.confidence} parts={signal.confidence_parts} />
        </div>
      </div>

      {/* Calibrated Move String */}
      {signal.calibrated_explanation && (
        <div className="text-[11px] font-mono text-cyan-300/90 bg-cyan-950/20 border border-cyan-800/30 rounded px-2 py-1 mb-2">
          {signal.calibrated_explanation}
        </div>
      )}

      {/* Themes and Tag Chips */}
      {signal.themes && signal.themes.length > 0 && signal.themes[0] !== 'none' && (
        <div className="flex flex-wrap gap-1 mb-1">
          {signal.themes.map((th) => (
            <span
              key={th}
              className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800/60 text-slate-300 border border-slate-700/60"
            >
              #{th}
            </span>
          ))}
        </div>
      )}

      {/* Suppressed Reason Banner */}
      {isSuppressed && signal.suppression_reason && (
        <div className="mt-2 text-[11px] text-amber-300/90 bg-amber-950/30 border border-amber-800/40 rounded p-1.5 flex items-start gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
          <span>Refused to trigger: {signal.suppression_reason}</span>
        </div>
      )}
    </motion.div>
  )
}
