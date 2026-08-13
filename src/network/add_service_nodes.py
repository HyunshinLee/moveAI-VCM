from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import pyogrio
from pyproj import Transformer

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from src.utils.config import (
    BACKBONE_DIR,
    FIGURES_DIR,
    INSTANCE_ROOT,
    LINK_FILE,
    OUTPUT_DIR,
    PHYSICAL_DIR,
    clean_name,
    ensure_project_dirs,
)


BACKBONE_NODES_CSV = BACKBONE_DIR / "backbone_nodes.csv"
BACKBONE_EDGES_CSV = BACKBONE_DIR / "backbone_edges.csv"
BACKBONE_EDGES_GEOJSON = BACKBONE_DIR / "backbone_edges.geojson"

DEPOTS_CSV = PHYSICAL_DIR / "depots.csv"
CUSTOMERS_CSV = PHYSICAL_DIR / "customers.csv"
INSTANCE_DEPOTS_CSV = INSTANCE_ROOT / "instance_01" / "depots.csv"
INSTANCE_CUSTOMERS_CSV = INSTANCE_ROOT / "instance_01" / "customers.csv"
PHYSICAL_NODES_CSV = PHYSICAL_DIR / "physical_nodes.csv"
PHYSICAL_EDGES_CSV = PHYSICAL_DIR / "physical_edges.csv"
PHYSICAL_NODES_GEOJSON = PHYSICAL_DIR / "physical_nodes.geojson"
PHYSICAL_EDGES_GEOJSON = PHYSICAL_DIR / "physical_edges.geojson"
PHYSICAL_REPORT_JSON = PHYSICAL_DIR / "physical_layer_report.json"
PHYSICAL_PNG = FIGURES_DIR / "physical_layer.png"
KOREA_BOUNDARY_GEOJSON = OUTPUT_DIR / "korea_boundary" / "south_korea_boundary.geojson"

CUSTOMER_COUNT = 50
CONNECTOR_K = 3
CONNECTOR_DETOUR_FACTOR = 1.25


@dataclass(frozen=True)
class DepotSpec:
    depot_id: str
    name: str
    address: str
    region_role: str
    road_name: str
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float


DEPOT_SPECS = [
    DepotSpec(
        "D01",
        "인천 산업재 물류센터",
        "인천 동구 방축로9번길 29",
        "수도권 Depot",
        "방축로9번길",
        126.63,
        126.67,
        37.47,
        37.51,
    ),
    DepotSpec(
        "D02",
        "당진 산업재 물류센터",
        "충남 당진시 송산면 가곡로 21",
        "충청권 Depot",
        "가곡로",
        126.65,
        126.85,
        36.90,
        37.10,
    ),
    DepotSpec(
        "D03",
        "포항 산업재 물류센터",
        "경북 포항시 남구 오천읍 송덕로212번길 45",
        "경북권 Depot",
        "송덕로212번길",
        129.35,
        129.41,
        35.93,
        35.97,
    ),
    DepotSpec(
        "D04",
        "울산 산업재 물류센터",
        "울산 북구 무룡1로 94",
        "울산·경남권 Depot",
        "무룡1로",
        129.35,
        129.38,
        35.56,
        35.59,
    ),
    DepotSpec(
        "D05",
        "광양 산업재 물류센터",
        "전남 광양시 광양읍 인덕로 360-156",
        "전남권 Depot",
        "인덕로",
        127.55,
        127.61,
        34.88,
        35.01,
    ),
]


def log(message: str) -> None:
    print(f"[physical_layer] {message}", flush=True)


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    )
    return 2.0 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def nearest_backbone_nodes(
    lon: float,
    lat: float,
    backbone_nodes: pd.DataFrame,
    k: int = CONNECTOR_K,
) -> list[dict[str, Any]]:
    distances = []
    for row in backbone_nodes.itertuples(index=False):
        distance_km = haversine_km(lon, lat, float(row.longitude), float(row.latitude))
        distances.append((distance_km, row.node_id, float(row.longitude), float(row.latitude)))
    distances.sort(key=lambda item: (item[0], item[1]))
    return [
        {
            "backbone_node": node_id,
            "backbone_longitude": node_lon,
            "backbone_latitude": node_lat,
            "straight_distance_km": distance_km,
            "connector_distance_km": distance_km * CONNECTOR_DETOUR_FACTOR,
        }
        for distance_km, node_id, node_lon, node_lat in distances[:k]
    ]


