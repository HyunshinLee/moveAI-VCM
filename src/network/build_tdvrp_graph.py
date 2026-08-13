from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from src.utils.config import PHYSICAL_DIR, TDVRP_DIR, configured_hours, ensure_project_dirs


PHYSICAL_NODES_CSV = PHYSICAL_DIR / "physical_nodes.csv"
PHYSICAL_EDGES_CSV = PHYSICAL_DIR / "physical_edges.csv"
EDGE_TIME_PROFILES_CSV = PHYSICAL_DIR / "edge_time_profiles.csv"

SERVICE_NODES_CSV = TDVRP_DIR / "service_nodes.csv"
TD_OD_MATRIX_CSV = TDVRP_DIR / "td_od_matrix.csv"
TD_PATHS_CSV = TDVRP_DIR / "td_paths.csv"

SERVICE_NODE_TYPES = {"DEPOT", "CUSTOMER"}


def log(message: str) -> None:
    print(f"[tdvrp_graph] {message}", flush=True)


def read_physical_network() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    nodes = pd.read_csv(PHYSICAL_NODES_CSV, dtype=str).fillna("")
    edges = pd.read_csv(PHYSICAL_EDGES_CSV, dtype=str).fillna("")
    profiles = pd.read_csv(EDGE_TIME_PROFILES_CSV, dtype={"edge_id": str})

    for col in ["latitude", "longitude", "demand", "service_time"]:
        if col in nodes.columns:
            nodes[col] = pd.to_numeric(nodes[col], errors="coerce")
    for col in ["distance_km", "distance_m"]:
        edges[col] = pd.to_numeric(edges[col], errors="coerce").fillna(0.0)
    profiles["hour"] = pd.to_numeric(profiles["hour"], errors="coerce").astype(int)
    profiles["travel_time_min"] = pd.to_numeric(profiles["travel_time_min"], errors="coerce")
    return nodes, edges, profiles


def extract_service_nodes(nodes: pd.DataFrame) -> pd.DataFrame:
    service_nodes = nodes[nodes["node_type"].isin(SERVICE_NODE_TYPES)].copy()
    type_order = {"DEPOT": 0, "CUSTOMER": 1}
    service_nodes["_type_order"] = service_nodes["node_type"].map(type_order)
    service_nodes = service_nodes.sort_values(["_type_order", "node_id"]).drop(columns=["_type_order"])

    desired_cols = [
        "node_id",
        "node_type",
        "latitude",
        "longitude",
        "demand",
        "tw_start",
        "tw_end",
        "service_time",
        "nearest_backbone_node",
        "nearest_backbone_distance_km",
    ]
    for col in desired_cols:
        if col not in service_nodes.columns:
            service_nodes[col] = ""
    return service_nodes[desired_cols]


def profile_lookup_for_hour(profiles: pd.DataFrame, hour: int) -> dict[str, float]:
    hour_profiles = profiles[profiles["hour"].eq(hour)]
    return {
        str(row.edge_id): float(row.travel_time_min)
        for row in hour_profiles.itertuples(index=False)
    }


