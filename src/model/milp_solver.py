from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import gurobipy as gp
    from gurobipy import GRB
except ImportError as exc:  # pragma: no cover
    gp = None
    GRB = None
    GUROBI_IMPORT_ERROR = exc
else:
    GUROBI_IMPORT_ERROR = None

from src.alns.evaluation import evaluate_solution
from src.model.objective import ObjectiveMode, parse_objective_mode
from src.model.problem_data import ProblemData
from src.model.solution import Route, Solution
from src.utils.config import OUTPUT_DIR, ensure_project_dirs
from src.utils.time_utils import departure_hour, minutes_to_hhmm


OBJECTIVE_CHOICES = [mode.value for mode in ObjectiveMode]
MILP_OUTPUT_DIR = OUTPUT_DIR / "milp"


@dataclass(frozen=True)
class MILPResult:
    objective_mode: str
    solver_status: str
    sol_count: int
    mip_gap: float | None
    objective_value: float | None
    best_bound: float | None
    runtime: float
    build_runtime: float
    solve_runtime: float
    feasible: bool
    total_tardiness: float | None
    total_travel_time: float | None
    total_distance: float | None
    vehicle_cost: float | None
    used_vehicle_count: int | None
    output_dir: str
    validation_errors: list[str]


class MILPSolver:
    def __init__(
        self,
        problem_data: ProblemData,
        objective_mode: ObjectiveMode,
        time_limit: float = 60.0,
        mip_gap: float | None = 0.05,
        solution_limit: int | None = None,
        output_flag: int = 1,
    ):
        if gp is None or GRB is None:
            raise ImportError("gurobipy is required for MILP solving") from GUROBI_IMPORT_ERROR
        self.problem_data = problem_data
        self.objective_mode = objective_mode
        self.time_limit = time_limit
        self.mip_gap = mip_gap
        self.solution_limit = solution_limit
        self.output_flag = output_flag
        self.model: gp.Model | None = None
        self.vars: dict[str, Any] = {}
        self.arcs_by_vehicle: dict[str, list[tuple[str, str]]] = {}
        self.lambda_hours: dict[tuple[str, str, str], list[int]] = {}

    def build_model(self) -> gp.Model:
        data = self.problem_data
        model = gp.Model(f"TD_MDCVRPTW_FED_{self.objective_mode.value}")
        model.Params.OutputFlag = self.output_flag
        model.Params.TimeLimit = self.time_limit
        model.Params.MIPFocus = 1
        if self.mip_gap is not None:
            model.Params.MIPGap = self.mip_gap
        if self.solution_limit is not None:
            model.Params.SolutionLimit = self.solution_limit

        vehicles = data.vehicle_ids
        customers = data.customer_ids
        depots = data.depot_ids
        nodes = depots + customers
        big_m = self._big_m()
        epsilon = 1e-4

        self.arcs_by_vehicle = {
            vehicle_id: self._vehicle_arcs(vehicle_id)
            for vehicle_id in vehicles
        }
        x_keys = [
            (vehicle_id, from_node, to_node)
            for vehicle_id in vehicles
            for from_node, to_node in self.arcs_by_vehicle[vehicle_id]
        ]
        lambda_keys: list[tuple[str, str, str, int]] = []
        for vehicle_id, from_node, to_node in x_keys:
            hours = self._arc_hours(vehicle_id, from_node)
            self.lambda_hours[(vehicle_id, from_node, to_node)] = hours
            lambda_keys.extend((vehicle_id, from_node, to_node, hour) for hour in hours)

        x = model.addVars(x_keys, vtype=GRB.BINARY, name="x")
        y = model.addVars(vehicles, customers, vtype=GRB.BINARY, name="y")
        z = model.addVars(vehicles, vtype=GRB.BINARY, name="z")
        r = model.addVars(vehicles, depots, vtype=GRB.BINARY, name="r")
        lam = model.addVars(lambda_keys, vtype=GRB.BINARY, name="lambda")
        a = model.addVars(vehicles, nodes, lb=0.0, vtype=GRB.CONTINUOUS, name="a")
        b = model.addVars(vehicles, customers, lb=0.0, vtype=GRB.CONTINUOUS, name="b")
        theta = model.addVars(vehicles, nodes, lb=0.0, vtype=GRB.CONTINUOUS, name="theta")
        tardiness = model.addVars(customers, lb=0.0, vtype=GRB.CONTINUOUS, name="T")
        early = model.addVars(vehicles, customers, vtype=GRB.BINARY, name="early_arrival")

        # (1) every customer is assigned exactly once.
        model.addConstrs(
            (gp.quicksum(y[vehicle_id, customer_id] for vehicle_id in vehicles) == 1
             for customer_id in customers),
            name="customer_exactly_once",
        )

        # (2)-(3) customer flow conservation per vehicle.
        for vehicle_id in vehicles:
            arcs = self.arcs_by_vehicle[vehicle_id]
            for customer_id in customers:
                model.addConstr(
                    gp.quicksum(x[vehicle_id, i, j] for i, j in arcs if i == customer_id)
                    == y[vehicle_id, customer_id],
                    name=f"customer_out[{vehicle_id},{customer_id}]",
                )
                model.addConstr(
                    gp.quicksum(x[vehicle_id, i, j] for i, j in arcs if j == customer_id)
                    == y[vehicle_id, customer_id],
                    name=f"customer_in[{vehicle_id},{customer_id}]",
                )

        # (4) assignment implies vehicle usage.
        model.addConstrs(
            (y[vehicle_id, customer_id] <= z[vehicle_id]
             for vehicle_id in vehicles for customer_id in customers),
            name="assignment_vehicle_usage",
        )

        # (5) used vehicle starts from its fixed home depot.
        for vehicle_id in vehicles:
            home = data.vehicles_by_id[vehicle_id].start_depot
            model.addConstr(
                gp.quicksum(x[vehicle_id, home, customer_id] for customer_id in customers)
                == z[vehicle_id],
                name=f"start_home_depot[{vehicle_id}]",
            )

        # (6)-(7) used vehicle selects exactly one flexible end depot.
        model.addConstrs(
            (gp.quicksum(r[vehicle_id, depot_id] for depot_id in depots) == z[vehicle_id]
             for vehicle_id in vehicles),
            name="select_end_depot",
        )
        for vehicle_id in vehicles:
            for depot_id in depots:
                model.addConstr(
                    gp.quicksum(x[vehicle_id, customer_id, depot_id] for customer_id in customers)
                    == r[vehicle_id, depot_id],
                    name=f"end_depot_link[{vehicle_id},{depot_id}]",
                )

        # (9) depot fleet availability. Vehicles are already enumerated by depot; this keeps md explicit.
        for depot_id in depots:
            depot_vehicle_ids = data.vehicles_by_depot.get(depot_id, [])
            model.addConstr(
                gp.quicksum(z[vehicle_id] for vehicle_id in depot_vehicle_ids)
                <= len(depot_vehicle_ids),
                name=f"depot_fleet[{depot_id}]",
            )

        # (10) vehicle capacity.
        for vehicle_id in vehicles:
            vehicle = data.vehicles_by_id[vehicle_id]
            model.addConstr(
                gp.quicksum(data.nodes[customer_id].demand * y[vehicle_id, customer_id]
                            for customer_id in customers)
                <= vehicle.capacity * z[vehicle_id],
                name=f"capacity[{vehicle_id}]",
            )

        # (11)-(13) time interval selection by departure time.
        for vehicle_id, from_node, to_node in x_keys:
            hours = self.lambda_hours[(vehicle_id, from_node, to_node)]
            model.addConstr(
                gp.quicksum(lam[vehicle_id, from_node, to_node, hour] for hour in hours)
                == x[vehicle_id, from_node, to_node],
                name=f"lambda_link[{vehicle_id},{from_node},{to_node}]",
            )
            for hour in hours:
                start = 60.0 * hour
                end = 60.0 * (hour + 1)
                model.addConstr(
                    theta[vehicle_id, from_node]
                    >= start - big_m * (1 - lam[vehicle_id, from_node, to_node, hour]),
                    name=f"lambda_start[{vehicle_id},{from_node},{to_node},{hour}]",
                )
                model.addConstr(
                    theta[vehicle_id, from_node]
                    <= end - epsilon + big_m * (1 - lam[vehicle_id, from_node, to_node, hour]),
                    name=f"lambda_end[{vehicle_id},{from_node},{to_node},{hour}]",
                )

        # (14)-(15) time-dependent travel propagation.
        for vehicle_id, from_node, to_node in x_keys:
            hours = self.lambda_hours[(vehicle_id, from_node, to_node)]
            travel_expr = gp.quicksum(
                data.travel_time_lookup[from_node, to_node, hour]
                * lam[vehicle_id, from_node, to_node, hour]
                for hour in hours
            )
            model.addConstr(
                a[vehicle_id, to_node]
                >= theta[vehicle_id, from_node] + travel_expr
                - big_m * (1 - x[vehicle_id, from_node, to_node]),
                name=f"arrival_lb[{vehicle_id},{from_node},{to_node}]",
            )
            model.addConstr(
                a[vehicle_id, to_node]
                <= theta[vehicle_id, from_node] + travel_expr
                + big_m * (1 - x[vehicle_id, from_node, to_node]),
                name=f"arrival_ub[{vehicle_id},{from_node},{to_node}]",
            )

        # (16)-(19) waiting until earliest time, service start, soft tardiness, departure time.
        for vehicle_id in vehicles:
            for customer_id in customers:
                customer = data.nodes[customer_id]
                model.addConstr(b[vehicle_id, customer_id] >= a[vehicle_id, customer_id],
                                name=f"service_after_arrival[{vehicle_id},{customer_id}]")
                model.addConstr(
                    b[vehicle_id, customer_id]
                    >= customer.tw_start - big_m * (1 - y[vehicle_id, customer_id]),
                    name=f"service_after_earliest[{vehicle_id},{customer_id}]",
                )
                # b = max(a, e) for assigned customers: waiting is only until earliest time.
                model.addConstr(
                    a[vehicle_id, customer_id] - customer.tw_start
                    <= big_m * (1 - early[vehicle_id, customer_id]) + big_m * (1 - y[vehicle_id, customer_id]),
                    name=f"early_case_ub[{vehicle_id},{customer_id}]",
                )
                model.addConstr(
                    a[vehicle_id, customer_id] - customer.tw_start
                    >= -big_m * early[vehicle_id, customer_id] - big_m * (1 - y[vehicle_id, customer_id]),
                    name=f"late_case_lb[{vehicle_id},{customer_id}]",
                )
                model.addConstr(
                    b[vehicle_id, customer_id]
                    <= customer.tw_start + big_m * (1 - early[vehicle_id, customer_id])
                    + big_m * (1 - y[vehicle_id, customer_id]),
                    name=f"service_max_earliest[{vehicle_id},{customer_id}]",
                )
                model.addConstr(
                    b[vehicle_id, customer_id]
                    <= a[vehicle_id, customer_id] + big_m * early[vehicle_id, customer_id]
                    + big_m * (1 - y[vehicle_id, customer_id]),
                    name=f"service_max_arrival[{vehicle_id},{customer_id}]",
                )
                model.addConstr(
                    tardiness[customer_id]
                    >= b[vehicle_id, customer_id] - customer.tw_end
                    - big_m * (1 - y[vehicle_id, customer_id]),
                    name=f"tardiness[{vehicle_id},{customer_id}]",
                )
                model.addConstr(
                    theta[vehicle_id, customer_id]
                    == b[vehicle_id, customer_id] + customer.service_time * y[vehicle_id, customer_id],
                    name=f"customer_departure[{vehicle_id},{customer_id}]",
                )

        # (20)-(24) bind time variables to visited customers/end depots/start depot usage.
        for vehicle_id in vehicles:
            vehicle = data.vehicles_by_id[vehicle_id]
            home = vehicle.start_depot
            for customer_id in customers:
                model.addConstr(a[vehicle_id, customer_id] <= big_m * y[vehicle_id, customer_id],
                                name=f"arrival_visit_link[{vehicle_id},{customer_id}]")
                model.addConstr(b[vehicle_id, customer_id] <= big_m * y[vehicle_id, customer_id],
                                name=f"service_visit_link[{vehicle_id},{customer_id}]")
                model.addConstr(theta[vehicle_id, customer_id] <= big_m * y[vehicle_id, customer_id],
                                name=f"departure_visit_link[{vehicle_id},{customer_id}]")
            for depot_id in depots:
                model.addConstr(a[vehicle_id, depot_id] <= big_m * r[vehicle_id, depot_id],
                                name=f"end_arrival_link[{vehicle_id},{depot_id}]")
                if depot_id != home:
                    model.addConstr(theta[vehicle_id, depot_id] == 0,
                                    name=f"non_home_depot_departure_zero[{vehicle_id},{depot_id}]")
            model.addConstr(theta[vehicle_id, home] == vehicle.start_time * z[vehicle_id],
                            name=f"home_departure_time[{vehicle_id}]")
            for depot_id in depots:
                model.addConstr(
                    a[vehicle_id, depot_id]
                    <= vehicle.end_time + big_m * (1 - r[vehicle_id, depot_id]),
                    name=f"vehicle_end_time[{vehicle_id},{depot_id}]",
                )
                model.addConstr(
                    a[vehicle_id, depot_id] - vehicle.start_time
                    <= vehicle.max_route_duration_min + big_m * (1 - r[vehicle_id, depot_id]),
                    name=f"max_route_duration[{vehicle_id},{depot_id}]",
                )

        if self.objective_mode == ObjectiveMode.TARDINESS:
            objective = gp.quicksum(data.nodes[customer_id].rho * tardiness[customer_id]
                                    for customer_id in customers)
        elif self.objective_mode == ObjectiveMode.TRAVEL_TIME:
            objective = gp.quicksum(
                data.travel_time_lookup[from_node, to_node, hour]
                * lam[vehicle_id, from_node, to_node, hour]
                for vehicle_id, from_node, to_node, hour in lambda_keys
            )
        elif self.objective_mode == ObjectiveMode.DISTANCE:
            objective = gp.quicksum(
                data.distance_lookup[from_node, to_node] * x[vehicle_id, from_node, to_node]
                for vehicle_id, from_node, to_node in x_keys
            )
        elif self.objective_mode == ObjectiveMode.VEHICLE_COST:
            objective = gp.quicksum(data.vehicles_by_id[vehicle_id].fixed_cost * z[vehicle_id]
                                    for vehicle_id in vehicles)
        else:  # pragma: no cover
            raise AssertionError(f"Unhandled objective mode: {self.objective_mode}")
        model.setObjective(objective, GRB.MINIMIZE)

        self.vars = {
            "x": x,
            "y": y,
            "z": z,
            "r": r,
            "lambda": lam,
            "a": a,
            "b": b,
            "theta": theta,
            "T": tardiness,
            "early_arrival": early,
            "x_keys": x_keys,
            "lambda_keys": lambda_keys,
            "big_m": big_m,
        }
        self.model = model
        return model

    def solve(self) -> tuple[Solution | None, MILPResult]:
        ensure_project_dirs()
        output_dir = MILP_OUTPUT_DIR / self.objective_mode.value
        output_dir.mkdir(parents=True, exist_ok=True)

        started = time.perf_counter()
        model = self.build_model()
        build_runtime = time.perf_counter() - started
        solve_started = time.perf_counter()
        model.optimize()
        solve_runtime = time.perf_counter() - solve_started
        runtime = time.perf_counter() - started

        solution = self.extract_solution() if model.SolCount > 0 else None
        evaluation = None
        if solution is not None:
            evaluation = evaluate_solution(solution, self.problem_data, self.objective_mode)
            self.write_outputs(solution, evaluation, output_dir)

        status = _status_name(model.Status)
        result = MILPResult(
            objective_mode=self.objective_mode.value,
            solver_status=status,
            sol_count=int(model.SolCount),
            mip_gap=float(model.MIPGap) if model.SolCount > 0 and math.isfinite(model.MIPGap) else None,
            objective_value=float(model.ObjVal) if model.SolCount > 0 else None,
            best_bound=float(model.ObjBound) if model.SolCount > 0 else None,
            runtime=runtime,
            build_runtime=build_runtime,
            solve_runtime=solve_runtime,
            feasible=bool(evaluation.feasible) if evaluation is not None else False,
            total_tardiness=evaluation.total_tardiness if evaluation is not None else None,
            total_travel_time=evaluation.total_travel_time if evaluation is not None else None,
            total_distance=evaluation.total_distance if evaluation is not None else None,
            vehicle_cost=evaluation.vehicle_cost if evaluation is not None else None,
            used_vehicle_count=evaluation.used_vehicle_count if evaluation is not None else None,
            output_dir=str(output_dir),
            validation_errors=list(evaluation.validation_errors) if evaluation is not None else [],
        )
        (output_dir / "summary.json").write_text(
            json.dumps(asdict(result), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return solution, result

    def extract_solution(self) -> Solution:
        data = self.problem_data
        x = self.vars["x"]
        z = self.vars["z"]
        routes: list[Route] = []

        for vehicle_id in data.vehicle_ids:
            vehicle = data.vehicles_by_id[vehicle_id]
            route = Route(
                vehicle_id=vehicle_id,
                depot_id=vehicle.start_depot,
                customers=[],
                end_depot=vehicle.start_depot,
            )
            if z[vehicle_id].X < 0.5:
                routes.append(route)
                continue
            current = vehicle.start_depot
            visited: set[str] = set()
            for _ in range(len(data.customer_ids) + 2):
                next_nodes = [
                    to_node
                    for from_node, to_node in self.arcs_by_vehicle[vehicle_id]
                    if from_node == current and x[vehicle_id, from_node, to_node].X > 0.5
                ]
                if not next_nodes:
                    break
                next_node = sorted(next_nodes)[0]
                if next_node in data.depot_ids:
                    route.end_depot = next_node
                    break
                if next_node in visited:
                    break
                visited.add(next_node)
                route.customers.append(next_node)
                current = next_node
            routes.append(route)
        return Solution(routes=routes, unassigned_customers=[])

    def write_outputs(self, solution: Solution, evaluation, output_dir: Path) -> None:
        solution_rows: list[dict[str, Any]] = []
        for route_eval in evaluation.route_evaluations:
            if not route_eval.customers:
                continue
            solution_rows.append(
                {
                    "vehicle_id": route_eval.vehicle_id,
                    "start_depot": route_eval.start_depot,
                    "customer_sequence": "|".join(route_eval.customers),
                    "end_depot": route_eval.end_depot,
                    "route_tardiness": route_eval.components.tardiness,
                    "route_travel_time": route_eval.components.travel_time,
                    "route_distance": route_eval.components.distance,
                    "route_vehicle_cost": route_eval.components.vehicle_cost,
                    "active_objective_value": route_eval.active_objective_value,
                }
            )
        pd.DataFrame(solution_rows).to_csv(
            output_dir / "best_solution.csv",
            index=False,
            encoding="utf-8-sig",
        )

        schedule_rows: list[dict[str, Any]] = []
        used_vehicle_ids = {route.vehicle_id for route in solution.used_routes()}
        for entry in evaluation.schedule:
            if entry.vehicle_id not in used_vehicle_ids:
                continue
            schedule_rows.append(
                {
                    "vehicle_id": entry.vehicle_id,
                    "sequence_no": entry.sequence_no,
                    "node_id": entry.node_id,
                    "arrival_time": minutes_to_hhmm(entry.arrival_time),
                    "waiting_time": entry.waiting_time,
                    "service_start": minutes_to_hhmm(entry.service_start),
                    "service_end": minutes_to_hhmm(entry.service_end),
                    "departure_time": minutes_to_hhmm(entry.departure_time),
                    "tardiness": entry.tardiness,
                    "cumulative_load": entry.cumulative_load,
                }
            )
        pd.DataFrame(schedule_rows).to_csv(
            output_dir / "best_schedule.csv",
            index=False,
            encoding="utf-8-sig",
        )

    def _vehicle_arcs(self, vehicle_id: str) -> list[tuple[str, str]]:
        data = self.problem_data
        home = data.vehicles_by_id[vehicle_id].start_depot
        arcs: list[tuple[str, str]] = [(home, customer_id) for customer_id in data.customer_ids]
        for from_customer in data.customer_ids:
            for to_node in data.customer_ids + data.depot_ids:
                if to_node != from_customer:
                    arcs.append((from_customer, to_node))
        return arcs

    def _arc_hours(self, vehicle_id: str, from_node: str) -> list[int]:
        vehicle = self.problem_data.vehicles_by_id[vehicle_id]
        if from_node in self.problem_data.depot_ids:
            return [departure_hour(vehicle.start_time)]
        latest_departure_hour = int((vehicle.start_time + vehicle.max_route_duration_min) // 60)
        return [
            hour
            for hour in self.problem_data.hours
            if departure_hour(vehicle.start_time) <= hour <= latest_departure_hour
        ]

    def _big_m(self) -> float:
        max_end = max(vehicle.end_time for vehicle in self.problem_data.vehicles_by_id.values())
        max_duration = max(vehicle.max_route_duration_min for vehicle in self.problem_data.vehicles_by_id.values())
        max_travel = max(self.problem_data.travel_time_lookup.values())
        max_service = max(node.service_time for node in self.problem_data.nodes.values())
        return max(10000.0, max_end + max_duration + max_travel + max_service + 1000.0)

def run_milp(
    objective: str | ObjectiveMode,
    time_limit: float = 60.0,
    mip_gap: float | None = 0.05,
    solution_limit: int | None = None,
    output_flag: int = 1,
) -> MILPResult:
    objective_mode = parse_objective_mode(objective)
    problem_data = ProblemData.from_files()
    solver = MILPSolver(
        problem_data=problem_data,
        objective_mode=objective_mode,
        time_limit=time_limit,
        mip_gap=mip_gap,
        solution_limit=solution_limit,
        output_flag=output_flag,
    )
    _, result = solver.solve()
    return result


def _status_name(status: int) -> str:
    if GRB is None:
        return str(status)
    names = {
        GRB.OPTIMAL: "OPTIMAL",
        GRB.INFEASIBLE: "INFEASIBLE",
        GRB.INF_OR_UNBD: "INF_OR_UNBD",
        GRB.UNBOUNDED: "UNBOUNDED",
        GRB.CUTOFF: "CUTOFF",
        GRB.ITERATION_LIMIT: "ITERATION_LIMIT",
        GRB.NODE_LIMIT: "NODE_LIMIT",
        GRB.TIME_LIMIT: "TIME_LIMIT",
        GRB.SOLUTION_LIMIT: "SOLUTION_LIMIT",
        GRB.INTERRUPTED: "INTERRUPTED",
        GRB.NUMERIC: "NUMERIC",
        GRB.SUBOPTIMAL: "SUBOPTIMAL",
    }
    return names.get(status, str(status))


def _optional_gap(value: str | None) -> float | None:
    if value is None or str(value).strip().lower() in {"", "none", "null"}:
        return None
    return float(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve TD-MDCVRPTW-FED with Gurobi MILP")
    parser.add_argument("--objective", choices=OBJECTIVE_CHOICES, default="TARDINESS")
    parser.add_argument("--time-limit", type=float, default=60.0)
    parser.add_argument("--mip-gap", type=str, default="0.05")
    parser.add_argument("--solution-limit", type=int, default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    result = run_milp(
        objective=args.objective,
        time_limit=args.time_limit,
        mip_gap=_optional_gap(args.mip_gap),
        solution_limit=args.solution_limit,
        output_flag=0 if args.quiet else 1,
    )
    print(pd.DataFrame([asdict(result)]).to_string(index=False))
    print(f"Wrote {result.output_dir}")


if __name__ == "__main__":
    main()
