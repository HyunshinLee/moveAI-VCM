from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.alns.acceptance import simulated_annealing_accept
from src.alns.destroy_operators import active_destroy_operators, destroy_by_name
from src.alns.evaluation import (
    SolutionEvaluation,
    assert_objective_consistency,
    evaluate_solution,
    iter_used_route_evaluations,
    optimize_end_depots,
)
from src.alns.initial_solution import build_initial_solution
from src.alns.local_search import local_search, route_elimination
from src.alns.operator_weights import (
    REWARD_ACCEPTED,
    REWARD_CURRENT_IMPROVEMENT,
    REWARD_GLOBAL_BEST,
    REWARD_REJECTED,
    AdaptiveOperatorWeights,
)
from src.alns.repair_operators import active_repair_operators, repair_by_name
from src.model.objective import ObjectiveMode, parse_objective_mode
from src.model.problem_data import ProblemData, TimeWindowMode, parse_time_window_mode
from src.model.solution import Solution
from src.utils.config import CONFIG_DIR, EXPERIMENTS_DIR, SOLUTIONS_DIR, ensure_project_dirs, load_yaml_config
from src.utils.time_utils import minutes_to_hhmm


OBJECTIVE_CHOICES = [mode.value for mode in ObjectiveMode] + ["ALL"]


@dataclass(frozen=True)
class ALNSConfig:
    active_objective: ObjectiveMode
    time_window_mode: TimeWindowMode
    random_seed: int = 20260813
    max_iterations: int = 300
    time_limit_sec: float | None = None
    removal_min: int = 5
    removal_max: int = 15
    initial_temperature: float = 1.0
    cooling_rate: float = 0.995
    local_search_enabled: bool = True
    local_search_max_moves: int = 8
    local_search_frequency: int = 25
    objective_tolerance: float = 1e-6
    operator_reaction: float = 0.2

    @classmethod
    def from_yaml(
        cls,
        objective: str | None = None,
        iterations: int | None = None,
        time_window_mode: str | None = None,
    ) -> "ALNSConfig":
        raw = load_yaml_config(CONFIG_DIR / "alns.yaml")
        active_objective = parse_objective_mode(
            objective or raw.get("active_objective") or raw.get("ACTIVE_OBJECTIVE") or "TARDINESS"
        )
        tw_mode = parse_time_window_mode(
            time_window_mode or raw.get("time_window_mode") or raw.get("TIME_WINDOW_MODE") or "SOFT"
        )
        return cls(
            active_objective=active_objective,
            time_window_mode=tw_mode,
            random_seed=int(raw.get("random_seed", raw.get("RANDOM_SEED", 20260813))),
            max_iterations=int(
                iterations if iterations is not None else raw.get("max_iterations", raw.get("MAX_ITERATIONS", 300))
            ),
            time_limit_sec=_optional_float(raw.get("time_limit_sec", raw.get("TIME_LIMIT_SEC"))),
            removal_min=int(raw.get("removal_min", raw.get("REMOVAL_MIN", 5))),
            removal_max=int(raw.get("removal_max", raw.get("REMOVAL_MAX", 15))),
            initial_temperature=float(raw.get("initial_temperature", raw.get("INITIAL_TEMPERATURE", 1.0))),
            cooling_rate=float(raw.get("cooling_rate", raw.get("COOLING_RATE", 0.995))),
            local_search_enabled=bool(raw.get("local_search_enabled", raw.get("LOCAL_SEARCH_ENABLED", True))),
            local_search_max_moves=int(raw.get("local_search_max_moves", raw.get("LOCAL_SEARCH_MAX_MOVES", 8))),
            local_search_frequency=int(raw.get("local_search_frequency", raw.get("LOCAL_SEARCH_FREQUENCY", 25))),
            objective_tolerance=float(raw.get("objective_tolerance", raw.get("OBJECTIVE_TOLERANCE", 1e-6))),
            operator_reaction=float(raw.get("operator_reaction", raw.get("OPERATOR_REACTION", 0.2))),
        )


@dataclass(frozen=True)
class ALNSRunResult:
    objective_mode: str
    active_objective_value: float
    total_tardiness: float
    total_travel_time: float
    total_distance: float
    vehicle_cost: float
    used_vehicle_count: int
    feasible: bool
    runtime: float
    iterations: int
    solution_dir: str
    validation_errors: list[str]


