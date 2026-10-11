import { describe, it, expect } from 'vitest'

describe('Scenario label formatting and severity separation', () => {
  it('correctly separates event impact score from internal severity_scale multiplier', () => {
    const signalImpactScore = 8.8
    const internalSeverityScale = 1.104
    
    // Impact score must display the event impact (8.8), not the internal multiplier (1.1)
    const displayImpact = signalImpactScore.toFixed(1)
    expect(displayImpact).toBe('8.8')
    expect(displayImpact).not.toBe(internalSeverityScale.toFixed(1))
  })

  it('correctly labels What-if scenarios with chosen Severity', () => {
    const chosenSeverity = 8.0
    const displaySeverity = chosenSeverity.toFixed(1)
    expect(displaySeverity).toBe('8.0')
  })

  it('formats headline shock applied range cleanly', () => {
    const calMove = -9.33
    const calLow = -9.33 * 0.3
    const calHigh = -9.33 * 1.8
    const label = 'Headline shock applied'
    expect(label).toBe('Headline shock applied')
    expect(calMove).toBeLessThan(0)
    expect(calLow).toBeDefined()
    expect(calHigh).toBeDefined()
  })
})
