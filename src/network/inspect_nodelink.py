from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pyogrio

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from src.utils.config import (
    CANDIDATE_ROAD_RANKS,
    DATA_DIR,
    LOGS_DIR,
    LINK_FILE,
    NODE_FILE,
    ROAD_RANK_LABELS,
    ROAD_TYPE_LABELS,
    clean_code,
    ensure_project_dirs,
    normalize_text_columns,
)


def print_file_inventory(data_dir: Path) -> None:
    print("== NODELINKDATA file inventory ==")
    for path in sorted(data_dir.iterdir()):
        if path.is_file():
            print(f"{path.name:24s} {path.stat().st_size / 1024 / 1024:10.2f} MB")


def print_vector_info(path: Path) -> None:
    info = pyogrio.read_info(path)
    print(f"\n== {path.name} ==")
    print(f"features      : {info.get('features')}")
    print(f"geometry_type : {info.get('geometry_type')}")
    print(f"encoding      : {info.get('encoding')}")
    print(f"crs           : {info.get('crs')}")
    print("fields:")
    for field, dtype in zip(info["fields"], info["dtypes"]):
        print(f"  - {field}: {dtype}")


def value_counts(path: Path, columns: list[str]) -> pd.DataFrame:
    df = pyogrio.read_dataframe(path, columns=columns, read_geometry=False)
    normalize_text_columns(df, columns)
    return df


def print_code_distribution() -> None:
    print("\n== LINK code distributions ==")
    link_df = value_counts(
        LINK_FILE,
        [
            "ROAD_RANK",
            "ROAD_TYPE",
            "ROAD_NO",
            "ROAD_NAME",
            "ROAD_USE",
            "MULTI_LINK",
            "CONNECT",
            "MAX_SPD",
            "LENGTH",
        ],
    )
    link_df["LENGTH"] = pd.to_numeric(link_df["LENGTH"], errors="coerce").fillna(0.0)
    link_df["MAX_SPD"] = pd.to_numeric(link_df["MAX_SPD"], errors="coerce").fillna(0).astype(int)
    for column in ["ROAD_RANK", "ROAD_TYPE", "ROAD_USE", "MULTI_LINK", "CONNECT", "MAX_SPD"]:
        print(f"\n-- {column} --")
        print(link_df[column].astype(str).value_counts(dropna=False).head(40).to_string())

    print("\n-- ROAD_RANK labels used by this project --")
    for code, label in ROAD_RANK_LABELS.items():
        count = int((link_df["ROAD_RANK"] == code).sum())
        km = float(link_df.loc[link_df["ROAD_RANK"] == code, "LENGTH"].sum()) / 1000.0
        print(f"{code}: {label:16s} count={count:8d} length_km={km:10.1f}")

    print("\n-- ROAD_TYPE labels used by this project --")
    for code, label in ROAD_TYPE_LABELS.items():
        count = int((link_df["ROAD_TYPE"] == code).sum())
        km = float(link_df.loc[link_df["ROAD_TYPE"] == code, "LENGTH"].sum()) / 1000.0
        print(f"{code}: {label:8s} count={count:8d} length_km={km:10.1f}")

    print("\n-- ROAD_RANK samples from actual ROAD_NAME values --")
    for rank in sorted(link_df["ROAD_RANK"].dropna().unique(), key=clean_code):
        sub = link_df[link_df["ROAD_RANK"] == rank]
        print(f"\nROAD_RANK {rank} ({ROAD_RANK_LABELS.get(rank, 'unknown')})")
        samples = (
            sub[["ROAD_NO", "ROAD_NAME", "ROAD_TYPE", "MAX_SPD", "LENGTH"]]
            .drop_duplicates(subset=["ROAD_NO", "ROAD_NAME"])
            .head(15)
        )
        print(samples.to_string(index=False))

    print("\n== NODE code distributions ==")
    node_df = value_counts(NODE_FILE, ["NODE_TYPE", "NODE_NAME", "TURN_P"])
    for column in ["NODE_TYPE", "TURN_P"]:
        print(f"\n-- {column} --")
        print(node_df[column].astype(str).value_counts(dropna=False).head(40).to_string())

    print("\n== Columns selected for graph construction ==")
    print("NODE: NODE_ID, NODE_TYPE, NODE_NAME, TURN_P, geometry")
    print(
        "LINK: LINK_ID, F_NODE, T_NODE, LENGTH, ROAD_RANK, ROAD_TYPE, "
        "ROAD_NO, ROAD_NAME, CONNECT, MULTI_LINK, MAX_SPD, geometry"
    )
    print(f"Backbone candidate ROAD_RANK codes: {', '.join(CANDIDATE_ROAD_RANKS)}")
    print("Primary ranks: 101 고속도로, 102 도시고속도로, 103 일반국도")
    print("Support ranks: 105 국가지원지방도, 106 지방도")
    print("Excluded by default: 104 특별광역시도, 107 시군구도/생활도로")

    ensure_project_dirs()
    report_path = LOGS_DIR / "schema_report.txt"
    with report_path.open("w", encoding="utf-8") as file:
        file.write("NODELINKDATA schema inspection completed.\n")
        file.write(f"Data directory: {DATA_DIR}\n")
        file.write("Use console output for detailed distributions and samples.\n")
    print(f"\nWrote lightweight schema marker: {report_path}")


def main() -> None:
    print_file_inventory(DATA_DIR)
    print_vector_info(NODE_FILE)
    print_vector_info(LINK_FILE)
    print_code_distribution()


if __name__ == "__main__":
    main()
