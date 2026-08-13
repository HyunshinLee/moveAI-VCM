from __future__ import annotations

import json
import os
import time
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
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


class UticIncidentProvider(TrafficProvider):
    """Apply UTIC real-time incidents to standard-node-link backbone arcs.

    UTIC incident ``linkId``/``lineLinkId`` values are matched directly to the
    MOCT standard link IDs retained in each compressed physical edge. Full
    control events close an arc; partial incidents apply an explicit estimated
    speed factor because this endpoint does not return measured link speed.
    """

    URL = "http://www.utic.go.kr/guide/imsOpenData.do"
    FULL_CLOSURE_TERMS = ("전면통제", "전면 통제", "양방향 통제", "통행금지")

    def __init__(
        self,
        api_key: str | None = None,
        *,
        timeout_s: float = 10.0,
        partial_speed_factor: float = 0.55,
    ):
        self.api_key = api_key or os.environ.get("UTIC_API_KEY")
        if not self.api_key:
            raise ValueError("UTIC_API_KEY is required")
        self.timeout_s = timeout_s
        self.partial_speed_factor = partial_speed_factor

    @staticmethod
    def _text(record: ET.Element, field: str) -> str:
        value = record.findtext(field)
        return "" if value in (None, "null") else value.strip()

    @classmethod
    def _link_ids(cls, record: ET.Element) -> set[str]:
        raw = ";".join((cls._text(record, "linkId"), cls._text(record, "lineLinkId")))
        return {
            value.strip() for value in raw.replace(",", ";").split(";")
            if value.strip()
        }

    def _fetch(self) -> ET.Element:
        url = f"{self.URL}?{urlencode({'key': self.api_key})}"
        request = Request(url, headers={"User-Agent": "moveAI-VCM/1.0"})
        with urlopen(request, timeout=self.timeout_s) as response:
            return ET.fromstring(response.read())

    def observe(self, graph: Graph, edges: Iterable[Edge]) -> list[TrafficObservation]:
        link_to_edges: dict[str, list[Edge]] = {}
        for edge in edges:
            for link_id in edge.metadata.get("original_link_ids", []):
                link_to_edges.setdefault(str(link_id), []).append(edge)

        by_edge: dict[tuple[str, str], list[ET.Element]] = {}
        for record in self._fetch().findall(".//record"):
            for link_id in self._link_ids(record):
                for edge in link_to_edges.get(link_id, []):
                    by_edge.setdefault(edge.key, []).append(record)

        observations: list[TrafficObservation] = []
        for edge_key, records in by_edge.items():
            edge = graph.edges[edge_key]
            titles = [self._text(record, "incidentTitle") for record in records]
            controls = [self._text(record, "controlType") for record in records]
            descriptions = " ".join(titles + controls)
            closed = any(term in descriptions for term in self.FULL_CLOSURE_TERMS)
            observations.append(TrafficObservation(
                source=edge.source,
                target=edge.target,
                current_speed_kph=(
                    None if closed else edge.base_speed_kph * self.partial_speed_factor
                ),
                closed=closed,
                provider="utic-incident",
                confidence=1.0 if closed else 0.6,
                metadata={
                    "incident_ids": sorted({
                        self._text(record, "incidentId") for record in records
                    }),
                    "incident_titles": titles,
                    "control_types": controls,
                    "speed_value_type": "not_applicable" if closed else "policy_estimate",
                    "matched_standard_link_ids": sorted(set().union(*(
                        self._link_ids(record) for record in records
                    )) & set(map(str, edge.metadata.get("original_link_ids", [])))),
                },
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
