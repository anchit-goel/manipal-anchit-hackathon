import React from 'react'
import { BookOpen, ShieldAlert, Cpu, CheckCircle2, GitBranch } from 'lucide-react'

export const MethodologyTab: React.FC = () => {
  return (
    <div className="glass-panel rounded-2xl p-6 max-w-4xl mx-auto h-full overflow-y-auto space-y-6 text-xs font-sans leading-relaxed">
      <div className="border-b border-slate-800 pb-3">
        <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-cyan-400" />
          <span>Institutional Methodology &amp; Mathematical Framework</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Detailed technical specifications of the Signal-to-Shock wholesale risk intelligence platform.
        </p>
      </div>

      {/* Synthetic Portfolio Disclosure */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-700">
        <h3 className="font-semibold text-slate-100 font-mono text-sm uppercase tracking-wide flex items-center gap-2 mb-1.5">
          <ShieldAlert className="w-4 h-4 text-cyan-400" />
          <span>Synthetic Wholesale Banking Portfolio Disclosure</span>
        </h3>
        <p className="text-slate-300 text-xs">
          The reference portfolio consists of 50 synthetic wholesale banking positions (~USD 1.32B notional) spanning corporate loans (revolvers, term loans, trade finance), investment-grade and high-yield corporate bonds, interest-rate and commodity derivatives, and strategic equities. Counterparty entities correspond to major systemic institutions purely to anchor realistic sector and country risk transmissions. <strong>No proprietary or actual bank client exposure data is used.</strong>
        </p>
      </div>

      {/* Multi-Factor Confidence Scoring */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
        <h3 className="font-semibold text-slate-100 font-mono text-sm uppercase tracking-wide flex items-center gap-2">
          <Cpu className="w-4 h-4 text-emerald-400" />
          <span>Multi-Factor Confidence Scoring Formula</span>
        </h3>
        <p className="text-slate-300">
          Risk managers cannot afford to trigger false-positive balance sheet hedges on speculative rumors. The platform computes a compound confidence score $C \in [0.0, 1.0]$:
        </p>
        <div className="bg-slate-950 p-3 rounded-lg font-mono text-[11px] text-cyan-300 border border-slate-800">
          Confidence = 0.30 &times; SourceReliability + 0.25 &times; Corroboration + 0.20 &times; FinBERT_Agreement + 0.15 &times; SelfConsistency + 0.10 &times; ClaimCertainty &minus; HypePenalty
        </div>
        <ul className="space-y-1.5 text-slate-400 list-disc list-inside">
          <li><strong>Source Reliability (30%):</strong> Prior table (Reuters/Bloomberg 85%, WSJ/FT 85%, NewsAPI 80%, GDELT 65%, Social/X 35%).</li>
          <li><strong>Corroboration (25%):</strong> Cross-source verification clustering items reporting the same entity and event class within 24h.</li>
          <li><strong>Sentiment Agreement (20%):</strong> Polarity consensus between generative LLM perspective and local FinBERT transformer.</li>
          <li><strong>Self-Consistency (15%):</strong> Pass 1 (greedy) vs Pass 2 (sampled temperature 0.3) categorical stability.</li>
          <li><strong>Claim Certainty (10%):</strong> Verified facts vs speculative rumor phrasing extracted from syntax.</li>
          <li><strong>Social Hype Penalty:</strong> Uncorroborated social spikes exceeding engagement medians are penalized up to 25%.</li>
        </ul>
      </div>

      {/* Transmission Mechanics & Shock Table */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
        <h3 className="font-semibold text-slate-100 font-mono text-sm uppercase tracking-wide flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-rose-400" />
          <span>Asset-Type Shock Transmission Mechanics</span>
        </h3>
        <p className="text-slate-300">
          Signals with impact &gt; 7.0 and confidence &ge; 60% trigger automated transmission across the exposure matrix:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
            <span className="font-mono font-bold text-slate-200 block mb-1">1. Strategic Equities</span>
            <p className="text-slate-400 text-[11px]">
              Direct percentage price shock based on measured event-study abnormal moves or assumed equity elasticity.
            </p>
          </div>
          <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
            <span className="font-mono font-bold text-slate-200 block mb-1">2. Corporate Bonds</span>
            <p className="text-slate-400 text-[11px]">
              Credit spread widening ($\Delta s$ bps) &times; modified duration ($D$) &times; market value repricing.
            </p>
          </div>
          <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
            <span className="font-mono font-bold text-slate-200 block mb-1">3. Corporate Loans &amp; Trade Finance</span>
            <p className="text-slate-400 text-[11px]">
              Expected Loss uplift: $\Delta PD \times LGD (45\%) \times (1 - Collateral\%) \times Notional$.
            </p>
          </div>
          <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
            <span className="font-mono font-bold text-slate-200 block mb-1">4. Derivatives &amp; Hedges</span>
            <p className="text-slate-400 text-[11px]">
              MTM swing based on Bank Delta &times; Underlying Move %, plus counterparty credit valuation adjustment (CVA).
            </p>
          </div>
        </div>
      </div>

      {/* Measured vs Assumed Legend */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
        <h3 className="font-semibold text-slate-100 font-mono text-sm uppercase tracking-wide flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-cyan-400" />
          <span>Rule Origin: Measured vs Assumed Legend</span>
        </h3>
        <p className="text-slate-300 text-xs">
          Every cell in the shock table and position explanation carries an origin tag:
        </p>
        <div className="flex flex-col sm:flex-row gap-3 pt-1">
          <div className="p-2.5 rounded bg-emerald-950/30 border border-emerald-800/40 text-emerald-300 flex-1">
            <strong className="block font-mono text-xs uppercase mb-1">MEASURED Origin</strong>
            Equity percentage moves derived directly from empirical CAPM cumulative abnormal return (CAR) medians from our 24-event benchmark where at least 2 historical occurrences match the theme and sector.
          </div>
          <div className="p-2.5 rounded bg-amber-950/30 border border-amber-800/40 text-amber-300 flex-1">
            <strong className="block font-mono text-xs uppercase mb-1">ASSUMED Origin</strong>
            Institutional banking heuristic estimates with documented rationale for transmission parameters lacking sufficient historical empirical observations ($n &lt; 2$).
          </div>
        </div>
      </div>
    </div>
  )
}
