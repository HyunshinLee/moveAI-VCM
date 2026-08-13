from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import pandas as pd

from src.model.objective import ObjectiveComponents, ObjectiveMode, get_active_objective_value
from src.model.problem_data import ProblemData, TimeWindowMode
from src.model.solution import Route, Solution
from src.utils.time_utils import departure_hour


@dataclass(frozen=True)
class ScheduleEntry:
    vehicle_id: str
    sequence_no: int
    node_id: str
    arrival_time: float
    waiting_time: float
    service_start: float
    service_end: float
    departure_time: float
    tardiness: float
    cumulative_load: float


@dataclass(frozen=True)
class RouteEvaluation:
    vehicle_id: str
    start_depot: str
    end_depot: str
    customers: tuple[str, ...]
    feasible: bool
    components: ObjectiveComponents
    waiting_time: float
    capacity_violation: float
    time_window_violation: float
    end_time_violation: float
    duration_violation: float
    route_duration: float
    active_objective_value: float
    schedule: tuple[ScheduleEntry, ...] = field(default_factory=tuple)
    validation_errors: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SolutionEvaluation:
    feasible: bool
    components: ObjectiveComponents
    active_objective_value: float
    route_evaluations: tuple[RouteEvaluation, ...]
    schedule: tuple[ScheduleEntry, ...]
    validation_errors: tuple[str, ...]
    canonical_signature: tuple

    @property
    def total_tardiness(self) -> float:
        return self.components.tardiness

    @property
    def total_travel_time(self) -> float:
        return self.components.travel_time

    @property
    def total_distance(self) -> float:
        return self.components.distance

    @property
    def vehicle_cost(self) -> float:
        return self.components.vehicle_cost

    @property
    def used_vehicle_count(self) -> int:
        return self.components.used_vehicle_count


class TravelTimeLookup:
    def __init__(self, td_od_matrix: pd.DataFrame):
        self._lookup = {
            (str(row.from_node), str(row.to_node), int(row.hour)): float(row.travel_time_min)
            for row in td_od_matrix.itertuples(index=False)
        }

    @classmethod
    def from_csv(cls, path: str) -> "TravelTimeLookup":
        return cls(pd.read_csv(path, dtype={"from_node": str, "to_node": str}))

    def travel_time(self, from_node: str, to_node: str, departure_min: int | float) -> float:
        return self._lookup[(from_node, to_node, departure_hour(departure_min))]


def evaluate_route(
    route: Route,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    choose_best_end_depot: bool = True,
) -> RouteEvaluation:
    end_depots = (
        problem_data.depot_ids
        if choose_best_end_depot and route.used
        else [route.end_depot or route.depot_id]
    )
    candidates = [
        _evaluate_route_with_fixed_end(route, problem_data, objective_mode, end_depot)
        for end_depot in end_depots
    ]
    feasible_candidates = [candidate for candidate in candidates if candidate.feasible]
    pool = feasible_candidates or candidates
    return min(
        pool,
        key=lambda item: (
            get_active_objective_value(item.components, objective_mode),
            item.end_depot,
        ),
    )


