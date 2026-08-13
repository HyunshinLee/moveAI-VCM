from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.model.problem_data import ProblemData
from src.network.build_tdvrp_graph import build_td_matrices, extract_service_nodes, read_physical_network
from src.rerouting.graph_update import update_edge_time_profiles
from src.rerouting.reoptimization import ReschedulingEngine, problem_data_with_updated_network, result_summary
from src.rerouting.solution_io import load_solution_csv
from src.rerouting.traffic_api import JsonTrafficProvider, UticIncidentProvider
from src.utils.config import PHYSICAL_DIR, SOLUTIONS_DIR


def run_pipeline(
    solution_csv: str | Path,
    *,
    provider: JsonTrafficProvider | UticIncidentProvider,
    update_hours: list[int],
    max_new_trucks: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, object]]]:
    """In-memory integration point for graph, TDVRP output, and rescheduling."""
    nodes, edges, profiles = read_physical_network()
    update = update_edge_time_profiles(edges, profiles, provider.fetch_events(), update_hours=update_hours)
    service_nodes = extract_service_nodes(nodes)
    updated_od, updated_paths, unreachable = build_td_matrices(
        nodes, edges, update.profiles, service_nodes, sorted(profiles["hour"].unique())
    )
    if unreachable:
        raise ValueError(f"Updated graph has {len(unreachable)} unreachable OD-hour pairs")

    initial_problem = ProblemData.from_files()
    updated_problem = problem_data_with_updated_network(initial_problem, updated_od, updated_paths)
    initial_solution = load_solution_csv(solution_csv, initial_problem)
    engine = ReschedulingEngine(initial_problem, updated_problem)
    results = engine.compare(
        initial_solution, max_new_trucks=max_new_trucks
    )
    recommended = engine.recommend(results).strategy
    baseline = ReschedulingEngine(initial_problem, initial_problem).detour(initial_solution).metrics
    summaries: list[dict[str, object]] = []
    for result in results:
        row = result_summary(result)
        row.update({
            "recommended": result.strategy == recommended,
            "delta_tardiness_min": result.metrics.tardiness_min - baseline.tardiness_min,
            "delta_travel_time_min": result.metrics.travel_time_min - baseline.travel_time_min,
            "delta_distance_km": result.metrics.distance_km - baseline.distance_km,
        })
        summaries.append(row)
    return update.profiles, update.event_log, summaries


def main() -> None:
    parser = argparse.ArgumentParser(description="Update physical graph and compare rescheduling alternatives")
    parser.add_argument("--solution", type=Path, default=SOLUTIONS_DIR / "TARDINESS" / "best_solution.csv")
    parser.add_argument("--provider", choices=["utic", "json"], default="utic")
    parser.add_argument("--snapshot", type=Path, help="JSON snapshot when --provider=json")
    parser.add_argument("--hours", type=int, nargs="+", default=[datetime.now().hour])
    parser.add_argument("--max-new-trucks", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=Path("output/rerouting"))
    args = parser.parse_args()

    if args.provider == "json":
        if args.snapshot is None:
            parser.error("--snapshot is required when --provider=json")
        provider = JsonTrafficProvider(args.snapshot)
    else:
        provider = UticIncidentProvider()

    profiles, event_log, summaries = run_pipeline(
        args.solution, provider=provider, update_hours=args.hours,
        max_new_trucks=args.max_new_trucks,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(args.output_dir / "updated_edge_time_profiles.csv", index=False, encoding="utf-8-sig")
    event_log.to_csv(args.output_dir / "matched_traffic_events.csv", index=False, encoding="utf-8-sig")
    (args.output_dir / "strategy_comparison.json").write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(pd.DataFrame(summaries).to_string(index=False))


if __name__ == "__main__":
    main()
