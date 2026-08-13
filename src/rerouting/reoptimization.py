from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

import pandas as pd

from src.alns.evaluation import SolutionEvaluation, evaluate_solution
from src.alns.local_search import local_search
from src.model.objective import ObjectiveMode
from src.model.problem_data import ProblemData
from src.model.solution import Solution


@dataclass(frozen=True)
class StrategyMetrics:
    tardiness_min: float
    travel_time_min: float
    distance_km: float
    vehicle_cost: float
    used_vehicle_count: int
    changed_positions: int
    reassigned_customers: int
    new_trucks: int
    feasible: bool


@dataclass(frozen=True)
class StrategyResult:
    strategy: str
    solution: Solution
    evaluation: SolutionEvaluation
    metrics: StrategyMetrics
    physical_paths: dict[str, list[dict[str, Any]]]


def problem_data_with_updated_network(
    base: ProblemData,
    td_od_matrix: pd.DataFrame,
    td_paths: pd.DataFrame,
) -> ProblemData:
    travel_lookup = {
        (str(row.from_node), str(row.to_node), int(row.hour)): float(row.travel_time_min)
        for row in td_od_matrix.itertuples(index=False)
    }
    distance_lookup: dict[tuple[str, str], float] = {}
    for row in td_od_matrix.sort_values("hour").itertuples(index=False):
        distance_lookup.setdefault((str(row.from_node), str(row.to_node)), float(row.distance_km))
    return replace(
        base,
        td_od_matrix=td_od_matrix,
        td_paths=td_paths,
        travel_time_lookup=travel_lookup,
        distance_lookup=distance_lookup,
        hours=sorted(map(int, td_od_matrix["hour"].unique())),
    )


class ReschedulingEngine:
    """Compare detour, visit-sequence reroute, and multi-new-truck alternatives."""

    def __init__(self, initial_problem: ProblemData, updated_problem: ProblemData) -> None:
        self.initial_problem = initial_problem
        self.updated_problem = updated_problem

    @staticmethod
    def _assignment(solution: Solution) -> tuple[dict[str, str], dict[str, int]]:
        owner, position = {}, {}
        for route in solution.routes:
            for index, customer in enumerate(route.customers):
                owner[customer], position[customer] = route.vehicle_id, index
        return owner, position

    def _result(self, name: str, solution: Solution, initial: Solution) -> StrategyResult:
        evaluation = evaluate_solution(solution, self.updated_problem, ObjectiveMode.TARDINESS)
        old_owner, old_position = self._assignment(initial)
        new_owner, new_position = self._assignment(solution)
        original_used = {route.vehicle_id for route in initial.used_routes()}
        metrics = StrategyMetrics(
            tardiness_min=evaluation.total_tardiness,
            travel_time_min=evaluation.total_travel_time,
            distance_km=evaluation.total_distance,
            vehicle_cost=evaluation.vehicle_cost,
            used_vehicle_count=evaluation.used_vehicle_count,
            changed_positions=sum(old_position.get(c) != p for c, p in new_position.items()),
            reassigned_customers=sum(old_owner.get(c) != v for c, v in new_owner.items()),
            new_trucks=sum(route.used and route.vehicle_id not in original_used for route in solution.routes),
            feasible=evaluation.feasible,
        )
        return StrategyResult(name, solution, evaluation, metrics, self._expand_paths(evaluation))

    def _expand_paths(self, evaluation: SolutionEvaluation) -> dict[str, list[dict[str, Any]]]:
        paths = self.updated_problem.td_paths
        if paths is None:
            return {}
        lookup = {
            (str(row.from_node), str(row.to_node), int(row.hour)): row
            for row in paths.itertuples(index=False)
        }
        result: dict[str, list[dict[str, Any]]] = {}
        for route_eval in evaluation.route_evaluations:
            legs: list[dict[str, Any]] = []
            for before, after in zip(route_eval.schedule[:-1], route_eval.schedule[1:]):
                hour = self.updated_problem.lookup_hour(before.departure_time)
                row = lookup.get((before.node_id, after.node_id, hour))
                if row is not None:
                    legs.append({
                        "from_node": before.node_id, "to_node": after.node_id, "hour": hour,
                        "path_nodes": str(row.path_nodes).split("|"),
                        "path_edges": str(row.path_edges).split("|"),
                    })
            if legs:
                result[route_eval.vehicle_id] = legs
        return result

    def detour(self, initial: Solution) -> StrategyResult:
        return self._result("DETOUR", initial.copy(), initial)

    def reroute(self, initial: Solution, *, max_moves: int = 20) -> StrategyResult:
        candidate = local_search(
            initial.copy(), self.updated_problem, ObjectiveMode.TARDINESS,
            tolerance=1e-6, max_moves=max_moves,
        )
        return self._result("REROUTE", candidate, initial)

    def new_truck(self, initial: Solution, *, max_new_trucks: int = 3) -> StrategyResult:
        best = initial.copy()
        best_eval = evaluate_solution(best, self.updated_problem, ObjectiveMode.TARDINESS)
        unused = [route.vehicle_id for route in initial.routes if not route.used]
        for vehicle_id in unused[:max_new_trucks]:
            improved = True
            while improved:
                improved = False
                move_best: Solution | None = None
                move_eval: SolutionEvaluation | None = None
                for source in best.used_routes():
                    if source.vehicle_id == vehicle_id:
                        continue
                    for customer in list(source.customers):
                        trial = best.copy()
                        trial_source = next(r for r in trial.routes if r.vehicle_id == source.vehicle_id)
                        trial_target = next(r for r in trial.routes if r.vehicle_id == vehicle_id)
                        trial_source.customers.remove(customer)
                        for position in range(len(trial_target.customers) + 1):
                            positioned = trial.copy()
                            next(r for r in positioned.routes if r.vehicle_id == vehicle_id).customers.insert(position, customer)
                            evaluation = evaluate_solution(positioned, self.updated_problem, ObjectiveMode.TARDINESS)
                            if evaluation.feasible and evaluation.total_tardiness + 1e-6 < best_eval.total_tardiness:
                                if move_eval is None or evaluation.total_tardiness < move_eval.total_tardiness:
                                    move_best, move_eval = positioned, evaluation
                if move_best is not None and move_eval is not None:
                    best, best_eval, improved = move_best, move_eval, True
        return self._result("NEW_TRUCK", best, initial)

    def compare(self, initial: Solution, *, max_new_trucks: int = 3) -> list[StrategyResult]:
        return [self.detour(initial), self.reroute(initial), self.new_truck(initial, max_new_trucks=max_new_trucks)]

    @staticmethod
    def recommend(results: list[StrategyResult]) -> StrategyResult:
        """Select a feasible alternative with an auditable business-priority ordering."""
        feasible = [result for result in results if result.metrics.feasible]
        if not feasible:
            raise ValueError("No feasible rescheduling alternative")
        return min(feasible, key=lambda result: (
            result.metrics.tardiness_min,
            result.metrics.vehicle_cost,
            result.metrics.travel_time_min,
            result.metrics.distance_km,
            result.metrics.changed_positions + result.metrics.reassigned_customers,
        ))


def result_summary(result: StrategyResult) -> dict[str, Any]:
    return {"strategy": result.strategy, **asdict(result.metrics)}