def _evaluate_route_with_fixed_end(
    route: Route,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    end_depot: str,
) -> RouteEvaluation:
    errors: list[str] = []
    vehicle = problem_data.vehicles_by_id.get(route.vehicle_id)
    if vehicle is None:
        raise ValueError(f"Unknown vehicle_id: {route.vehicle_id}")
    if route.depot_id != vehicle.start_depot:
        errors.append(f"vehicle {route.vehicle_id} start depot mismatch")
    if route.depot_id not in problem_data.depot_ids:
        errors.append(f"invalid start depot {route.depot_id}")
    if end_depot not in problem_data.depot_ids:
        errors.append(f"invalid end depot {end_depot}")

    total_demand = sum(problem_data.customer_demand(customer_id) for customer_id in route.customers)
    capacity_violation = max(0.0, total_demand - vehicle.capacity)
    if capacity_violation > 0:
        errors.append(f"capacity violation {capacity_violation:.3f}")

    if not route.used:
        components = ObjectiveComponents()
        return RouteEvaluation(
            vehicle_id=route.vehicle_id,
            start_depot=route.depot_id,
            end_depot=end_depot,
            customers=tuple(),
            feasible=not errors,
            components=components,
            waiting_time=0.0,
            capacity_violation=capacity_violation,
            time_window_violation=0.0,
            end_time_violation=0.0,
            duration_violation=0.0,
            route_duration=0.0,
            active_objective_value=get_active_objective_value(components, objective_mode),
            schedule=tuple(),
            validation_errors=tuple(errors),
        )

    schedule: list[ScheduleEntry] = []
    cumulative_load = total_demand
    current_node = route.depot_id
    current_time = float(vehicle.start_time)
    sequence_no = 0
    schedule.append(
        ScheduleEntry(
            vehicle_id=route.vehicle_id,
            sequence_no=sequence_no,
            node_id=route.depot_id,
            arrival_time=current_time,
            waiting_time=0.0,
            service_start=current_time,
            service_end=current_time,
            departure_time=current_time,
            tardiness=0.0,
            cumulative_load=cumulative_load,
        )
    )

    total_travel_time = 0.0
    total_distance = 0.0
    total_waiting = 0.0
    total_tardiness = 0.0

    for customer_id in route.customers:
        if customer_id not in problem_data.nodes:
            errors.append(f"unknown customer {customer_id}")
            continue
        customer = problem_data.nodes[customer_id]
        if customer.node_type != "CUSTOMER":
            errors.append(f"non-customer node in route {customer_id}")
            continue

        travel_time = problem_data.travel_time(current_node, customer_id, current_time)
        distance = problem_data.distance(current_node, customer_id)
        arrival_time = current_time + travel_time
        waiting_time = max(0.0, customer.tw_start - arrival_time)
        service_start = max(arrival_time, float(customer.tw_start))
        tardiness = max(0.0, service_start - customer.tw_end) * customer.rho
        service_end = service_start + customer.service_time
        cumulative_load -= customer.demand

        total_travel_time += travel_time
        total_distance += distance
        total_waiting += waiting_time
        total_tardiness += tardiness
        sequence_no += 1
        schedule.append(
            ScheduleEntry(
                vehicle_id=route.vehicle_id,
                sequence_no=sequence_no,
                node_id=customer_id,
                arrival_time=arrival_time,
                waiting_time=waiting_time,
                service_start=service_start,
                service_end=service_end,
                departure_time=service_end,
                tardiness=tardiness,
                cumulative_load=max(0.0, cumulative_load),
            )
        )
        current_node = customer_id
        current_time = service_end

    end_travel_time = problem_data.travel_time(current_node, end_depot, current_time)
    end_distance = problem_data.distance(current_node, end_depot)
    end_arrival = current_time + end_travel_time
    total_travel_time += end_travel_time
    total_distance += end_distance
    sequence_no += 1
    schedule.append(
        ScheduleEntry(
            vehicle_id=route.vehicle_id,
            sequence_no=sequence_no,
            node_id=end_depot,
            arrival_time=end_arrival,
            waiting_time=0.0,
            service_start=end_arrival,
            service_end=end_arrival,
            departure_time=end_arrival,
            tardiness=0.0,
            cumulative_load=0.0,
        )
    )

    route_duration = end_arrival - vehicle.start_time
    time_window_violation = total_tardiness if problem_data.time_window_mode == TimeWindowMode.HARD else 0.0
    end_time_violation = max(0.0, end_arrival - vehicle.end_time)
    duration_violation = max(0.0, route_duration - vehicle.max_route_duration_min)

    if time_window_violation > 0:
        errors.append(f"time window violation {time_window_violation:.3f}")
    if end_time_violation > 0:
        errors.append(f"vehicle end time violation {end_time_violation:.3f}")
    if duration_violation > 0:
        errors.append(f"route duration violation {duration_violation:.3f}")

    components = ObjectiveComponents(
        tardiness=total_tardiness,
        travel_time=total_travel_time,
        distance=total_distance,
        vehicle_cost=vehicle.fixed_cost,
        used_vehicle_count=1,
    )
    return RouteEvaluation(
        vehicle_id=route.vehicle_id,
        start_depot=route.depot_id,
        end_depot=end_depot,
        customers=tuple(route.customers),
        feasible=not errors,
        components=components,
        waiting_time=total_waiting,
        capacity_violation=capacity_violation,
        time_window_violation=time_window_violation,
        end_time_violation=end_time_violation,
        duration_violation=duration_violation,
        route_duration=route_duration,
        active_objective_value=get_active_objective_value(components, objective_mode),
        schedule=tuple(schedule),
        validation_errors=tuple(errors),
    )


