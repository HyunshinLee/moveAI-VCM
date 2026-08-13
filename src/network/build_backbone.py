from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd
import pyogrio
from pyproj import Transformer
from shapely.geometry import LineString

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from src.utils.config import (
    BACKBONE_DIR,
    CANDIDATE_ROAD_RANKS,
    LINK_COLUMNS,
    LINK_FILE,
    MAX_TARGET_NODES,
    MIN_TARGET_NODES,
    NODE_COLUMNS,
    NODE_FILE,
    PRIMARY_ROAD_RANKS,
    PROTECTED_NODE_TYPES,
    ROAD_RANK_LABELS,
    ROAD_TYPE_LABELS,
    TARGET_NODES,
    clean_code,
    clean_name,
    ensure_backbone_dir,
    is_important_name,
    join_unique,
    node_role_from_attrs,
    normalize_text_columns,
    pairwise,
    rank_priority,
    road_rank_label,
    road_type_label,
    safe_float,
)


TEXT_LINK_COLUMNS = [
    "LINK_ID",
    "F_NODE",
    "T_NODE",
    "ROAD_RANK",
    "ROAD_TYPE",
    "ROAD_NO",
    "ROAD_NAME",
    "ROAD_USE",
    "MULTI_LINK",
    "CONNECT",
]

TEXT_NODE_COLUMNS = ["NODE_ID", "NODE_TYPE", "NODE_NAME", "TURN_P"]


def log(message: str) -> None:
    print(f"[build_backbone] {message}", flush=True)


def edge_key(u: str, v: str) -> tuple[str, str]:
    return (u, v) if u <= v else (v, u)


def sq_dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def representative_rank(ranks: list[str]) -> str:
    if not ranks:
        return ""
    counts = Counter(ranks)
    return sorted(counts, key=lambda code: (-rank_priority(code), -counts[code], code))[0]


def representative_value(values: list[str]) -> str:
    cleaned = [clean_name(v) for v in values if clean_name(v)]
    if not cleaned:
        return ""
    counts = Counter(cleaned)
    return counts.most_common(1)[0][0]


def load_candidate_links() -> pd.DataFrame:
    log(f"Reading link shapefile: {LINK_FILE}")
    links = pyogrio.read_dataframe(LINK_FILE, columns=LINK_COLUMNS)
    normalize_text_columns(links, TEXT_LINK_COLUMNS)
    links["LENGTH"] = pd.to_numeric(links["LENGTH"], errors="coerce").fillna(0.0)
    links["MAX_SPD"] = pd.to_numeric(links["MAX_SPD"], errors="coerce").fillna(0).astype(int)

    before = len(links)
    links = links[
        links["ROAD_RANK"].isin(CANDIDATE_ROAD_RANKS)
        & links["F_NODE"].ne("")
        & links["T_NODE"].ne("")
        & links["F_NODE"].ne(links["T_NODE"])
    ].copy()
    log(
        "Filtered links by ROAD_RANK "
        f"{CANDIDATE_ROAD_RANKS}: {len(links):,} / {before:,} rows"
    )
    log("Candidate ROAD_RANK distribution:")
    for code, count in links["ROAD_RANK"].value_counts().sort_index().items():
        km = links.loc[links["ROAD_RANK"] == code, "LENGTH"].sum() / 1000.0
        log(f"  {code} {road_rank_label(code)}: {count:,} links, {km:,.1f} km")
    return links


