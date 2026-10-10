import { describe, it, expect } from 'vitest'
import { formatCurrency, formatPct, cleanModelName, getSeverityColor } from '../utils'

describe('Frontend utility formatting and helpers', () => {
  it('formats currency with metric prefixes correctly', () => {
    expect(formatCurrency(1320000000)).toBe('$1.32B')
    expect(formatCurrency(-54000000)).toBe('-$54.00M')
    expect(formatCurrency(12500)).toBe('$12.50K')
    expect(formatCurrency(250)).toBe('$250.00')
    expect(formatCurrency(0)).toBe('$0.00')
  })

  it('formats percentages with signs and precision', () => {
    expect(formatPct(4.123)).toBe('+4.12%')
    expect(formatPct(-7.54)).toBe('-7.54%')
    expect(formatPct(0)).toBe('0.00%')
  })

  it('cleans duplicate model name prefixes', () => {
    expect(cleanModelName('gemini-gemini-3.5-flash')).toBe('gemini-3.5-flash')
    expect(cleanModelName('gemini-3.5-flash')).toBe('gemini-3.5-flash')
    expect(cleanModelName('')).toBe('rules-fallback')
  })

  it('assigns severity colors based on impact score tiers', () => {
    expect(getSeverityColor(9.0).text).toBe('text-rose-400')
    expect(getSeverityColor(7.5).text).toBe('text-amber-400')
    expect(getSeverityColor(5.0).text).toBe('text-blue-400')
    expect(getSeverityColor(2.0).text).toBe('text-slate-400')
  })
})
