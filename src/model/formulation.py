from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class TDVRPTWData:
    service_nodes: pd.DataFrame
    td_od_matrix: pd.DataFrame
    vehicles: pd.DataFrame
    parameters: dict
    td_paths: pd.DataFrame | None = None


def load_problem_data(
    service_nodes: pd.DataFrame,
    td_od_matrix: pd.DataFrame,
    vehicles: pd.DataFrame,
    parameters: dict,
    td_paths: pd.DataFrame | None = None,
) -> TDVRPTWData:
    return TDVRPTWData(
        service_nodes=service_nodes,
        td_od_matrix=td_od_matrix,
        vehicles=vehicles,
        parameters=parameters,
        td_paths=td_paths,
    )