def build_raw_graph(
    links: pd.DataFrame,
) -> tuple[nx.Graph, dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    log("Building weighted undirected raw graph and directed link lookup")
    graph = nx.Graph()
    pair_store: dict[tuple[str, str], dict[str, Any]] = {}
    directed_best: dict[tuple[str, str], dict[str, Any]] = {}

    for row in links.itertuples(index=False):
        f_node = clean_code(row.F_NODE)
        t_node = clean_code(row.T_NODE)
        if not f_node or not t_node or f_node == t_node:
            continue
        length = safe_float(row.LENGTH)
        geometry = row.geometry
        if length <= 0 and geometry is not None:
            length = safe_float(getattr(geometry, "length", 0.0))
        if length <= 0:
            continue

        attr = {
            "link_id": clean_code(row.LINK_ID),
            "f_node": f_node,
            "t_node": t_node,
            "length": length,
            "road_rank": clean_code(row.ROAD_RANK),
            "road_type": clean_code(row.ROAD_TYPE),
            "road_no": clean_name(row.ROAD_NO),
            "road_name": clean_name(row.ROAD_NAME),
            "road_use": clean_code(row.ROAD_USE),
            "multi_link": clean_code(row.MULTI_LINK),
            "connect": clean_code(row.CONNECT),
            "max_spd": int(row.MAX_SPD),
            "geometry": geometry,
        }

        key = edge_key(f_node, t_node)
        store = pair_store.setdefault(
            key,
            {
                "link_ids": [],
                "road_ranks": [],
                "road_types": [],
                "road_nos": [],
                "road_names": [],
                "max_spds": [],
                "directions": defaultdict(list),
                "best": None,
            },
        )
        store["link_ids"].append(attr["link_id"])
        store["road_ranks"].append(attr["road_rank"])
        store["road_types"].append(attr["road_type"])
        store["road_nos"].append(attr["road_no"])
        store["road_names"].append(attr["road_name"])
        store["max_spds"].append(attr["max_spd"])
        store["directions"][(f_node, t_node)].append(attr)
        if store["best"] is None or length < store["best"]["length"]:
            store["best"] = attr

        direction_key = (f_node, t_node)
        if direction_key not in directed_best or length < directed_best[direction_key]["length"]:
            directed_best[direction_key] = attr

        graph_attr = {
            "weight": length,
            "pair_key": key,
            "best_link_id": attr["link_id"],
            "road_rank": attr["road_rank"],
            "road_type": attr["road_type"],
            "road_no": attr["road_no"],
            "road_name": attr["road_name"],
            "max_spd": attr["max_spd"],
        }
        if not graph.has_edge(f_node, t_node) or length < graph[f_node][t_node]["weight"]:
            graph.add_edge(f_node, t_node, **graph_attr)

    log(f"Raw graph: {graph.number_of_nodes():,} nodes, {graph.number_of_edges():,} undirected edges")
    return graph, pair_store, directed_best


def keep_largest_component(graph: nx.Graph) -> tuple[nx.Graph, set[str], list[int]]:
    components = sorted(nx.connected_components(graph), key=len, reverse=True)
    sizes = [len(component) for component in components]
    largest = set(components[0])
    log(f"Connected components in candidate graph: {len(sizes):,}")
    log(f"Top component sizes: {sizes[:10]}")
    log(
        "Using largest mainland component. Smaller components usually include islands or "
        "isolated road updates without mainland continuity."
    )
    return graph.subgraph(largest).copy(), largest, sizes


def load_node_attributes(component_nodes: set[str]) -> tuple[dict[str, dict[str, Any]], Transformer, str]:
    log(f"Reading node shapefile: {NODE_FILE}")
    nodes = pyogrio.read_dataframe(NODE_FILE, columns=NODE_COLUMNS)
    normalize_text_columns(nodes, TEXT_NODE_COLUMNS)
    nodes = nodes[nodes["NODE_ID"].isin(component_nodes)].copy()
    crs_text = str(nodes.crs)
    transformer = Transformer.from_crs(nodes.crs, "EPSG:4326", always_xy=True)
    log(f"Node CRS: {crs_text}")
    log(f"Node rows retained for largest component: {len(nodes):,}")

    attrs: dict[str, dict[str, Any]] = {}
    for row in nodes.itertuples(index=False):
        node_id = clean_code(row.NODE_ID)
        geom = row.geometry
        if geom is None or geom.is_empty:
            x = y = lon = lat = None
        else:
            x = float(geom.x)
            y = float(geom.y)
            lon, lat = transformer.transform(x, y)
            lon = float(lon)
            lat = float(lat)
        attrs[node_id] = {
            "original_node_id": node_id,
            "node_type": clean_code(row.NODE_TYPE),
            "node_name": clean_name(row.NODE_NAME),
            "turn_p": clean_code(row.TURN_P),
            "x": x,
            "y": y,
            "longitude": lon,
            "latitude": lat,
        }

    missing = component_nodes - set(attrs)
    for node_id in missing:
        attrs[node_id] = {
            "original_node_id": node_id,
            "node_type": "",
            "node_name": "",
            "turn_p": "",
            "x": None,
            "y": None,
            "longitude": None,
            "latitude": None,
        }
    if missing:
        log(f"Warning: {len(missing):,} graph nodes were missing from MOCT_NODE and kept without geometry")
    return attrs, transformer, crs_text


def edge_signature(data: dict[str, Any]) -> tuple[str, str]:
    rank = clean_code(data.get("road_rank"))
    road_no = clean_name(data.get("road_no"))
    road_name = clean_name(data.get("road_name"))
    route_id = road_no or road_name
    return rank, route_id


def determine_corridor_core_nodes(graph: nx.Graph, node_attrs: dict[str, dict[str, Any]]) -> set[str]:
    log("Identifying non-contractable nodes for first corridor contraction")
    core: set[str] = set()
    for node in graph.nodes:
        degree = graph.degree(node)
        attrs = node_attrs.get(node, {})
        node_name = attrs.get("node_name", "")
        node_type = attrs.get("node_type", "")
        turn_p = attrs.get("turn_p", "")

        keep = degree != 2
        keep = keep or is_important_name(node_name)
        keep = keep or node_type in PROTECTED_NODE_TYPES
        keep = keep or turn_p == "1"

        if not keep and degree == 2:
            neighbors = list(graph.neighbors(node))
            first = edge_signature(graph[node][neighbors[0]])
            second = edge_signature(graph[node][neighbors[1]])
            keep = first != second

        if keep:
            core.add(node)

    log(f"First-pass core nodes: {len(core):,} / {graph.number_of_nodes():,}")
    return core


def summarize_corridor(graph: nx.Graph, path: list[str]) -> dict[str, Any]:
    ranks: list[str] = []
    types: list[str] = []
    road_nos: list[str] = []
    road_names: list[str] = []
    link_ids: list[str] = []
    max_spds: list[int] = []
    distance = 0.0
    for u, v in pairwise(path):
        data = graph[u][v]
        distance += float(data["weight"])
        ranks.append(clean_code(data.get("road_rank")))
        types.append(clean_code(data.get("road_type")))
        road_nos.append(clean_name(data.get("road_no")))
        road_names.append(clean_name(data.get("road_name")))
        link_ids.append(clean_code(data.get("best_link_id")))
        max_spds.append(int(data.get("max_spd", 0)))
    rank = representative_rank(ranks)
    return {
        "weight": distance,
        "node_path": path,
        "road_rank": rank,
        "road_class": road_rank_label(rank),
        "road_type": representative_value(types),
        "road_no": representative_value(road_nos),
        "road_name": representative_value(road_names),
        "road_ranks": ranks,
        "road_types": types,
        "road_nos": road_nos,
        "road_names": road_names,
        "best_link_ids": link_ids,
        "max_spd": max(max_spds) if max_spds else 0,
    }


def contract_to_corridor_graph(graph: nx.Graph, core_nodes: set[str]) -> nx.Graph:
    log("Contracting degree-2 pass-through nodes into corridor graph")
    corridor = nx.Graph()
    corridor.add_nodes_from(core_nodes)
    visited_edges: set[tuple[str, str]] = set()

    for start in list(core_nodes):
        if start not in graph:
            continue
        for neighbor in list(graph.neighbors(start)):
            first_key = edge_key(start, neighbor)
            if first_key in visited_edges:
                continue

            path = [start]
            previous = start
            current = neighbor
            aborted = False
            while True:
                key = edge_key(previous, current)
                if key in visited_edges:
                    aborted = True
                    break
                visited_edges.add(key)
                path.append(current)
                if current in core_nodes:
                    break
                next_nodes = [candidate for candidate in graph.neighbors(current) if candidate != previous]
                if not next_nodes:
                    break
                previous, current = current, next_nodes[0]

            if aborted or len(path) < 2 or path[0] == path[-1]:
                continue
            attrs = summarize_corridor(graph, path)
            u, v = path[0], path[-1]
            if corridor.has_edge(u, v):
                if attrs["weight"] < corridor[u][v]["weight"]:
                    corridor[u][v].update(attrs)
            else:
                corridor.add_edge(u, v, **attrs)

    unvisited = graph.number_of_edges() - len(visited_edges)
    if unvisited:
        log(f"Warning: {unvisited:,} raw edges were not visited during contraction")
    isolated = [node for node, degree in corridor.degree() if degree == 0]
    corridor.remove_nodes_from(isolated)
    log(
        f"Corridor graph: {corridor.number_of_nodes():,} nodes, "
        f"{corridor.number_of_edges():,} edges"
    )
    return corridor


def approximate_centrality(graph: nx.Graph) -> dict[str, float]:
    node_count = graph.number_of_nodes()
    if node_count < 3:
        return {node: 0.0 for node in graph.nodes}
    if node_count > 80_000:
        k = 35
    elif node_count > 40_000:
        k = 50
    elif node_count > 15_000:
        k = 80
    else:
        k = min(120, node_count)
    log(f"Computing approximate betweenness centrality on corridor graph (k={k})")
    started = time.time()
    centrality = nx.betweenness_centrality(graph, k=k, normalized=True, weight="weight", seed=20260813)
    log(f"Centrality finished in {time.time() - started:,.1f} seconds")
    return centrality


def score_corridor_nodes(
    graph: nx.Graph,
    node_attrs: dict[str, dict[str, Any]],
    centrality: dict[str, float],
) -> dict[str, float]:
    max_centrality = max(centrality.values()) if centrality else 0.0
    scores: dict[str, float] = {}
    for node in graph.nodes:
        attrs = node_attrs.get(node, {})
        incident_ranks = [data.get("road_rank", "") for _, _, data in graph.edges(node, data=True)]
        best_rank = max((rank_priority(rank) for rank in incident_ranks), default=0)
        primary_bonus = 10.0 if any(rank in PRIMARY_ROAD_RANKS for rank in incident_ranks) else 0.0
        central = centrality.get(node, 0.0) / max_centrality if max_centrality else 0.0
        degree = graph.degree(node)
        score = (
            min(degree, 8) * 8.0
            + best_rank * 9.0
            + primary_bonus
            + central * 70.0
            + (35.0 if is_important_name(attrs.get("node_name", "")) else 0.0)
            + (18.0 if attrs.get("node_type") in PROTECTED_NODE_TYPES else 0.0)
            + (8.0 if attrs.get("turn_p") == "1" else 0.0)
        )
        scores[node] = score
    return scores


def node_coord(node: str, node_attrs: dict[str, dict[str, Any]]) -> tuple[float, float] | None:
    attrs = node_attrs.get(node, {})
    lon = attrs.get("longitude")
    lat = attrs.get("latitude")
    if lon is None or lat is None:
        return None
    return float(lon), float(lat)


def select_anchors(
    graph: nx.Graph,
    node_attrs: dict[str, dict[str, Any]],
    scores: dict[str, float],
    target_count: int,
) -> set[str]:
    candidates = [node for node in graph.nodes if node_coord(node, node_attrs) is not None]
    ranked = sorted(candidates, key=lambda node: (-scores.get(node, 0.0), node))
    anchors: list[str] = []
    anchor_set: set[str] = set()

    def add(node: str) -> None:
        if node not in anchor_set and len(anchor_set) < target_count:
            anchor_set.add(node)
            anchors.append(node)

    important_quota = max(20, min(65, target_count // 3))
    for node in ranked:
        attrs = node_attrs.get(node, {})
        incident_primary = any(
            data.get("road_rank") in PRIMARY_ROAD_RANKS for _, _, data in graph.edges(node, data=True)
        )
        if (
            is_important_name(attrs.get("node_name", ""))
            or attrs.get("node_type") in PROTECTED_NODE_TYPES
            or (graph.degree(node) >= 4 and incident_primary)
        ):
            add(node)
        if len(anchor_set) >= important_quota:
            break

    coords = {node: node_coord(node, node_attrs) for node in candidates}
    valid_coords = [coord for coord in coords.values() if coord is not None]
    min_lon = min(coord[0] for coord in valid_coords)
    max_lon = max(coord[0] for coord in valid_coords)
    min_lat = min(coord[1] for coord in valid_coords)
    max_lat = max(coord[1] for coord in valid_coords)
    lon_range = max(max_lon - min_lon, 0.01)
    lat_range = max(max_lat - min_lat, 0.01)

    grid_cells = max(target_count, int(target_count * 1.25))
    cols = max(8, int(round(math.sqrt(grid_cells * lon_range / lat_range))))
    rows = max(8, int(math.ceil(grid_cells / cols)))

    best_by_cell: dict[tuple[int, int], str] = {}
    for node, coord in coords.items():
        if coord is None:
            continue
        col = min(cols - 1, max(0, int((coord[0] - min_lon) / lon_range * cols)))
        row = min(rows - 1, max(0, int((coord[1] - min_lat) / lat_range * rows)))
        cell = (col, row)
        current = best_by_cell.get(cell)
        if current is None or scores.get(node, 0.0) > scores.get(current, 0.0):
            best_by_cell[cell] = node

    grid_quota = max(important_quota, int(target_count * 0.82))
    for node in sorted(best_by_cell.values(), key=lambda candidate: (-scores.get(candidate, 0.0), candidate)):
        add(node)
        if len(anchor_set) >= grid_quota:
            break

    for node in ranked:
        add(node)
        if len(anchor_set) >= target_count:
            break

    log(f"Selected {len(anchor_set):,} anchor nodes for target_count={target_count}")
    return anchor_set


def path_weight(graph: nx.Graph, path: list[str]) -> float:
    return sum(float(graph[u][v]["weight"]) for u, v in pairwise(path))


def shortest_path_cached(
    graph: nx.Graph,
    source: str,
    target: str,
    cache: dict[tuple[str, str], tuple[float, list[str]]],
) -> tuple[float, list[str]] | None:
    key = edge_key(source, target)
    if key in cache:
        return cache[key]
    try:
        path = nx.shortest_path(graph, source, target, weight="weight")
    except nx.NetworkXNoPath:
        return None
    result = (path_weight(graph, path), path)
    cache[key] = result
    return result


def add_anchor_pair(
    anchor_graph: nx.Graph,
    corridor_graph: nx.Graph,
    source: str,
    target: str,
    cache: dict[tuple[str, str], tuple[float, list[str]]],
) -> bool:
    if source == target or anchor_graph.has_edge(source, target):
        return False
    result = shortest_path_cached(corridor_graph, source, target, cache)
    if result is None:
        return False
    distance, path = result
    anchor_graph.add_edge(source, target, weight=distance, path=path)
    return True


def build_anchor_graph(
    corridor_graph: nx.Graph,
    anchors: set[str],
    node_attrs: dict[str, dict[str, Any]],
    neighbor_count: int,
    cache: dict[tuple[str, str], tuple[float, list[str]]],
) -> nx.Graph:
    anchor_graph = nx.Graph()
    anchor_graph.add_nodes_from(anchors)
    coords = {node: node_coord(node, node_attrs) for node in anchors}
    anchors_sorted = sorted(anchors)
    for source in anchors_sorted:
        source_coord = coords[source]
        if source_coord is None:
            continue
        nearest = sorted(
            (
                (sq_dist(source_coord, coords[target]), target)
                for target in anchors_sorted
                if target != source and coords[target] is not None
            ),
            key=lambda item: (item[0], item[1]),
        )[:neighbor_count]
        for _, target in nearest:
            add_anchor_pair(anchor_graph, corridor_graph, source, target, cache)

    while anchor_graph.number_of_nodes() > 1 and not nx.is_connected(anchor_graph):
        components = [set(component) for component in nx.connected_components(anchor_graph)]
        base = components[0]
        best: tuple[float, str, str] | None = None
        for comp in components[1:]:
            for u in base:
                coord_u = coords.get(u)
                if coord_u is None:
                    continue
                for v in comp:
                    coord_v = coords.get(v)
                    if coord_v is None:
                        continue
                    dist = sq_dist(coord_u, coord_v)
                    if best is None or dist < best[0]:
                        best = (dist, u, v)
        if best is None:
            break
        _, source, target = best
        if not add_anchor_pair(anchor_graph, corridor_graph, source, target, cache):
            break

    log(
        f"Anchor graph: {anchor_graph.number_of_nodes():,} nodes, "
        f"{anchor_graph.number_of_edges():,} candidate shortest-path links"
    )
    return anchor_graph


def scaffold_from_anchor_graph(
    corridor_graph: nx.Graph,
    anchor_graph: nx.Graph,
    extra_cycle_edges: int,
) -> nx.Graph:
    if anchor_graph.number_of_nodes() == 0:
        return nx.Graph()
    if nx.is_connected(anchor_graph):
        selected_graph = nx.minimum_spanning_tree(anchor_graph, weight="weight")
    else:
        selected_graph = nx.Graph()
        for component in nx.connected_components(anchor_graph):
            selected_graph.update(nx.minimum_spanning_tree(anchor_graph.subgraph(component), weight="weight"))

    selected_pairs = {edge_key(u, v) for u, v in selected_graph.edges}
    extras = []
    for u, v, data in anchor_graph.edges(data=True):
        key = edge_key(u, v)
        if key in selected_pairs:
            continue
        extras.append((float(data["weight"]), u, v))
    extras.sort(key=lambda item: item[0])
    for _, u, v in extras[:extra_cycle_edges]:
        selected_graph.add_edge(u, v, **anchor_graph[u][v])
        selected_pairs.add(edge_key(u, v))

    scaffold = nx.Graph()
    for u, v, data in selected_graph.edges(data=True):
        path = data["path"]
        for a, b in pairwise(path):
            scaffold.add_edge(a, b, **corridor_graph[a][b])

    return scaffold


def stitch_raw_path(scaffold: nx.Graph, h_path: list[str]) -> list[str]:
    raw_path: list[str] = []
    for u, v in pairwise(h_path):
        segment = list(scaffold[u][v]["node_path"])
        if segment[0] != u:
            segment.reverse()
        if raw_path and raw_path[-1] == segment[0]:
            raw_path.extend(segment[1:])
        else:
            raw_path.extend(segment)
    return raw_path


def stitch_raw_path_from_corridor(corridor_graph: nx.Graph, h_path: list[str]) -> list[str]:
    raw_path: list[str] = []
    for u, v in pairwise(h_path):
        segment = list(corridor_graph[u][v]["node_path"])
        if segment[0] != u:
            segment.reverse()
        if raw_path and raw_path[-1] == segment[0]:
            raw_path.extend(segment[1:])
        else:
            raw_path.extend(segment)
    return raw_path


def selected_anchor_path_edges(
    corridor_graph: nx.Graph,
    anchor_graph: nx.Graph,
    extra_cycle_edges: int,
) -> tuple[set[str], list[dict[str, Any]], nx.Graph]:
    if anchor_graph.number_of_nodes() == 0:
        return set(), [], nx.Graph()
    if nx.is_connected(anchor_graph):
        selected_graph = nx.minimum_spanning_tree(anchor_graph, weight="weight")
    else:
        selected_graph = nx.Graph()
        for component in nx.connected_components(anchor_graph):
            selected_graph.update(nx.minimum_spanning_tree(anchor_graph.subgraph(component), weight="weight"))

    selected_pairs = {edge_key(u, v) for u, v in selected_graph.edges}
    extra_added = 0
    min_degree = 3 if extra_cycle_edges >= anchor_graph.number_of_nodes() else 2

    for node in anchor_graph.nodes:
        if selected_graph.degree(node) >= min_degree:
            continue
        incident = sorted(
            (
                (float(data["weight"]), node, target)
                for _, target, data in anchor_graph.edges(node, data=True)
                if edge_key(node, target) not in selected_pairs
            ),
            key=lambda item: item[0],
        )
        for _, u, v in incident:
            if selected_graph.degree(node) >= min_degree or extra_added >= extra_cycle_edges:
                break
            selected_graph.add_edge(u, v, **anchor_graph[u][v])
            selected_pairs.add(edge_key(u, v))
            extra_added += 1

    extras: list[tuple[float, str, str]] = []
    for u, v, data in anchor_graph.edges(data=True):
        key = edge_key(u, v)
        if key in selected_pairs:
            continue
        extras.append((float(data["weight"]), u, v))
    extras.sort(key=lambda item: item[0])
    for _, u, v in extras:
        if extra_added >= extra_cycle_edges:
            break
        selected_graph.add_edge(u, v, **anchor_graph[u][v])
        selected_pairs.add(edge_key(u, v))
        extra_added += 1

    final_graph = nx.Graph()
    final_graph.add_nodes_from(anchor_graph.nodes)
    final_edges: list[dict[str, Any]] = []
    for u, v, data in selected_graph.edges(data=True):
        h_path = data["path"]
        raw_path = stitch_raw_path_from_corridor(corridor_graph, h_path)
        distance = float(data["weight"])
        final_edges.append(
            {
                "u": u,
                "v": v,
                "h_node_path": h_path,
                "raw_node_path": raw_path,
                "distance_m": distance,
            }
        )
        final_graph.add_edge(u, v, weight=distance)
    return set(anchor_graph.nodes), final_edges, final_graph


def contract_scaffold(
    scaffold: nx.Graph,
    anchors: set[str],
    node_attrs: dict[str, dict[str, Any]],
) -> tuple[set[str], list[dict[str, Any]], nx.Graph]:
    if scaffold.number_of_nodes() == 0:
        return set(), [], nx.Graph()

    final_nodes = {
        node
        for node in scaffold.nodes
        if node in anchors
        or scaffold.degree(node) != 2
        or is_important_name(node_attrs.get(node, {}).get("node_name", ""))
    }
    visited_edges: set[tuple[str, str]] = set()
    final_edges: list[dict[str, Any]] = []
    final_graph = nx.Graph()
    final_graph.add_nodes_from(final_nodes)

    for start in list(final_nodes):
        for neighbor in list(scaffold.neighbors(start)):
            first_key = edge_key(start, neighbor)
            if first_key in visited_edges:
                continue
            h_path = [start]
            previous = start
            current = neighbor
            aborted = False
            while True:
                key = edge_key(previous, current)
                if key in visited_edges:
                    aborted = True
                    break
                visited_edges.add(key)
                h_path.append(current)
                if current in final_nodes:
                    break
                next_nodes = [candidate for candidate in scaffold.neighbors(current) if candidate != previous]
                if not next_nodes:
                    break
                previous, current = current, next_nodes[0]

            if aborted or len(h_path) < 2 or h_path[0] == h_path[-1]:
                continue
            raw_path = stitch_raw_path(scaffold, h_path)
            distance = path_weight(scaffold, h_path)
            edge = {
                "u": h_path[0],
                "v": h_path[-1],
                "h_node_path": h_path,
                "raw_node_path": raw_path,
                "distance_m": distance,
            }
            final_edges.append(edge)
            final_graph.add_edge(h_path[0], h_path[-1], weight=distance)

    return final_nodes, final_edges, final_graph


def evaluate_candidate(final_graph: nx.Graph) -> dict[str, Any]:
    if final_graph.number_of_nodes() == 0:
        return {
            "nodes": 0,
            "edges": 0,
            "components": 0,
            "cycle_rank": 0,
            "articulation_points": 0,
            "bridges": 0,
            "density": 0.0,
            "avg_degree": 0.0,
        }
    components = nx.number_connected_components(final_graph)
    cycle_rank = final_graph.number_of_edges() - final_graph.number_of_nodes() + components
    articulation_points = list(nx.articulation_points(final_graph))
    bridges = list(nx.bridges(final_graph))
    return {
        "nodes": final_graph.number_of_nodes(),
        "edges": final_graph.number_of_edges(),
        "components": components,
        "cycle_rank": cycle_rank,
        "articulation_points": len(articulation_points),
        "bridges": len(bridges),
        "density": nx.density(final_graph),
        "avg_degree": (
            sum(dict(final_graph.degree()).values()) / final_graph.number_of_nodes()
            if final_graph.number_of_nodes()
            else 0.0
        ),
    }


def candidate_penalty(metrics: dict[str, Any]) -> float:
    nodes = metrics["nodes"]
    range_penalty = 0.0
    if nodes < MIN_TARGET_NODES:
        range_penalty = (MIN_TARGET_NODES - nodes) * 5.0
    elif nodes > MAX_TARGET_NODES:
        range_penalty = (nodes - MAX_TARGET_NODES) * 5.0
    cycle_penalty = max(0, 25 - metrics["cycle_rank"]) * 2.5
    component_penalty = max(0, metrics["components"] - 1) * 1000.0
    return abs(nodes - TARGET_NODES) + range_penalty + cycle_penalty + component_penalty


def choose_backbone(
    corridor_graph: nx.Graph,
    node_attrs: dict[str, dict[str, Any]],
    scores: dict[str, float],
) -> tuple[set[str], list[dict[str, Any]], nx.Graph, dict[str, Any], set[str]]:
    path_cache: dict[tuple[str, str], tuple[float, list[str]]] = {}
    configs: list[tuple[int, int, int]] = []
    preferred_targets = [
        TARGET_NODES,
        max(80, TARGET_NODES - 20),
        min(MAX_TARGET_NODES, TARGET_NODES + 20),
        max(80, TARGET_NODES - 40),
    ]
    for anchor_target in dict.fromkeys(preferred_targets):
        configs.append((anchor_target, 8, int(anchor_target * 2.0)))
        configs.append((anchor_target, 6, int(anchor_target * 1.5)))
        configs.append((anchor_target, 5, int(anchor_target * 1.0)))
        configs.append((anchor_target, 4, int(anchor_target * 0.55)))

    best: tuple[float, set[str], list[dict[str, Any]], nx.Graph, dict[str, Any], set[str]] | None = None
    for anchor_target, neighbor_count, extra_edges in configs:
        log(
            f"Trying backbone config: anchors={anchor_target}, "
            f"neighbor_count={neighbor_count}, extra_cycle_edges={extra_edges}"
        )
        anchors = select_anchors(corridor_graph, node_attrs, scores, anchor_target)
        anchor_graph = build_anchor_graph(
            corridor_graph, anchors, node_attrs, neighbor_count=neighbor_count, cache=path_cache
        )
        final_nodes, final_edges, final_graph = selected_anchor_path_edges(
            corridor_graph, anchor_graph, extra_edges
        )
        metrics = evaluate_candidate(final_graph)
        penalty = candidate_penalty(metrics)
        log(f"  metrics={metrics}, penalty={penalty:,.1f}")
        if best is None or penalty < best[0]:
            best = (penalty, final_nodes, final_edges, final_graph, metrics, anchors)
        if (
            MIN_TARGET_NODES <= metrics["nodes"] <= MAX_TARGET_NODES
            and metrics["components"] == 1
            and metrics["cycle_rank"] >= 25
        ):
            log("  Accepted this config because it satisfies target size and cycle constraints")
            break

    if best is None:
        raise RuntimeError("Could not build a backbone candidate")
    _, final_nodes, final_edges, final_graph, metrics, anchors = best
    log(f"Selected backbone metrics: {metrics}")
    return final_nodes, final_edges, final_graph, metrics, anchors


def orient_coords(
    geometry: Any,
    from_xy: tuple[float, float] | None,
    to_xy: tuple[float, float] | None,
) -> list[tuple[float, float]]:
    if geometry is None or getattr(geometry, "is_empty", True):
        if from_xy and to_xy:
            return [from_xy, to_xy]
        return []
    if geometry.geom_type == "LineString":
        coords = [(float(x), float(y)) for x, y in geometry.coords]
    else:
        coords = []
        for part in geometry.geoms:
            coords.extend((float(x), float(y)) for x, y in part.coords)
    if not coords:
        return []
    if from_xy and to_xy:
        forward = sq_dist(coords[0], from_xy) + sq_dist(coords[-1], to_xy)
        reverse = sq_dist(coords[-1], from_xy) + sq_dist(coords[0], to_xy)
        if reverse < forward:
            coords.reverse()
    return coords


def append_coords(target: list[tuple[float, float]], coords: list[tuple[float, float]]) -> None:
    for coord in coords:
        if target and sq_dist(target[-1], coord) < 1.0e-10:
            continue
        target.append(coord)


def transform_coords(
    coords: list[tuple[float, float]], transformer: Transformer
) -> list[tuple[float, float]]:
    if not coords:
        return []
    xs = [coord[0] for coord in coords]
    ys = [coord[1] for coord in coords]
    lons, lats = transformer.transform(xs, ys)
    return [(float(lon), float(lat)) for lon, lat in zip(lons, lats)]


def collect_directed_path(
    raw_path: list[str],
    directed_best: dict[tuple[str, str], dict[str, Any]],
    raw_graph: nx.Graph,
    node_attrs: dict[str, dict[str, Any]],
    transformer: Transformer,
) -> dict[str, Any] | None:
    link_ids: list[str] = []
    ranks: list[str] = []
    types: list[str] = []
    road_nos: list[str] = []
    road_names: list[str] = []
    original_coords: list[tuple[float, float]] = []
    total = 0.0

    for u, v in pairwise(raw_path):
        attr = directed_best.get((u, v))
        if attr is None:
            return None
        from_attrs = node_attrs.get(u, {})
        to_attrs = node_attrs.get(v, {})
        from_xy = (
            (from_attrs.get("x"), from_attrs.get("y"))
            if from_attrs.get("x") is not None and from_attrs.get("y") is not None
            else None
        )
        to_xy = (
            (to_attrs.get("x"), to_attrs.get("y"))
            if to_attrs.get("x") is not None and to_attrs.get("y") is not None
            else None
        )
        coords = orient_coords(attr.get("geometry"), from_xy, to_xy)
        if not coords and from_xy and to_xy:
            coords = [from_xy, to_xy]
        append_coords(original_coords, coords)
        total += float(attr["length"])
        link_ids.append(attr["link_id"])
        ranks.append(attr["road_rank"])
        types.append(attr["road_type"])
        road_nos.append(attr["road_no"])
        road_names.append(attr["road_name"])

    if len(original_coords) < 2:
        # Fall back to raw node coordinates if a short geometry is absent.
        for node in raw_path:
            attrs = node_attrs.get(node, {})
            if attrs.get("x") is not None and attrs.get("y") is not None:
                append_coords(original_coords, [(float(attrs["x"]), float(attrs["y"]))])
    if len(original_coords) < 2:
        return None

    wgs84_coords = transform_coords(original_coords, transformer)
    rank = representative_rank(ranks)
    return {
        "distance_m": total,
        "road_rank": rank,
        "road_class": road_rank_label(rank),
        "road_type": representative_value(types),
        "road_type_label": road_type_label(representative_value(types)),
        "road_no": join_unique(road_nos),
        "road_name": join_unique(road_names),
        "original_link_ids": link_ids,
        "geometry_coords": wgs84_coords,
        "direction": "observed_link_direction",
    }


def collect_undirected_fallback_path(
    raw_path: list[str],
    raw_graph: nx.Graph,
    node_attrs: dict[str, dict[str, Any]],
    transformer: Transformer,
) -> dict[str, Any] | None:
    link_ids: list[str] = []
    ranks: list[str] = []
    types: list[str] = []
    road_nos: list[str] = []
    road_names: list[str] = []
    original_coords: list[tuple[float, float]] = []
    total = 0.0
    for u, v in pairwise(raw_path):
        data = raw_graph[u][v]
        from_attrs = node_attrs.get(u, {})
        to_attrs = node_attrs.get(v, {})
        if from_attrs.get("x") is not None and from_attrs.get("y") is not None:
            append_coords(original_coords, [(float(from_attrs["x"]), float(from_attrs["y"]))])
        if to_attrs.get("x") is not None and to_attrs.get("y") is not None:
            append_coords(original_coords, [(float(to_attrs["x"]), float(to_attrs["y"]))])
        total += float(data["weight"])
        link_ids.append(clean_code(data.get("best_link_id")))
        ranks.append(clean_code(data.get("road_rank")))
        types.append(clean_code(data.get("road_type")))
        road_nos.append(clean_name(data.get("road_no")))
        road_names.append(clean_name(data.get("road_name")))
    if len(original_coords) < 2:
        return None
    rank = representative_rank(ranks)
    return {
        "distance_m": total,
        "road_rank": rank,
        "road_class": road_rank_label(rank),
        "road_type": representative_value(types),
        "road_type_label": road_type_label(representative_value(types)),
        "road_no": join_unique(road_nos),
        "road_name": join_unique(road_names),
        "original_link_ids": link_ids,
        "geometry_coords": transform_coords(original_coords, transformer),
        "direction": "undirected_geometry_fallback",
    }


def edge_road_summary(raw_graph: nx.Graph, raw_path: list[str]) -> dict[str, str]:
    ranks: list[str] = []
    types: list[str] = []
    road_nos: list[str] = []
    road_names: list[str] = []
    for u, v in pairwise(raw_path):
        data = raw_graph[u][v]
        ranks.append(clean_code(data.get("road_rank")))
        types.append(clean_code(data.get("road_type")))
        road_nos.append(clean_name(data.get("road_no")))
        road_names.append(clean_name(data.get("road_name")))
    rank = representative_rank(ranks)
    return {
        "road_rank": rank,
        "road_class": road_rank_label(rank),
        "road_type": representative_value(types),
        "road_type_label": road_type_label(representative_value(types)),
        "road_no": join_unique(road_nos),
        "road_name": join_unique(road_names),
    }


def write_outputs(
    final_nodes: set[str],
    final_edges: list[dict[str, Any]],
    final_graph: nx.Graph,
    anchors: set[str],
    scores: dict[str, float],
    node_attrs: dict[str, dict[str, Any]],
    raw_graph: nx.Graph,
    directed_best: dict[tuple[str, str], dict[str, Any]],
    transformer: Transformer,
    metrics: dict[str, Any],
    component_sizes: list[int],
    crs_text: str,
) -> None:
    output_dir = ensure_backbone_dir()
    sorted_nodes = sorted(final_nodes, key=lambda node: (-scores.get(node, 0.0), node))
    node_id_map = {node: f"R{idx:03d}" for idx, node in enumerate(sorted_nodes, start=1)}

    incident_ranks: dict[str, list[str]] = defaultdict(list)
    for edge in final_edges:
        summary = edge_road_summary(raw_graph, edge["raw_node_path"])
        incident_ranks[edge["u"]].append(summary["road_rank"])
        incident_ranks[edge["v"]].append(summary["road_rank"])

    node_rows: list[dict[str, Any]] = []
    node_features: list[dict[str, Any]] = []
    for node in sorted_nodes:
        attrs = node_attrs[node]
        degree = final_graph.degree(node)
        rank = representative_rank(incident_ranks.get(node, []))
        row = {
            "node_id": node_id_map[node],
            "original_node_id": node,
            "latitude": attrs.get("latitude"),
            "longitude": attrs.get("longitude"),
            "x": attrs.get("x"),
            "y": attrs.get("y"),
            "degree": degree,
            "node_role": node_role_from_attrs(
                attrs.get("node_type", ""), attrs.get("node_name", ""), node in anchors, degree
            ),
            "road_rank": rank,
            "road_class": road_rank_label(rank),
            "importance_score": round(float(scores.get(node, 0.0)), 6),
            "node_type": attrs.get("node_type", ""),
            "node_name": attrs.get("node_name", ""),
            "turn_p": attrs.get("turn_p", ""),
        }
        node_rows.append(row)
        if row["longitude"] is not None and row["latitude"] is not None:
            node_features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [row["longitude"], row["latitude"]],
                    },
                    "properties": {key: value for key, value in row.items() if key not in {"latitude", "longitude"}},
                }
            )

    edge_rows: list[dict[str, Any]] = []
    edge_features: list[dict[str, Any]] = []
    edge_index = 1
    for undirected_index, edge in enumerate(final_edges, start=1):
        raw_path = edge["raw_node_path"]
        directions = [
            raw_path,
            list(reversed(raw_path)),
        ]
        emitted = 0
        for directed_path in directions:
            collected = collect_directed_path(directed_path, directed_best, raw_graph, node_attrs, transformer)
            if collected is None:
                collected = collect_undirected_fallback_path(directed_path, raw_graph, node_attrs, transformer)
            if collected is None:
                continue
            row = {
                "edge_id": f"E{edge_index:04d}",
                "undirected_edge_id": f"UE{undirected_index:04d}",
                "from_node": node_id_map[directed_path[0]],
                "to_node": node_id_map[directed_path[-1]],
                "from_original_node": directed_path[0],
                "to_original_node": directed_path[-1],
                "distance_m": round(collected["distance_m"], 3),
                "distance_km": round(collected["distance_m"] / 1000.0, 6),
                "road_rank": collected["road_rank"],
                "road_class": collected["road_class"],
                "road_type": collected["road_type"],
                "road_type_label": collected["road_type_label"],
                "road_no": collected["road_no"],
                "road_name": collected["road_name"],
                "direction": collected["direction"],
                "original_link_count": len(collected["original_link_ids"]),
                "original_link_ids": ";".join(collected["original_link_ids"]),
                "original_node_count": len(directed_path),
                "original_node_path": ";".join(directed_path),
            }
            edge_rows.append(row)
            if len(collected["geometry_coords"]) >= 2:
                edge_features.append(
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [
                                [float(lon), float(lat)] for lon, lat in collected["geometry_coords"]
                            ],
                        },
                        "properties": row,
                    }
                )
            edge_index += 1
            emitted += 1

        if emitted == 0:
            collected = collect_undirected_fallback_path(raw_path, raw_graph, node_attrs, transformer)
            if collected is None:
                continue
            row = {
                "edge_id": f"E{edge_index:04d}",
                "undirected_edge_id": f"UE{undirected_index:04d}",
                "from_node": node_id_map[raw_path[0]],
                "to_node": node_id_map[raw_path[-1]],
                "from_original_node": raw_path[0],
                "to_original_node": raw_path[-1],
                "distance_m": round(collected["distance_m"], 3),
                "distance_km": round(collected["distance_m"] / 1000.0, 6),
                "road_rank": collected["road_rank"],
                "road_class": collected["road_class"],
                "road_type": collected["road_type"],
                "road_type_label": collected["road_type_label"],
                "road_no": collected["road_no"],
                "road_name": collected["road_name"],
                "direction": collected["direction"],
                "original_link_count": len(collected["original_link_ids"]),
                "original_link_ids": ";".join(collected["original_link_ids"]),
                "original_node_count": len(raw_path),
                "original_node_path": ";".join(raw_path),
            }
            edge_rows.append(row)
            edge_features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[float(lon), float(lat)] for lon, lat in collected["geometry_coords"]],
                    },
                    "properties": row,
                }
            )
            edge_index += 1

    nodes_csv = output_dir / "backbone_nodes.csv"
    edges_csv = output_dir / "backbone_edges.csv"
    nodes_geojson = output_dir / "backbone_nodes.geojson"
    edges_geojson = output_dir / "backbone_edges.geojson"
    report_path = output_dir / "backbone_build_report.json"

    pd.DataFrame(node_rows).to_csv(nodes_csv, index=False, encoding="utf-8-sig")
    pd.DataFrame(edge_rows).to_csv(edges_csv, index=False, encoding="utf-8-sig")
    nodes_geojson.write_text(
        json.dumps({"type": "FeatureCollection", "features": node_features}, ensure_ascii=False),
        encoding="utf-8",
    )
    edges_geojson.write_text(
        json.dumps({"type": "FeatureCollection", "features": edge_features}, ensure_ascii=False),
        encoding="utf-8",
    )
    report_path.write_text(
        json.dumps(
            {
                "target_nodes": TARGET_NODES,
                "accepted_node_range": [MIN_TARGET_NODES, MAX_TARGET_NODES],
                "candidate_road_ranks": {
                    code: ROAD_RANK_LABELS.get(code, code) for code in CANDIDATE_ROAD_RANKS
                },
                "road_type_labels": ROAD_TYPE_LABELS,
                "source_crs": crs_text,
                "largest_component_sizes": component_sizes[:20],
                "metrics": metrics,
                "directed_edge_rows": len(edge_rows),
                "undirected_edge_rows": len(final_edges),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    log(f"Wrote {nodes_csv}")
    log(f"Wrote {edges_csv}")
    log(f"Wrote {nodes_geojson}")
    log(f"Wrote {edges_geojson}")
    log(f"Wrote {report_path}")


def main() -> None:
    ensure_backbone_dir()
    links = load_candidate_links()
    raw_graph, pair_store, directed_best = build_raw_graph(links)
    del links
    raw_graph, component_nodes, component_sizes = keep_largest_component(raw_graph)
    node_attrs, transformer, crs_text = load_node_attributes(component_nodes)
    core_nodes = determine_corridor_core_nodes(raw_graph, node_attrs)
    corridor_graph = contract_to_corridor_graph(raw_graph, core_nodes)
    centrality = approximate_centrality(corridor_graph)
    scores = score_corridor_nodes(corridor_graph, node_attrs, centrality)
    final_nodes, final_edges, final_graph, metrics, anchors = choose_backbone(
        corridor_graph, node_attrs, scores
    )
    write_outputs(
        final_nodes=final_nodes,
        final_edges=final_edges,
        final_graph=final_graph,
        anchors=anchors,
        scores=scores,
        node_attrs=node_attrs,
        raw_graph=raw_graph,
        directed_best=directed_best,
        transformer=transformer,
        metrics=metrics,
        component_sizes=component_sizes,
        crs_text=crs_text,
    )
    log("Done")
    # pair_store is intentionally retained until the end while debugging memory-sensitive runs.
    _ = pair_store


if __name__ == "__main__":
    main()
