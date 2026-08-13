from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.alns.evaluation import evaluate_route, optimize_end_depots
from src.model.objective import ObjectiveMode
from src.model.problem_data import ProblemData, TimeWindowMode
from src.model.solution import Route, Solution


@dataclass(frozen=True)
class InsertionCandidate:
    customer_id: str
    route_index: int
    position: int
    delta: float
    route: Route
    end_depot: str

    def sort_key(self) -> tuple:
        return (
            round(self.delta, 9),
            self.customer_id,
            self.route.vehicle_id,
            self.position,
            self.end_depot,
        )


def greedy_insert(
    solution: Solution,
    removed_customers: Iterable[str],
    problem_data: ProblemData,
    objective_mode: ObjectiveMode = ObjectiveMode.DISTANCE,
) -> Solution:
    return greedy_insertion(solution, removed_customers, problem_data, objective_mode)


def greedy_insertion(
    solution: Solution,
    removed_customers: Iterable[str],
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    allowed_route_indices: list[int] | None = None,
) -> Solution:
    working = solution.copy()
    remaining = sorted(set(removed_customers))
    while remaining:
        candidates = [
            candidate
            for customer_id in remaining
            for candidate in insertion_candidates(
                working,
                customer_id,
                problem_data,
                objective_mode,
                allowed_route_indices=allowed_route_indices,
            )
        ]
        if not candidates:
            working.unassigned_customers.extend(remaining)
            break
        best = min(candidates, key=lambda item: item.sort_key())
        apply_insertion_candidate(working, best)
        remaining.remove(best.customer_id)
    return optimize_end_depots(working, problem_data, objective_mode)


def regret2_insertion(
    solution: Solution,
    removed_customers: Iterable[str],
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    allowed_route_indices: list[int] | None = None,
) -> Solution:
    working = solution.copy()
    remaining = sorted(set(removed_customers))
    while remaining:
        choices: list[tuple[float, InsertionCandidate]] = []
        missing: list[str] = []
        for customer_id in remaining:
            candidates = sorted(
                insertion_candidates(
                    working,
                    customer_id,
                    problem_data,
                    objective_mode,
                    allowed_route_indices=allowed_route_indices,
                ),
                key=lambda item: item.sort_key(),
            )
            if not candidates:
                missing.append(customer_id)
                continue
            best_delta = candidates[0].delta
            second_delta = candidates[1].delta if len(candidates) > 1 else best_delta
            choices.append((second_delta - best_delta, candidates[0]))

        if not choices:
            working.unassigned_customers.extend(sorted(set(remaining)))
            break

        _, best_candidate = max(
            choices,
            key=lambda item: (
                round(item[0], 9),
                -round(item[1].delta, 9),
                _reverse_lex_key(item[1].customer_id),
            ),
        )
        apply_insertion_candidate(working, best_candidate)
        remaining.remove(best_candidate.customer_id)
        for customer_id in missing:
            if customer_id not in remaining:
                remaining.append(customer_id)
    return optimize_end_depots(working, problem_data, objective_mode)


def time_window_aware_insertion(
    solution: Solution,
    removed_customers: Iterable[str],
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
) -> Solution:
    ordered = sorted(
        set(removed_customers),
        key=lambda customer_id: (
            problem_data.nodes[customer_id].tw_end,
            problem_data.nodes[customer_id].tw_end - problem_data.nodes[customer_id].tw_start,
            customer_id,
        ),
    )
    return greedy_insertion(solution, ordered, problem_data, objective_mode)


def depot_vehicle_aware_insertion(
    solution: Solution,
    removed_customers: Iterable[str],
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
) -> Solution:
    return regret2_insertion(solution, removed_customers, problem_data, objective_mode)


def insertion_candidates(
    solution: Solution,
    customer_id: str,
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
    allowed_route_indices: list[int] | None = None,
) -> list[InsertionCandidate]:
    route_indices = allowed_route_indices if allowed_route_indices is not None else list(range(len(solution.routes)))
    candidates: list[InsertionCandidate] = []
    for route_index in route_indices:
        route = solution.routes[route_index]
        old_eval = evaluate_route(route, problem_data, objective_mode, choose_best_end_depot=True)
        for position in range(len(route.customers) + 1):
            new_route = route.copy()
            new_route.customers.insert(position, customer_id)
            new_eval = evaluate_route(new_route, problem_data, objective_mode, choose_best_end_depot=True)
            if not new_eval.feasible:
                continue
            new_route.end_depot = new_eval.end_depot
            candidates.append(
                InsertionCandidate(
                    customer_id=customer_id,
                    route_index=route_index,
                    position=position,
                    delta=new_eval.active_objective_value - old_eval.active_objective_value,
                    route=new_route,
                    end_depot=new_eval.end_depot,
                )
            )
    return candidates


def apply_insertion_candidate(solution: Solution, candidate: InsertionCandidate) -> None:
    solution.routes[candidate.route_index] = candidate.route.copy()
    solution.routes[candidate.route_index].end_depot = candidate.end_depot
    solution.unassigned_customers = [
        customer_id for customer_id in solution.unassigned_customers if customer_id != candidate.customer_id
    ]


def repair_by_name(
    name: str,
    solution: Solution,
    removed_customers: Iterable[str],
    problem_data: ProblemData,
    objective_mode: ObjectiveMode,
) -> Solution:
    if name == "greedy":
        return greedy_insertion(solution, removed_customers, problem_data, objective_mode)
    if name == "regret2":
        return regret2_insertion(solution, removed_customers, problem_data, objective_mode)
    if name == "tw_aware":
        return time_window_aware_insertion(solution, removed_customers, problem_data, objective_mode)
    if name == "depot_vehicle":
        return depot_vehicle_aware_insertion(solution, removed_customers, problem_data, objective_mode)
    raise ValueError(f"Unknown repair operator: {name}")


def active_repair_operators(
    objective_mode: ObjectiveMode,
    time_window_mode: TimeWindowMode,
    configured: list[str] | None = None,
) -> list[str]:
    if configured:
        return configured
    names = ["greedy", "regret2", "depot_vehicle"]
    if objective_mode == ObjectiveMode.TARDINESS or time_window_mode == TimeWindowMode.HARD:
        names.append("tw_aware")
    return names


def _reverse_lex_key(value: str) -> tuple[int, ...]:
    return tuple(-ord(char) for char in value)