def derive_depot_coordinates_from_its_links() -> pd.DataFrame:
    log("Deriving depot access coordinates from MOCT_LINK road-name geometry clusters")
    links = pyogrio.read_dataframe(
        LINK_FILE,
        columns=["LINK_ID", "ROAD_NAME", "ROAD_RANK", "LENGTH"],
    )
    links["ROAD_NAME"] = links["ROAD_NAME"].map(clean_name)
    links["LINK_ID"] = links["LINK_ID"].astype(str).str.strip().str.strip("'").str.strip('"')
    links["LENGTH"] = pd.to_numeric(links["LENGTH"], errors="coerce").fillna(0.0)
    transformer = Transformer.from_crs(links.crs, "EPSG:4326", always_xy=True)

    depot_rows = []
    for spec in DEPOT_SPECS:
        road_links = links[links["ROAD_NAME"].eq(spec.road_name)].copy()
        matched = []
        for row in road_links.itertuples(index=False):
            centroid = row.geometry.centroid
            lon, lat = transformer.transform(centroid.x, centroid.y)
            if spec.lon_min <= lon <= spec.lon_max and spec.lat_min <= lat <= spec.lat_max:
                matched.append(
                    {
                        "link_id": row.LINK_ID,
                        "x": centroid.x,
                        "y": centroid.y,
                        "longitude": float(lon),
                        "latitude": float(lat),
                        "length": float(row.LENGTH) if row.LENGTH else float(row.geometry.length),
                    }
                )

        if not matched:
            raise RuntimeError(f"No MOCT_LINK road-name match found for {spec.depot_id}: {spec.address}")

        total_weight = sum(max(item["length"], 1.0) for item in matched)
        lon = sum(item["longitude"] * max(item["length"], 1.0) for item in matched) / total_weight
        lat = sum(item["latitude"] * max(item["length"], 1.0) for item in matched) / total_weight
        x = sum(item["x"] * max(item["length"], 1.0) for item in matched) / total_weight
        y = sum(item["y"] * max(item["length"], 1.0) for item in matched) / total_weight
        depot_rows.append(
            {
                "depot_id": spec.depot_id,
                "node_id": spec.depot_id,
                "node_type": "DEPOT",
                "name": spec.name,
                "address": spec.address,
                "region_role": spec.region_role,
                "latitude": lat,
                "longitude": lon,
                "x": x,
                "y": y,
                "coordinate_method": "MOCT_LINK road-name cluster length-weighted centroid",
                "matched_road_name": spec.road_name,
                "matched_link_count": len(matched),
                "matched_link_ids_sample": ";".join(item["link_id"] for item in matched[:30]),
            }
        )
        log(
            f"  {spec.depot_id} {spec.name}: {lat:.6f}, {lon:.6f} "
            f"from {len(matched)} '{spec.road_name}' links"
        )
    return pd.DataFrame(depot_rows)


def projected_xy(lon: float, lat: float, mean_lat: float) -> tuple[float, float]:
    return lon * 111.320 * math.cos(math.radians(mean_lat)), lat * 110.574