class ALNS:
    def __init__(self, problem_data: ProblemData, config: ALNSConfig):
        self.problem_data = problem_data
        self.config = config
        self.rng = random.Random(config.random_seed)
        self.destroy_weights = AdaptiveOperatorWeights(
            active_destroy_operators(config.active_objective),
            reaction=config.operator_reaction,
        )
        self.repair_weights = AdaptiveOperatorWeights(
            active_repair_operators(config.active_objective, problem_data.time_window_mode),
            reaction=config.operator_reaction,
        )

    def run(self) -> tuple[Solution, SolutionEvaluation, pd.DataFrame]:
        initial = build_initial_solution(self.problem_data, self.config.active_objective)
        initial_eval = evaluate_solution(initial, self.problem_data, self.config.active_objective)
        assert_objective_consistency(initial_eval, self.config.active_objective, self.config.objective_tolerance)
        if not initial_eval.feasible:
            raise ValueError(f"Initial solution is infeasible: {initial_eval.validation_errors}")

        current = initial.copy()
        current_eval = initial_eval
        best = initial.copy()
        best_eval = initial_eval
        logs: list[dict[str, Any]] = []

        temperature = self.config.initial_temperature
        start_time = time.perf_counter()
        completed_iterations = 0
        for iteration in range(1, self.config.max_iterations + 1):
            if self.config.time_limit_sec is not None:
                if time.perf_counter() - start_time >= self.config.time_limit_sec:
                    break

            degree = self.rng.randint(
                self.config.removal_min,
                min(self.config.removal_max, len(self.problem_data.customer_ids)),
            )
            destroy_name = self.destroy_weights.select(self.rng)
            repair_name = self.repair_weights.select(self.rng)

            partial, removed = destroy_by_name(
                destroy_name,
                current,
                degree,
                self.rng,
                self.problem_data,
                self.config.active_objective,
            )
            candidate = repair_by_name(
                repair_name,
                partial,
                removed,
                self.problem_data,
                self.config.active_objective,
            )
            candidate = optimize_end_depots(candidate, self.problem_data, self.config.active_objective)

            if self.config.active_objective == ObjectiveMode.VEHICLE_COST:
                candidate = route_elimination(
                    candidate,
                    self.problem_data,
                    self.config.active_objective,
                    self.config.objective_tolerance,
                )
            if self.config.local_search_enabled and iteration % self.config.local_search_frequency == 0:
                candidate = local_search(
                    candidate,
                    self.problem_data,
                    self.config.active_objective,
                    tolerance=self.config.objective_tolerance,
                    max_moves=self.config.local_search_max_moves,
                )

            candidate_eval = evaluate_solution(candidate, self.problem_data, self.config.active_objective)
            assert_objective_consistency(
                candidate_eval,
                self.config.active_objective,
                self.config.objective_tolerance,
            )

            accepted = False
            reward = REWARD_REJECTED
            event = "REJECTED"
            if candidate_eval.feasible:
                if _is_better(candidate_eval, best_eval, self.config.objective_tolerance):
                    best = candidate.copy()
                    best_eval = candidate_eval
                    current = candidate.copy()
                    current_eval = candidate_eval
                    accepted = True
                    reward = REWARD_GLOBAL_BEST
                    event = "GLOBAL_BEST"
                elif _is_better(candidate_eval, current_eval, self.config.objective_tolerance):
                    current = candidate.copy()
                    current_eval = candidate_eval
                    accepted = True
                    reward = REWARD_CURRENT_IMPROVEMENT
                    event = "CURRENT_IMPROVEMENT"
                elif simulated_annealing_accept(
                    current_eval.active_objective_value,
                    candidate_eval.active_objective_value,
                    temperature,
                    self.rng,
                ):
                    current = candidate.copy()
                    current_eval = candidate_eval
                    accepted = True
                    reward = REWARD_ACCEPTED
                    event = "SA_ACCEPTED"

            self.destroy_weights.update(destroy_name, reward)
            self.repair_weights.update(repair_name, reward)
            logs.append(
                {
                    "iteration": iteration,
                    "destroy_operator": destroy_name,
                    "repair_operator": repair_name,
                    "removed_count": len(removed),
                    "accepted": accepted,
                    "event": event,
                    "temperature": temperature,
                    "candidate_feasible": candidate_eval.feasible,
                    "candidate_active_objective": candidate_eval.active_objective_value,
                    "current_active_objective": current_eval.active_objective_value,
                    "best_active_objective": best_eval.active_objective_value,
                    "best_tardiness": best_eval.total_tardiness,
                    "best_travel_time": best_eval.total_travel_time,
                    "best_distance": best_eval.total_distance,
                    "best_vehicle_cost": best_eval.vehicle_cost,
                    "best_used_vehicle_count": best_eval.used_vehicle_count,
                }
            )
            temperature *= self.config.cooling_rate
            completed_iterations = iteration

        log_df = pd.DataFrame(logs)
        best_eval = evaluate_solution(best, self.problem_data, self.config.active_objective)
        best.evaluation = best_eval
        return best, best_eval, log_df.assign(completed_iterations=completed_iterations)


