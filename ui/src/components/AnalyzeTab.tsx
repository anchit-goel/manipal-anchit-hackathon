import React, { useState } from 'react'
import {
  Search,
  Play,
  ArrowDown,
  ArrowUp,
  Minus,
  CheckCircle,
  AlertTriangle,
  Info,
} from 'lucide-react'
import type { Preset, Signal, StressResult } from '../types'
import {
  cleanModelName,
  formatPct,
  formatConfidence,
  humanizeTheme,
  humanizeEventClass,
  formatCurrency,
} from '../utils'

interface AnalyzeTabProps {
  presets: Preset[]
  onAnalyze: (text: string) => Promise<Signal>
  onRunStressForSignal: (sig: Signal) => Promise<StressResult | null>
}

// Plain preset label mapping
const PRESET_PLAIN_LABELS: Record<string, string> = {
  opec_cut: 'OPEC production cut',
  bank_downgrade: 'Bank rating downgrade',
  shipping_attack: 'Red Sea naval incident',
  rumor: 'Unverified bank rumor',
  product_launch: 'Product release',
}

export const AnalyzeTab: React.FC<AnalyzeTabProps> = ({
  presets,
  onAnalyze,
  onRunStressForSignal,
}) => {
  const [text, setText] = useState<string>('')
  const [analyzedSignal, setAnalyzedSignal] = useState<Signal | null>(null)
  const [stressResult, setStressResult] = useState<StressResult | null>(null)
  const [analyzing, setAnalyzing] = useState<boolean>(false)
  const [stressing, setStressing] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const handleSelectPreset = (p: Preset) => {
    setText(p.text)
    setError(null)
    setStressResult(null)
  }

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    setError(null)
    setStressResult(null)
    setAnalyzing(true)
    try {
      const sig = await onAnalyze(text)
      setAnalyzedSignal(sig)
    } catch (err: any) {
      setError(err?.message || 'Text analysis failed')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleRunStress = async () => {
    if (!analyzedSignal) return
    setStressing(true)
    setError(null)
    try {
      const res = await onRunStressForSignal(analyzedSignal)
      setStressResult(res)
    } catch (err: any) {
      setError(err?.message || 'Failed to execute stress test for this signal')
    } finally {
      setStressing(false)
    }
  }

  const modelClean = cleanModelName(analyzedSignal?.model_versions?.extractor)
  const isFallback = modelClean.includes('fallback')

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start text-left">
      {/* Left Column: Input & Presets (5 cols) */}
      <div className="lg:col-span-5 bg-white border border-[#E3E6EB] rounded-lg p-5 space-y-4">
        <div>
          <h2 className="text-base font-bold text-[#0F1B2D]">Analyze Text</h2>
          <p className="text-xs text-[#5B6676] mt-0.5">
            Submit unstructured news or market chatter to extract structured risk signals.
          </p>
        </div>

        {/* Preset Buttons */}
        <div>
          <div className="text-xs font-semibold text-[#0F1B2D] mb-1.5">Preset narratives:</div>
          <div className="flex flex-wrap gap-1.5">
            {presets.map((p) => {
              const label = PRESET_PLAIN_LABELS[p.id] || p.label
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleSelectPreset(p)}
                  className="px-2.5 py-1 text-xs rounded-md border border-[#E3E6EB] bg-[#F9FAFB] hover:bg-[#F2F4F7] text-[#0F1B2D] transition-colors"
                >
                  {label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Text Input Form */}
        <form onSubmit={handleAnalyze} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#0F1B2D] mb-1.5">
              Narrative text
            </label>
            <textarea
              rows={5}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste financial news, regulatory filing, or market chatter here..."
              className="w-full p-3 text-xs bg-[#F9FAFB] border border-[#E3E6EB] rounded-md text-[#0F1B2D] focus:border-[#1F4E9C] focus:bg-white focus:outline-none transition-colors"
            />
          </div>

          {error && (
            <div className="p-2.5 rounded bg-[#FEF3F2] border border-[#FECDCA] text-[#B42318] text-xs">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={analyzing || !text.trim()}
            className="w-full py-2 px-4 rounded-md font-medium text-xs bg-[#1F4E9C] text-white hover:bg-[#163A75] transition-colors flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <Search className="w-3.5 h-3.5" />
            <span>{analyzing ? 'Extracting signal...' : 'Analyze text'}</span>
          </button>
        </form>
      </div>

      {/* Right Column: Signal Detail & Stress Trigger (7 cols) */}
      <div className="lg:col-span-7 bg-white border border-[#E3E6EB] rounded-lg p-5">
        {!analyzedSignal ? (
          <div className="p-8 text-center text-[#5B6676] space-y-2">
            <Info className="w-6 h-6 mx-auto text-[#8A94A6]" />
            <div className="text-sm font-semibold text-[#0F1B2D]">No text analyzed yet</div>
            <p className="text-xs max-w-sm mx-auto">
              Select one of the preset narratives on the left or enter custom text to inspect entity grounding, sentiment, impact, and stress test eligibility.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Header */}
            <div className="border-b border-[#E3E6EB] pb-3">
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="font-semibold text-sm text-[#0F1B2D]">
                  {analyzedSignal.entity}
                </span>
                {analyzedSignal.ticker && (
                  <span className="font-mono-id text-xs text-[#5B6676] px-1.5 py-0.5 bg-[#F2F4F7] rounded">
                    {analyzedSignal.ticker}
                  </span>
                )}
              </div>
              <p className="text-xs text-[#0F1B2D] leading-relaxed">{analyzedSignal.headline}</p>
            </div>

            {/* Extractor Provenance Banner */}
            <div
              className={`p-2.5 rounded text-xs border ${
                isFallback
                  ? 'bg-[#FFFAEB] border-[#FEDF89] text-[#B54708]'
                  : 'bg-[#EDFDF5] border-[#A6F4C5] text-[#067647]'
              }`}
            >
              <strong>Extractor: </strong>
              <span>
                {isFallback
                  ? 'Rules fallback (Heuristic regex & lexicon applied offline)'
                  : `Gemini LLM (${modelClean})`}
              </span>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {/* Event class */}
              <div className="bg-[#F9FAFB] border border-[#E3E6EB] rounded p-2.5">
                <div className="text-[11px] text-[#5B6676] mb-0.5">Event classification</div>
                <div className="text-xs font-semibold text-[#0F1B2D]">
                  {humanizeEventClass(analyzedSignal.event_class)}
                </div>
              </div>

              {/* Sentiment */}
              <div className="bg-[#F9FAFB] border border-[#E3E6EB] rounded p-2.5">
                <div className="text-[11px] text-[#5B6676] mb-0.5">Sentiment score</div>
                <div className="text-xs font-semibold tabular-nums flex items-center gap-1">
                  {analyzedSignal.sentiment_score < 0 ? (
                    <ArrowDown className="w-3.5 h-3.5 text-[#B42318]" />
                  ) : analyzedSignal.sentiment_score > 0 ? (
                    <ArrowUp className="w-3.5 h-3.5 text-[#067647]" />
                  ) : (
                    <Minus className="w-3.5 h-3.5 text-[#5B6676]" />
                  )}
                  <span>{analyzedSignal.sentiment_score.toFixed(2)}</span>
                </div>
              </div>

              {/* Impact */}
              <div className="bg-[#F9FAFB] border border-[#E3E6EB] rounded p-2.5">
                <div className="text-[11px] text-[#5B6676] mb-0.5">Impact score (1–10)</div>
                <div className="text-xs font-bold text-[#0F1B2D] tabular-nums">
                  {analyzedSignal.impact_score.toFixed(1)}
                </div>
              </div>

              {/* Confidence */}
              <div className="bg-[#F9FAFB] border border-[#E3E6EB] rounded p-2.5">
                <div className="text-[11px] text-[#5B6676] mb-0.5">Confidence score</div>
                <div className="text-xs font-bold text-[#1F4E9C] tabular-nums">
                  {formatConfidence(analyzedSignal.confidence)}
                </div>
              </div>
            </div>

            {/* Confidence Breakdown Bars */}
            {analyzedSignal.confidence_parts && (
              <div className="space-y-1.5 p-3 rounded bg-[#F9FAFB] border border-[#E3E6EB]">
                <div className="text-xs font-semibold text-[#0F1B2D] mb-1">
                  Confidence component breakdown
                </div>
                {Object.entries(analyzedSignal.confidence_parts).map(([k, v]) => {
                  if (v === undefined || v === null) return null
                  const label = k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
                  const valPct = Math.round(v * 100)
                  return (
                    <div key={k} className="text-xs">
                      <div className="flex justify-between text-[#5B6676] mb-0.5">
                        <span>{label}</span>
                        <span className="tabular-nums font-medium text-[#0F1B2D]">{valPct}%</span>
                      </div>
                      <div className="w-full bg-[#EAECF0] h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-[#1F4E9C] h-full rounded-full"
                          style={{ width: `${Math.min(100, Math.max(0, valPct))}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Themes */}
            {analyzedSignal.themes && analyzedSignal.themes.length > 0 && analyzedSignal.themes[0] !== 'none' && (
              <div>
                <span className="text-xs text-[#5B6676] block mb-1">Identified themes:</span>
                <div className="flex flex-wrap gap-1.5">
                  {analyzedSignal.themes.map((t) => (
                    <span
                      key={t}
                      className="px-2.5 py-0.5 rounded text-xs font-medium bg-[#EDF3FC] text-[#1F4E9C] border border-[#B2CCF2]"
                    >
                      {humanizeTheme(t)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Headline Shock Applied */}
            {analyzedSignal.calibrated_move_pct !== null && analyzedSignal.calibrated_move_pct !== undefined && (
              <div className="text-xs text-[#5B6676] bg-[#F2F4F7] p-2.5 rounded border border-[#EAECF0]">
                Headline shock applied: <strong className="text-[#0F1B2D]">{formatPct(analyzedSignal.calibrated_move_pct, 1)}</strong>
                {analyzedSignal.calibrated_explanation && ` (${analyzedSignal.calibrated_explanation})`}
              </div>
            )}

            {/* Trigger Eligibility & Action Button */}
            <div className="pt-2 border-t border-[#E3E6EB]">
              {analyzedSignal.trigger_eligible ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-xs text-[#067647] font-medium bg-[#EDFDF5] p-2.5 rounded border border-[#A6F4C5]">
                    <CheckCircle className="w-4 h-4 shrink-0" />
                    <span>Signal passed trigger gating thresholds (Impact &ge; 7.0 &amp; Confidence &ge; 0.60). Eligible to stress wholesale book.</span>
                  </div>

                  <button
                    type="button"
                    onClick={handleRunStress}
                    disabled={stressing}
                    className="w-full py-2 px-4 rounded-md font-semibold text-xs bg-[#B42318] text-white hover:bg-[#912018] transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>{stressing ? 'Calculating portfolio shock...' : 'Run stress test on wholesale portfolio'}</span>
                  </button>

                  {/* Stress result preview */}
                  {stressResult && (
                    <div className="p-3 bg-[#FEF3F2] border border-[#FECDCA] rounded-lg text-xs space-y-1.5">
                      <div className="font-semibold text-[#B42318]">Stress test completed</div>
                      <div className="text-[#0F1B2D]">
                        Portfolio P&L: <strong>{formatCurrency(stressResult.pnl_abs, 1)} ({formatPct(stressResult.pnl_pct, 1)})</strong>
                      </div>
                      <div className="text-[11px] text-[#5B6676]">
                        {stressResult.positions_hit} of 50 positions impacted across the balance sheet.
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-2 text-xs text-[#5B6676] bg-[#F2F4F7] p-2.5 rounded border border-[#EAECF0]">
                  <AlertTriangle className="w-4 h-4 text-[#B54708] shrink-0" />
                  <span>
                    Signal filtered from automatic portfolio stress:{' '}
                    <strong>{analyzedSignal.suppression_reason || 'Does not meet impact/confidence thresholds.'}</strong>
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
