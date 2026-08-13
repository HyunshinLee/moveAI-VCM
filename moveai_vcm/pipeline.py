from __future__ import annotations

from .models import Graph, RoutePlan
from .routing import expand_service_sequence


def compile_initial_paths(graph: Graph, plans: list[RoutePlan]) -> dict[str, list[list[str]]]:
    """Expand TDVRP service sequences on the pre-update backbone.

    Call this before applying live traffic. The returned paths are the fixed
    no-action baseline; detour and other strategies use the updated graph.
    """
    output: dict[str, list[list[str]]] = {}
    for plan in plans:
        sequence = [plan.vehicle.current_node] + [s.node_id for s in plan.stops] + [plan.vehicle.end_depot]
        expanded = expand_service_sequence(
            graph, sequence, plan.vehicle.available_at_s, use_live=False,
        )
        if expanded is None:
            raise ValueError(f"Initial sequence for {plan.vehicle.vehicle_id} is disconnected")
        output[plan.vehicle.vehicle_id] = [path.nodes for path in expanded]
    return output
