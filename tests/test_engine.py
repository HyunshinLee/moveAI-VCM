from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from moveai_vcm.graph_io import load_graph, load_physical_graph, load_tdvrp_solution
from moveai_vcm.models import Edge, Graph, Node, RoutePlan, Stop, VehicleState
from moveai_vcm.pipeline import compile_initial_paths
from moveai_vcm.rescheduler import Rescheduler, ReschedulingConfig
from moveai_vcm.traffic import MockTrafficProvider, TrafficGraphUpdater, UticIncidentProvider


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
                [Stop(node, 1, planned_arrival_s=60, job_id=f"J{i}")],
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

    def test_team_physical_graph_loader(self) -> None:
        graph = load_physical_graph(ROOT / "graph")
        self.assertEqual(len(graph.nodes), 255)
        self.assertEqual(len(graph.edges), 1528)
        edge = next(e for e in graph.edges.values() if e.metadata["edge_type"] == "road_backbone")
        self.assertTrue(edge.metadata["original_link_ids"])

    def test_utic_incident_matches_standard_link_and_marks_closure(self) -> None:
        edge = Edge(
            "A", "B", 1000, 80,
            metadata={"original_link_ids": ["1234567890"]},
        )
        graph = Graph(
            {"A": Node("A", 37.5, 127.0), "B": Node("B", 37.6, 127.1)},
            {edge.key: edge},
        )
        provider = UticIncidentProvider("test-key")
        provider._fetch = lambda: ET.fromstring("""
            <result><record>
              <incidentId>I1</incidentId><linkId>1234567890</linkId>
              <lineLinkId></lineLinkId><incidentTitle>사고로 전면통제</incidentTitle>
              <controlType>전면 통제</controlType>
            </record></result>
        """)
        observations = provider.observe(graph, graph.edges.values())
        self.assertEqual(len(observations), 1)
        self.assertTrue(observations[0].closed)
        self.assertEqual(observations[0].metadata["matched_standard_link_ids"], ["1234567890"])


if __name__ == "__main__":
    unittest.main()
