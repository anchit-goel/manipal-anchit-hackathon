"""Generate high-resolution architecture diagram for Signal-to-Shock."""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_diagram(output_path: Path):
    fig = plt.figure(figsize=(16, 9), dpi=300)
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor('#0B0F17')
    ax.set_facecolor('#0B0F17')

    # Remove axes
    ax.axis('off')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)

    # Title Banner
    ax.text(8.0, 8.5, "SIGNAL-TO-SHOCK: END-TO-END ARCHITECTURE PIPELINE",
            ha='center', va='center', fontsize=18, fontweight='bold', color='#38BDF8', family='sans-serif')
    ax.text(8.0, 8.15, "Multi-source news & social ingestion -> NLP extraction -> Trigger debounce -> Calibrated exposure stress -> Web UI",
            ha='center', va='center', fontsize=10, color='#94A3B8', family='sans-serif')

    # Define Column Boxes
    cols = [
        {
            "title": "1. Ingestion & Grounding",
            "x": 0.5, "y": 1.2, "w": 2.7, "h": 6.3,
            "border": "#38BDF8", "bg": "#0F172A",
            "items": [
                ("GDELT Project v2", "Global geopolitical news"),
                ("NewsAPI Financials", "Business & market news"),
                ("Social / X Feeds", "Real-time rumors & alerts"),
                ("Deduplication Engine", "Title normalization & hash"),
                ("Entity Matcher", "50-ticker canonical universe"),
            ]
        },
        {
            "title": "2. NLP & Signal Engine",
            "x": 3.6, "y": 1.2, "w": 2.7, "h": 6.3,
            "border": "#818CF8", "bg": "#0F172A",
            "items": [
                ("Gemini LLM Extractor", "Entity, themes, impact (1-10)"),
                ("LLM Disk Cache & Backoff", "Zero-cost offline execution"),
                ("Rules Fallback Extractor", "Keyword & regex heuristics"),
                ("FinBERT Sentiment", "Domain-trained [-1.0, 1.0]"),
                ("Confidence Calculator", "Multi-factor credibility score"),
            ]
        },
        {
            "title": "3. Trigger & Debounce",
            "x": 6.7, "y": 1.2, "w": 2.7, "h": 6.3,
            "border": "#F59E0B", "bg": "#0F172A",
            "items": [
                ("Trigger Threshold Gate", "Impact >= 7.0 & Conf >= 0.75"),
                ("Suppression Logic", "Filters unverified rumors"),
                ("Debounce Engine", "48h window per theme"),
                ("Scenario Merger", "Corroborating event synthesis"),
                ("Event Sequence Store", "signals.jsonl replay track"),
            ]
        },
        {
            "title": "4. Stress Transmission",
            "x": 9.8, "y": 1.2, "w": 2.7, "h": 6.3,
            "border": "#EF4444", "bg": "#0F172A",
            "items": [
                ("Synthetic Portfolio", "$1.32B wholesale bank book"),
                ("50 Positions Across 4 Types", "Loans, Bonds, Equity, Derivs"),
                ("Calibration Power-Law", "y = a * x^b (n=24 events)"),
                ("Asset Transmission Models", "Bond duration, loan collateral"),
                ("Shock Table & Heatmap", "Theme x Exposure Tag matrix"),
            ]
        },
        {
            "title": "5. Command Centre UI",
            "x": 12.9, "y": 1.2, "w": 2.6, "h": 6.3,
            "border": "#10B981", "bg": "#0F172A",
            "items": [
                ("FastAPI Service", "REST API + SSE Replay Stream"),
                ("React 19 + Vite + Tailwind", "Dark mode risk command centre"),
                ("Live Stress Waterfall", "Gross PnL & top movers"),
                ("What-If Simulator", "Real-time theme & severity slider"),
                ("Calibration & Audit", "Residuals, LOO MAE, full audit"),
            ]
        }
    ]

    for col in cols:
        # Card container
        rect = patches.FancyBboxPatch(
            (col["x"], col["y"]), col["w"], col["h"],
            boxstyle="round,pad=0.1,rounding_size=0.15",
            edgecolor=col["border"], facecolor=col["bg"],
            linewidth=1.8, alpha=0.9
        )
        ax.add_patch(rect)

        # Header banner
        hdr_rect = patches.FancyBboxPatch(
            (col["x"] + 0.05, col["y"] + col["h"] - 0.7), col["w"] - 0.1, 0.65,
            boxstyle="round,pad=0.05,rounding_size=0.1",
            edgecolor="none", facecolor=col["border"], alpha=0.25
        )
        ax.add_patch(hdr_rect)
        ax.text(col["x"] + col["w"]/2, col["y"] + col["h"] - 0.38, col["title"],
                ha='center', va='center', fontsize=10.5, fontweight='bold', color='#F8FAFC', family='sans-serif')

        # Items
        item_y = col["y"] + col["h"] - 1.2
        for title, desc in col["items"]:
            # item pill
            item_bg = patches.FancyBboxPatch(
                (col["x"] + 0.12, item_y - 0.75), col["w"] - 0.24, 0.82,
                boxstyle="round,pad=0.05,rounding_size=0.08",
                edgecolor='#334155', facecolor='#1E293B', linewidth=1.0
            )
            ax.add_patch(item_bg)
            ax.text(col["x"] + 0.22, item_y - 0.22, title,
                    fontsize=9, fontweight='bold', color='#F1F5F9', family='sans-serif')
            ax.text(col["x"] + 0.22, item_y - 0.52, desc,
                    fontsize=7.5, color='#94A3B8', family='sans-serif')
            item_y -= 1.0

    # Connector Arrows
    arrow_props = dict(arrowstyle="-|>", color="#64748B", lw=2, mutation_scale=15)
    for i in range(len(cols) - 1):
        x_start = cols[i]["x"] + cols[i]["w"]
        x_end = cols[i+1]["x"]
        y_pos = 4.35
        ax.annotate('', xy=(x_end, y_pos), xytext=(x_start, y_pos), arrowprops=arrow_props)

    # Footer note
    ax.text(8.0, 0.5, "Deterministic & Offline-First: All models fall back to local cached inferences & rules without internet access.",
            ha='center', va='center', fontsize=9, color='#64748B', style='italic', family='sans-serif')

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close()
    print(f"Generated architecture diagram at {output_path}")

if __name__ == "__main__":
    generate_diagram(Path("docs/architecture.png"))
