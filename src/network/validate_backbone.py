from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
import pandas as pd

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from src.utils.config import BACKBONE_DIR, LOGS_DIR, TARGET_NODES, ensure_project_dirs


NODES_CSV = BACKBONE_DIR / "backbone_nodes.csv"
EDGES_CSV = BACKBONE_DIR / "backbone_edges.csv"


def build_graphs(nodes: pd.DataFrame, edges: pd.DataFrame) -> tuple[nx.Graph, nx.DiGraph]:
    undirected = nx.Graph()
    directed = nx.DiGraph()
    for row in nodes.itertuples(index=False):
        undirected.add_node(row.node_id, latitude=row.latitude, longitude=row.longitude)
        directed.add_node(row.node_id, latitude=row.latitude, longitude=row.longitude)

    for row in edges.itertuples(index=False):
        distance = float(row.distance_m)
        if undirected.has_edge(row.from_node, row.to_node):
            if distance < undirected[row.from_node][row.to_node]["distance_m"]:
                undirected[row.from_node][row.to_node]["distance_m"] = distance
        else:
            undirected.add_edge(row.from_node, row.to_node, distance_m=distance)
        directed.add_edge(row.from_node, row.to_node, distance_m=distance)
    return undirected, directed


def graph_metrics(graph: nx.Graph) -> dict[str, float | int | bool]:
    if graph.number_of_nodes() == 0:
        return {
            "number_of_nodes": 0,
            "number_of_edges": 0,
            "average_degree": 0.0,
            "connected_components": 0,
            "graph_density": 0.0,
            "number_of_articulation_points": 0,
            "number_of_bridges": 0,
            "cycle_exists": False,
            "cycle_rank": 0,
        }
    components = nx.number_connected_components(graph)
    articulation = list(nx.articulation_points(graph))
    bridges = list(nx.bridges(graph))
    cycle_rank = graph.number_of_edges() - graph.number_of_nodes() + components
    return {
        "number_of_nodes": graph.number_of_nodes(),
        "number_of_edges": graph.number_of_edges(),
        "average_degree": sum(dict(graph.degree()).values()) / graph.number_of_nodes(),
        "connected_components": components,
        "graph_density": nx.density(graph),
        "number_of_articulation_points": len(articulation),
        "number_of_bridges": len(bridges),
        "cycle_exists": cycle_rank > 0,
        "cycle_rank": cycle_rank,
    }


def representative_node_pairs(nodes: pd.DataFrame, max_pairs: int = 10) -> list[tuple[str, str, str]]:
    df = nodes.dropna(subset=["latitude", "longitude"]).copy()
    if len(df) < 2:
        return []

    extremes = {
        "west-east": (
            df.sort_values("longitude").iloc[0].node_id,
            df.sort_values("longitude").iloc[-1].node_id,
        ),
        "south-north": (
            df.sort_values("latitude").iloc[0].node_id,
            df.sort_values("latitude").iloc[-1].node_id,
        ),
        "northwest-southeast": (
            df.assign(score=df["latitude"] - df["longitude"]).sort_values("score").iloc[-1].node_id,
            df.assign(score=df["latitude"] - df["longitude"]).sort_values("score").iloc[0].node_id,
        ),
        "southwest-northeast": (
            df.assign(score=df["latitude"] + df["longitude"]).sort_values("score").iloc[0].node_id,
            df.assign(score=df["latitude"] + df["longitude"]).sort_values("score").iloc[-1].node_id,
        ),
    }

    ranked = df.sort_values("importance_score", ascending=False).head(20)["node_id"].tolist()
    for idx in range(0, min(len(ranked) - 1, 12), 2):
        extremes[f"important-{idx // 2 + 1}"] = (ranked[idx], ranked[idx + 1])

    pairs: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for label, (source, target) in extremes.items():
        key = tuple(sorted((source, target)))
        if source == target or key in seen:
            continue
        seen.add(key)
        pairs.append((label, source, target))
        if len(pairs) >= max_pairs:
            break
    return pairs


def robustness_tests(graph: nx.Graph, nodes: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for label, source, target in representative_node_pairs(nodes):
        if source not in graph or target not in graph:
            continue
        try:
            path = nx.shortest_path(graph, source, target, weight="distance_m")
            distance = nx.shortest_path_length(graph, source, target, weight="distance_m")
        except nx.NetworkXNoPath:
            rows.append(
                {
                    "pair_label": label,
                    "source": source,
                    "target": target,
                    "shortest_path_exists": False,
                    "shortest_distance_km": None,
                    "removed_edge": None,
                    "alternative_path_exists": False,
                    "alternative_distance_km": None,
                    "detour_ratio": None,
                    "path_node_count": None,
                }
            )
            continue

        removed = None
        alternative_exists = False
        alternative_distance = None
        detour_ratio = None
        if len(path) >= 2:
            edge_candidates = list(zip(path[:-1], path[1:]))
            removed = edge_candidates[len(edge_candidates) // 2]
            test_graph = graph.copy()
            test_graph.remove_edge(*removed)
            try:
                alternative_distance = nx.shortest_path_length(
                    test_graph, source, target, weight="distance_m"
                )
                alternative_exists = True
                detour_ratio = alternative_distance / distance if distance else None
            except nx.NetworkXNoPath:
                alternative_exists = False

        rows.append(
            {
                "pair_label": label,
                "source": source,
                "target": target,
                "shortest_path_exists": True,
                "shortest_distance_km": round(distance / 1000.0, 3),
                "removed_edge": f"{removed[0]}->{removed[1]}" if removed else None,
                "alternative_path_exists": alternative_exists,
                "alternative_distance_km": (
                    round(alternative_distance / 1000.0, 3)
                    if alternative_distance is not None
                    else None
                ),
                "detour_ratio": round(detour_ratio, 4) if detour_ratio is not None else None,
                "path_node_count": len(path),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    nodes = pd.read_csv(NODES_CSV)
    edges = pd.read_csv(EDGES_CSV)
    undirected, directed = build_graphs(nodes, edges)
    metrics = graph_metrics(undirected)
    directed_metrics = {
        "number_of_directed_edges": directed.number_of_edges(),
        "weakly_connected_components": nx.number_weakly_connected_components(directed),
        "strongly_connected_components": nx.number_strongly_connected_components(directed),
    }
    tests = robustness_tests(undirected, nodes)

    report = {
        "target_nodes": TARGET_NODES,
        "undirected_metrics": metrics,
        "directed_metrics": directed_metrics,
        "robustness_summary": {
            "tested_pairs": int(len(tests)),
            "shortest_path_successes": int(tests["shortest_path_exists"].sum()) if len(tests) else 0,
            "alternative_path_successes": (
                int(tests["alternative_path_exists"].sum()) if len(tests) else 0
            ),
        },
    }

    ensure_project_dirs()
    tests_path = LOGS_DIR / "robustness_tests.csv"
    report_path = LOGS_DIR / "validation_report.json"
    tests.to_csv(tests_path, index=False, encoding="utf-8-sig")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("== Backbone validation metrics ==")
    for key, value in metrics.items():
        print(f"{key}: {value}")
    print("\n== Directed graph metrics ==")
    for key, value in directed_metrics.items():
        print(f"{key}: {value}")
    print("\n== Robustness tests ==")
    print(tests.to_string(index=False))
    print(f"\nWrote {tests_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
