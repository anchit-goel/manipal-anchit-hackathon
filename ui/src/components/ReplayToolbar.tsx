import React from 'react'
import { Play, Pause, RotateCcw } from 'lucide-react'

interface ReplayToolbarProps {
  isPlaying: boolean
  onTogglePlay: () => void
  onRestart: () => void
  speed: number
  onChangeSpeed: (speed: number) => void
  currentIndex: number
  totalCount: number
  connectionState: 'connecting' | 'connected' | 'paused' | 'done' | 'error'
}

export const ReplayToolbar: React.FC<ReplayToolbarProps> = ({
  isPlaying,
  onTogglePlay,
  onRestart,
  speed,
  onChangeSpeed,
  currentIndex,
  totalCount,
  connectionState,
}) => {
  const speeds = [1, 2, 5, 10, 20]

  const connectionLabelMap = {
    connecting: 'Connecting to feed',
    connected: 'Feed active',
    paused: 'Feed paused',
    done: 'Replay complete',
    error: 'Connection interrupted',
  }

  const dotColorMap = {
    connecting: 'bg-[#B54708]',
    connected: 'bg-[#067647]',
    paused: 'bg-[#5B6676]',
    done: 'bg-[#1F4E9C]',
    error: 'bg-[#B42318]',
  }

  return (
    <div className="bg-white border border-[#E3E6EB] rounded-lg px-4 py-2 flex items-center justify-between gap-4 text-xs">
      {/* Play/Pause & Restart */}
      <div className="flex items-center gap-2">
        <button
          onClick={onTogglePlay}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium text-xs bg-[#1F4E9C] text-white hover:bg-[#163A75] transition-colors"
          aria-label={isPlaying ? 'Pause replay' : 'Play replay'}
        >
          {isPlaying ? (
            <>
              <Pause className="w-3.5 h-3.5" />
              <span>Pause</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Play</span>
            </>
          )}
        </button>

        <button
          onClick={onRestart}
          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-[#5B6676] hover:text-[#0F1B2D] hover:bg-[#F2F4F7] transition-colors border border-[#E3E6EB]"
          title="Restart replay from beginning"
          aria-label="Restart replay"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Restart</span>
        </button>

        {/* Speed Selector */}
        <div className="flex items-center gap-1 ml-2 pl-3 border-l border-[#E3E6EB]">
          <span className="text-[#5B6676] mr-1">Speed</span>
          {speeds.map((s) => (
            <button
              key={s}
              onClick={() => onChangeSpeed(s)}
              className={`px-1.5 py-0.5 rounded text-[11px] font-medium tabular-nums transition-colors ${
                speed === s
                  ? 'bg-[#1F4E9C] text-white'
                  : 'text-[#5B6676] hover:bg-[#F2F4F7] hover:text-[#0F1B2D]'
              }`}
            >
              {s}×
            </button>
          ))}
        </div>
      </div>

      {/* Progress & Stream Status */}
      <div className="flex items-center gap-4">
        {/* Progress */}
        <div className="flex items-center gap-2 text-[#5B6676]">
          <span>Progress</span>
          <span className="font-medium text-[#0F1B2D] tabular-nums">
            {currentIndex} of {totalCount} signals
          </span>
          <div className="w-24 h-1.5 bg-[#EAECF0] rounded-full overflow-hidden">
            <div
              className="h-full bg-[#1F4E9C] transition-all duration-300"
              style={{
                width: `${totalCount > 0 ? (currentIndex / totalCount) * 100 : 0}%`,
              }}
            />
          </div>
        </div>

        {/* Labeled Connection Dot */}
        <div className="flex items-center gap-1.5 pl-3 border-l border-[#E3E6EB] text-[#5B6676]">
          <span className={`w-2 h-2 rounded-full ${dotColorMap[connectionState]}`} />
          <span className="text-[11px]">{connectionLabelMap[connectionState]}</span>
        </div>
      </div>
    </div>
  )
}