def optimize_end_depots(
    solution: Solution,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
) -> Solution:
    for route in solution.routes:
        route_eval = evaluate_route(route, problem_data, objective_mode, choose_best_end_depot=True)
        route.end_depot = route_eval.end_depot
    return solution


def evaluate_solution(
    solution: Solution,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    update_end_depots: bool = True,
) -> SolutionEvaluation:
    if update_end_depots:
        optimize_end_depots(solution, problem_data, objective_mode)

    route_evaluations: list[RouteEvaluation] = []
    components = ObjectiveComponents()
    errors: list[str] = []
    schedule: list[ScheduleEntry] = []

    assigned_customers: list[str] = []
    for route in sorted(solution.routes, key=lambda item: item.vehicle_id):
        route_eval = evaluate_route(route, problem_data, objective_mode, choose_best_end_depot=False)
        route_evaluations.append(route_eval)
        components += route_eval.components
        assigned_customers.extend(route.customers)
        schedule.extend(route_eval.schedule)
        if not route_eval.feasible:
            errors.extend(f"{route.vehicle_id}: {error}" for error in route_eval.validation_errors)

    expected = set(problem_data.customer_ids)
    assigned = set(assigned_customers)
    duplicate_customers = sorted(
        customer_id for customer_id in assigned if assigned_customers.count(customer_id) > 1
    )
    missing_customers = sorted(expected.difference(assigned))
    unknown_customers = sorted(assigned.difference(expected))
    if duplicate_customers:
        errors.append(f"duplicate customers: {duplicate_customers}")
    if missing_customers:
        errors.append(f"missing customers: {missing_customers}")
    if unknown_customers:
        errors.append(f"unknown customers: {unknown_customers}")
    if solution.unassigned_customers:
        errors.append(f"unassigned customers: {sorted(solution.unassigned_customers)}")

    active_value = get_active_objective_value(components, objective_mode)
    evaluation = SolutionEvaluation(
        feasible=not errors,
        components=components,
        active_objective_value=active_value,
        route_evaluations=tuple(route_evaluations),
        schedule=tuple(schedule),
        validation_errors=tuple(errors),
        canonical_signature=solution.canonical_signature(),
    )
    solution.feasible = evaluation.feasible
    solution.objective_value = active_value
    solution.evaluation = evaluation
    return evaluation


def assert_objective_consistency(
    evaluation: SolutionEvaluation,
    objective_mode: ObjectiveMode,
    tolerance: float = 1e-6,
) -> None:
    expected = get_active_objective_value(evaluation.components, objective_mode)
    if abs(evaluation.active_objective_value - expected) > tolerance:
        raise ValueError(
            f"Active objective mismatch for {objective_mode.value}: "
            f"{evaluation.active_objective_value} != {expected}"
        )


def evaluate_solution_cost(
    solution: Solution,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
) -> float:
    return evaluate_solution(solution, problem_data, objective_mode).active_objective_value


def customer_route_positions(solution: Solution) -> dict[str, tuple[int, int]]:
    positions: dict[str, tuple[int, int]] = {}
    for route_idx, route in enumerate(solution.routes):
        for customer_idx, customer_id in enumerate(route.customers):
            positions[customer_id] = (route_idx, customer_idx)
    return positions


def iter_used_route_evaluations(evaluation: SolutionEvaluation) -> Iterable[RouteEvaluation]:
    return (route_eval for route_eval in evaluation.route_evaluations if route_eval.customers)
