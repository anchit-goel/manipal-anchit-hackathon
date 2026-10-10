import React from 'react'
import {
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Database,
  Cpu,
  Sliders,
  Filter,
  TrendingDown,
} from 'lucide-react'

export const MethodologyTab: React.FC = () => {
  const steps = [
    {
      step: '1. Ingest',
      title: 'Multi-source ingestion',
      desc: 'Ingests NewsAPI, GDELT, and social chatter feeds. Deduplicates by headline signature and grounds entities to the 50-counterparty universe.',
      icon: Database,
    },
    {
      step: '2. Extract',
      title: 'Dual NLP extraction',
      desc: 'Gemini LLM (with backoff & cache) extracts event classes, macro themes, and severity. Always-offline rules fallback guarantees continuity.',
      icon: Cpu,
    },
    {
      step: '3. Calibrate',
      title: 'Empirical scaling',
      desc: 'Maps qualitative scores (1–10) to historical Cumulative Abnormal Returns (CAR) fitted across 24 ground-truth historical crisis events.',
      icon: Sliders,
    },
    {
      step: '4. Gate',
      title: 'Trigger & debounce gate',
      desc: 'Suppresses unverified rumors (confidence < 0.70) and non-material news. Debounces recurring theme headlines across a rolling 48-hour window.',
      icon: Filter,
    },
    {
      step: '5. Stress',
      title: 'Portfolio transmission',
      desc: 'Propagates theme shocks across loans, bonds, equities, and derivatives using exposure tags, duration, collateral, and delta sensitivities.',
      icon: TrendingDown,
    },
  ]

  return (
    <div className="bg-white border border-[#E3E6EB] rounded-lg p-6 space-y-6 text-left max-w-5xl mx-auto text-xs">
      {/* Header */}
      <div className="border-b border-[#E3E6EB] pb-3">
        <h2 className="text-base font-bold text-[#0F1B2D]">Methodology &amp; Architecture</h2>
        <p className="text-xs text-[#5B6676] mt-0.5">
          End-to-end mathematical specifications and transmission mechanics for wholesale banking stress testing.
        </p>
      </div>

      {/* Step Diagram */}
      <div>
        <div className="text-xs font-semibold text-[#0F1B2D] mb-3">
          End-to-end processing pipeline
        </div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {steps.map((st, i) => {
            const Icon = st.icon
            return (
              <div
                key={st.step}
                className="bg-[#F9FAFB] border border-[#E3E6EB] rounded-lg p-3 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-[11px] font-bold text-[#1F4E9C] mb-1">
                    <span>{st.step}</span>
                    <Icon className="w-3.5 h-3.5 text-[#5B6676]" />
                  </div>
                  <div className="font-semibold text-[#0F1B2D] mb-1 text-xs">{st.title}</div>
                  <p className="text-[11px] text-[#5B6676] leading-relaxed">{st.desc}</p>
                </div>
                {i < steps.length - 1 && (
                  <div className="hidden md:flex justify-end mt-2 text-[#8A94A6]">
                    <ArrowRight className="w-3 h-3" />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Multi-Factor Confidence Formula */}
      <div className="border border-[#E3E6EB] rounded-lg p-4 space-y-3">
        <h3 className="font-semibold text-xs text-[#0F1B2D]">
          Multi-factor confidence scoring formula
        </h3>
        <p className="text-[#5B6676] leading-relaxed">
          Wholesale balance sheets cannot afford automated hedge triggers based on speculative rumors or uncorroborated social chatter. The platform computes an objective confidence index:
        </p>

        <div className="bg-[#F2F4F7] p-3 rounded border border-[#EAECF0] font-mono-id text-xs text-[#0F1B2D] overflow-x-auto leading-relaxed">
          Confidence = 0.30 &times; SourceReliability + 0.25 &times; Corroboration + 0.20 &times; FinBERT_Agreement + 0.15 &times; SelfConsistency + 0.10 &times; ClaimCertainty &minus; HypePenalty
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-[#5B6676]">
          <div>
            &bull; <strong>Source Reliability (30%):</strong> Credibility weights (Reuters/Bloomberg 85%, Financial Times 85%, NewsAPI 80%, GDELT 65%, Social/X 35%).
          </div>
          <div>
            &bull; <strong>Corroboration (25%):</strong> Cross-feed corroboration matching the same counterparty within a 24-hour window.
          </div>
          <div>
            &bull; <strong>FinBERT Agreement (20%):</strong> Sentiment direction consensus between the LLM and the local FinBERT domain model.
          </div>
          <div>
            &bull; <strong>Self-Consistency (15%):</strong> Categorical extraction agreement across multi-prompt evaluations.
          </div>
          <div>
            &bull; <strong>Claim Certainty (10%):</strong> Syntactic penalization for hedging language (&ldquo;rumors&rdquo;, &ldquo;unconfirmed&rdquo;).
          </div>
          <div>
            &bull; <strong>Hype Penalty:</strong> Uncorroborated social engagement spikes penalized up to 25% to prevent retail manipulation.
          </div>
        </div>
      </div>

      {/* Measured vs Assumed Rule Source Legend */}
      <div className="border border-[#E3E6EB] rounded-lg p-4 space-y-3">
        <h3 className="font-semibold text-xs text-[#0F1B2D]">
          Transmission Rule Provenance: Measured vs. Assumed
        </h3>
        <p className="text-[#5B6676] leading-relaxed">
          Every line item in the Shock Table and position stress breakdown discloses its calibration provenance:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded bg-[#EDFDF5] border border-[#A6F4C5] space-y-1">
            <div className="font-semibold text-[#067647] flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Measured provenance</span>
            </div>
            <p className="text-[#5B6676] text-[11px] leading-relaxed">
              Derived directly from empirical event-study abnormal return distributions across 24 historical market shocks (e.g., historical shipping sector moves during Red Sea missile attacks, bank stock drops during credit downgrades).
            </p>
          </div>

          <div className="p-3 rounded bg-[#F9FAFB] border border-[#E3E6EB] space-y-1">
            <div className="font-semibold text-[#475467] flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Assumed provenance</span>
            </div>
            <p className="text-[#5B6676] text-[11px] leading-relaxed">
              Structural risk desk heuristics applied where liquid historical event data is scarce (e.g., trade finance loan probability-of-default multipliers, collateral haircuts, and OTC derivative delta sensitivities).
            </p>
          </div>
        </div>
      </div>

      {/* Synthetic Portfolio Disclosure */}
      <div className="p-3.5 rounded bg-[#F9FAFB] border border-[#E3E6EB] space-y-1 text-xs">
        <h4 className="font-semibold text-[#0F1B2D]">
          Synthetic Portfolio Disclosure &amp; Scope
        </h4>
        <p className="text-[#5B6676] leading-relaxed">
          The reference portfolio is composed of 50 synthetic wholesale banking positions ($1.32B total market value) designed to benchmark realistic wholesale counterparty concentrations across loans, bonds, equities, and derivatives. <strong>No real client or proprietary bank data is contained in this demonstration.</strong>
        </p>
      </div>
    </div>
  )
}
