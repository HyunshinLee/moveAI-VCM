from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from copy import deepcopy


@dataclass
class Route:
    vehicle_id: str
    depot_id: str
    customers: list[str] = field(default_factory=list)
    end_depot: str | None = None

    @property
    def start_depot(self) -> str:
        return self.depot_id

    @property
    def used(self) -> bool:
        return bool(self.customers)

    def copy(self) -> "Route":
        return Route(
            vehicle_id=self.vehicle_id,
            depot_id=self.depot_id,
            customers=list(self.customers),
            end_depot=self.end_depot,
        )


@dataclass
class Solution:
    routes: list[Route] = field(default_factory=list)
    objective_value: float | None = None
    feasible: bool = False
    unassigned_customers: list[str] = field(default_factory=list)
    evaluation: Any | None = None

    def copy(self) -> "Solution":
        return deepcopy(self)

    def used_routes(self) -> list[Route]:
        return [route for route in self.routes if route.used]

    def assigned_customers(self) -> list[str]:
        return [customer for route in self.routes for customer in route.customers]

    def canonical_signature(self) -> tuple:
        return tuple(
            (
                route.vehicle_id,
                route.depot_id,
                tuple(route.customers),
                route.end_depot or route.depot_id,
            )
            for route in sorted(self.routes, key=lambda item: item.vehicle_id)
            if route.used
        )
