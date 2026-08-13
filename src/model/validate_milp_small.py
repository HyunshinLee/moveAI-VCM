from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.model.milp_solver import MILPSolver
from src.model.objective import ObjectiveMode, parse_objective_mode
from src.model.problem_data import NodeInfo, ProblemData, TimeWindowMode, VehicleInfo
from src.utils.config import OUTPUT_DIR
from src.utils.time_utils import parse_hhmm


def build_small_problem() -> ProblemData:
    depots = ["D01", "D02"]
    customers = ["C001", "C002", "C003", "C004"]
    vehicles = ["V001", "V002"]
    hours = [8, 9, 10, 11]

    nodes = {
        "D01": NodeInfo("D01", "DEPOT", 37.0, 127.0, 0.0, parse_hhmm("08:00"), parse_hhmm("18:00"), 0.0),
        "D02": NodeInfo("D02", "DEPOT", 37.3, 127.5, 0.0, parse_hhmm("08:00"), parse_hhmm("18:00"), 0.0),
        "C001": NodeInfo("C001", "CUSTOMER", 37.05, 127.05, 4.0, parse_hhmm("08:20"), parse_hhmm("10:00"), 10.0, "D01"),
        "C002": NodeInfo("C002", "CUSTOMER", 37.10, 127.15, 5.0, parse_hhmm("08:40"), parse_hhmm("11:00"), 10.0, "D01"),
        "C003": NodeInfo("C003", "CUSTOMER", 37.25, 127.45, 6.0, parse_hhmm("09:00"), parse_hhmm("12:00"), 10.0, "D02"),
        "C004": NodeInfo("C004", "CUSTOMER", 37.32, 127.55, 4.0, parse_hhmm("09:20"), parse_hhmm("12:30"), 10.0, "D02"),
    }
    vehicles_by_id = {
        "V001": VehicleInfo("V001", "D01", 12.0, parse_hhmm("08:00"), parse_hhmm("14:00"), 100.0, 1.0, 360.0),
        "V002": VehicleInfo("V002", "D02", 12.0, parse_hhmm("08:00"), parse_hhmm("14:00"), 100.0, 1.0, 360.0),
    }
    vehicles_by_depot = {"D01": ["V001"], "D02": ["V002"]}

    base_distance = {
        ("D01", "C001"): 8.0,
        ("D01", "C002"): 12.0,
        ("D01", "C003"): 35.0,
        ("D01", "C004"): 44.0,
        ("D02", "C001"): 42.0,
        ("D02", "C002"): 36.0,
        ("D02", "C003"): 9.0,
        ("D02", "C004"): 7.0,
    }
    for depot, customer in list(base_distance):
        base_distance[(customer, depot)] = base_distance[(depot, customer)]
    customer_pairs = {
        ("C001", "C002"): 7.0,
        ("C001", "C003"): 28.0,
        ("C001", "C004"): 34.0,
        ("C002", "C003"): 24.0,
        ("C002", "C004"): 29.0,
        ("C003", "C004"): 6.0,
    }
    for (left, right), distance in customer_pairs.items():
        base_distance[(left, right)] = distance
        base_distance[(right, left)] = distance

    distance_lookup = dict(base_distance)
    travel_time_lookup: dict[tuple[str, str, int], float] = {}
    td_rows = []
    for (from_node, to_node), distance in sorted(distance_lookup.items()):
        for hour in hours:
            congestion = 1.25 if hour == 9 else 1.0
            travel_time = distance * 1.8 * congestion
            travel_time_lookup[(from_node, to_node, hour)] = travel_time
            td_rows.append(
                {
                    "from_node": from_node,
                    "to_node": to_node,
                    "hour": hour,
                    "travel_time_min": travel_time,
                    "distance_km": distance,
                }
            )

    service_nodes = pd.DataFrame(
        [
            {
                "node_id": node.node_id,
                "node_type": node.node_type,
                "latitude": node.latitude,
                "longitude": node.longitude,
                "demand": node.demand,
                "tw_start": "08:00",
                "tw_end": "18:00",
                "service_time": node.service_time,
                "assigned_depot": node.assigned_depot,
            }
            for node in nodes.values()
        ]
    )
    vehicles_df = pd.DataFrame(
        [
            {
                "vehicle_id": vehicle.vehicle_id,
                "depot_id": vehicle.start_depot,
                "capacity_ton": vehicle.capacity,
                "start_time": "08:00",
                "end_time": "14:00",
                "fixed_cost": vehicle.fixed_cost,
                "variable_cost_per_km": vehicle.variable_cost_per_km,
                "max_route_duration_min": vehicle.max_route_duration_min,
            }
            for vehicle in vehicles_by_id.values()
        ]
    )

    return ProblemData(
        service_nodes=service_nodes,
        td_od_matrix=pd.DataFrame(td_rows),
        td_paths=None,
        vehicles=vehicles_df,
        parameters={"instance_id": "small_milp_validation"},
        nodes=nodes,
        vehicles_by_id=vehicles_by_id,
        customer_ids=customers,
        depot_ids=depots,
        vehicle_ids=vehicles,
        vehicles_by_depot=vehicles_by_depot,
        travel_time_lookup=travel_time_lookup,
        distance_lookup=distance_lookup,
        hours=hours,
        time_window_mode=TimeWindowMode.SOFT,
    )


def run_small_validation(objective: str = "DISTANCE") -> None:
    problem = build_small_problem()
    mode = parse_objective_mode(objective)
    solver = MILPSolver(
        problem_data=problem,
        objective_mode=mode,
        time_limit=30,
        mip_gap=0.0,
        output_flag=0,
    )
    _, result = solver.solve()
    out_dir = Path(result.output_dir)
    print(pd.DataFrame([result.__dict__]).to_string(index=False))
    if result.sol_count <= 0:
        raise RuntimeError("Small MILP validation did not produce a solution")
    if not result.feasible:
        raise RuntimeError(f"Small MILP solution failed evaluation: {result.validation_errors}")
    print((out_dir / "best_solution.csv").read_text(encoding="utf-8-sig"))


def main() -> None:
    run_small_validation()


if __name__ == "__main__":
    main()
