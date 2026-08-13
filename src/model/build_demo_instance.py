from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from src.utils.config import INSTANCE_ROOT, PHYSICAL_DIR, TDVRP_DIR, ensure_project_dirs


INSTANCE_DIR = INSTANCE_ROOT / "instance_01"
SERVICE_NODES_CSV = TDVRP_DIR / "service_nodes.csv"
TD_OD_MATRIX_CSV = TDVRP_DIR / "td_od_matrix.csv"
PHYSICAL_CUSTOMERS_CSV = PHYSICAL_DIR / "customers.csv"
PHYSICAL_DEPOTS_CSV = PHYSICAL_DIR / "depots.csv"
PHYSICAL_NODES_CSV = PHYSICAL_DIR / "physical_nodes.csv"

INSTANCE_CUSTOMERS_CSV = INSTANCE_DIR / "customers.csv"
INSTANCE_DEPOTS_CSV = INSTANCE_DIR / "depots.csv"
INSTANCE_VEHICLES_CSV = INSTANCE_DIR / "vehicles.csv"
INSTANCE_PARAMETERS_JSON = INSTANCE_DIR / "parameters.json"

ASSIGNMENT_HOUR = 8
VEHICLE_CAPACITY_TON = 30
CAPACITY_SLACK_FACTOR = 1.25
MIN_VEHICLES_BY_DEPOT = {
    "D01": 3,
    "D02": 3,
    "D03": 3,
    "D04": 2,
    "D05": 3,
}

TIME_WINDOW_PATTERNS = [
    ("08:00", "12:00"),
    ("09:00", "15:00"),
    ("10:00", "17:00"),
    ("13:00", "18:00"),
    ("08:00", "16:00"),
]


def log(message: str) -> None:
    print(f"[demo_instance] {message}", flush=True)


def customer_index(customer_id: str) -> int:
    return int(str(customer_id).replace("C", ""))


def demo_demand_ton(customer_id: str) -> int:
    idx = customer_index(customer_id)
    return 4 + ((idx * 7) % 17)


def demo_service_time_min(demand_ton: int) -> int:
    raw = 20 + 2 * demand_ton
    return int(5 * round(raw / 5))


def assign_customers_to_nearest_depot(
    service_nodes: pd.DataFrame,
    td_od_matrix: pd.DataFrame,
) -> pd.DataFrame:
    depots = service_nodes[service_nodes["node_type"].eq("DEPOT")]["node_id"].tolist()
    customers = service_nodes[service_nodes["node_type"].eq("CUSTOMER")]["node_id"].tolist()
    available_hours = sorted(td_od_matrix["hour"].unique())
    hour = ASSIGNMENT_HOUR if ASSIGNMENT_HOUR in available_hours else available_hours[0]

    od = td_od_matrix[
        td_od_matrix["hour"].eq(hour)
        & td_od_matrix["from_node"].isin(depots)
        & td_od_matrix["to_node"].isin(customers)
    ].copy()
    rows: list[dict[str, Any]] = []
    for customer_id in customers:
        nearest = od[od["to_node"].eq(customer_id)].sort_values("travel_time_min").iloc[0]
        rows.append(
            {
                "node_id": customer_id,
                "assigned_depot": nearest["from_node"],
                "assignment_hour": hour,
                "assignment_travel_time_min": round(float(nearest["travel_time_min"]), 6),
                "assignment_distance_km": round(float(nearest["distance_km"]), 6),
            }
        )
    return pd.DataFrame(rows)


def build_customer_attributes(service_nodes: pd.DataFrame, assignments: pd.DataFrame) -> pd.DataFrame:
    customers = service_nodes[service_nodes["node_type"].eq("CUSTOMER")].copy()
    existing_assignment_columns = [column for column in assignments.columns if column != "node_id"]
    customers = customers.drop(columns=existing_assignment_columns, errors="ignore")
    customers = customers.merge(assignments, on="node_id", how="left")

    depot_order = {"D01": 0, "D02": 1, "D03": 2, "D04": 3, "D05": 4}
    demands = []
    tw_starts = []
    tw_ends = []
    service_times = []
    for row in customers.itertuples(index=False):
        idx = customer_index(row.node_id)
        demand = demo_demand_ton(row.node_id)
        pattern_idx = (idx + depot_order.get(row.assigned_depot, 0)) % len(TIME_WINDOW_PATTERNS)
        tw_start, tw_end = TIME_WINDOW_PATTERNS[pattern_idx]
        demands.append(demand)
        tw_starts.append(tw_start)
        tw_ends.append(tw_end)
        service_times.append(demo_service_time_min(demand))

    customers["demand"] = demands
    customers["tw_start"] = tw_starts
    customers["tw_end"] = tw_ends
    customers["service_time"] = service_times
    return customers