def build_hour_graph(edges: pd.DataFrame, travel_time_lookup: dict[str, float]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for row in edges.itertuples(index=False):
        edge_id = str(row.edge_id)
        if edge_id not in travel_time_lookup:
            continue
        u = str(row.from_node)
        v = str(row.to_node)
        travel_time = float(travel_time_lookup[edge_id])
        distance_km = float(row.distance_km)
        if graph.has_edge(u, v) and graph[u][v]["travel_time_min"] <= travel_time:
            continue
        graph.add_edge(
            u,
            v,
            edge_id=edge_id,
            travel_time_min=travel_time,
            distance_km=distance_km,
        )
    return graph


def path_edge_ids_and_distance(graph: nx.DiGraph, path_nodes: list[str]) -> tuple[list[str], float]:
    edge_ids: list[str] = []
    distance_km = 0.0
    for u, v in zip(path_nodes[:-1], path_nodes[1:]):
        data = graph[u][v]
        edge_ids.append(str(data["edge_id"]))
        distance_km += float(data["distance_km"])
    return edge_ids, distance_km


def build_td_matrices(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    profiles: pd.DataFrame,
    service_nodes: pd.DataFrame,
    hours: list[int],
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    service_ids = service_nodes["node_id"].tolist()
    od_rows: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    unreachable: list[dict[str, Any]] = []

    for hour in hours:
        travel_time_lookup = profile_lookup_for_hour(profiles, hour)
        graph = build_hour_graph(edges, travel_time_lookup)
        graph.add_nodes_from(nodes["node_id"].tolist())

        for origin in service_ids:
            try:
                lengths, paths = nx.single_source_dijkstra(
                    graph, origin, weight="travel_time_min"
                )
            except nx.NetworkXNoPath:
                lengths, paths = {}, {}

            for destination in service_ids:
                if origin == destination:
                    continue
                if destination not in lengths:
                    unreachable.append(
                        {"from_node": origin, "to_node": destination, "hour": hour}
                    )
                    continue

                path_nodes = [str(node) for node in paths[destination]]
                path_edges, distance_km = path_edge_ids_and_distance(graph, path_nodes)
                travel_time_min = float(lengths[destination])
                common = {
                    "from_node": origin,
                    "to_node": destination,
                    "hour": hour,
                    "travel_time_min": round(travel_time_min, 6),
                    "distance_km": round(distance_km, 6),
                }
                od_rows.append(common)
                path_rows.append(
                    {
                        **common,
                        "path_nodes": "|".join(path_nodes),
                        "path_edges": "|".join(path_edges),
                    }
                )

    return pd.DataFrame(od_rows), pd.DataFrame(path_rows), unreachable


def print_validation(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    service_nodes: pd.DataFrame,
    hours: list[int],
    od_matrix: pd.DataFrame,
    paths: pd.DataFrame,
    unreachable: list[dict[str, Any]],
) -> None:
    print("== TDVRP graph validation ==")
    print(f"physical node count: {len(nodes):,}")
    print(f"physical edge count: {len(edges):,}")
    print(f"number of ROAD nodes: {int(nodes.node_type.eq('ROAD').sum()):,}")
    print(f"number of DEPOT nodes: {int(nodes.node_type.eq('DEPOT').sum()):,}")
    print(f"number of CUSTOMER nodes: {int(nodes.node_type.eq('CUSTOMER').sum()):,}")
    print(f"service node count: {len(service_nodes):,}")
    print(f"number of hours: {len(hours)} ({hours[0]}-{hours[-1]})")
    print(f"generated OD-hour entries: {len(od_matrix):,}")
    print(f"unreachable OD pairs: {len(unreachable):,}")

    if len(od_matrix):
        print(f"minimum travel time: {od_matrix.travel_time_min.min():.3f} min")
        print(f"maximum travel time: {od_matrix.travel_time_min.max():.3f} min")
        print(f"average travel time: {od_matrix.travel_time_min.mean():.3f} min")

    if unreachable:
        print("WARNING: at least one service OD-hour pair is unreachable.")
        print(pd.DataFrame(unreachable).head(20).to_string(index=False))

    sample_pairs = []
    service_ids = service_nodes["node_id"].tolist()
    for candidate in [("D01", "C001"), ("D03", "C002"), ("C001", "C010")]:
        if candidate[0] in service_ids and candidate[1] in service_ids:
            sample_pairs.append(candidate)
    if len(service_ids) >= 2:
        sample_pairs.append((service_ids[0], service_ids[-1]))

    sample_hours = sorted(set([hours[0], hours[len(hours) // 2], hours[-1]]))
    print("\n== Sample OD-hour travel times and physical paths ==")
    for origin, destination in sample_pairs[:4]:
        subset = paths[
            paths["from_node"].eq(origin)
            & paths["to_node"].eq(destination)
            & paths["hour"].isin(sample_hours)
        ].sort_values("hour")
        if subset.empty:
            continue
        print(f"\n{origin} -> {destination}")
        for row in subset.itertuples(index=False):
            print(
                f"  h={row.hour}: {row.travel_time_min:.2f} min, "
                f"{row.distance_km:.2f} km, path={row.path_nodes}"
            )


def main() -> None:
    ensure_project_dirs()
    hours = configured_hours()
    nodes, edges, profiles = read_physical_network()
    service_nodes = extract_service_nodes(nodes)
    service_nodes.to_csv(SERVICE_NODES_CSV, index=False, encoding="utf-8-sig")

    od_matrix, paths, unreachable = build_td_matrices(nodes, edges, profiles, service_nodes, hours)
    od_matrix.to_csv(TD_OD_MATRIX_CSV, index=False, encoding="utf-8-sig")
    paths.to_csv(TD_PATHS_CSV, index=False, encoding="utf-8-sig")

    print_validation(nodes, edges, service_nodes, hours, od_matrix, paths, unreachable)
    log(f"Wrote {SERVICE_NODES_CSV}")
    log(f"Wrote {TD_OD_MATRIX_CSV}")
    log(f"Wrote {TD_PATHS_CSV}")


if __name__ == "__main__":
    main()
