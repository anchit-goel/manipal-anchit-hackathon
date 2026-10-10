import React from 'react'
import {
  Play,
  Pause,
  RotateCcw,
  Activity,
  Radio,
  Sliders,
  Search,
  LineChart,
  BookOpen,
} from 'lucide-react'
import { formatCurrency } from '../utils'
import type { HealthInfo } from '../types'

interface TopBarProps {
  totalMarketValue: number
  health: HealthInfo | null
  isPlaying: boolean
  onTogglePlay: () => void
  onRestart: () => void
  speed: number
  onChangeSpeed: (speed: number) => void
  activeTab: 'stress' | 'whatif' | 'analyze' | 'calibration' | 'methodology'
  onSelectTab: (tab: 'stress' | 'whatif' | 'analyze' | 'calibration' | 'methodology') => void
  connectionState: 'connecting' | 'connected' | 'paused' | 'done' | 'error'
}

export const TopBar: React.FC<TopBarProps> = ({
  totalMarketValue,
  health,
  isPlaying,
  onTogglePlay,
  onRestart,
  speed,
  onChangeSpeed,
  activeTab,
  onSelectTab,
  connectionState,
}) => {
  const isOffline = health ? health.offline_mode : true

  return (
    <header className="glass-panel border-b border-slate-800 px-4 py-2.5 flex items-center justify-between gap-4 sticky top-0 z-40">
      {/* Brand & Mode Badge */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wider text-slate-100 uppercase">
              SIGNAL-TO-SHOCK
            </h1>
            <span className="text-[10px] text-slate-400 block -mt-0.5">
              Wholesale Risk Intelligence
            </span>
          </div>
        </div>

        <span
          className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold tracking-wider uppercase border flex items-center gap-1.5 ${
            isOffline
              ? 'bg-amber-950/40 text-amber-300 border-amber-600/40'
              : 'bg-emerald-950/40 text-emerald-300 border-emerald-600/40'
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${isOffline ? 'bg-amber-400' : 'bg-emerald-400 animate-ping'}`} />
          {isOffline ? 'REPLAY · OFFLINE' : 'LIVE'}
        </span>
      </div>

      {/* Portfolio Value & Replay Controls */}
      <div className="flex items-center gap-4">
        {/* Book Total Ticker */}
        <div className="hidden md:flex flex-col text-right font-mono pr-4 border-r border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">Book Notional</span>
          <span className="text-sm font-bold text-slate-100 tabular-nums">
            {formatCurrency(totalMarketValue || 1.32e9)}
          </span>
        </div>

        {/* Replay Controls */}
        <div className="flex items-center gap-1.5 bg-slate-900/80 border border-slate-800 p-1 rounded-xl">
          <button
            type="button"
            onClick={onTogglePlay}
            className={`p-1.5 rounded-lg text-xs font-mono transition-colors flex items-center gap-1 cursor-pointer ${
              isPlaying
                ? 'bg-amber-500/20 text-amber-300 hover:bg-amber-500/30'
                : 'bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30'
            }`}
            title={isPlaying ? 'Pause Replay Stream' : 'Resume Replay Stream'}
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-cyan-300" />}
            <span className="hidden sm:inline">{isPlaying ? 'Pause' : 'Play'}</span>
          </button>

          <button
            type="button"
            onClick={onRestart}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
            title="Restart Replay Stream from Beginning"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Speed Toggle */}
          <div className="flex items-center pl-1 border-l border-slate-800 text-[11px] font-mono">
            {[1, 2, 4].map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => onChangeSpeed(s)}
                className={`px-1.5 py-0.5 rounded cursor-pointer ${
                  speed === s
                    ? 'bg-slate-800 text-cyan-300 font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Connection Indicator */}
          <div className="pl-2 pr-1 flex items-center" title={`Stream Status: ${connectionState}`}>
            <span
              className={`w-2 h-2 rounded-full ${
                connectionState === 'connected'
                  ? 'bg-emerald-400 shadow-sm shadow-emerald-400'
                  : connectionState === 'connecting'
                  ? 'bg-cyan-400 animate-ping'
                  : connectionState === 'paused'
                  ? 'bg-amber-400'
                  : connectionState === 'done'
                  ? 'bg-blue-400'
                  : 'bg-rose-400'
              }`}
            />
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-slate-800 font-mono text-xs">
        <button
          type="button"
          onClick={() => onSelectTab('stress')}
          className={`px-2.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer ${
            activeTab === 'stress'
              ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Radio className="w-3.5 h-3.5" />
          <span>Stress Hub</span>
        </button>

        <button
          type="button"
          onClick={() => onSelectTab('whatif')}
          className={`px-2.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer ${
            activeTab === 'whatif'
              ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>What-If</span>
        </button>

        <button
          type="button"
          onClick={() => onSelectTab('analyze')}
          className={`px-2.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer ${
            activeTab === 'analyze'
              ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Search className="w-3.5 h-3.5" />
          <span>Analyze</span>
        </button>

        <button
          type="button"
          onClick={() => onSelectTab('calibration')}
          className={`px-2.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer ${
            activeTab === 'calibration'
              ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <LineChart className="w-3.5 h-3.5" />
          <span>Calibration</span>
        </button>

        <button
          type="button"
          onClick={() => onSelectTab('methodology')}
          className={`px-2.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer ${
            activeTab === 'methodology'
              ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span>Methodology</span>
        </button>
      </nav>
    </header>
  )
}