def build_vehicle_table(customer_attrs: pd.DataFrame) -> pd.DataFrame:
    demand_by_depot = customer_attrs.groupby("assigned_depot")["demand"].sum().to_dict()
    rows: list[dict[str, Any]] = []
    vehicle_counter = 1
    for depot_id in ["D01", "D02", "D03", "D04", "D05"]:
        total_demand = float(demand_by_depot.get(depot_id, 0.0))
        required = math.ceil(total_demand * CAPACITY_SLACK_FACTOR / VEHICLE_CAPACITY_TON)
        vehicle_count = max(MIN_VEHICLES_BY_DEPOT.get(depot_id, 2), required)
        for local_idx in range(1, vehicle_count + 1):
            rows.append(
                {
                    "vehicle_id": f"V{vehicle_counter:03d}",
                    "depot_id": depot_id,
                    "vehicle_no_at_depot": local_idx,
                    "capacity_ton": VEHICLE_CAPACITY_TON,
                    "start_time": "06:00",
                    "end_time": "22:00",
                    "fixed_cost": 120000,
                    "variable_cost_per_km": 1450,
                    "max_route_duration_min": 720,
                }
            )
            vehicle_counter += 1
    return pd.DataFrame(rows)


def update_service_nodes(service_nodes: pd.DataFrame, customer_attrs: pd.DataFrame) -> pd.DataFrame:
    updated = service_nodes.copy()
    for column in ["assigned_depot", "assignment_hour", "assignment_travel_time_min", "assignment_distance_km"]:
        if column not in updated.columns:
            updated[column] = ""

    attrs = customer_attrs.set_index("node_id")
    for node_id, row in attrs.iterrows():
        mask = updated["node_id"].eq(node_id)
        updated.loc[mask, "demand"] = row["demand"]
        updated.loc[mask, "tw_start"] = row["tw_start"]
        updated.loc[mask, "tw_end"] = row["tw_end"]
        updated.loc[mask, "service_time"] = row["service_time"]
        updated.loc[mask, "assigned_depot"] = row["assigned_depot"]
        updated.loc[mask, "assignment_hour"] = row["assignment_hour"]
        updated.loc[mask, "assignment_travel_time_min"] = row["assignment_travel_time_min"]
        updated.loc[mask, "assignment_distance_km"] = row["assignment_distance_km"]

    depot_mask = updated["node_type"].eq("DEPOT")
    updated.loc[depot_mask, "demand"] = 0
    updated.loc[depot_mask, "service_time"] = 0
    updated.loc[depot_mask, "tw_start"] = "06:00"
    updated.loc[depot_mask, "tw_end"] = "22:00"
    updated.loc[depot_mask, "assigned_depot"] = updated.loc[depot_mask, "node_id"]
    return updated


def sync_physical_customer_files(customer_attrs: pd.DataFrame) -> None:
    if PHYSICAL_CUSTOMERS_CSV.exists():
        physical_customers = pd.read_csv(PHYSICAL_CUSTOMERS_CSV, dtype=str).fillna("")
        attrs = customer_attrs.set_index("node_id")
        for node_id, row in attrs.iterrows():
            mask = physical_customers["node_id"].eq(node_id)
            physical_customers.loc[mask, "demand_ton"] = row["demand"]
            physical_customers.loc[mask, "service_time_min"] = row["service_time"]
            physical_customers.loc[mask, "time_window_start"] = row["tw_start"]
            physical_customers.loc[mask, "time_window_end"] = row["tw_end"]
            physical_customers.loc[mask, "assigned_depot"] = row["assigned_depot"]
        physical_customers.to_csv(PHYSICAL_CUSTOMERS_CSV, index=False, encoding="utf-8-sig")
        physical_customers.to_csv(INSTANCE_CUSTOMERS_CSV, index=False, encoding="utf-8-sig")

    if PHYSICAL_NODES_CSV.exists():
        physical_nodes = pd.read_csv(PHYSICAL_NODES_CSV, dtype=str).fillna("")
        attrs = customer_attrs.set_index("node_id")
        if "assigned_depot" not in physical_nodes.columns:
            physical_nodes["assigned_depot"] = ""
        for node_id, row in attrs.iterrows():
            mask = physical_nodes["node_id"].eq(node_id)
            physical_nodes.loc[mask, "demand"] = row["demand"]
            physical_nodes.loc[mask, "service_time"] = row["service_time"]
            physical_nodes.loc[mask, "tw_start"] = row["tw_start"]
            physical_nodes.loc[mask, "tw_end"] = row["tw_end"]
            physical_nodes.loc[mask, "assigned_depot"] = row["assigned_depot"]
        depot_mask = physical_nodes["node_type"].eq("DEPOT")
        physical_nodes.loc[depot_mask, "demand"] = 0
        physical_nodes.loc[depot_mask, "service_time"] = 0
        physical_nodes.loc[depot_mask, "tw_start"] = "06:00"
        physical_nodes.loc[depot_mask, "tw_end"] = "22:00"
        physical_nodes.to_csv(PHYSICAL_NODES_CSV, index=False, encoding="utf-8-sig")


