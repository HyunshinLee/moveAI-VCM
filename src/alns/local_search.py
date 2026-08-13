from __future__ import annotations

from itertools import combinations

from src.alns.evaluation import evaluate_route, evaluate_solution, optimize_end_depots
from src.model.objective import ObjectiveMode
from src.model.problem_data import ProblemData
from src.model.solution import Solution


def local_search(
    solution: Solution,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    tolerance: float = 1e-6,
    max_moves: int = 10,
    max_candidates_per_operator: int = 500,
) -> Solution:
    working = optimize_end_depots(solution.copy(), problem_data, objective_mode)
    moves = 0
    while moves < max_moves:
        improved = (
            relocate_first_improvement(working, problem_data, objective_mode, tolerance, max_candidates_per_operator)
            or swap_first_improvement(working, problem_data, objective_mode, tolerance, max_candidates_per_operator)
            or two_opt_first_improvement(working, problem_data, objective_mode, tolerance, max_candidates_per_operator)
            or two_opt_star_first_improvement(working, problem_data, objective_mode, tolerance, max_candidates_per_operator)
        )
        if not improved:
            break
        moves += 1
    return optimize_end_depots(working, problem_data, objective_mode)


def relocate_first_improvement(
    solution: Solution,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    tolerance: float,
    max_candidates: int,
) -> bool:
    current_eval = evaluate_solution(solution.copy(), problem_data, objective_mode)
    current_value = current_eval.active_objective_value
    checked = 0
    for from_idx, from_route in enumerate(solution.routes):
        for customer_pos, customer_id in enumerate(list(from_route.customers)):
            for to_idx, to_route in enumerate(solution.routes):
                for insert_pos in range(len(to_route.customers) + 1):
                    checked += 1
                    if checked > max_candidates:
                        return False
                    if from_idx == to_idx and insert_pos in {customer_pos, customer_pos + 1}:
                        continue
                    candidate = solution.copy()
                    moved = candidate.routes[from_idx].customers.pop(customer_pos)
                    adjusted_pos = insert_pos
                    if from_idx == to_idx and insert_pos > customer_pos:
                        adjusted_pos -= 1
                    candidate.routes[to_idx].customers.insert(adjusted_pos, moved)
                    if _accept_improving_move(candidate, solution, problem_data, objective_mode, current_value, tolerance):
                        return True
    return False


def swap_first_improvement(
    solution: Solution,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    tolerance: float,
    max_candidates: int,
) -> bool:
    current_eval = evaluate_solution(solution.copy(), problem_data, objective_mode)
    current_value = current_eval.active_objective_value
    positions = [
        (route_idx, customer_idx)
        for route_idx, route in enumerate(solution.routes)
        for customer_idx, _ in enumerate(route.customers)
    ]
    for (route_a, pos_a), (route_b, pos_b) in combinations(positions, 2):
        if max_candidates <= 0:
            return False
        max_candidates -= 1
        candidate = solution.copy()
        candidate.routes[route_a].customers[pos_a], candidate.routes[route_b].customers[pos_b] = (
            candidate.routes[route_b].customers[pos_b],
            candidate.routes[route_a].customers[pos_a],
        )
        if _accept_improving_move(candidate, solution, problem_data, objective_mode, current_value, tolerance):
            return True
    return False


def two_opt_first_improvement(
    solution: Solution,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    tolerance: float,
    max_candidates: int,
) -> bool:
    current_eval = evaluate_solution(solution.copy(), problem_data, objective_mode)
    current_value = current_eval.active_objective_value
    for route_idx, route in enumerate(solution.routes):
        if len(route.customers) < 4:
            continue
        for start in range(len(route.customers) - 2):
            for end in range(start + 2, len(route.customers)):
                if max_candidates <= 0:
                    return False
                max_candidates -= 1
                candidate = solution.copy()
                candidate.routes[route_idx].customers[start : end + 1] = reversed(
                    candidate.routes[route_idx].customers[start : end + 1]
                )
                if _accept_improving_move(candidate, solution, problem_data, objective_mode, current_value, tolerance):
                    return True
    return False


def two_opt_star_first_improvement(
    solution: Solution,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    tolerance: float,
    max_candidates: int,
) -> bool:
    current_eval = evaluate_solution(solution.copy(), problem_data, objective_mode)
    current_value = current_eval.active_objective_value
    route_indices = [idx for idx, route in enumerate(solution.routes) if route.customers]
    for left_idx, right_idx in combinations(route_indices, 2):
        left = solution.routes[left_idx]
        right = solution.routes[right_idx]
        for left_cut in range(1, len(left.customers) + 1):
            for right_cut in range(1, len(right.customers) + 1):
                if max_candidates <= 0:
                    return False
                max_candidates -= 1
                candidate = solution.copy()
                left_head = candidate.routes[left_idx].customers[:left_cut]
                left_tail = candidate.routes[left_idx].customers[left_cut:]
                right_head = candidate.routes[right_idx].customers[:right_cut]
                right_tail = candidate.routes[right_idx].customers[right_cut:]
                candidate.routes[left_idx].customers = left_head + right_tail
                candidate.routes[right_idx].customers = right_head + left_tail
                if _accept_improving_move(candidate, solution, problem_data, objective_mode, current_value, tolerance):
                    return True
    return False


def route_elimination(
    solution: Solution,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    tolerance: float = 1e-6,
) -> Solution:
    from src.alns.destroy_operators import remove_customers
    from src.alns.repair_operators import regret2_insertion

    current_eval = evaluate_solution(solution.copy(), problem_data, objective_mode)
    best = solution.copy()
    for route in sorted(solution.used_routes(), key=lambda item: item.vehicle_id):
        removed = list(route.customers)
        partial = remove_customers(solution, removed)
        route_index = next(
            idx for idx, candidate_route in enumerate(partial.routes) if candidate_route.vehicle_id == route.vehicle_id
        )
        partial.routes[route_index].customers = []
        allowed_routes = [
            idx for idx, candidate_route in enumerate(partial.routes) if candidate_route.vehicle_id != route.vehicle_id
        ]
        candidate = regret2_insertion(
            partial,
            removed,
            problem_data,
            objective_mode,
            allowed_route_indices=allowed_routes,
        )
        candidate_eval = evaluate_solution(candidate, problem_data, objective_mode)
        if candidate_eval.feasible and candidate_eval.active_objective_value < current_eval.active_objective_value - tolerance:
            best = candidate
            current_eval = candidate_eval
    return best


def _accept_improving_move(
    candidate: Solution,
    target: Solution,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    current_value: float,
    tolerance: float,
) -> bool:
    candidate_eval = evaluate_solution(candidate, problem_data, objective_mode)
    if not candidate_eval.feasible:
        return False
    if candidate_eval.active_objective_value < current_value - tolerance:
        target.routes = candidate.routes
        target.unassigned_customers = candidate.unassigned_customers
        target.objective_value = candidate_eval.active_objective_value
        target.feasible = True
        target.evaluation = candidate_eval
        return True
    return False
