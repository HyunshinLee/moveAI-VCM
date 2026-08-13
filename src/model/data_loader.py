from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.model.formulation import TDVRPTWData
from src.utils.config import INSTANCE_ROOT, TDVRP_DIR


DEFAULT_INSTANCE_DIR = INSTANCE_ROOT / "instance_01"


def load_service_nodes(path: Path = TDVRP_DIR / "service_nodes.csv") -> pd.DataFrame:
    nodes = pd.read_csv(path, dtype={"node_id": str, "node_type": str}).fillna("")
    for column in ["latitude", "longitude", "demand", "service_time"]:
        if column in nodes.columns:
            nodes[column] = pd.to_numeric(nodes[column], errors="coerce").fillna(0.0)
    return nodes


def load_td_od_matrix(path: Path = TDVRP_DIR / "td_od_matrix.csv") -> pd.DataFrame:
    matrix = pd.read_csv(path, dtype={"from_node": str, "to_node": str})
    matrix["hour"] = pd.to_numeric(matrix["hour"], errors="coerce").astype(int)
    matrix["travel_time_min"] = pd.to_numeric(matrix["travel_time_min"], errors="coerce")
    matrix["distance_km"] = pd.to_numeric(matrix["distance_km"], errors="coerce")
    return matrix


def load_td_paths(path: Path = TDVRP_DIR / "td_paths.csv") -> pd.DataFrame:
    paths = pd.read_csv(path, dtype={"from_node": str, "to_node": str, "path_nodes": str, "path_edges": str})
    paths["hour"] = pd.to_numeric(paths["hour"], errors="coerce").astype(int)
    return paths


def load_vehicles(path: Path = DEFAULT_INSTANCE_DIR / "vehicles.csv") -> pd.DataFrame:
    vehicles = pd.read_csv(path, dtype={"vehicle_id": str, "depot_id": str}).fillna("")
    for column in ["capacity_ton", "fixed_cost", "variable_cost_per_km", "max_route_duration_min"]:
        if column in vehicles.columns:
            vehicles[column] = pd.to_numeric(vehicles[column], errors="coerce").fillna(0.0)
    return vehicles


def load_parameters(path: Path = DEFAULT_INSTANCE_DIR / "parameters.json") -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_tdvrptw_data(instance_dir: Path = DEFAULT_INSTANCE_DIR) -> TDVRPTWData:
    service_nodes = load_service_nodes()
    td_od_matrix = load_td_od_matrix()
    td_paths = load_td_paths()
    vehicles = load_vehicles(instance_dir / "vehicles.csv")
    parameters = load_parameters(instance_dir / "parameters.json")
    return TDVRPTWData(
        service_nodes=service_nodes,
        td_od_matrix=td_od_matrix,
        vehicles=vehicles,
        parameters=parameters,
        td_paths=td_paths,
    )


def validate_loaded_data(data: TDVRPTWData) -> dict[str, Any]:
    depots = data.service_nodes[data.service_nodes["node_type"].eq("DEPOT")]
    customers = data.service_nodes[data.service_nodes["node_type"].eq("CUSTOMER")]
    hours = sorted(data.td_od_matrix["hour"].unique())
    expected_od_rows = len(data.service_nodes) * (len(data.service_nodes) - 1) * len(hours)
    return {
        "service_nodes": int(len(data.service_nodes)),
        "depots": int(len(depots)),
        "customers": int(len(customers)),
        "vehicles": int(len(data.vehicles)),
        "hours": [int(hours[0]), int(hours[-1])] if hours else [],
        "td_od_rows": int(len(data.td_od_matrix)),
        "expected_td_od_rows": int(expected_od_rows),
        "td_paths_rows": int(len(data.td_paths)) if data.td_paths is not None else 0,
        "total_customer_demand_ton": float(customers["demand"].sum()),
        "total_vehicle_capacity_ton": float(data.vehicles["capacity_ton"].sum()),
    }


def main() -> None:
    data = load_tdvrptw_data()
    summary = validate_loaded_data(data)
    print("== Loaded TDVRPTW data summary ==")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
