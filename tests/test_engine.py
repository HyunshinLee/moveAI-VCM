from __future__ import annotations

import unittest
from pathlib import Path

from moveai_vcm.graph_io import load_graph, load_tdvrp_solution
from moveai_vcm.models import Edge, Graph, Node, RoutePlan, Stop, VehicleState
from moveai_vcm.pipeline import compile_initial_paths
from moveai_vcm.rescheduler import Rescheduler, ReschedulingConfig
from moveai_vcm.traffic import MockTrafficProvider, TrafficGraphUpdater


ROOT = Path(__file__).resolve().parents[1]


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = load_graph(ROOT / "examples/backbone_graph.json")
        self.plans = load_tdvrp_solution(ROOT / "examples/tdvrp_solution.json")
        self.initial_paths = compile_initial_paths(self.graph, self.plans)

    def update(self) -> None:
        TrafficGraphUpdater(MockTrafficProvider(ROOT / "examples/traffic_snapshot.json")).update(self.graph)

    def test_multiple_disruptions_update_one_snapshot(self) -> None:
        self.update()
        self.assertEqual(self.graph.edge("D0", "W1").current_speed_kph, 8)
        self.assertTrue(self.graph.edge("W2", "C2").closed)
        self.assertEqual(self.graph.edge("C2", "D1").current_speed_kph, 15)

    def test_detour_avoids_closed_arc_but_no_action_keeps_it(self) -> None:
        self.update()
        scheduler = Rescheduler(self.graph, initial_paths=self.initial_paths)
        no_action = scheduler.no_action(self.plans)
        detour = scheduler.detour(self.plans)
        self.assertIn("W2", no_action.detailed_paths["T1"][1])
        self.assertEqual(detour.detailed_paths["T1"][1], ["C1", "W2", "X", "C2"])
        self.assertLess(detour.metrics.total_travel_time_s, no_action.metrics.total_travel_time_s)

    def test_end_to_end_returns_ranked_strategies(self) -> None:
        self.update()
        results = Rescheduler(self.graph, initial_paths=self.initial_paths).solve(self.plans, [])
        self.assertEqual({r.strategy for r in results}, {"no_action", "detour", "reroute"})
        self.assertTrue(results[0].feasible)
        self.assertGreaterEqual(results[0].metrics.on_time_rate, 0)

    def test_multiple_extra_trucks_can_be_dispatched(self) -> None:
        nodes = {
            node_id: Node(node_id, 37.5, 127.0, "customer")
            for node_id in ("D", "A", "B", "Z")
        }
        nodes["D"].kind = nodes["Z"].kind = "depot"
        edges = {}
        for source, target in (("D", "A"), ("D", "B"), ("A", "Z"), ("B", "Z")):
            edge = Edge(source, target, 1000, 60)
            edges[edge.key] = edge
        graph = Graph(nodes, edges)
        plans = [
            RoutePlan(
                VehicleState(f"T{i}", "D", "Z", 1, 1, available_at_s=2000),
                [Stop(node, -1, planned_arrival_s=60, job_id=f"J{i}")],
            )
            for i, node in enumerate(("A", "B"), start=1)
        ]
        extras = [
            VehicleState(f"E{i}", "D", "Z", 1, 1, is_extra=True)
            for i in (1, 2)
        ]
        result = Rescheduler(
            graph, ReschedulingConfig(max_extra_trucks=2, reassignment_penalty=0),
        ).new_trucks(plans, extras)
        self.assertEqual(result.metrics.extra_trucks, 2)
        self.assertEqual(result.metrics.reassigned_jobs, 2)


if __name__ == "__main__":
    unittest.main()
