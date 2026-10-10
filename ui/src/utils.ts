/**
 * Institutional formatting helpers and label humanisation.
 * Respects true minus sign (−), single-decimal percentages,
 * integer confidence strings, and human-readable domain text.
 */

export function formatCurrency(
  value: number,
  decimals: number = 1,
  useUnicodeMinus: boolean = true
): string {
  if (value === undefined || value === null || isNaN(value)) return '$0.0M'
  const abs = Math.abs(value)
  const minus = useUnicodeMinus ? '−' : '-'
  const prefix = value < 0 ? minus : ''

  if (abs >= 1e9) {
    return `${prefix}$${(abs / 1e9).toFixed(decimals >= 2 ? decimals : 2)}B`
  }
  if (abs >= 1e6) {
    return `${prefix}$${(abs / 1e6).toFixed(decimals)}M`
  }
  if (abs >= 1e3) {
    return `${prefix}$${(abs / 1e3).toFixed(decimals)}K`
  }
  return `${prefix}$${abs.toFixed(decimals)}`
}

export function formatPct(
  value: number,
  decimals: number = 1,
  showSign: boolean = true,
  useUnicodeMinus: boolean = true
): string {
  if (value === undefined || value === null || isNaN(value)) return '0.0%'
  const minus = useUnicodeMinus ? '−' : '-'
  if (value < 0) {
    return `${minus}${Math.abs(value).toFixed(decimals)}%`
  }
  if (value > 0) {
    return `${showSign ? '+' : ''}${value.toFixed(decimals)}%`
  }
  return `0.0%`
}

export function formatConfidence(value: number): string {
  if (value === undefined || value === null || isNaN(value)) return '0%'
  // If between 0 and 1, multiply by 100
  const pct = value <= 1.0 ? Math.round(value * 100) : Math.round(value)
  return `${pct}%`
}

export function formatShortDate(isoString: string): string {
  if (!isoString) return ''
  try {
    const d = new Date(isoString)
    if (isNaN(d.getTime())) return isoString
    return d.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'UTC',
    }) + ' UTC'
  } catch {
    return isoString
  }
}

const THEME_LABELS: Record<string, string> = {
  shipping_disruption: 'Shipping disruption',
  oil_price_up: 'Oil price increase',
  oil_price_down: 'Oil price decrease',
  credit_downgrade: 'Credit downgrade',
  credit_default: 'Credit default',
  banking_stress: 'Banking sector stress',
  rate_hike: 'Interest rate hike',
  rate_cut: 'Interest rate cut',
  sovereign_risk: 'Sovereign risk',
  semiconductor_shortage: 'Semiconductor shortage',
  none: 'None',
}

export function humanizeTheme(theme: string = ''): string {
  if (!theme) return 'General'
  const clean = theme.toLowerCase().trim()
  if (THEME_LABELS[clean]) return THEME_LABELS[clean]
  return clean
    .split('_')
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

const EVENT_CLASS_LABELS: Record<string, string> = {
  Geopolitical: 'Geopolitical event',
  'Credit Event': 'Credit event',
  Macroeconomic: 'Macroeconomic shock',
  'Product Launch': 'Product announcement',
  'Merger/Acquisition': 'Merger & acquisition',
  Regulatory: 'Regulatory action',
  Other: 'General corporate',
}

export function humanizeEventClass(eventClass: string = ''): string {
  if (!eventClass) return 'General corporate'
  return EVENT_CLASS_LABELS[eventClass] || eventClass
}

export function humanizeAssetType(assetType: string = ''): string {
  const map: Record<string, string> = {
    loan: 'Corporate loan',
    bond: 'Institutional bond',
    equity: 'Public equity',
    derivative: 'Derivative contract',
  }
  return map[assetType.toLowerCase()] || assetType
}

export function cleanModelName(model: string = ''): string {
  let cleaned = model
  while (cleaned.startsWith('gemini-gemini-')) {
    cleaned = cleaned.substring('gemini-'.length)
  }
  return cleaned || 'rules-fallback'
}

export function getSeverityStyle(impact: number): {
  label: string
  bg: string
  border: string
  text: string
} {
  if (impact >= 8.5) {
    return {
      label: 'Critical',
      bg: 'bg-[#FEF3F2]',
      border: 'border-[#FECDCA]',
      text: 'text-[#B42318]',
    }
  }
  if (impact >= 7.0) {
    return {
      label: 'Major',
      bg: 'bg-[#FFFAEB]',
      border: 'border-[#FEDF89]',
      text: 'text-[#B54708]',
    }
  }
  if (impact >= 4.0) {
    return {
      label: 'Moderate',
      bg: 'bg-[#F2F4F7]',
      border: 'border-[#EAECF0]',
      text: 'text-[#475467]',
    }
  }
  return {
    label: 'Low',
    bg: 'bg-[#F9FAFB]',
    border: 'border-[#E3E6EB]',
    text: 'text-[#5B6676]',
  }
}
