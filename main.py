from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


PIPELINE = [
    "src.network.add_service_nodes",
    "src.network.build_edge_time_profiles",
    "src.network.build_tdvrp_graph",
    "src.model.build_demo_instance",
]


def run_module(module: str) -> None:
    subprocess.run([sys.executable, "-m", module], cwd=PROJECT_ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="TDVRPTW-rerouting pipeline runner")
    parser.add_argument(
        "stage",
        choices=["physical", "profiles", "tdvrp", "instance", "solve", "milp", "all"],
        default=None,
        nargs="?",
        help="Pipeline stage to run",
    )
    parser.add_argument(
        "--objective",
        choices=["TARDINESS", "TRAVEL_TIME", "DISTANCE", "VEHICLE_COST", "ALL"],
        default=None,
        help="Run ALNS with the selected single objective. Use ALL for four independent runs.",
    )
    parser.add_argument("--iterations", type=int, default=None, help="Override ALNS max iterations")
    parser.add_argument(
        "--time-window-mode",
        choices=["SOFT", "HARD"],
        default=None,
        help="Override ALNS time-window handling",
    )
    parser.add_argument("--time-limit", type=float, default=None, help="Override MILP solver time limit")
    parser.add_argument("--mip-gap", type=str, default=None, help="Override MILP relative MIP gap")
    parser.add_argument("--solution-limit", type=int, default=None, help="Override MILP solution limit")
    parser.add_argument("--quiet", action="store_true", help="Suppress solver output for MILP/ALNS subcommands")
    args = parser.parse_args()
    stage = args.stage
    if stage is None:
        stage = "solve" if args.objective else "all"

    if stage == "solve":
        command = [sys.executable, "-m", "src.alns.alns"]
        if args.objective:
            command.extend(["--objective", args.objective])
        if args.iterations is not None:
            command.extend(["--iterations", str(args.iterations)])
        if args.time_window_mode:
            command.extend(["--time-window-mode", args.time_window_mode])
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
        return

    if stage == "milp":
        command = [sys.executable, "-m", "src.model.milp_solver"]
        if args.objective:
            if args.objective == "ALL":
                raise ValueError("MILP stage supports one objective at a time")
            command.extend(["--objective", args.objective])
        if args.time_limit is not None:
            command.extend(["--time-limit", str(args.time_limit)])
        if args.mip_gap is not None:
            command.extend(["--mip-gap", args.mip_gap])
        if args.solution_limit is not None:
            command.extend(["--solution-limit", str(args.solution_limit)])
        if args.quiet:
            command.append("--quiet")
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
        return

    if args.objective:
        raise ValueError("--objective can only be used with the solve/milp stage or without a stage")

    if stage == "physical":
        modules = ["src.network.add_service_nodes"]
    elif stage == "profiles":
        modules = ["src.network.build_edge_time_profiles"]
    elif stage == "tdvrp":
        modules = ["src.network.build_tdvrp_graph"]
    elif stage == "instance":
        modules = ["src.model.build_demo_instance"]
    else:
        modules = PIPELINE

    for module in modules:
        run_module(module)


if __name__ == "__main__":
    main()
