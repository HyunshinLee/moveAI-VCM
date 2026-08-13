from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Disruption:
    disrupted_edge_ids: list[str]
    start_hour: int
    end_hour: int
    travel_time_multiplier: float = 999.0
    description: str = ""

