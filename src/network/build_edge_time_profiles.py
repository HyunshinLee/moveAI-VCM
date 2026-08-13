from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from src.utils.config import (
    PHYSICAL_DIR,
    configured_hours,
    ensure_project_dirs,
    load_network_config,
)


PHYSICAL_EDGES_CSV = PHYSICAL_DIR / "physical_edges.csv"
EDGE_TIME_PROFILES_CSV = PHYSICAL_DIR / "edge_time_profiles.csv"


def log(message: str) -> None:
    print(f"[edge_time_profiles] {message}", flush=True)


def normalized_road_key(row: pd.Series) -> str:
    edge_type = str(row.get("edge_type", "")).upper()
    road_rank = str(row.get("road_rank", "")).strip()
    if edge_type == "CONNECTOR" or road_rank.upper() == "CONNECTOR":
        return "CONNECTOR"
    return road_rank if road_rank and road_rank.lower() != "nan" else "DEFAULT"


def speed_for_edge(row: pd.Series, config: dict[str, Any]) -> float:
    speeds = config.get("FREE_FLOW_SPEED_KPH", {})
    key = normalized_road_key(row)
    return float(speeds.get(key, speeds.get("DEFAULT", 45.0)))


def congestion_factor_for_hour(hour: int, config: dict[str, Any]) -> float:
    factors = config.get("CONGESTION_FACTOR", {})
    return float(factors.get(str(hour), 1.0))


def build_prototype_profiles(edges: pd.DataFrame, hours: list[int], config: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for edge in edges.to_dict(orient="records"):
        edge_id = str(edge["edge_id"])
        distance_km = float(edge["distance_km"])
        free_flow_speed = speed_for_edge(pd.Series(edge), config)
        for hour in hours:
            congestion_factor = congestion_factor_for_hour(hour, config)
            travel_time_min = (distance_km / free_flow_speed) * 60.0 * congestion_factor
            travel_time_min = max(travel_time_min, 0.01)
            speed_kph = distance_km / (travel_time_min / 60.0) if travel_time_min > 0 else free_flow_speed
            rows.append(
                {
                    "edge_id": edge_id,
                    "hour": hour,
                    "travel_time_min": round(travel_time_min, 6),
                    "speed_kph": round(speed_kph, 6),
                    "data_source": "prototype",
                }
            )
    return pd.DataFrame(rows)


class EdgeTimeProfileProvider:
    def __init__(self, profiles: pd.DataFrame):
        self._lookup = {
            (str(row.edge_id), int(row.hour)): float(row.travel_time_min)
            for row in profiles.itertuples(index=False)
        }

    @classmethod
    def from_csv(cls, path: Path = EDGE_TIME_PROFILES_CSV) -> "EdgeTimeProfileProvider":
        profiles = pd.read_csv(path, dtype={"edge_id": str})
        return cls(profiles)

    def get_edge_travel_time(self, edge_id: str, hour: int) -> float:
        return self._lookup[(str(edge_id), int(hour))]


def get_edge_travel_time(edge_id: str, hour: int, profiles: pd.DataFrame | None = None) -> float:
    if profiles is None:
        provider = EdgeTimeProfileProvider.from_csv()
        return provider.get_edge_travel_time(edge_id, hour)
    lookup = profiles.set_index(["edge_id", "hour"])["travel_time_min"]
    return float(lookup.loc[(str(edge_id), int(hour))])


def main() -> None:
    ensure_project_dirs()
    config = load_network_config()
    mode = str(config.get("TRAFFIC_PROFILE_MODE", "prototype"))
    hours = configured_hours()

    edges = pd.read_csv(PHYSICAL_EDGES_CSV, dtype={"edge_id": str}).fillna("")
    edges["distance_km"] = pd.to_numeric(edges["distance_km"], errors="coerce").fillna(0.0)

    if mode != "prototype":
        raise NotImplementedError(
            f"TRAFFIC_PROFILE_MODE={mode!r} is not implemented yet. "
            "Use prototype or add a historical-data provider."
        )

    profiles = build_prototype_profiles(edges, hours, config)
    profiles.to_csv(EDGE_TIME_PROFILES_CSV, index=False, encoding="utf-8-sig")

    print("== Edge time profile validation ==")
    print(f"physical edge count: {len(edges):,}")
    print(f"number of hours: {len(hours)} ({hours[0]}-{hours[-1]})")
    print(f"generated rows: {len(profiles):,}")
    print(f"min travel_time_min: {profiles.travel_time_min.min():.4f}")
    print(f"max travel_time_min: {profiles.travel_time_min.max():.4f}")
    print(f"avg travel_time_min: {profiles.travel_time_min.mean():.4f}")
    print("\nSample:")
    print(profiles.head(12).to_string(index=False))
    log(f"Wrote {EDGE_TIME_PROFILES_CSV}")


if __name__ == "__main__":
    main()
