from __future__ import annotations


def parse_hhmm(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def minutes_to_hhmm(minutes: int | float) -> str:
    minutes_int = int(round(minutes))
    hour = (minutes_int // 60) % 24
    minute = minutes_int % 60
    return f"{hour:02d}:{minute:02d}"


def departure_hour(departure_min: int | float) -> int:
    return int(departure_min // 60) % 24

