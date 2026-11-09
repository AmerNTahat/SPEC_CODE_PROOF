"""Reproduce the manuscript comparison figure using Python and Matplotlib.

Run from any directory: python figures/plot-comparison.py
The input is evidence/comparison-plot-data.json. No experiments are executed.
"""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "evidence/comparison-plot-data.json").read_text())
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 9,
    "svg.fonttype": "none",
    "svg.hashsalt": "scp-comparison-v39",
})
BLUE = "#1f4e79"
GREEN = "#306b40"
GRAY = "#595959"

fig = plt.figure(figsize=(5.47, 6.8), facecolor="white")
ax = fig.add_axes([0.23, 0.65, 0.74, 0.28])
y = [3.6, 2.6, 1.0, 0.0]
for row, ypos in zip(DATA["comparisons"], y):
    retained = row["arm"] == "K+"
    value = row["measured_tokens"] / 1000
    ax.barh(ypos, value, height=0.52,
            color="#dcebf5" if retained else "#eeeeee",
            edgecolor=BLUE if retained else GRAY,
            hatch="///" if retained else "", linewidth=0.8, zorder=3)
    outcome = row["outcome"].replace("Model stage passed", "Stage passed")
    if row["estimated_unknown_usage_debit"]:
        outcome += "*"
    ax.text(value + 9, ypos, f'{row["measured_tokens"]:,}\n{outcome}',
            ha="left", va="center", fontsize=8, linespacing=1.25)
ax.set_yticks(y)
ax.set_yticklabels(["Later P/C $K$", "Later P/C $K^{+}$",
                    "Later SNG $K$", "Later SNG $K^{+}$"])
ax.set_xlim(0, 575)
ax.set_ylim(-0.65, 4.25)
ax.set_xticks([0, 100, 200, 300, 400, 500])
ax.set_xlabel("Measured experiment tokens (thousands)", labelpad=5)
ax.xaxis.grid(True, color="#dddddd", linewidth=0.5, zorder=0)
ax.tick_params(axis="y", length=0, pad=6)
for side in ["top", "right", "left"]:
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color("#888888")
fig.text(0.06, 0.97, "(a) Model-stage comparisons", fontsize=10, weight="bold")
fig.text(0.23, 0.575, "*The interrupted run also retains a 1M estimated debit.",
         fontsize=7.7, color=GRAY)

flow = fig.add_axes([0.055, 0.025, 0.91, 0.50])
flow.set_xlim(0, 1)
flow.set_ylim(0, 1)
flow.axis("off")
flow.text(0, 1, "(b) Later SNG $K^{+}$ continuation", fontsize=10, weight="bold", va="top")

def box(cx, cy, width, height, text, edge, fill, fontsize=8.5):
    patch = FancyBboxPatch((cx-width/2, cy-height/2), width, height,
                          boxstyle="round,pad=0.008,rounding_size=0.012",
                          linewidth=0.9, edgecolor=edge, facecolor=fill)
    flow.add_patch(patch)
    flow.text(cx, cy, text, fontsize=fontsize, ha="center", va="center",
              linespacing=1.3)

def arrow(start, end):
    flow.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>",
                                  mutation_scale=10, linewidth=0.9, color=GRAY))

centers = [0.16, 0.50, 0.84]
for cx, row in zip(centers, DATA["sng_milestones"]):
    label = row["label"].replace("Model stage passed", "Model stage\npassed").replace(
        "Proposal rejected", "Proposal\nrejected").replace("Paid repairs", "Authorized\npaid repairs")
    box(cx, 0.80, 0.29, 0.18,
        f'{label}\n{row["cumulative_tokens"]:,}', BLUE, "#eef5fa")
arrow((0.315, 0.80), (0.345, 0.80))
arrow((0.655, 0.80), (0.685, 0.80))
flow.text(0.5, 0.665, "Cumulative tokens for experiment model calls", fontsize=8,
          ha="center", color=GRAY)
arrow((0.84, 0.70), (0.84, 0.60))
flow.text(0.5, 0.56, "Later authorized repairs and checks\nSix completed categories",
          fontsize=9, ha="center", va="center", weight="bold", linespacing=1.25)
for i, row in enumerate(DATA["sng_completed_categories"]):
    cy = 0.425 if i < 3 else 0.255
    text = row["label"] + "\n" + row["result"]
    if i == 5:
        text = "QEMU observation\n20.033 s\nafter readiness"
    box(centers[i % 3], cy, 0.29, 0.125, text, GREEN, "#f0f6f0", fontsize=8)
flow.text(0.5, 0.12,
          "$K$ stopped at the model repair limit. Downstream checks were not run.",
          ha="center", fontsize=7.9, color=GRAY)
flow.text(0.5, 0.045,
          "$K^{+}$ start through observation: 2 h 31 min, including pauses.",
          ha="center", fontsize=8)

out = ROOT / "assets"
out.mkdir(exist_ok=True)
fig.savefig(out / "comparison-results.png", dpi=500, facecolor="white")
fig.savefig(out / "comparison-results.svg", facecolor="white",
            metadata={"Date": None, "Creator": "Matplotlib"})
plt.close(fig)