def select_customer_anchor_nodes(backbone_nodes: pd.DataFrame, count: int = CUSTOMER_COUNT) -> list[str]:
    nodes = backbone_nodes.dropna(subset=["longitude", "latitude"]).copy()
    mean_lat = float(nodes["latitude"].mean())
    coords = {
        row.node_id: projected_xy(float(row.longitude), float(row.latitude), mean_lat)
        for row in nodes.itertuples(index=False)
    }
    importance = {
        row.node_id: float(getattr(row, "importance_score", 0.0))
        for row in nodes.itertuples(index=False)
    }
    max_importance = max(importance.values()) if importance else 1.0

    seed_nodes = [
        nodes.sort_values("longitude").iloc[0].node_id,
        nodes.sort_values("longitude").iloc[-1].node_id,
        nodes.sort_values("latitude").iloc[0].node_id,
        nodes.sort_values("latitude").iloc[-1].node_id,
        nodes.sort_values("importance_score", ascending=False).iloc[0].node_id,
    ]
    selected: list[str] = []
    selected_set: set[str] = set()
    for node_id in seed_nodes:
        if node_id not in selected_set:
            selected.append(node_id)
            selected_set.add(node_id)

    while len(selected) < count:
        best_node = None
        best_score = -1.0
        for node_id, coord in coords.items():
            if node_id in selected_set:
                continue
            min_dist = min(
                math.hypot(coord[0] - coords[chosen][0], coord[1] - coords[chosen][1])
                for chosen in selected
            )
            importance_bonus = 12.0 * (importance.get(node_id, 0.0) / max_importance)
            score = min_dist + importance_bonus
            if score > best_score:
                best_score = score
                best_node = node_id
        if best_node is None:
            break
        selected.append(best_node)
        selected_set.add(best_node)

    return selected


def generate_customers(backbone_nodes: pd.DataFrame) -> pd.DataFrame:
    log(f"Generating {CUSTOMER_COUNT} synthetic customers by spatial maximin sampling")
    selected_nodes = select_customer_anchor_nodes(backbone_nodes, CUSTOMER_COUNT)
    node_lookup = backbone_nodes.set_index("node_id").to_dict(orient="index")
    min_lon = float(backbone_nodes["longitude"].min()) - 0.02
    max_lon = float(backbone_nodes["longitude"].max()) + 0.02
    min_lat = float(backbone_nodes["latitude"].min()) - 0.02
    max_lat = float(backbone_nodes["latitude"].max()) + 0.02
    rows = []
    for idx, anchor_id in enumerate(selected_nodes, start=1):
        anchor = node_lookup[anchor_id]
        base_lon = float(anchor["longitude"])
        base_lat = float(anchor["latitude"])
        radius_km = 0.6 + ((idx * 7) % 7) * 0.25
        angle = math.radians((idx * 137.508) % 360.0)
        lat_offset = (radius_km * math.sin(angle)) / 110.574
        lon_offset = (radius_km * math.cos(angle)) / (111.320 * math.cos(math.radians(base_lat)))
        lat = base_lat + lat_offset
        lon = base_lon + lon_offset
        if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
            lat = base_lat - lat_offset
            lon = base_lon - lon_offset
        if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
            lat = base_lat
            lon = base_lon
        rows.append(
            {
                "customer_id": f"C{idx:03d}",
                "node_id": f"C{idx:03d}",
                "node_type": "CUSTOMER",
                "name": f"Synthetic Customer {idx:03d}",
                "latitude": lat,
                "longitude": lon,
                "anchor_backbone_node": anchor_id,
                "generation_method": "maximin spatial sampling from backbone nodes with deterministic local offset",
                "demand_ton": 4 + ((idx * 7) % 17),
                "service_time_min": 25 + ((idx * 5) % 4) * 10,
                "time_window_start": ["08:00", "09:00", "10:00", "13:00"][idx % 4],
                "time_window_end": ["12:00", "15:00", "17:00", "18:00"][idx % 4],
            }
        )
    customers = pd.DataFrame(rows)
    log(
        "Customer coordinate range: "
        f"lat {customers.latitude.min():.3f}-{customers.latitude.max():.3f}, "
        f"lon {customers.longitude.min():.3f}-{customers.longitude.max():.3f}"
    )
    return customers


