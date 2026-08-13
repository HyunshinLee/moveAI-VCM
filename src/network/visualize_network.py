from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from src.utils.config import BACKBONE_DIR, FIGURES_DIR, ensure_figures_dir


NODES_CSV = BACKBONE_DIR / "backbone_nodes.csv"
EDGES_GEOJSON = BACKBONE_DIR / "backbone_edges.geojson"
PNG_PATH = FIGURES_DIR / "backbone_network.png"


def main() -> None:
    ensure_figures_dir()
    nodes = pd.read_csv(NODES_CSV)
    edge_geojson = json.loads(EDGES_GEOJSON.read_text(encoding="utf-8"))

    fig, ax = plt.subplots(figsize=(9, 11), dpi=220)
    for feature in edge_geojson["features"]:
        coords = feature["geometry"]["coordinates"]
        if len(coords) < 2:
            continue
        xs = [coord[0] for coord in coords]
        ys = [coord[1] for coord in coords]
        rank = str(feature["properties"].get("road_rank", ""))
        color = {
            "101": "#d73027",
            "102": "#fc8d59",
            "103": "#4575b4",
            "105": "#74add1",
            "106": "#66bd63",
        }.get(rank, "#5f6b73")
        linewidth = {
            "101": 1.25,
            "102": 1.05,
            "103": 0.85,
            "105": 0.65,
            "106": 0.55,
        }.get(rank, 0.5)
        ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=0.55, zorder=1)

    ax.scatter(
        nodes["longitude"],
        nodes["latitude"],
        s=12,
        color="#111827",
        edgecolor="white",
        linewidth=0.35,
        alpha=0.9,
        zorder=2,
    )

    ax.set_title("Simplified Nationwide Road Backbone Network", fontsize=13, pad=10)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, linewidth=0.3, color="#d1d5db", alpha=0.65)
    ax.margins(0.04)
    fig.tight_layout()
    fig.savefig(PNG_PATH)
    plt.close(fig)
    print(f"Wrote {PNG_PATH}")


if __name__ == "__main__":
    main()
