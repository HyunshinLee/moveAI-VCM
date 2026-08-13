from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.rerouting.traffic_api import TrafficEvent


@dataclass(frozen=True)
class GraphUpdateResult:
    profiles: pd.DataFrame
    event_log: pd.DataFrame
    unmatched_event_ids: tuple[str, ...]


def standard_link_index(physical_edges: pd.DataFrame) -> dict[str, set[str]]:
    """Map every retained national standard link ID to simplified physical edges."""
    index: dict[str, set[str]] = {}
    for row in physical_edges.itertuples(index=False):
        for link_id in str(getattr(row, "original_link_ids", "") or "").split(";"):
            if link_id:
                index.setdefault(link_id, set()).add(str(row.edge_id))
    return index


def update_edge_time_profiles(
    physical_edges: pd.DataFrame,
    edge_time_profiles: pd.DataFrame,
    events: list[TrafficEvent],
    *,
    update_hours: list[int],
    closure_multiplier: float = 999.0,
    minimum_speed_factor: float = 0.05,
) -> GraphUpdateResult:
    """Apply multiple simultaneous incidents/congestion events to team profile schema."""
    updated = edge_time_profiles.copy()
    updated["edge_id"] = updated["edge_id"].astype(str)
    link_index = standard_link_index(physical_edges)
    log_rows: list[dict[str, object]] = []
    unmatched: list[str] = []
    multipliers = pd.Series(1.0, index=updated.index)

    for event in events:
        edge_ids = sorted(set().union(*(link_index.get(link, set()) for link in event.link_ids)))
        if not edge_ids:
            unmatched.append(event.event_id)
            continue
        factor = closure_multiplier if event.closed else 1.0 / max(event.speed_factor, minimum_speed_factor)
        mask = updated["edge_id"].isin(edge_ids) & updated["hour"].isin(update_hours)
        # Overlapping event records represent the same snapshot. Use the worst
        # multiplier instead of compounding duplicate incident reports.
        multipliers.loc[mask] = multipliers.loc[mask].clip(lower=factor)
        for edge_id in edge_ids:
            log_rows.append({
                "event_id": event.event_id,
                "edge_id": edge_id,
                "hours": "|".join(map(str, update_hours)),
                "closed": event.closed,
                "travel_time_multiplier": factor,
                "description": event.description,
            })

    affected = multipliers.gt(1.0)
    updated.loc[affected, "travel_time_min"] *= multipliers.loc[affected]
    updated.loc[affected, "speed_kph"] /= multipliers.loc[affected]
    updated.loc[affected, "data_source"] = "traffic_adjusted"
    return GraphUpdateResult(updated, pd.DataFrame(log_rows), tuple(unmatched))
