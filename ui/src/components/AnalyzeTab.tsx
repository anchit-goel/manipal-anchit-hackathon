import React, { useState } from 'react'
import { Search, Sparkles, AlertTriangle, Play } from 'lucide-react'
import type { Preset, Signal, StressResult } from '../types'
import { SignalCard } from './SignalCard'

interface AnalyzeTabProps {
  presets: Preset[]
  onAnalyze: (text: string) => Promise<Signal>
  onRunStressForSignal: (sig: Signal) => Promise<StressResult | null>
}

export const AnalyzeTab: React.FC<AnalyzeTabProps> = ({
  presets,
  onAnalyze,
  onRunStressForSignal,
}) => {
  const [text, setText] = useState<string>('')
  const [analyzedSignal, setAnalyzedSignal] = useState<Signal | null>(null)
  const [analyzing, setAnalyzing] = useState<boolean>(false)
  const [stressing, setStressing] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const handleSelectPreset = (p: Preset) => {
    setText(p.text)
    setError(null)
  }

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    setError(null)
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
      await onRunStressForSignal(analyzedSignal)
    } catch (err: any) {
      setError(err?.message || 'Failed to propagate stress test for signal')
    } finally {
      setStressing(false)
    }
  }

  return (
    <div className="glass-panel rounded-2xl p-6 max-w-3xl mx-auto h-full overflow-y-auto space-y-6">
      <div className="border-b border-slate-800 pb-3">
        <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <Search className="w-5 h-5 text-cyan-400" />
          <span>Real-Time Unstructured Risk Narrative Ingestion</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Ingest raw market headlines or social chatter through the dual LLM + FinBERT extraction engine to produce validated risk signals.
        </p>
      </div>

      {/* Preset Chips */}
      <div>
        <span className="block text-xs font-mono font-medium text-slate-300 uppercase tracking-wide mb-2 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>Institutional Test Presets (Guaranteed Offline-Cached)</span>
        </span>
        <div className="flex flex-wrap gap-2">
          {presets.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => handleSelectPreset(p)}
              className="text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-500/60 hover:text-cyan-300 text-slate-300 transition-colors text-left cursor-pointer"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Text Form */}
      <form onSubmit={handleAnalyze} className="space-y-4">
        <div>
          <label className="block text-xs font-mono font-medium text-slate-300 uppercase tracking-wide mb-2">
            Narrative Content / Financial Headline
          </label>
          <textarea
            rows={3}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste raw market headline, news wire excerpt, or social rumor..."
            className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-slate-100 font-sans text-sm focus:outline-none focus:ring-1 focus:ring-cyan-400 resize-none"
          />
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={analyzing || !text.trim()}
          className="w-full py-2.5 px-4 rounded-xl font-mono text-xs font-bold uppercase tracking-wider bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 hover:border-cyan-500/50 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
        >
          {analyzing ? 'Extracting Signal & Scoring FinBERT...' : 'Analyze Market Narrative'}
        </button>
      </form>

      {/* Analyzed Signal Card Result */}
      {analyzedSignal && (
        <div className="space-y-4 pt-4 border-t border-slate-800">
          <div className="flex justify-between items-center">
            <h3 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wide">
              Extraction Engine Signal Output
            </h3>
            {analyzedSignal.trigger_eligible && (
              <span className="text-[11px] font-mono text-emerald-400 font-bold">
                &check; Qualified for Stress Testing
              </span>
            )}
          </div>

          <SignalCard signal={analyzedSignal} />

          {analyzedSignal.trigger_eligible ? (
            <button
              type="button"
              onClick={handleRunStress}
              disabled={stressing}
              className="w-full py-3 px-4 rounded-xl font-mono text-xs font-bold uppercase tracking-wider bg-gradient-to-r from-rose-500 to-amber-600 hover:from-rose-400 hover:to-amber-500 text-slate-950 shadow-lg shadow-rose-500/20 flex items-center justify-center gap-2 cursor-pointer transition-all"
            >
              <Play className="w-4 h-4 fill-slate-950" />
              <span>{stressing ? 'Computing Book Repricing...' : 'Propagate Shock to Wholesale Book'}</span>
            </button>
          ) : (
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono text-slate-400">
              Signal does not qualify for automated stress test trigger (Severity &le; 7.0 or uncorroborated rumor).
            </div>
          )}
        </div>
      )}
    </div>
  )
}