def sync_depots_instance() -> None:
    if PHYSICAL_DEPOTS_CSV.exists():
        depots = pd.read_csv(PHYSICAL_DEPOTS_CSV, dtype=str).fillna("")
        depots.to_csv(INSTANCE_DEPOTS_CSV, index=False, encoding="utf-8-sig")


def write_parameters(customer_attrs: pd.DataFrame, vehicles: pd.DataFrame) -> None:
    depot_summary = (
        customer_attrs.groupby("assigned_depot")
        .agg(customers=("node_id", "count"), total_demand_ton=("demand", "sum"))
        .reset_index()
    )
    vehicle_summary = vehicles.groupby("depot_id").size().rename("vehicle_count").reset_index()
    summary = depot_summary.merge(vehicle_summary, left_on="assigned_depot", right_on="depot_id", how="outer")
    summary = summary.fillna({"customers": 0, "total_demand_ton": 0, "vehicle_count": 0})
    summary["assigned_depot"] = summary["assigned_depot"].fillna(summary["depot_id"])
    summary["customers"] = summary["customers"].astype(int)
    summary["vehicle_count"] = summary["vehicle_count"].astype(int)
    summary["total_demand_ton"] = summary["total_demand_ton"].astype(float)

    parameters = {
        "instance_id": "instance_01",
        "description": "Demo 5-depot, 50-customer TD-MDVRPTW instance with deterministic synthetic demand, time windows, and depot vehicle fleet.",
        "service_node_count": 55,
        "customer_count": 50,
        "depot_count": 5,
        "vehicle_count": int(len(vehicles)),
        "vehicle_capacity_ton": VEHICLE_CAPACITY_TON,
        "capacity_slack_factor": CAPACITY_SLACK_FACTOR,
        "assignment_hour": ASSIGNMENT_HOUR,
        "time_dependent_mode": "hourly_snapshot",
        "depot_summary": summary[
            ["assigned_depot", "customers", "total_demand_ton", "vehicle_count"]
        ].to_dict(orient="records"),
    }
    INSTANCE_PARAMETERS_JSON.write_text(
        json.dumps(parameters, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    ensure_project_dirs()
    service_nodes = pd.read_csv(SERVICE_NODES_CSV, dtype=str).fillna("")
    td_od_matrix = pd.read_csv(TD_OD_MATRIX_CSV)
    td_od_matrix["from_node"] = td_od_matrix["from_node"].astype(str)
    td_od_matrix["to_node"] = td_od_matrix["to_node"].astype(str)

    assignments = assign_customers_to_nearest_depot(service_nodes, td_od_matrix)
    customer_attrs = build_customer_attributes(service_nodes, assignments)
    updated_service_nodes = update_service_nodes(service_nodes, customer_attrs)
    vehicles = build_vehicle_table(customer_attrs)

    updated_service_nodes.to_csv(SERVICE_NODES_CSV, index=False, encoding="utf-8-sig")
    sync_physical_customer_files(customer_attrs)
    sync_depots_instance()
    vehicles.to_csv(INSTANCE_VEHICLES_CSV, index=False, encoding="utf-8-sig")
    write_parameters(customer_attrs, vehicles)

    print("== Demo instance summary ==")
    print(f"customers: {len(customer_attrs)}")
    print(f"total demand ton: {customer_attrs['demand'].sum():.0f}")
    print(f"vehicles: {len(vehicles)}")
    print("\nCustomer demand/time window sample:")
    print(
        customer_attrs[
            ["node_id", "assigned_depot", "demand", "tw_start", "tw_end", "service_time"]
        ].head(15).to_string(index=False)
    )
    print("\nDepot fleet summary:")
    print(
        vehicles.groupby("depot_id")
        .agg(vehicle_count=("vehicle_id", "count"), capacity_ton=("capacity_ton", "sum"))
        .to_string()
    )
    log(f"Wrote {SERVICE_NODES_CSV}")
    log(f"Wrote {INSTANCE_CUSTOMERS_CSV}")
    log(f"Wrote {INSTANCE_DEPOTS_CSV}")
    log(f"Wrote {INSTANCE_VEHICLES_CSV}")
    log(f"Wrote {INSTANCE_PARAMETERS_JSON}")


if __name__ == "__main__":
    main()
