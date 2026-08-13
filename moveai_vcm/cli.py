from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .graph_io import dump_graph, dump_results, load_graph, load_physical_graph, load_tdvrp_solution
from .models import VehicleState
from .pipeline import compile_initial_paths
from .rescheduler import Rescheduler, ReschedulingConfig
from .traffic import MockTrafficProvider, TrafficGraphUpdater, UticIncidentProvider


def load_extra_vehicles(path: str | Path | None) -> list[VehicleState]:
    if not path:
        return []
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [VehicleState(**item, is_extra=True) for item in raw["vehicles"]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MOVE-AI real-time graph updater and rescheduler")
    parser.add_argument("--graph", required=True, help="Graph JSON or physical graph directory")
    parser.add_argument("--solution", required=True, help="TDVRP team's final sequence JSON")
    parser.add_argument("--extras", help="Available extra trucks JSON")
    parser.add_argument("--provider", choices=["mock", "utic"], default="mock")
    parser.add_argument("--traffic-snapshot", help="Required for mock provider")
    parser.add_argument("--output", default="rescheduling_results.json")
    parser.add_argument("--updated-graph", default="updated_graph.json")
    parser.add_argument("--max-extra-trucks", type=int, default=3)
    parser.add_argument("--wtp", type=float, default=100000, help="KRW per delay-hour saved")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    graph_path = Path(args.graph)
    graph = load_physical_graph(graph_path) if graph_path.is_dir() else load_graph(graph_path)
    plans = load_tdvrp_solution(args.solution)
    initial_paths = compile_initial_paths(graph, plans)

    if args.provider == "mock":
        if not args.traffic_snapshot:
            raise SystemExit("--traffic-snapshot is required for mock provider")
        provider = MockTrafficProvider(args.traffic_snapshot)
    else:
        provider = UticIncidentProvider(os.environ.get("UTIC_API_KEY"))
    observations = TrafficGraphUpdater(provider).update(graph)
    dump_graph(graph, args.updated_graph)

    config = ReschedulingConfig(
        max_extra_trucks=args.max_extra_trucks,
        willingness_to_pay_per_delay_hour=args.wtp,
    )
    results = Rescheduler(graph, config, initial_paths=initial_paths).solve(
        plans, load_extra_vehicles(args.extras),
    )
    dump_results(results, args.output)
    print(json.dumps({
        "traffic_observations": len(observations),
        "recommended_strategy": results[0].strategy,
        "metrics": results[0].metrics.to_dict(),
        "output": str(Path(args.output).resolve()),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
