from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from math import inf
from typing import Any, Iterable


@dataclass(slots=True)
class Node:
    id: str
    lat: float
    lon: float
    kind: str = "waypoint"  # depot | customer | waypoint | virtual


@dataclass(slots=True)
class Edge:
    source: str
    target: str
    distance_m: float
    base_speed_kph: float
    current_speed_kph: float | None = None
    closed: bool = False
    updated_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str]:
        return self.source, self.target

    def travel_time_s(self, *, use_live: bool = True) -> float:
        if use_live and self.closed:
            return inf
        speed = self.current_speed_kph if use_live and self.current_speed_kph else self.base_speed_kph
        return self.distance_m / max(speed, 0.1) * 3.6


@dataclass
class Graph:
    nodes: dict[str, Node]
    edges: dict[tuple[str, str], Edge]
    adjacency: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.adjacency:
            self.adjacency = {node_id: [] for node_id in self.nodes}
            for source, target in self.edges:
                self.adjacency.setdefault(source, []).append(target)

    def edge(self, source: str, target: str) -> Edge:
        return self.edges[(source, target)]

    def outgoing(self, source: str) -> Iterable[Edge]:
        for target in self.adjacency.get(source, []):
            yield self.edges[(source, target)]


@dataclass(slots=True)
class Stop:
    node_id: str
    load_delta: float = 0.0  # pickup +, delivery -
    service_time_s: float = 0.0
    planned_arrival_s: float | None = None
    due_time_s: float | None = None
    priority: float = 1.0
    job_id: str | None = None


@dataclass(slots=True)
class VehicleState:
    vehicle_id: str
    current_node: str
    end_depot: str
    capacity: float
    current_load: float
    available_at_s: float = 0.0
    max_route_time_s: float = 12 * 3600
    fixed_dispatch_cost: float = 0.0
    cost_per_km: float = 0.0
    cost_per_hour: float = 0.0
    is_extra: bool = False


@dataclass
class RoutePlan:
    vehicle: VehicleState
    stops: list[Stop]
    frozen_prefix: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TrafficObservation:
    source: str
    target: str
    current_speed_kph: float | None = None
    free_flow_speed_kph: float | None = None
    closed: bool = False
    confidence: float = 1.0
    provider: str = "unknown"
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RouteMetrics:
    total_travel_time_s: float
    total_distance_m: float
    total_delay_s: float
    max_delay_s: float
    late_stops: int
    on_time_rate: float
    operating_cost: float
    changed_stop_positions: int
    reassigned_jobs: int
    extra_trucks: int
    infeasible_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StrategyResult:
    strategy: str
    plans: list[RoutePlan]
    detailed_paths: dict[str, list[list[str]]]
    metrics: RouteMetrics
    explanation: list[str] = field(default_factory=list)
    icer_cost_per_delay_hour_saved: float | None = None

    @property
    def feasible(self) -> bool:
        return self.metrics.infeasible_reason is None