def enrich_external_nodes_with_connectors(
    external_nodes: pd.DataFrame,
    backbone_nodes: pd.DataFrame,
    id_column: str,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    enriched_rows = []
    connector_edges = []
    for row in external_nodes.itertuples(index=False):
        node_id = getattr(row, "node_id")
        lon = float(getattr(row, "longitude"))
        lat = float(getattr(row, "latitude"))
        nearest = nearest_backbone_nodes(lon, lat, backbone_nodes, CONNECTOR_K)
        enriched = row._asdict()
        enriched["nearest_backbone_node"] = nearest[0]["backbone_node"]
        enriched["nearest_backbone_distance_km"] = round(nearest[0]["connector_distance_km"], 6)
        enriched["connector_backbone_nodes"] = ";".join(item["backbone_node"] for item in nearest)
        enriched_rows.append(enriched)

        for rank, item in enumerate(nearest, start=1):
            distance_km = item["connector_distance_km"]
            for direction, source, target in [
                ("access_to_backbone", node_id, item["backbone_node"]),
                ("backbone_to_access", item["backbone_node"], node_id),
            ]:
                connector_edges.append(
                    {
                        "from_node": source,
                        "to_node": target,
                        "edge_type": "CONNECTOR",
                        "access_node_type": getattr(row, "node_type"),
                        "connector_rank": rank,
                        "distance_m": round(distance_km * 1000.0, 3),
                        "distance_km": round(distance_km, 6),
                        "road_rank": "CONNECTOR",
                        "road_class": "local access connector",
                        "road_type": "",
                        "road_type_label": "",
                        "road_no": "",
                        "road_name": "",
                        "direction": direction,
                        "original_link_count": 0,
                        "original_link_ids": "",
                        "original_node_count": 0,
                        "original_node_path": "",
                        "geometry_coords": [
                            [lon, lat],
                            [item["backbone_longitude"], item["backbone_latitude"]],
                        ]
                        if direction == "access_to_backbone"
                        else [
                            [item["backbone_longitude"], item["backbone_latitude"]],
                            [lon, lat],
                        ],
                    }
                )
    return pd.DataFrame(enriched_rows), connector_edges


def read_backbone_edge_geometries() -> dict[str, list[list[float]]]:
    edge_geojson = json.loads(BACKBONE_EDGES_GEOJSON.read_text(encoding="utf-8"))
    return {
        feature["properties"]["edge_id"]: feature["geometry"]["coordinates"]
        for feature in edge_geojson["features"]
    }


def build_physical_edges(
    backbone_edges: pd.DataFrame,
    connector_edges: list[dict[str, Any]],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    road_geometries = read_backbone_edge_geometries()
    rows = []
    features = []

    for idx, row in enumerate(backbone_edges.itertuples(index=False), start=1):
        row_dict = row._asdict()
        edge_id = f"PE{idx:05d}"
        physical_row = {
            "edge_id": edge_id,
            "source_edge_id": row_dict.get("edge_id"),
            "from_node": row_dict["from_node"],
            "to_node": row_dict["to_node"],
            "edge_type": "ROAD",
            "connector_rank": "",
            "distance_m": row_dict["distance_m"],
            "distance_km": row_dict["distance_km"],
            "road_rank": row_dict.get("road_rank", ""),
            "road_class": row_dict.get("road_class", ""),
            "road_type": row_dict.get("road_type", ""),
            "road_type_label": row_dict.get("road_type_label", ""),
            "road_no": row_dict.get("road_no", ""),
            "road_name": row_dict.get("road_name", ""),
            "direction": row_dict.get("direction", ""),
            "original_link_count": row_dict.get("original_link_count", ""),
            "original_link_ids": row_dict.get("original_link_ids", ""),
            "original_node_count": row_dict.get("original_node_count", ""),
            "original_node_path": row_dict.get("original_node_path", ""),
        }
        rows.append(physical_row)
        coords = road_geometries.get(row_dict.get("edge_id"))
        if coords:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords},
                    "properties": physical_row,
                }
            )

    offset = len(rows)
    for local_idx, connector in enumerate(connector_edges, start=1):
        edge_id = f"PE{offset + local_idx:05d}"
        geometry_coords = connector.pop("geometry_coords")
        physical_row = {"edge_id": edge_id, "source_edge_id": "", **connector}
        rows.append(physical_row)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": geometry_coords},
                "properties": physical_row,
            }
        )

    return pd.DataFrame(rows), {"type": "FeatureCollection", "features": features}