def run_objective(
    objective: str | ObjectiveMode,
    iterations: int | None = None,
    time_window_mode: str | None = None,
) -> ALNSRunResult:
    ensure_project_dirs()
    mode = parse_objective_mode(objective)
    config = ALNSConfig.from_yaml(
        objective=mode.value,
        iterations=iterations,
        time_window_mode=time_window_mode,
    )
    problem_data = ProblemData.from_files(time_window_mode=config.time_window_mode)
    solver = ALNS(problem_data, config)

    start_time = time.perf_counter()
    solution, evaluation, log_df = solver.run()
    runtime = time.perf_counter() - start_time
    solution_dir = SOLUTIONS_DIR / mode.value
    solution_dir.mkdir(parents=True, exist_ok=True)
    write_solution_outputs(solution, evaluation, log_df, problem_data, config, runtime, solution_dir)

    iterations_completed = int(log_df["iteration"].max()) if not log_df.empty else 0
    return ALNSRunResult(
        objective_mode=mode.value,
        active_objective_value=evaluation.active_objective_value,
        total_tardiness=evaluation.total_tardiness,
        total_travel_time=evaluation.total_travel_time,
        total_distance=evaluation.total_distance,
        vehicle_cost=evaluation.vehicle_cost,
        used_vehicle_count=evaluation.used_vehicle_count,
        feasible=evaluation.feasible,
        runtime=runtime,
        iterations=iterations_completed,
        solution_dir=str(solution_dir),
        validation_errors=list(evaluation.validation_errors),
    )


def run_all_objectives(
    iterations: int | None = None,
    time_window_mode: str | None = None,
) -> pd.DataFrame:
    results = [
        run_objective(mode, iterations=iterations, time_window_mode=time_window_mode)
        for mode in ObjectiveMode
    ]
    comparison = pd.DataFrame([asdict(result) for result in results])
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    comparison_path = EXPERIMENTS_DIR / "objective_comparison.csv"
    comparison.to_csv(comparison_path, index=False, encoding="utf-8-sig")
    return comparison


def write_solution_outputs(
    solution: Solution,
    evaluation: SolutionEvaluation,
    log_df: pd.DataFrame,
    problem_data: ProblemData,
    config: ALNSConfig,
    runtime: float,
    solution_dir: Path,
) -> None:
    solution_rows: list[dict[str, Any]] = []
    for route_eval in iter_used_route_evaluations(evaluation):
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
        solution_dir / "best_solution.csv",
        index=False,
        encoding="utf-8-sig",
    )

    schedule_rows: list[dict[str, Any]] = []
    for entry in evaluation.schedule:
        if not solution_route_used(solution, entry.vehicle_id):
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
        solution_dir / "best_schedule.csv",
        index=False,
        encoding="utf-8-sig",
    )
    log_df.to_csv(solution_dir / "alns_log.csv", index=False, encoding="utf-8-sig")

    summary = {
        "objective_mode": config.active_objective.value,
        "time_window_mode": config.time_window_mode.value,
        "objective_weights": {
            "tardiness": 1 if config.active_objective == ObjectiveMode.TARDINESS else 0,
            "travel_time": 1 if config.active_objective == ObjectiveMode.TRAVEL_TIME else 0,
            "distance": 1 if config.active_objective == ObjectiveMode.DISTANCE else 0,
            "vehicle_cost": 1 if config.active_objective == ObjectiveMode.VEHICLE_COST else 0,
        },
        "feasible": evaluation.feasible,
        "active_objective_value": evaluation.active_objective_value,
        "total_tardiness": evaluation.total_tardiness,
        "total_travel_time": evaluation.total_travel_time,
        "total_distance": evaluation.total_distance,
        "vehicle_cost": evaluation.vehicle_cost,
        "used_vehicle_count": evaluation.used_vehicle_count,
        "runtime": runtime,
        "iterations": int(log_df["iteration"].max()) if not log_df.empty else 0,
        "customer_count": len(problem_data.customer_ids),
        "vehicle_count": len(problem_data.vehicle_ids),
        "validation_errors": list(evaluation.validation_errors),
        "canonical_signature": repr(evaluation.canonical_signature),
    }
    (solution_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def solution_route_used(solution: Solution, vehicle_id: str) -> bool:
    return any(route.vehicle_id == vehicle_id and route.used for route in solution.routes)


def _is_better(
    candidate_eval: SolutionEvaluation,
    incumbent_eval: SolutionEvaluation,
    tolerance: float,
) -> bool:
    diff = candidate_eval.active_objective_value - incumbent_eval.active_objective_value
    if diff < -tolerance:
        return True
    if abs(diff) <= tolerance:
        return candidate_eval.canonical_signature < incumbent_eval.canonical_signature
    return False


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TD-MDCVRPTW-FED ALNS")
    parser.add_argument("--objective", choices=OBJECTIVE_CHOICES, default=None)
    parser.add_argument("--iterations", type=int, default=None)
    parser.add_argument("--time-window-mode", choices=[mode.value for mode in TimeWindowMode], default=None)
    args = parser.parse_args()

    if args.objective == "ALL":
        comparison = run_all_objectives(
            iterations=args.iterations,
            time_window_mode=args.time_window_mode,
        )
        print(comparison.to_string(index=False))
        print(f"Wrote {EXPERIMENTS_DIR / 'objective_comparison.csv'}")
        return

    config = ALNSConfig.from_yaml(
        objective=args.objective,
        iterations=args.iterations,
        time_window_mode=args.time_window_mode,
    )
    result = run_objective(
        config.active_objective,
        iterations=args.iterations,
        time_window_mode=config.time_window_mode.value,
    )
    print(pd.DataFrame([asdict(result)]).to_string(index=False))
    print(f"Wrote {Path(result.solution_dir)}")


if __name__ == "__main__":
    main()
