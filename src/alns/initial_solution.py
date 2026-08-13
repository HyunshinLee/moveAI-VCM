from __future__ import annotations

from src.alns.repair_operators import regret2_insertion
from src.model.objective import ObjectiveMode
from src.model.problem_data import ProblemData
from src.model.solution import Route, Solution


def build_empty_solution(problem_data: ProblemData) -> Solution:
    routes = [
        Route(
            vehicle_id=vehicle_id,
            depot_id=problem_data.vehicles_by_id[vehicle_id].start_depot,
            customers=[],
            end_depot=problem_data.vehicles_by_id[vehicle_id].start_depot,
        )
        for vehicle_id in problem_data.vehicle_ids
    ]
    return Solution(routes=routes, unassigned_customers=[])


def build_initial_solution(
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
) -> Solution:
    solution = build_empty_solution(problem_data)
    customers_by_depot: dict[str, list[str]] = {depot_id: [] for depot_id in problem_data.depot_ids}
    for customer_id in problem_data.customer_ids:
        depot_id = problem_data.assigned_depot(customer_id)
        customers_by_depot.setdefault(depot_id, []).append(customer_id)

    for depot_id in problem_data.depot_ids:
        cluster = sorted(
            customers_by_depot.get(depot_id, []),
            key=lambda customer_id: (
                problem_data.distance(depot_id, customer_id),
                problem_data.nodes[customer_id].tw_end,
                customer_id,
            ),
        )
        route_indices = [
            idx for idx, route in enumerate(solution.routes) if route.depot_id == depot_id
        ]
        solution = regret2_insertion(
            solution,
            cluster,
            problem_data,
            objective_mode,
            allowed_route_indices=route_indices,
        )

    if solution.unassigned_customers:
        remaining = list(solution.unassigned_customers)
        solution.unassigned_customers = []
        solution = regret2_insertion(
            solution,
            remaining,
            problem_data,
            objective_mode,
            allowed_route_indices=None,
        )
    return solution