def build_physical_nodes(
    backbone_nodes: pd.DataFrame,
    depots: pd.DataFrame,
    customers: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    road_rows = []
    for row in backbone_nodes.itertuples(index=False):
        road_rows.append(
            {
                "node_id": row.node_id,
                "node_type": "ROAD",
                "name": getattr(row, "node_name", ""),
                "latitude": row.latitude,
                "longitude": row.longitude,
                "x": getattr(row, "x", ""),
                "y": getattr(row, "y", ""),
                "original_node_id": getattr(row, "original_node_id", ""),
                "role": getattr(row, "node_role", ""),
                "nearest_backbone_node": row.node_id,
                "nearest_backbone_distance_km": 0.0,
                "connector_backbone_nodes": row.node_id,
                "demand": "",
                "tw_start": "",
                "tw_end": "",
                "service_time": "",
            }
        )

    depot_rows = []
    for row in depots.itertuples(index=False):
        depot_rows.append(
            {
                "node_id": row.node_id,
                "node_type": "DEPOT",
                "name": row.name,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "x": getattr(row, "x", ""),
                "y": getattr(row, "y", ""),
                "original_node_id": "",
                "role": row.region_role,
                "nearest_backbone_node": row.nearest_backbone_node,
                "nearest_backbone_distance_km": row.nearest_backbone_distance_km,
                "connector_backbone_nodes": row.connector_backbone_nodes,
                "demand": "",
                "tw_start": "",
                "tw_end": "",
                "service_time": 0,
            }
        )

    customer_rows = []
    for row in customers.itertuples(index=False):
        customer_rows.append(
            {
                "node_id": row.node_id,
                "node_type": "CUSTOMER",
                "name": row.name,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "x": "",
                "y": "",
                "original_node_id": "",
                "role": "synthetic_customer",
                "nearest_backbone_node": row.nearest_backbone_node,
                "nearest_backbone_distance_km": row.nearest_backbone_distance_km,
                "connector_backbone_nodes": row.connector_backbone_nodes,
                "demand": getattr(row, "demand_ton", ""),
                "tw_start": getattr(row, "time_window_start", ""),
                "tw_end": getattr(row, "time_window_end", ""),
                "service_time": getattr(row, "service_time_min", ""),
            }
        )

    physical_nodes = pd.DataFrame(road_rows + depot_rows + customer_rows)
    features = []
    for row in physical_nodes.itertuples(index=False):
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row.longitude), float(row.latitude)],
                },
                "properties": row._asdict(),
            }
        )
    return physical_nodes, {"type": "FeatureCollection", "features": features}


def validate_physical_layer(nodes: pd.DataFrame, edges: pd.DataFrame) -> dict[str, Any]:
    directed = nx.DiGraph()
    for row in nodes.itertuples(index=False):
        directed.add_node(row.node_id, node_type=row.node_type)
    for row in edges.itertuples(index=False):
        directed.add_edge(row.from_node, row.to_node, distance_m=float(row.distance_m))

    depots = nodes[nodes["node_type"].eq("DEPOT")]["node_id"].tolist()
    customers = nodes[nodes["node_type"].eq("CUSTOMER")]["node_id"].tolist()
    reachable = 0
    total = len(depots) * len(customers)
    sample_paths = []
    for depot in depots:
        lengths = nx.single_source_dijkstra_path_length(directed, depot, weight="distance_m")
        for customer in customers:
            if customer in lengths:
                reachable += 1
        closest = sorted(
            ((lengths.get(customer, math.inf), customer) for customer in customers),
            key=lambda item: item[0],
        )[:5]
        sample_paths.append(
            {
                "depot": depot,
                "nearest_customers": [
                    {"customer": customer, "distance_km": round(distance / 1000.0, 3)}
                    for distance, customer in closest
                    if math.isfinite(distance)
                ],
            }
        )

    return {
        "nodes": directed.number_of_nodes(),
        "edges": directed.number_of_edges(),
        "road_backbone_nodes": int(nodes["node_type"].eq("ROAD").sum()),
        "depots": len(depots),
        "customers": len(customers),
        "weakly_connected_components": nx.number_weakly_connected_components(directed),
        "strongly_connected_components": nx.number_strongly_connected_components(directed),
        "depot_customer_pairs": total,
        "reachable_depot_customer_pairs": reachable,
        "all_depot_customer_pairs_reachable": reachable == total,
        "connector_k": CONNECTOR_K,
        "connector_detour_factor": CONNECTOR_DETOUR_FACTOR,
        "sample_nearest_customers_by_depot": sample_paths,
    }


