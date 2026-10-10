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
import { KpiStrip } from './components/KpiStrip'
import { ReplayToolbar } from './components/ReplayToolbar'
import { SignalCard } from './components/SignalCard'
import { StressPanel } from './components/StressPanel'
import { ExposureHeatmap } from './components/ExposureHeatmap'
import { WhatIfTab } from './components/WhatIfTab'
import { AnalyzeTab } from './components/AnalyzeTab'
import { CalibrationTab } from './components/CalibrationTab'
import { MethodologyTab } from './components/MethodologyTab'
import { Filter } from 'lucide-react'

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

  // Feed Filter ('all' | 'triggered' | 'suppressed')
  const [feedFilter, setFeedFilter] = useState<'all' | 'triggered' | 'suppressed'>('all')

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
        if (payload.index !== undefined) {
          setLastIndex(payload.index + 1)
        }

        if (payload.type === 'signal') {
          setSignals((prev) => {
            const exists = prev.some((s) => s.signal_id === payload.signal.signal_id)
            if (exists) return prev
            return [payload.signal, ...prev]
          })
        } else if (payload.type === 'stress_result') {
          setStressResult(payload.result)
          setSignals((prev) =>
            prev.map((s) =>
              s.signal_id === payload.result.lead_signal_id
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
    return data
  }

  // Filtered signals for the feed column
  const filteredSignals = signals.filter((s) => {
    if (feedFilter === 'triggered') {
      return s.trigger_eligible && s.outcome_type !== 'suppressed' && s.outcome_type !== 'merged'
    }
    if (feedFilter === 'suppressed') {
      return s.outcome_type === 'suppressed' || (!s.trigger_eligible && !!s.suppression_reason)
    }
    return true
  })

  const totalMarketValue = portfolio?.total_market_value ?? 1320368000
  const totalReplayCount = health?.signal_count ?? 14

  return (
    <div className="min-h-screen bg-[#F5F6F8] text-[#0F1B2D] flex flex-col font-sans selection:bg-[#B2CCF2] selection:text-[#0F1B2D]">
      {/* Slim Institutional Header */}
      <TopBar
        totalMarketValue={totalMarketValue}
        health={health}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        connectionState={connectionState}
      />

      {/* Main Content Area */}
      <main className="flex-1 p-4 max-w-[1520px] w-full mx-auto space-y-4">
        {activeTab === 'stress' && (
          <div className="space-y-4">
            {/* KPI Strip */}
            <KpiStrip
              totalMarketValue={totalMarketValue}
              activeResult={stressResult}
              signals={signals}
              totalSignalsCount={totalReplayCount}
            />

            {/* Replay Toolbar */}
            <ReplayToolbar
              isPlaying={isPlaying}
              onTogglePlay={handleTogglePlay}
              onRestart={handleRestart}
              speed={speed}
              onChangeSpeed={handleChangeSpeed}
              currentIndex={lastIndex}
              totalCount={totalReplayCount}
              connectionState={connectionState}
            />

            {/* Three Column Monitor View */}
            <div className="flex flex-col lg:flex-row gap-4 items-start">
              {/* Left Column: Compact Signal Feed (340px) */}
              <section
                aria-label="Signal Feed"
                className="w-full lg:w-[340px] shrink-0 bg-white border border-[#E3E6EB] rounded-lg p-3.5 flex flex-col space-y-3"
              >
                {/* Header & Filter Toggle */}
                <div className="flex items-center justify-between pb-2 border-b border-[#E3E6EB]">
                  <div className="flex items-center gap-1.5">
                    <Filter className="w-3.5 h-3.5 text-[#5B6676]" />
                    <span className="text-xs font-bold text-[#0F1B2D]">Narrative signals</span>
                  </div>

                  {/* Filter Pills */}
                  <div className="flex items-center gap-1 text-[11px]">
                    <button
                      type="button"
                      onClick={() => setFeedFilter('all')}
                      className={`px-1.5 py-0.5 rounded transition-colors ${
                        feedFilter === 'all'
                          ? 'bg-[#1F4E9C] text-white font-medium'
                          : 'text-[#5B6676] hover:text-[#0F1B2D]'
                      }`}
                    >
                      All ({signals.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setFeedFilter('triggered')}
                      className={`px-1.5 py-0.5 rounded transition-colors ${
                        feedFilter === 'triggered'
                          ? 'bg-[#1F4E9C] text-white font-medium'
                          : 'text-[#5B6676] hover:text-[#0F1B2D]'
                      }`}
                    >
                      Trig
                    </button>
                    <button
                      type="button"
                      onClick={() => setFeedFilter('suppressed')}
                      className={`px-1.5 py-0.5 rounded transition-colors ${
                        feedFilter === 'suppressed'
                          ? 'bg-[#1F4E9C] text-white font-medium'
                          : 'text-[#5B6676] hover:text-[#0F1B2D]'
                      }`}
                    >
                      Supp
                    </button>
                  </div>
                </div>

                {/* Scrollable feed list */}
                <div className="max-h-[720px] overflow-y-auto space-y-2 pr-1">
                  {filteredSignals.length === 0 ? (
                    <div className="py-12 text-center text-[#8A94A6] text-xs">
                      {signals.length === 0 ? (
                        <>
                          <div>Waiting for incoming events...</div>
                          <div className="text-[11px] text-[#5B6676] mt-1">Press Play to stream replay</div>
                        </>
                      ) : (
                        <div>No signals match this filter.</div>
                      )}
                    </div>
                  ) : (
                    filteredSignals.map((sig) => (
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

              {/* Middle Column: Hero Stress Panel (Flexible) */}
              <section
                aria-label="Scenario Result"
                className="flex-1 min-w-0"
              >
                <StressPanel
                  result={stressResult}
                  portfolio={portfolio}
                  leadSignal={selectedSignal}
                  headline={
                    selectedSignal?.headline ||
                    signals.find((s) => s.signal_id === stressResult?.lead_signal_id)?.headline
                  }
                />
              </section>

              {/* Right Column: Exposure Panel & Treemap (380px) */}
              <section
                aria-label="Exposure Treemap"
                className="w-full lg:w-[380px] shrink-0"
              >
                <ExposureHeatmap portfolio={portfolio} result={stressResult} />
              </section>
            </div>
          </div>
        )}

        {/* Tab 2: Scenario Lab */}
        {activeTab === 'whatif' && (
          <WhatIfTab
            onRunCustom={handleRunCustom}
            portfolio={portfolio}
          />
        )}

        {/* Tab 3: Analyze Text */}
        {activeTab === 'analyze' && (
          <AnalyzeTab
            presets={presets}
            onAnalyze={handleAnalyze}
            onRunStressForSignal={handleRunStressForSignal}
          />
        )}

        {/* Tab 4: Calibration */}
        {activeTab === 'calibration' && (
          <CalibrationTab data={calibrationData} />
        )}

        {/* Tab 5: Methodology */}
        {activeTab === 'methodology' && (
          <MethodologyTab />
        )}
      </main>

      {/* Institutional Footer */}
      <footer className="bg-white border-t border-[#E3E6EB] px-6 py-2.5 text-[11px] text-[#5B6676] flex flex-wrap justify-between items-center gap-2 mt-auto">
        <div className="flex items-center gap-2">
          <span>Data sources: GDELT v2 &middot; NewsAPI Financials &middot; Social chatter &middot; CAPM Event Studies</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="font-medium text-[#0F1B2D]">Synthetic wholesale portfolio, illustrative</span>
          <span>S&amp;P Global &amp; CRISIL Hackathon 2026</span>
        </div>
      </footer>
    </div>
  )
}

export default App
