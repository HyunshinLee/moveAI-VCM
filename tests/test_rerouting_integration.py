from __future__ import annotations

import unittest

import pandas as pd

from src.model.problem_data import ProblemData
from src.rerouting.graph_update import update_edge_time_profiles
from src.rerouting.reoptimization import ReschedulingEngine
from src.rerouting.solution_io import load_solution_csv
from src.rerouting.traffic_api import TrafficEvent


class GraphUpdateTest(unittest.TestCase):
    def test_multiple_events_match_original_link_ids(self) -> None:
        edges = pd.DataFrame([
            {"edge_id": "PE1", "original_link_ids": "11;12"},
            {"edge_id": "PE2", "original_link_ids": "21"},
        ])
        profiles = pd.DataFrame([
            {"edge_id": edge, "hour": hour, "travel_time_min": 10.0, "speed_kph": 60.0, "data_source": "base"}
            for edge in ("PE1", "PE2") for hour in (8, 9)
        ])
        result = update_edge_time_profiles(
            edges, profiles,
            [TrafficEvent("A", ("12",), closed=True), TrafficEvent("B", ("21",), speed_factor=0.5)],
            update_hours=[9], closure_multiplier=100.0,
        )
        values = result.profiles.set_index(["edge_id", "hour"])["travel_time_min"]
        self.assertEqual(values["PE1", 8], 10.0)
        self.assertEqual(values["PE1", 9], 1000.0)
        self.assertEqual(values["PE2", 9], 20.0)


class TeamContractSmokeTest(unittest.TestCase):
    def test_solution_csv_is_directly_accepted(self) -> None:
        problem = ProblemData.from_files()
        solution = load_solution_csv("output/solutions/TARDINESS/best_solution.csv", problem)
        self.assertEqual(len(solution.routes), len(problem.vehicle_ids))
        result = ReschedulingEngine(problem, problem).detour(solution)
        self.assertTrue(result.metrics.feasible)
        self.assertEqual(set(solution.assigned_customers()), set(problem.customer_ids))


if __name__ == "__main__":
    unittest.main()
