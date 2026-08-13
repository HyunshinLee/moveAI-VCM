from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.model.problem_data import ProblemData
from src.model.solution import Route, Solution


def load_solution_csv(path: str | Path, problem_data: ProblemData) -> Solution:
    """Load ALNS/MILP best_solution.csv and retain all unused fleet vehicles."""
    frame = pd.read_csv(path, dtype=str).fillna("")
    by_vehicle = {str(row.vehicle_id): row for row in frame.itertuples(index=False)}
    routes: list[Route] = []
    for vehicle_id in problem_data.vehicle_ids:
        vehicle = problem_data.vehicles_by_id[vehicle_id]
        row = by_vehicle.get(vehicle_id)
        customers = [] if row is None else [item for item in str(row.customer_sequence).split("|") if item]
        routes.append(Route(
            vehicle_id=vehicle_id,
            depot_id=vehicle.start_depot,
            customers=customers,
            end_depot=(str(row.end_depot) if row is not None and str(row.end_depot) else vehicle.start_depot),
        ))
    return Solution(routes=routes)
