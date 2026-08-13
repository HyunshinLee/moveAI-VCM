from __future__ import annotations

import heapq
from dataclasses import dataclass
from math import inf

from .models import Graph


@dataclass(slots=True)
class PathResult:
    nodes: list[str]
    distance_m: float
    travel_time_s: float


def shortest_path(
    graph: Graph,
    source: str,
    target: str,
    departure_s: float,
    *,
    use_live: bool = True,
) -> PathResult | None:
    """FIFO time-dependent Dijkstra.

    Edge travel time is evaluated when the vehicle enters the edge. The current
    graph implementation stores a live speed snapshot; it can later be replaced
    by a speed-profile callable without changing the rescheduler API.
    """
    if source == target:
        return PathResult([source], 0.0, 0.0)
    arrival = {source: departure_s}
    distance = {source: 0.0}
    parent: dict[str, str] = {}
    queue = [(departure_s, source)]
    while queue:
        time_at_u, u = heapq.heappop(queue)
        if time_at_u != arrival.get(u):
            continue
        if u == target:
            break
        for edge in graph.outgoing(u):
            travel = edge.travel_time_s(use_live=use_live)
            if travel == inf:
                continue
            candidate = time_at_u + travel
            if candidate < arrival.get(edge.target, inf):
                arrival[edge.target] = candidate
                distance[edge.target] = distance[u] + edge.distance_m
                parent[edge.target] = u
                heapq.heappush(queue, (candidate, edge.target))
    if target not in arrival:
        return None
    nodes = [target]
    while nodes[-1] != source:
        nodes.append(parent[nodes[-1]])
    nodes.reverse()
    return PathResult(nodes, distance[target], arrival[target] - departure_s)


def evaluate_fixed_path(graph: Graph, nodes: list[str], departure_s: float) -> PathResult | None:
    elapsed = 0.0
    distance = 0.0
    for source, target in zip(nodes, nodes[1:]):
        edge = graph.edges.get((source, target))
        if edge is None or edge.closed:
            return None
        elapsed += edge.travel_time_s(use_live=True)
        distance += edge.distance_m
    return PathResult(nodes, distance, elapsed)


def expand_service_sequence(
    graph: Graph,
    sequence: list[str],
    departure_s: float,
    *,
    use_live: bool,
) -> list[PathResult] | None:
    paths: list[PathResult] = []
    clock = departure_s
    for source, target in zip(sequence, sequence[1:]):
        path = shortest_path(graph, source, target, clock, use_live=use_live)
        if path is None:
            return None
        paths.append(path)
        clock += path.travel_time_s
    return paths
