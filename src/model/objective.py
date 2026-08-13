from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ObjectiveMode(str, Enum):
    TARDINESS = "TARDINESS"
    TRAVEL_TIME = "TRAVEL_TIME"
    DISTANCE = "DISTANCE"
    VEHICLE_COST = "VEHICLE_COST"


@dataclass(frozen=True)
class ObjectiveComponents:
    tardiness: float = 0.0
    travel_time: float = 0.0
    distance: float = 0.0
    vehicle_cost: float = 0.0
    used_vehicle_count: int = 0

    def __add__(self, other: "ObjectiveComponents") -> "ObjectiveComponents":
        return ObjectiveComponents(
            tardiness=self.tardiness + other.tardiness,
            travel_time=self.travel_time + other.travel_time,
            distance=self.distance + other.distance,
            vehicle_cost=self.vehicle_cost + other.vehicle_cost,
            used_vehicle_count=self.used_vehicle_count + other.used_vehicle_count,
        )


def parse_objective_mode(value: str | ObjectiveMode) -> ObjectiveMode:
    if isinstance(value, ObjectiveMode):
        return value
    normalized = str(value).strip().upper()
    try:
        return ObjectiveMode(normalized)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in ObjectiveMode)
        raise ValueError(f"Invalid active_objective '{value}'. Allowed values: {allowed}") from exc


def objective_weights(mode: str | ObjectiveMode) -> dict[str, int]:
    parsed = parse_objective_mode(mode)
    return {
        "tardiness": 1 if parsed == ObjectiveMode.TARDINESS else 0,
        "travel_time": 1 if parsed == ObjectiveMode.TRAVEL_TIME else 0,
        "distance": 1 if parsed == ObjectiveMode.DISTANCE else 0,
        "vehicle_cost": 1 if parsed == ObjectiveMode.VEHICLE_COST else 0,
    }


def get_active_objective_value(
    components: ObjectiveComponents,
    mode: str | ObjectiveMode,
) -> float:
    parsed = parse_objective_mode(mode)
    if parsed == ObjectiveMode.TARDINESS:
        return float(components.tardiness)
    if parsed == ObjectiveMode.TRAVEL_TIME:
        return float(components.travel_time)
    if parsed == ObjectiveMode.DISTANCE:
        return float(components.distance)
    if parsed == ObjectiveMode.VEHICLE_COST:
        return float(components.vehicle_cost)
    raise AssertionError(f"Unhandled objective mode: {parsed}")
