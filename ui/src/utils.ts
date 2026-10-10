export function formatCurrency(value: number, decimals: number = 2): string {
  if (value === undefined || value === null || isNaN(value)) return '$0.00'
  const abs = Math.abs(value)
  if (abs >= 1e9) {
    return `${value < 0 ? '-' : ''}$${(abs / 1e9).toFixed(decimals)}B`
  }
  if (abs >= 1e6) {
    return `${value < 0 ? '-' : ''}$${(abs / 1e6).toFixed(decimals)}M`
  }
  if (abs >= 1e3) {
    return `${value < 0 ? '-' : ''}$${(abs / 1e3).toFixed(decimals)}K`
  }
  return `${value < 0 ? '-' : ''}$${abs.toFixed(decimals)}`
}

export function formatPct(value: number, decimals: number = 2): string {
  if (value === undefined || value === null || isNaN(value)) return '0.00%'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(decimals)}%`
}

export function cleanModelName(model: string = ''): string {
  let cleaned = model
  while (cleaned.startsWith('gemini-gemini-')) {
    cleaned = cleaned.substring('gemini-'.length)
  }
  return cleaned || 'rules-fallback'
}

export function getSeverityColor(impact: number): {
  bg: string
  border: string
  text: string
  badge: string
} {
  if (impact >= 8.5) {
    return {
      bg: 'bg-rose-950/40',
      border: 'border-rose-500/50',
      text: 'text-rose-400',
      badge: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
    }
  }
  if (impact >= 7.0) {
    return {
      bg: 'bg-amber-950/40',
      border: 'border-amber-500/50',
      text: 'text-amber-400',
      badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    }
  }
  if (impact >= 4.0) {
    return {
      bg: 'bg-blue-950/40',
      border: 'border-blue-500/50',
      text: 'text-blue-400',
      badge: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
    }
  }
  return {
    bg: 'bg-slate-900/40',
    border: 'border-slate-700/50',
    text: 'text-slate-400',
    badge: 'bg-slate-800 text-slate-300 border-slate-700',
  }
}
