from __future__ import annotations

import pandas as pd

from src.rerouting.disruption import Disruption


def apply_disruption_to_profiles(
    edge_time_profiles: pd.DataFrame,
    disruption: Disruption,
) -> pd.DataFrame:
    updated = edge_time_profiles.copy()
    mask = (
        updated["edge_id"].astype(str).isin(disruption.disrupted_edge_ids)
        & updated["hour"].between(disruption.start_hour, disruption.end_hour)
    )
    updated.loc[mask, "travel_time_min"] *= disruption.travel_time_multiplier
    updated.loc[mask, "data_source"] = "disruption_adjusted"
    return updated

