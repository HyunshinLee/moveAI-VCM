from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Edge, Graph, TrafficObservation


class TrafficProvider(ABC):
    @abstractmethod
    def observe(self, graph: Graph, edges: Iterable[Edge]) -> list[TrafficObservation]:
        raise NotImplementedError


class MockTrafficProvider(TrafficProvider):
    """Deterministic provider for tests and offline demos.

    The JSON contains an ``observations`` list. Multiple simultaneous disruptions
    are represented by multiple rows, including closures and congestion updates.
    """

    def __init__(self, snapshot_path: str | Path):
        self.snapshot_path = Path(snapshot_path)

    def observe(self, graph: Graph, edges: Iterable[Edge]) -> list[TrafficObservation]:
        del graph, edges
        raw = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
        return [
            TrafficObservation(**item, observed_at=datetime.now(timezone.utc))
            for item in raw["observations"]
        ]


class TomTomFlowProvider(TrafficProvider):
    """Update each backbone arc from TomTom Flow Segment Data.

    The nearest road segment to an arc midpoint is queried. For a production map,
    persist provider segment IDs during backbone construction to avoid ambiguous
    midpoint matching at intersections.
    """

    BASE_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

    def __init__(self, api_key: str | None = None, *, workers: int = 8, timeout_s: float = 8.0):
        self.api_key = api_key or os.environ.get("TOMTOM_API_KEY")
        if not self.api_key:
            raise ValueError("TOMTOM_API_KEY is required")
        self.workers = workers
        self.timeout_s = timeout_s

    def _observe_edge(self, graph: Graph, edge: Edge) -> TrafficObservation:
        a, b = graph.nodes[edge.source], graph.nodes[edge.target]
        point = f"{(a.lat + b.lat) / 2:.7f},{(a.lon + b.lon) / 2:.7f}"
        url = f"{self.BASE_URL}?{urlencode({'key': self.api_key, 'point': point, 'unit': 'KMPH'})}"
        request = Request(url, headers={"User-Agent": "moveAI-VCM/1.0"})
        with urlopen(request, timeout=self.timeout_s) as response:
            payload = json.loads(response.read().decode("utf-8"))["flowSegmentData"]
        return TrafficObservation(
            source=edge.source, target=edge.target,
            current_speed_kph=float(payload["currentSpeed"]),
            free_flow_speed_kph=float(payload["freeFlowSpeed"]),
            closed=bool(payload.get("roadClosure", False)), provider="tomtom-flow",
            metadata={"confidence": payload.get("confidence"), "frc": payload.get("frc")},
        )

    def observe(self, graph: Graph, edges: Iterable[Edge]) -> list[TrafficObservation]:
        observations: list[TrafficObservation] = []
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {pool.submit(self._observe_edge, graph, edge): edge for edge in edges}
            for future in as_completed(futures):
                edge = futures[future]
                try:
                    observations.append(future.result())
                except Exception as exc:  # keep prior graph value if one API request fails
                    observations.append(TrafficObservation(
                        source=edge.source, target=edge.target,
                        current_speed_kph=edge.current_speed_kph or edge.base_speed_kph,
                        provider="tomtom-flow-error", confidence=0.0,
                        metadata={"error": str(exc)},
                    ))
        return observations


class TrafficGraphUpdater:
    def __init__(self, provider: TrafficProvider, *, min_speed_kph: float = 3.0):
        self.provider = provider
        self.min_speed_kph = min_speed_kph

    def update(self, graph: Graph) -> list[TrafficObservation]:
        observations = self.provider.observe(graph, graph.edges.values())
        for obs in observations:
            edge = graph.edges.get((obs.source, obs.target))
            if edge is None:
                continue
            edge.closed = obs.closed
            if obs.current_speed_kph is not None:
                edge.current_speed_kph = max(obs.current_speed_kph, self.min_speed_kph)
            edge.updated_at = obs.observed_at
            edge.metadata.update({
                "traffic_provider": obs.provider,
                "traffic_confidence": obs.confidence,
                **obs.metadata,
            })
        return observations

    def poll(self, graph: Graph, *, interval_s: float, iterations: int | None = None):
        count = 0
        while iterations is None or count < iterations:
            yield self.update(graph)
            count += 1
            if iterations is None or count < iterations:
                time.sleep(interval_s)
