"""Generate high-resolution architecture diagram for Signal-to-Shock in the light institutional theme."""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_diagram(output_path: Path):
    # Target: 1920x900 pixels
    fig = plt.figure(figsize=(19.2, 9.0), dpi=100)
    ax = fig.add_subplot(111)
    
    bg_color = '#F5F6F8'
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    # Remove axes
    ax.axis('off')
    ax.set_xlim(0, 19.2)
    ax.set_ylim(0, 9.0)

    # Title Banner (Institutional Typography)
    ax.text(9.6, 8.45, "SIGNAL-TO-SHOCK: END-TO-END RISK ARCHITECTURE",
            ha='center', va='center', fontsize=22, fontweight='bold', color='#0F1B2D', family='sans-serif')
    ax.text(9.6, 8.08, "Multi-Source Ingestion  →  Dual-Path NLP  →  Empirical Calibration  →  Trigger Gate & Debounce  →  $1.32B Wholesale Stress Web Dashboard",
            ha='center', va='center', fontsize=12.5, color='#5B6676', family='sans-serif')

    # 5 Stages Left to Right
    cols = [
        {
            "stage": "STAGE 1",
            "title": "Ingest & Cache",
            "x": 0.55, "y": 0.7, "w": 3.35, "h": 7.0,
            "badge_bg": "#EDF3FC", "badge_text": "#1F4E9C",
            "items": [
                ("GDELT DOC 2.0 API", "Real global macro & geopolitical news"),
                ("NewsAPI & Social Ingest", "Financial news & institutional chatter"),
                ("Deterministic Disk Cache", "Zero-cost 100% offline reproducibility"),
                ("Pipeline Normalization", "Title dedup, text bounds (20k chars)"),
                ("Canonical Grounding", "20 systemic wholesale counterparties"),
            ]
        },
        {
            "stage": "STAGE 2",
            "title": "Extract (LLM + FinBERT)",
            "x": 4.25, "y": 0.7, "w": 3.35, "h": 7.0,
            "badge_bg": "#EDF3FC", "badge_text": "#1F4E9C",
            "items": [
                ("Gemini Structured LLM", "JSON schema: entity, theme, impact 1–10"),
                ("Heuristic Rules Fallback", "Keyword & regex safety net (zero hallucination)"),
                ("ProsusAI / FinBERT", "Independent domain sentiment [-1.0, +1.0]"),
                ("Controlled Vocabulary", "15 normalized systemic risk themes"),
                ("Claim Certainty", "Confirmed vs unverified rumor flags"),
            ]
        },
        {
            "stage": "STAGE 3",
            "title": "Confidence & Calibration",
            "x": 7.95, "y": 0.7, "w": 3.35, "h": 7.0,
            "badge_bg": "#EDF3FC", "badge_text": "#1F4E9C",
            "items": [
                ("5-Factor Credibility Score", "Source trust, corroboration, consistency"),
                ("Historical Event Study", "n = 24 market shocks (2020–2025 events)"),
                ("Empirical Linear Model", "|CAR| = 0.53% + 1.00 × Impact Score"),
                ("Leave-One-Out MAE 5.72%", "Spearman rank ρ = 0.529 (p = 0.008)"),
                ("80% Bootstrap Slope Band", "Uncertainty range [0.42, 1.58] per shock"),
            ]
        },
        {
            "stage": "STAGE 4",
            "title": "Trigger Gate & Debounce",
            "x": 11.65, "y": 0.7, "w": 3.35, "h": 7.0,
            "badge_bg": "#EDF3FC", "badge_text": "#1F4E9C",
            "items": [
                ("Dual Trigger Threshold", "Impact ≥ 7.0 and Confidence ≥ 0.60"),
                ("Rumor Isolation Filter", "Uncorroborated posts logged without stress"),
                ("48h Rolling Debounce", "Theme deduplication prevents double-count"),
                ("Scenario Synthesizer", "Merges evolving headlines into compound shock"),
                ("Audit Trail Storage", "Audit event logging to signals.jsonl"),
            ]
        },
        {
            "stage": "STAGE 5",
            "title": "Stress & Web Dashboard",
            "x": 15.35, "y": 0.7, "w": 3.35, "h": 7.0,
            "badge_bg": "#EDFDF5", "badge_text": "#067647",
            "items": [
                ("Synthetic Wholesale Book", "$1.32B balance sheet across 50 positions"),
                ("41 Shock Transmission Rules", "7 measured from CAR seed, 34 assumed"),
                ("Instrument Mechanics", "Bond duration, loan collateral, derivative delta"),
                ("FastAPI & SSE Service", "Real-time non-blocking event stream"),
                ("Institutional Web UI", "React 19, exposure treemap, what-if lab"),
            ]
        }
    ]

    for i, col in enumerate(cols):
        # Outer Card Container (White with clean 1px border)
        card_rect = patches.FancyBboxPatch(
            (col["x"], col["y"]), col["w"], col["h"],
            boxstyle="round,pad=0.04,rounding_size=0.12",
            edgecolor='#D0D5DD', facecolor='#FFFFFF',
            linewidth=1.2, zorder=2
        )
        ax.add_patch(card_rect)

        # Header area of card
        hdr_bg = patches.FancyBboxPatch(
            (col["x"] + 0.08, col["y"] + col["h"] - 0.95), col["w"] - 0.16, 0.85,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            edgecolor='#E3E6EB', facecolor='#F9FAFB',
            linewidth=0.8, zorder=3
        )
        ax.add_patch(hdr_bg)

        # Stage Badge (e.g. STAGE 1)
        ax.text(col["x"] + 0.2, col["y"] + col["h"] - 0.32, col["stage"],
                ha='left', va='center', fontsize=9.5, fontweight='bold',
                color=col["badge_text"], family='sans-serif', zorder=4)

        # Column Title
        ax.text(col["x"] + 0.2, col["y"] + col["h"] - 0.65, col["title"],
                ha='left', va='center', fontsize=13.0, fontweight='bold',
                color='#0F1B2D', family='sans-serif', zorder=4)

        # Item cards inside column (5 items per column)
        y_start = col["y"] + col["h"] - 1.15
        item_h = 1.08
        gap = 0.08

        for idx, (head, sub) in enumerate(col["items"]):
            item_y = y_start - (idx + 1) * (item_h + gap) + gap
            item_rect = patches.FancyBboxPatch(
                (col["x"] + 0.12, item_y), col["w"] - 0.24, item_h,
                boxstyle="round,pad=0.02,rounding_size=0.06",
                edgecolor='#EEF0F3', facecolor='#F8F9FA',
                linewidth=0.8, zorder=3
            )
            ax.add_patch(item_rect)

            # Bullet / Accent indicator
            bullet = patches.Circle(
                (col["x"] + 0.30, item_y + item_h * 0.68), 0.055,
                facecolor='#1F4E9C', edgecolor='none', zorder=4
            )
            ax.add_patch(bullet)

            # Header text
            ax.text(col["x"] + 0.44, item_y + item_h * 0.68, head,
                    ha='left', va='center', fontsize=11.2, fontweight='bold',
                    color='#0F1B2D', family='sans-serif', zorder=4)

            # Sub text / details
            ax.text(col["x"] + 0.44, item_y + item_h * 0.30, sub,
                    ha='left', va='center', fontsize=9.2,
                    color='#5B6676', family='sans-serif', zorder=4)

        # Flow Connector Arrow to Next Column
        if i < len(cols) - 1:
            arrow_x_start = col["x"] + col["w"] + 0.03
            arrow_x_end = cols[i+1]["x"] - 0.03
            arrow_y = col["y"] + col["h"] * 0.52
            
            arrow = patches.FancyArrowPatch(
                (arrow_x_start, arrow_y), (arrow_x_end, arrow_y),
                arrowstyle='->,head_width=4.0,head_length=6.0',
                connectionstyle='arc3',
                color='#1F4E9C', linewidth=2.0, zorder=5
            )
            ax.add_patch(arrow)

    # Bottom Metadata Strip
    footer_text = "Repository Facts: 50 Wholesale Positions ($1.32B Book)  •  41 Shock Transmission Rules (7 Measured, 34 Assumed)  •  n=24 Empirical Shocks (LOO MAE 5.72%)  •  Zero API Keys Needed Offline"
    ax.text(9.6, 0.28, footer_text, ha='center', va='center', fontsize=10.0, color='#8A94A6', family='sans-serif')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=100, facecolor=fig.get_facecolor(), bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    print(f"Architecture diagram generated: {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "architecture.png"
    generate_diagram(out)
