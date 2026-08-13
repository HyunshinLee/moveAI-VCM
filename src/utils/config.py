from __future__ import annotations

import math
import os
import re
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_ROOT = PROJECT_ROOT / "data"
RAW_DIR = DATA_ROOT / "raw"
RAW_NODELINK_DIR = RAW_DIR / "nodelink"
RAW_TRAFFIC_DIR = RAW_DIR / "traffic"
BACKBONE_DIR = DATA_ROOT / "backbone"
PHYSICAL_DIR = DATA_ROOT / "physical"
TDVRP_DIR = DATA_ROOT / "tdvrp"
INSTANCE_ROOT = DATA_ROOT / "instances"

OUTPUT_DIR = PROJECT_ROOT / "output"
FIGURES_DIR = OUTPUT_DIR / "figures"
SOLUTIONS_DIR = OUTPUT_DIR / "solutions"
LOGS_DIR = OUTPUT_DIR / "logs"
EXPERIMENTS_DIR = OUTPUT_DIR / "experiments"

DATA_DIR = Path(os.environ.get("NODELINKDATA_DIR", PROJECT_ROOT / "[2026-08-12]NODELINKDATA"))

NODE_FILE = DATA_DIR / "MOCT_NODE.shp"
LINK_FILE = DATA_DIR / "MOCT_LINK.shp"

TARGET_NODES = int(os.environ.get("TARGET_NODES", "200"))
MIN_TARGET_NODES = int(os.environ.get("MIN_TARGET_NODES", "180"))
MAX_TARGET_NODES = int(os.environ.get("MAX_TARGET_NODES", "220"))

PRIMARY_ROAD_RANKS = ("101", "102", "103")
SUPPORT_ROAD_RANKS = ("105", "106")
CANDIDATE_ROAD_RANKS = PRIMARY_ROAD_RANKS + SUPPORT_ROAD_RANKS

LINK_COLUMNS = [
    "LINK_ID",
    "F_NODE",
    "T_NODE",
    "LANES",
    "ROAD_RANK",
    "ROAD_TYPE",
    "ROAD_NO",
    "ROAD_NAME",
    "ROAD_USE",
    "MULTI_LINK",
    "CONNECT",
    "MAX_SPD",
    "LENGTH",
]

NODE_COLUMNS = [
    "NODE_ID",
    "NODE_TYPE",
    "NODE_NAME",
    "TURN_P",
]

ROAD_RANK_LABELS = {
    "101": "고속국도/고속도로",
    "102": "도시고속도로",
    "103": "일반국도",
    "104": "특별광역시도",
    "105": "국가지원지방도",
    "106": "지방도",
    "107": "시군구도/생활도로",
}

ROAD_TYPE_LABELS = {
    "000": "일반도로",
    "001": "고가차도",
    "002": "지하차도",
    "003": "교량",
    "004": "터널",
}

NODE_TYPE_NOTES = {
    "101": "교차/일반 노드 계열",
    "102": "주요 연결 노드 계열",
    "103": "속성변화점 샘플 확인",
    "104": "교량 관련 노드 샘플 확인",
    "105": "주요 연결 노드 계열",
    "106": "IC 샘플 확인",
    "107": "최소노드배치점 샘플 확인",
}

ROAD_RANK_PRIORITY = {
    "101": 6,
    "102": 5,
    "103": 4,
    "105": 3,
    "106": 2,
    "104": 1,
    "107": 0,
}

IMPORTANT_NAME_RE = re.compile(
    r"(IC|JCT|JC|TG|분기점|교차로|나들목|인터체인지|사거리|삼거리|요금소)",
    re.IGNORECASE,
)

PROTECTED_NODE_TYPES = {"102", "105", "106"}


def load_yaml_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in config file: {path}")
    return data


def load_network_config() -> dict[str, Any]:
    return load_yaml_config(CONFIG_DIR / "network.yaml")


def configured_hours() -> list[int]:
    config = load_network_config()
    start = int(config.get("START_HOUR", 0))
    end = int(config.get("END_HOUR", 23))
    if end < start:
        raise ValueError("END_HOUR must be greater than or equal to START_HOUR")
    return list(range(start, end + 1))


def ensure_project_dirs() -> None:
    for path in [
        RAW_NODELINK_DIR,
        RAW_TRAFFIC_DIR,
        BACKBONE_DIR,
        PHYSICAL_DIR,
        TDVRP_DIR,
        INSTANCE_ROOT / "instance_01",
        FIGURES_DIR,
        SOLUTIONS_DIR,
        LOGS_DIR,
        EXPERIMENTS_DIR,
        CONFIG_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def ensure_backbone_dir() -> Path:
    BACKBONE_DIR.mkdir(parents=True, exist_ok=True)
    return BACKBONE_DIR


def ensure_physical_dir() -> Path:
    PHYSICAL_DIR.mkdir(parents=True, exist_ok=True)
    return PHYSICAL_DIR


def ensure_tdvrp_dir() -> Path:
    TDVRP_DIR.mkdir(parents=True, exist_ok=True)
    return TDVRP_DIR


def ensure_figures_dir() -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return FIGURES_DIR


def clean_value(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    text = str(value).strip()
    text = text.strip("'").strip('"').strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def clean_code(value: object) -> str:
    return clean_value(value)


def clean_name(value: object) -> str:
    text = clean_value(value)
    return "" if text in {"-", "_"} else text


def normalize_text_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            if column in {"ROAD_NAME", "ROAD_NO", "NODE_NAME"}:
                df[column] = df[column].map(clean_name)
            else:
                df[column] = df[column].map(clean_code)
    return df


def road_rank_label(code: object) -> str:
    code = clean_code(code)
    return ROAD_RANK_LABELS.get(code, code or "unknown")


def road_type_label(code: object) -> str:
    code = clean_code(code)
    return ROAD_TYPE_LABELS.get(code, code or "unknown")


def rank_priority(code: object) -> int:
    return ROAD_RANK_PRIORITY.get(clean_code(code), -1)


def is_important_name(name: object) -> bool:
    return bool(IMPORTANT_NAME_RE.search(clean_name(name)))


def node_role_from_attrs(node_type: str, node_name: str, is_anchor: bool, degree: int) -> str:
    roles: list[str] = []
    if is_anchor:
        roles.append("anchor")
    if is_important_name(node_name):
        roles.append("named_interchange_or_intersection")
    if degree >= 3:
        roles.append("branch")
    elif degree <= 1:
        roles.append("terminal")
    else:
        roles.append("corridor")
    if node_type:
        roles.append(f"node_type_{node_type}")
    return "|".join(dict.fromkeys(roles))


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(result) or math.isinf(result):
        return default
    return result


def pairwise(values: list[str]) -> Iterable[tuple[str, str]]:
    for idx in range(len(values) - 1):
        yield values[idx], values[idx + 1]


def join_unique(values: Iterable[object], sep: str = "|") -> str:
    seen: dict[str, None] = {}
    for value in values:
        text = clean_value(value)
        if text:
            seen.setdefault(text, None)
    return sep.join(seen.keys())
