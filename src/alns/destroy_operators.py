from __future__ import annotations

import random
from math import hypot
from typing import Iterable

from src.alns.evaluation import customer_route_positions, evaluate_solution
from src.model.objective import ObjectiveMode
from src.model.problem_data import ProblemData
from src.model.solution import Solution


def random_removal(solution, degree: int):
    rng = random.Random()
    customers = solution.assigned_customers()
    removed = rng.sample(customers, min(degree, len(customers)))
    return remove_customers(solution, removed), removed


def remove_customers(solution: Solution, customers: Iterable[str]) -> Solution:
    removed_set = set(customers)
    working = solution.copy()
    for route in working.routes:
        route.customers = [customer_id for customer_id in route.customers if customer_id not in removed_set]
    working.unassigned_customers = sorted(set(working.unassigned_customers).union(removed_set))
    return working


def random_removal_operator(solution: Solution, degree: int, rng: random.Random) -> tuple[Solution, list[str]]:
    customers = sorted(solution.assigned_customers())
    removed = rng.sample(customers, min(degree, len(customers)))
    return remove_customers(solution, removed), sorted(removed)


def worst_removal_operator(
    solution: Solution,
    degree: int,
    rng: random.Random,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
) -> tuple[Solution, list[str]]:
    current_eval = evaluate_solution(solution.copy(), problem_data, objective_mode)
    savings: list[tuple[float, str]] = []
    for customer_id in sorted(solution.assigned_customers()):
        candidate = remove_customers(solution, [customer_id])
        candidate.unassigned_customers = []
        candidate_eval = evaluate_solution(candidate, problem_data, objective_mode)
        saving = current_eval.active_objective_value - candidate_eval.active_objective_value
        savings.append((saving, customer_id))
    savings.sort(key=lambda item: (-round(item[0], 9), item[1]))
    removed = [customer_id for _, customer_id in savings[:degree]]
    return remove_customers(solution, removed), removed


def shaw_removal_operator(
    solution: Solution,
    degree: int,
    rng: random.Random,
    problem_data: ProblemData,
) -> tuple[Solution, list[str]]:
    customers = sorted(solution.assigned_customers())
    if not customers:
        return solution.copy(), []
    seed = rng.choice(customers)
    positions = customer_route_positions(solution)
    related = sorted(
        (customer_id for customer_id in customers if customer_id != seed),
        key=lambda customer_id: (
            _relatedness(seed, customer_id, positions, problem_data),
            customer_id,
        ),
    )
    removed = [seed] + related[: max(0, degree - 1)]
    return remove_customers(solution, removed), sorted(removed)


def tardiness_removal_operator(
    solution: Solution,
    degree: int,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
) -> tuple[Solution, list[str]]:
    evaluation = evaluate_solution(solution.copy(), problem_data, objective_mode)
    scores: dict[str, float] = {}
    for entry in evaluation.schedule:
        if entry.node_id in problem_data.customer_ids:
            scores[entry.node_id] = max(scores.get(entry.node_id, 0.0), entry.tardiness)
    ranked = sorted(scores.items(), key=lambda item: (-round(item[1], 9), item[0]))
    removed = [customer_id for customer_id, _ in ranked[:degree]]
    return remove_customers(solution, removed), removed


def route_removal_operator(
    solution: Solution,
    degree: int,
    rng: random.Random,
) -> tuple[Solution, list[str]]:
    used_routes = [route for route in solution.routes if route.customers]
    if not used_routes:
        return solution.copy(), []
    route = rng.choice(sorted(used_routes, key=lambda item: item.vehicle_id))
    removed = list(route.customers)
    if len(removed) > degree:
        removed = removed[:degree]
    return remove_customers(solution, removed), removed


def destroy_by_name(
    name: str,
    solution: Solution,
    degree: int,
    rng: random.Random,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
) -> tuple[Solution, list[str]]:
    if name == "random":
        return random_removal_operator(solution, degree, rng)
    if name == "worst":
        return worst_removal_operator(solution, degree, rng, problem_data, objective_mode)
    if name == "shaw":
        return shaw_removal_operator(solution, degree, rng, problem_data)
    if name == "tardiness":
        return tardiness_removal_operator(solution, degree, problem_data, objective_mode)
    if name == "route":
        return route_removal_operator(solution, degree, rng)
    raise ValueError(f"Unknown destroy operator: {name}")


def active_destroy_operators(
    objective_mode: ObjectiveMode,
    configured: list[str] | None = None,
) -> list[str]:
    if configured:
        return configured
    if objective_mode == ObjectiveMode.TARDINESS:
        return ["random", "worst", "shaw", "tardiness", "route"]
    if objective_mode == ObjectiveMode.VEHICLE_COST:
        return ["random", "route", "worst"]
    return ["random", "worst", "shaw", "route"]


def _relatedness(
    left_customer: str,
    right_customer: str,
    positions: dict[str, tuple[int, int]],
    problem_data: ProblemData,
) -> float:
    left = problem_data.nodes[left_customer]
    right = problem_data.nodes[right_customer]
    spatial = hypot(left.latitude - right.latitude, left.longitude - right.longitude) * 100.0
    tw_similarity = abs(left.tw_start - right.tw_start) / 60.0 + abs(left.tw_end - right.tw_end) / 60.0
    demand_similarity = abs(left.demand - right.demand)
    same_route_penalty = 0.0 if positions.get(left_customer, (-1, -1))[0] == positions.get(right_customer, (-2, -2))[0] else 10.0
    return spatial + tw_similarity + demand_similarity + same_route_penalty