def write_visualization(
    physical_nodes: pd.DataFrame,
    physical_edges_geojson: dict[str, Any],
) -> None:
    fig, ax = plt.subplots(figsize=(9, 11), dpi=220)

    if KOREA_BOUNDARY_GEOJSON.exists():
        try:
            import geopandas as gpd

            boundary = gpd.read_file(KOREA_BOUNDARY_GEOJSON)
            boundary.plot(
                ax=ax,
                facecolor="#f8fafc",
                edgecolor="#475569",
                linewidth=1.15,
                alpha=0.34,
                zorder=-4,
            )
            boundary.boundary.plot(ax=ax, color="#334155", linewidth=1.05, zorder=-3)
        except Exception as exc:
            log(f"Could not plot Korea boundary overlay: {exc}")

    for feature in physical_edges_geojson["features"]:
        props = feature["properties"]
        coords = feature["geometry"]["coordinates"]
        xs = [coord[0] for coord in coords]
        ys = [coord[1] for coord in coords]
        if props["edge_type"] == "ROAD":
            color = {
                "101": "#dc2626",
                "102": "#fb923c",
                "103": "#2563eb",
                "105": "#38bdf8",
                "106": "#16a34a",
            }.get(str(props.get("road_rank", "")), "#64748b")
            ax.plot(xs, ys, color=color, linewidth=0.55, alpha=0.38, zorder=1)
        elif str(props["direction"]) == "access_to_backbone":
            rank = int(float(props.get("connector_rank") or 1))
            if props.get("access_node_type") == "DEPOT":
                color = "#7c2d12"
                linewidth = 1.0 if rank == 1 else 0.62
                alpha = 0.76 if rank == 1 else 0.34
            else:
                color = "#111827"
                linewidth = 0.58 if rank == 1 else 0.38
                alpha = 0.44 if rank == 1 else 0.22
            linestyle = "-" if rank == 1 else ":"
            ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha, linestyle=linestyle, zorder=2)

    roads = physical_nodes[physical_nodes["node_type"].eq("ROAD")]
    customers = physical_nodes[physical_nodes["node_type"].eq("CUSTOMER")]
    depots = physical_nodes[physical_nodes["node_type"].eq("DEPOT")]

    ax.scatter(
        roads["longitude"],
        roads["latitude"],
        s=4,
        color="#334155",
        alpha=0.55,
        linewidth=0,
        zorder=2,
        label="Backbone node",
    )
    ax.scatter(
        customers["longitude"],
        customers["latitude"],
        s=19,
        color="#020617",
        edgecolor="white",
        linewidth=0.35,
        alpha=0.92,
        zorder=4,
        label="Customer",
    )
    ax.scatter(
        depots["longitude"],
        depots["latitude"],
        s=72,
        marker="s",
        color="#7c2d12",
        edgecolor="white",
        linewidth=0.7,
        zorder=5,
        label="Depot",
    )
    for row in depots.itertuples(index=False):
        ax.annotate(
            row.node_id,
            (row.longitude, row.latitude),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7,
            color="#111827",
            zorder=6,
        )

    ax.set_title("Physical Layer: Road Backbone + Depots + Synthetic Customers", fontsize=12, pad=10)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, linewidth=0.3, color="#d1d5db", alpha=0.65)
    ax.legend(loc="lower right", frameon=True, fontsize=7)
    min_lon = float(physical_nodes["longitude"].min())
    max_lon = float(physical_nodes["longitude"].max())
    min_lat = float(physical_nodes["latitude"].min())
    max_lat = float(physical_nodes["latitude"].max())
    ax.set_xlim(min_lon - 0.18, max_lon + 0.18)
    ax.set_ylim(min_lat - 0.14, max_lat + 0.14)
    fig.tight_layout()
    fig.savefig(PHYSICAL_PNG)
    plt.close(fig)
    log(f"Wrote {PHYSICAL_PNG}")


