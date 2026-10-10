import React, { useState, useEffect, useRef } from 'react'
import type {
  Signal,
  StressResult,
  PortfolioData,
  CalibrationData,
  Preset,
  HealthInfo,
} from './types'
import { TopBar } from './components/TopBar'
import { SignalCard } from './components/SignalCard'
import { StressPanel } from './components/StressPanel'
import { ExposureHeatmap } from './components/ExposureHeatmap'
import { WhatIfTab } from './components/WhatIfTab'
import { AnalyzeTab } from './components/AnalyzeTab'
import { CalibrationTab } from './components/CalibrationTab'
import { MethodologyTab } from './components/MethodologyTab'
import { ShieldAlert, Radio } from 'lucide-react'

export const App: React.FC = () => {
  // Navigation
  const [activeTab, setActiveTab] = useState<'stress' | 'whatif' | 'analyze' | 'calibration' | 'methodology'>('stress')

  // Core State
  const [signals, setSignals] = useState<Signal[]>([])
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null)
  const [stressResult, setStressResult] = useState<StressResult | null>(null)
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null)
  const [calibrationData, setCalibrationData] = useState<CalibrationData | null>(null)
  const [presets, setPresets] = useState<Preset[]>([])
  const [health, setHealth] = useState<HealthInfo | null>(null)

  // Replay Streaming State
  const [isPlaying, setIsPlaying] = useState<boolean>(true)
  const [speed, setSpeed] = useState<number>(1)
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'paused' | 'done' | 'error'>('connecting')
  const [lastIndex, setLastIndex] = useState<number>(0)
  const eventSourceRef = useRef<EventSource | null>(null)

  // Initial Data Fetch
  useEffect(() => {
    fetch('/health')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setHealth(data))
      .catch(() => null)

    fetch('/portfolio')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setPortfolio(data))
      .catch(() => null)

    fetch('/calibration')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setCalibrationData(data))
      .catch(() => null)

    fetch('/presets')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setPresets(data || []))
      .catch(() => null)
  }, [])

  // Setup / Teardown SSE Replay Stream
  useEffect(() => {
    if (!isPlaying) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      setConnectionState('paused')
      return
    }

    setConnectionState('connecting')
    const url = `/replay/stream?speed=${speed}&start=${lastIndex}`
    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => {
      setConnectionState('connected')
    }

    es.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (!payload || !payload.type) return

        if (payload.type === 'signal') {
          const sig: Signal = payload.signal
          setLastIndex(payload.index + 1)
          setSignals((prev) => {
            if (prev.some((s) => s.signal_id === sig.signal_id)) return prev
            return [sig, ...prev]
          })
        } else if (payload.type === 'stress_result') {
          const res: StressResult = payload.result
          setStressResult(res)
          setSignals((prev) =>
            prev.map((s) =>
              s.signal_id === res.lead_signal_id
                ? { ...s, outcome_type: 'stress_result' }
                : s
            )
          )
        } else if (payload.type === 'suppressed') {
          setSignals((prev) =>
            prev.map((s) =>
              s.signal_id === payload.signal_id
                ? {
                    ...s,
                    outcome_type: 'suppressed',
                    suppression_reason: payload.reason,
                    trigger_eligible: false,
                  }
                : s
            )
          )
        } else if (payload.type === 'merged') {
          setSignals((prev) =>
            prev.map((s) =>
              s.signal_id === payload.signal_id
                ? {
                    ...s,
                    outcome_type: 'merged',
                    merged_into: payload.into,
                  }
                : s
            )
          )
        } else if (payload.type === 'end') {
          setConnectionState('done')
          setIsPlaying(false)
        }
      } catch (err) {
        console.error('Error parsing SSE message', err)
      }
    }

    es.onerror = () => {
      setConnectionState('error')
      es.close()
    }

    return () => {
      es.close()
    }
  }, [isPlaying, speed, lastIndex])

  // Replay Handlers
  const handleTogglePlay = () => {
    setIsPlaying((prev) => !prev)
  }

  const handleRestart = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setSignals([])
    setSelectedSignal(null)
    setStressResult(null)
    setLastIndex(0)
    setIsPlaying(true)
  }

  const handleChangeSpeed = (newSpeed: number) => {
    setSpeed(newSpeed)
  }

  // Handle Signal Selection
  const handleSelectSignal = async (sig: Signal) => {
    setSelectedSignal(sig)
    if (sig.trigger_eligible && sig.outcome_type !== 'suppressed') {
      try {
        const res = await fetch(`/stress/${sig.signal_id}`)
        if (res.ok) {
          const data = await res.json()
          setStressResult(data)
          setActiveTab('stress')
        }
      } catch (err) {
        console.error('Failed to fetch stress result for signal', err)
      }
    }
  }

  // Handle What-If Execution
  const handleRunCustom = async (theme: string, severity: number) => {
    const res = await fetch('/stress/custom', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theme, severity }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'What-if stress test failed')
    }
    const data = await res.json()
    setStressResult(data)
    setActiveTab('stress')
    return data
  }

  // Handle Live Analyze
  const handleAnalyze = async (text: string): Promise<Signal> => {
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Analysis request failed')
    }
    const data = await res.json()
    return data
  }

  // Handle Run Stress for Analyzed Signal
  const handleRunStressForSignal = async (sig: Signal): Promise<StressResult | null> => {
    const res = await fetch('/stress/signal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sig),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail?.reason || 'Signal does not qualify for stress test')
    }
    const data = await res.json()
    setStressResult(data)
    setActiveTab('stress')
    return data
  }

  return (
    <div className="min-h-screen bg-[#070a12] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Bar Navigation & Controls */}
      <TopBar
        totalMarketValue={portfolio?.total_market_value || 1.32e9}
        health={health}
        isPlaying={isPlaying}
        onTogglePlay={handleTogglePlay}
        onRestart={handleRestart}
        speed={speed}
        onChangeSpeed={handleChangeSpeed}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        connectionState={connectionState}
      />

      {/* Main Content Area */}
      <main className="flex-1 p-3 md:p-4 max-w-[1920px] w-full mx-auto overflow-hidden">
        {activeTab === 'stress' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[calc(100vh-105px)]">
            {/* LEFT: Live Signal Feed (Col 1-4) */}
            <section
              aria-label="Live Signal Feed"
              className="lg:col-span-4 glass-panel rounded-2xl p-4 flex flex-col h-full overflow-hidden"
            >
              <div className="flex justify-between items-center pb-2.5 mb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Radio className="w-4 h-4 text-cyan-400" />
                  <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
                    Live Narrative Signal Feed
                  </h2>
                </div>
                <span className="text-[11px] font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                  {signals.length} Signals
                </span>
              </div>

              {/* Scrollable feed items */}
              <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {signals.length === 0 ? (
                  <div className="h-48 flex flex-col items-center justify-center text-center text-slate-500 font-mono text-xs">
                    <p>Replay stream initialized...</p>
                    <span className="text-[10px] text-slate-600 mt-1">Press Play to stream market events</span>
                  </div>
                ) : (
                  signals.map((sig) => (
                    <SignalCard
                      key={sig.signal_id}
                      signal={sig}
                      isSelected={selectedSignal?.signal_id === sig.signal_id}
                      onSelect={handleSelectSignal}
                    />
                  ))
                )}
              </div>
            </section>

            {/* CENTRE: Hero Stress Testing Panel (Col 5-9) */}
            <section
              aria-label="Stress Panel"
              className="lg:col-span-5 h-full overflow-hidden"
            >
              <StressPanel
                result={stressResult}
                headline={selectedSignal?.headline || signals.find((s) => s.signal_id === stressResult?.lead_signal_id)?.headline}
              />
            </section>

            {/* RIGHT: Exposure Heatmap & Top Movers (Col 10-12) */}
            <section
              aria-label="Exposure Heatmap"
              className="lg:col-span-3 h-full overflow-hidden"
            >
              <ExposureHeatmap portfolio={portfolio} result={stressResult} />
            </section>
          </div>
        )}

        {activeTab === 'whatif' && (
          <div className="h-[calc(100vh-105px)]">
            <WhatIfTab onRunCustom={handleRunCustom} />
          </div>
        )}

        {activeTab === 'analyze' && (
          <div className="h-[calc(100vh-105px)]">
            <AnalyzeTab
              presets={presets}
              onAnalyze={handleAnalyze}
              onRunStressForSignal={handleRunStressForSignal}
            />
          </div>
        )}

        {activeTab === 'calibration' && (
          <div className="h-[calc(100vh-105px)]">
            <CalibrationTab data={calibrationData} />
          </div>
        )}

        {activeTab === 'methodology' && (
          <div className="h-[calc(100vh-105px)]">
            <MethodologyTab />
          </div>
        )}
      </main>

      {/* Institutional Footer & Disclaimers */}
      <footer className="glass-panel border-t border-slate-800/80 px-4 py-2 text-[11px] font-mono text-slate-500 flex flex-wrap justify-between items-center gap-2">
        <div className="flex items-center gap-3">
          <span className="text-amber-400/90 font-medium flex items-center gap-1">
            <ShieldAlert className="w-3.5 h-3.5" />
            SYNTHETIC PORTFOLIO DISCLAIMER:
          </span>
          <span>50 notional wholesale banking exposures (~$1.32B) modeled for academic demonstration.</span>
        </div>

        <div className="flex items-center gap-4">
          <span>Sources: GDELT · NewsAPI · yfinance Event Studies · Local FinBERT</span>
          <span className="text-slate-400">S&amp;P Global &amp; CRISIL Hackathon 2026</span>
        </div>
      </footer>
    </div>
  )
}

export default App
