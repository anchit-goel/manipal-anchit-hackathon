import { describe, it, expect } from 'vitest'
import {
  formatCurrency,
  formatPct,
  formatConfidence,
  formatShortDate,
  cleanModelName,
  humanizeTheme,
  humanizeEventClass,
  humanizeAssetType,
  getSeverityStyle,
} from '../utils'

describe('Institutional utility formatting and humanisation', () => {
  it('formats currency with metric prefixes and true minus signs', () => {
    expect(formatCurrency(1320000000)).toBe('$1.32B')
    expect(formatCurrency(-54000000)).toBe('−$54.0M')
    expect(formatCurrency(12500)).toBe('$12.5K')
    expect(formatCurrency(250)).toBe('$250.0')
    expect(formatCurrency(0)).toBe('$0.0')
  })

  it('formats percentages with single decimal and unicode minus', () => {
    expect(formatPct(4.123)).toBe('+4.1%')
    expect(formatPct(-9.34)).toBe('−9.3%')
    expect(formatPct(0)).toBe('0.0%')
  })

  it('formats confidence as integer percent string', () => {
    expect(formatConfidence(0.55)).toBe('55%')
    expect(formatConfidence(0.784)).toBe('78%')
    expect(formatConfidence(1.0)).toBe('100%')
  })

  it('humanises controlled themes to plain titles', () => {
    expect(humanizeTheme('shipping_disruption')).toBe('Shipping disruption')
    expect(humanizeTheme('oil_price_up')).toBe('Oil price increase')
    expect(humanizeTheme('banking_stress')).toBe('Banking sector stress')
    expect(humanizeTheme('credit_default')).toBe('Credit default')
    expect(humanizeTheme('none')).toBe('None')
  })

  it('humanises event classes and asset types', () => {
    expect(humanizeEventClass('Geopolitical')).toBe('Geopolitical event')
    expect(humanizeEventClass('Credit Event')).toBe('Credit event')
    expect(humanizeAssetType('loan')).toBe('Corporate loan')
    expect(humanizeAssetType('bond')).toBe('Institutional bond')
  })

  it('cleans duplicate model name prefixes', () => {
    expect(cleanModelName('gemini-gemini-3.5-flash')).toBe('gemini-3.5-flash')
    expect(cleanModelName('gemini-3.5-flash')).toBe('gemini-3.5-flash')
    expect(cleanModelName('')).toBe('rules-fallback')
  })

  it('formats short dates in UTC', () => {
    const formatted = formatShortDate('2026-10-07T14:30:00Z')
    expect(formatted).toContain('14:30')
    expect(formatted).toContain('UTC')
  })

  it('assigns severity styles with labels', () => {
    expect(getSeverityStyle(9.0).label).toBe('Critical')
    expect(getSeverityStyle(7.5).label).toBe('Major')
    expect(getSeverityStyle(5.0).label).toBe('Moderate')
    expect(getSeverityStyle(2.0).label).toBe('Low')
  })
})