def main() -> None:
    ensure_project_dirs()
    backbone_nodes = pd.read_csv(
        BACKBONE_NODES_CSV,
        dtype={
            "node_id": str,
            "original_node_id": str,
            "node_role": str,
            "road_rank": str,
            "road_class": str,
            "node_type": str,
            "node_name": str,
            "turn_p": str,
        },
    ).fillna("")
    for column in ["latitude", "longitude", "x", "y", "degree", "importance_score"]:
        backbone_nodes[column] = pd.to_numeric(backbone_nodes[column], errors="coerce")

    backbone_edges = pd.read_csv(BACKBONE_EDGES_CSV, dtype=str).fillna("")
    for column in ["distance_m", "distance_km", "original_link_count", "original_node_count"]:
        backbone_edges[column] = pd.to_numeric(backbone_edges[column], errors="coerce").fillna(0.0)

    depots = derive_depot_coordinates_from_its_links()
    customers = generate_customers(backbone_nodes)
    depots, depot_connectors = enrich_external_nodes_with_connectors(
        depots, backbone_nodes, "depot_id"
    )
    customers, customer_connectors = enrich_external_nodes_with_connectors(
        customers, backbone_nodes, "customer_id"
    )

    physical_nodes, physical_nodes_geojson = build_physical_nodes(backbone_nodes, depots, customers)
    physical_edges, physical_edges_geojson = build_physical_edges(
        backbone_edges, depot_connectors + customer_connectors
    )
    validation = validate_physical_layer(physical_nodes, physical_edges)

    depots.to_csv(DEPOTS_CSV, index=False, encoding="utf-8-sig")
    customers.to_csv(CUSTOMERS_CSV, index=False, encoding="utf-8-sig")
    depots.to_csv(INSTANCE_DEPOTS_CSV, index=False, encoding="utf-8-sig")
    customers.to_csv(INSTANCE_CUSTOMERS_CSV, index=False, encoding="utf-8-sig")
    physical_nodes.to_csv(PHYSICAL_NODES_CSV, index=False, encoding="utf-8-sig")
    physical_edges.to_csv(PHYSICAL_EDGES_CSV, index=False, encoding="utf-8-sig")
    PHYSICAL_NODES_GEOJSON.write_text(
        json.dumps(physical_nodes_geojson, ensure_ascii=False),
        encoding="utf-8",
    )
    PHYSICAL_EDGES_GEOJSON.write_text(
        json.dumps(physical_edges_geojson, ensure_ascii=False),
        encoding="utf-8",
    )
    PHYSICAL_REPORT_JSON.write_text(
        json.dumps(
            {
                "description": "Physical layer with 200 road backbone nodes, 5 depot nodes, and 50 synthetic customer nodes.",
                "depot_coordinate_method": "Depot coordinates are derived from the MOCT_LINK geometry cluster matching each depot road name inside a depot-specific bounding box. This gives a road-access coordinate when address-level geocoding is unavailable.",
                "customer_generation_method": "Spatial maximin sampling from backbone nodes with deterministic local offsets; no random sampling.",
                "connector_method": f"Each depot/customer is connected bidirectionally to its {CONNECTOR_K} nearest backbone nodes using haversine distance times {CONNECTOR_DETOUR_FACTOR}.",
                "validation": validation,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    write_visualization(physical_nodes, physical_edges_geojson)

    log(f"Wrote {DEPOTS_CSV}")
    log(f"Wrote {CUSTOMERS_CSV}")
    log(f"Wrote {INSTANCE_DEPOTS_CSV}")
    log(f"Wrote {INSTANCE_CUSTOMERS_CSV}")
    log(f"Wrote {PHYSICAL_NODES_CSV}")
    log(f"Wrote {PHYSICAL_EDGES_CSV}")
    log(f"Wrote {PHYSICAL_NODES_GEOJSON}")
    log(f"Wrote {PHYSICAL_EDGES_GEOJSON}")
    log(f"Wrote {PHYSICAL_REPORT_JSON}")
    log(f"Validation: {validation}")


if __name__ == "__main__":
    main()
