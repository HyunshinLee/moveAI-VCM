from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd

from src.model.data_loader import DEFAULT_INSTANCE_DIR, load_tdvrptw_data
from src.utils.time_utils import departure_hour, parse_hhmm


class TimeWindowMode(str, Enum):
    SOFT = "SOFT"
    HARD = "HARD"


@dataclass(frozen=True)
class NodeInfo:
    node_id: str
    node_type: str
    latitude: float
    longitude: float
    demand: float
    tw_start: int
    tw_end: int
    service_time: float
    assigned_depot: str = ""
    rho: float = 1.0


@dataclass(frozen=True)
class VehicleInfo:
    vehicle_id: str
    start_depot: str
    capacity: float
    start_time: int
    end_time: int
    fixed_cost: float
    variable_cost_per_km: float
    max_route_duration_min: float


@dataclass(frozen=True)
class ProblemData:
    service_nodes: pd.DataFrame
    td_od_matrix: pd.DataFrame
    td_paths: pd.DataFrame | None
    vehicles: pd.DataFrame
    parameters: dict[str, Any]
    nodes: dict[str, NodeInfo]
    vehicles_by_id: dict[str, VehicleInfo]
    customer_ids: list[str]
    depot_ids: list[str]
    vehicle_ids: list[str]
    vehicles_by_depot: dict[str, list[str]]
    travel_time_lookup: dict[tuple[str, str, int], float]
    distance_lookup: dict[tuple[str, str], float]
    hours: list[int]
    time_window_mode: TimeWindowMode = TimeWindowMode.SOFT

    @classmethod
    def from_files(
        cls,
        instance_dir: Path = DEFAULT_INSTANCE_DIR,
        time_window_mode: str | TimeWindowMode = TimeWindowMode.SOFT,
    ) -> "ProblemData":
        raw = load_tdvrptw_data(instance_dir)
        service_nodes = raw.service_nodes.copy()
        td_od_matrix = raw.td_od_matrix.copy()
        vehicles = raw.vehicles.copy()
        parameters = dict(raw.parameters)

        required_node_columns = {
            "node_id",
            "node_type",
            "latitude",
            "longitude",
            "demand",
            "tw_start",
            "tw_end",
            "service_time",
        }
        missing_node_columns = required_node_columns.difference(service_nodes.columns)
        if missing_node_columns:
            raise ValueError(f"Missing service_nodes columns: {sorted(missing_node_columns)}")

        required_vehicle_columns = {
            "vehicle_id",
            "depot_id",
            "capacity_ton",
            "start_time",
            "end_time",
            "fixed_cost",
            "variable_cost_per_km",
            "max_route_duration_min",
        }
        missing_vehicle_columns = required_vehicle_columns.difference(vehicles.columns)
        if missing_vehicle_columns:
            raise ValueError(f"Missing vehicles columns: {sorted(missing_vehicle_columns)}")

        nodes: dict[str, NodeInfo] = {}
        for row in service_nodes.itertuples(index=False):
            node_id = str(row.node_id)
            tw_start = str(row.tw_start) if str(row.tw_start).strip() else "00:00"
            tw_end = str(row.tw_end) if str(row.tw_end).strip() else "23:59"
            nodes[node_id] = NodeInfo(
                node_id=node_id,
                node_type=str(row.node_type),
                latitude=float(row.latitude),
                longitude=float(row.longitude),
                demand=float(row.demand),
                tw_start=parse_hhmm(tw_start),
                tw_end=parse_hhmm(tw_end),
                service_time=float(row.service_time),
                assigned_depot=str(getattr(row, "assigned_depot", "") or ""),
                rho=float(getattr(row, "rho", 1.0) or 1.0),
            )

        vehicles_by_id: dict[str, VehicleInfo] = {}
        vehicles_by_depot: dict[str, list[str]] = {}
        for row in vehicles.itertuples(index=False):
            vehicle_id = str(row.vehicle_id)
            start_depot = str(row.depot_id)
            vehicles_by_id[vehicle_id] = VehicleInfo(
                vehicle_id=vehicle_id,
                start_depot=start_depot,
                capacity=float(row.capacity_ton),
                start_time=parse_hhmm(str(row.start_time)),
                end_time=parse_hhmm(str(row.end_time)),
                fixed_cost=float(row.fixed_cost),
                variable_cost_per_km=float(row.variable_cost_per_km),
                max_route_duration_min=float(row.max_route_duration_min),
            )
            vehicles_by_depot.setdefault(start_depot, []).append(vehicle_id)

        td_od_matrix["from_node"] = td_od_matrix["from_node"].astype(str)
        td_od_matrix["to_node"] = td_od_matrix["to_node"].astype(str)
        hours = sorted(int(hour) for hour in td_od_matrix["hour"].unique())
        travel_time_lookup = {
            (str(row.from_node), str(row.to_node), int(row.hour)): float(row.travel_time_min)
            for row in td_od_matrix.itertuples(index=False)
        }
        distance_lookup: dict[tuple[str, str], float] = {}
        for row in td_od_matrix.sort_values("hour").itertuples(index=False):
            key = (str(row.from_node), str(row.to_node))
            if key not in distance_lookup:
                distance_lookup[key] = float(row.distance_km)

        customer_ids = sorted(
            node_id for node_id, node in nodes.items() if node.node_type == "CUSTOMER"
        )
        depot_ids = sorted(node_id for node_id, node in nodes.items() if node.node_type == "DEPOT")
        vehicle_ids = sorted(vehicles_by_id)

        return cls(
            service_nodes=service_nodes,
            td_od_matrix=td_od_matrix,
            td_paths=raw.td_paths,
            vehicles=vehicles,
            parameters=parameters,
            nodes=nodes,
            vehicles_by_id=vehicles_by_id,
            customer_ids=customer_ids,
            depot_ids=depot_ids,
            vehicle_ids=vehicle_ids,
            vehicles_by_depot=vehicles_by_depot,
            travel_time_lookup=travel_time_lookup,
            distance_lookup=distance_lookup,
            hours=hours,
            time_window_mode=parse_time_window_mode(time_window_mode),
        )

    def lookup_hour(self, departure_min: int | float) -> int:
        hour = departure_hour(departure_min)
        if hour in self.hours:
            return hour
        if departure_min < self.hours[0] * 60:
            return self.hours[0]
        return self.hours[-1]

    def travel_time(self, from_node: str, to_node: str, departure_min: int | float) -> float:
        if from_node == to_node:
            return 0.0
        key = (from_node, to_node, self.lookup_hour(departure_min))
        if key not in self.travel_time_lookup:
            raise KeyError(f"Missing TD travel time lookup: {key}")
        return self.travel_time_lookup[key]

    def distance(self, from_node: str, to_node: str) -> float:
        if from_node == to_node:
            return 0.0
        key = (from_node, to_node)
        if key not in self.distance_lookup:
            raise KeyError(f"Missing distance lookup: {key}")
        return self.distance_lookup[key]

    def customer_demand(self, customer_id: str) -> float:
        return self.nodes[customer_id].demand

    def assigned_depot(self, customer_id: str) -> str:
        assigned = self.nodes[customer_id].assigned_depot
        return assigned if assigned in self.depot_ids else self.nearest_depot_by_distance(customer_id)

    def nearest_depot_by_distance(self, customer_id: str) -> str:
        return min(self.depot_ids, key=lambda depot_id: (self.distance(depot_id, customer_id), depot_id))


def parse_time_window_mode(value: str | TimeWindowMode) -> TimeWindowMode:
    if isinstance(value, TimeWindowMode):
        return value
    normalized = str(value).strip().upper()
    try:
        return TimeWindowMode(normalized)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in TimeWindowMode)
        raise ValueError(f"Invalid time_window_mode '{value}'. Allowed values: {allowed}") from exc
