from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any

from .models import Edge, Graph, Node, RoutePlan, Stop, VehicleState


def load_physical_graph(directory: str | Path) -> Graph:
    """Load the team's compressed standard-node-link backbone CSV files."""
    directory = Path(directory)
    nodes: dict[str, Node] = {}
    with (directory / "physical_nodes.csv").open(encoding="utf-8-sig", newline="") as file:
        for item in csv.DictReader(file):
            node_type = item["node_type"]
            kind = {
                "road_backbone": "waypoint",
                "depot": "depot",
                "customer": "customer",
            }.get(node_type, node_type)
            nodes[item["node_id"]] = Node(
                id=item["node_id"], lat=float(item["latitude"]),
                lon=float(item["longitude"]), kind=kind,
            )
    edges: dict[tuple[str, str], Edge] = {}
    with (directory / "physical_edges.csv").open(encoding="utf-8-sig", newline="") as file:
        for item in csv.DictReader(file):
            road_class = item["road_class"]
            default_speed = 100.0 if road_class == "고속국도/고속도로" else 70.0
            if item["edge_type"] != "road_backbone":
                default_speed = 30.0
            edge = Edge(
                source=item["from_node"], target=item["to_node"],
                distance_m=float(item["distance_m"]),
                base_speed_kph=default_speed,
                metadata={
                    "physical_edge_id": item["physical_edge_id"],
                    "source_edge_id": item["source_edge_id"],
                    "edge_type": item["edge_type"],
                    "road_class": road_class,
                    "road_no": item["road_no"],
                    "road_name": item["road_name"],
                    "base_speed_source": "road_class_default",
                    "original_link_ids": [
                        value for value in item["original_link_ids"].split(";") if value
                    ],
                },
            )
            edges[edge.key] = edge
    return Graph(nodes=nodes, edges=edges)


def load_graph(path: str | Path) -> Graph:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    nodes = {
        item["id"]: Node(
            id=item["id"], lat=float(item["lat"]), lon=float(item["lon"]),
            kind=item.get("kind", "waypoint"),
        )
        for item in raw["nodes"]
    }
    edges: dict[tuple[str, str], Edge] = {}
    for item in raw["edges"]:
        edge = Edge(
            source=item["source"], target=item["target"],
            distance_m=float(item["distance_m"]),
            base_speed_kph=float(item["base_speed_kph"]),
            current_speed_kph=(float(item["current_speed_kph"]) if item.get("current_speed_kph") else None),
            closed=bool(item.get("closed", False)), metadata=item.get("metadata", {}),
        )
        edges[edge.key] = edge
        if item.get("bidirectional", False):
            reverse = Edge(
                source=edge.target, target=edge.source, distance_m=edge.distance_m,
                base_speed_kph=edge.base_speed_kph,
                current_speed_kph=edge.current_speed_kph, closed=edge.closed,
                metadata=dict(edge.metadata),
            )
            edges[reverse.key] = reverse
    return Graph(nodes=nodes, edges=edges)


def dump_graph(graph: Graph, path: str | Path) -> None:
    payload = {
        "nodes": [
            {"id": n.id, "lat": n.lat, "lon": n.lon, "kind": n.kind}
            for n in graph.nodes.values()
        ],
        "edges": [
            {
                "source": e.source, "target": e.target,
                "distance_m": e.distance_m, "base_speed_kph": e.base_speed_kph,
                "current_speed_kph": e.current_speed_kph, "closed": e.closed,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
                "metadata": e.metadata,
            }
            for e in graph.edges.values()
        ],
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_tdvrp_solution(path: str | Path) -> list[RoutePlan]:
    """Load the other team's final vehicle sequences; no initial TDVRP solving occurs here."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    plans: list[RoutePlan] = []
    for route in raw["routes"]:
        vehicle = VehicleState(**route["vehicle"])
        stops = [Stop(**stop) for stop in route["stops"]]
        plans.append(RoutePlan(vehicle=vehicle, stops=stops, frozen_prefix=route.get("frozen_prefix", [])))
    return plans


def dump_results(results: list[Any], path: str | Path) -> None:
    payload = []
    for result in results:
        payload.append({
            "strategy": result.strategy,
            "metrics": result.metrics.to_dict(),
            "paths": result.detailed_paths,
            "routes": [
                {
                    "vehicle_id": plan.vehicle.vehicle_id,
                    "sequence": [plan.vehicle.current_node] + [s.node_id for s in plan.stops] + [plan.vehicle.end_depot],
                    "job_ids": [s.job_id for s in plan.stops],
                }
                for plan in result.plans
            ],
            "explanation": result.explanation,
            "icer_cost_per_delay_hour_saved": result.icer_cost_per_delay_hour_saved,
        })
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
