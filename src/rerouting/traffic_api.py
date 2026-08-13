from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import requests


@dataclass(frozen=True)
class TrafficEvent:
    """Provider-neutral traffic event expressed with standard link IDs."""

    event_id: str
    link_ids: tuple[str, ...]
    description: str = ""
    closed: bool = False
    speed_factor: float = 1.0
    metadata: dict[str, object] = field(default_factory=dict)


class TrafficProvider(Protocol):
    def fetch_events(self) -> list[TrafficEvent]: ...


class UticIncidentProvider:
    """UTIC incident adapter. The API key is read from ``UTIC_API_KEY`` only."""

    URL = "http://www.utic.go.kr/guide/imsOpenData.do"
    FULL_CLOSURE_TERMS = ("전면통제", "전면 통제", "양방향 통제", "통행금지")

    def __init__(
        self,
        api_key: str | None = None,
        *,
        timeout_sec: float = 10.0,
        partial_speed_factor: float = 0.55,
    ) -> None:
        self.api_key = api_key or os.environ.get("UTIC_API_KEY")
        if not self.api_key:
            raise ValueError("UTIC_API_KEY environment variable is required")
        self.timeout_sec = timeout_sec
        self.partial_speed_factor = partial_speed_factor

    @staticmethod
    def _text(record: ET.Element, name: str) -> str:
        value = record.findtext(name)
        return "" if value in (None, "null") else value.strip()

    @classmethod
    def _links(cls, record: ET.Element) -> tuple[str, ...]:
        raw = ";".join((cls._text(record, "linkId"), cls._text(record, "lineLinkId")))
        return tuple(sorted({item.strip() for item in raw.replace(",", ";").split(";") if item.strip()}))

    def fetch_events(self) -> list[TrafficEvent]:
        response = requests.get(
            self.URL,
            params={"key": self.api_key},
            headers={"User-Agent": "moveAI-VCM/1.0"},
            timeout=self.timeout_sec,
        )
        response.raise_for_status()
        root = ET.fromstring(response.content)
        events: list[TrafficEvent] = []
        for index, record in enumerate(root.findall(".//record")):
            links = self._links(record)
            if not links:
                continue
            title = self._text(record, "incidentTitle")
            control = self._text(record, "controlType")
            description = " ".join(part for part in (title, control) if part)
            closed = any(term in description for term in self.FULL_CLOSURE_TERMS)
            events.append(TrafficEvent(
                event_id=self._text(record, "incidentId") or f"utic-{index}",
                link_ids=links,
                description=description,
                closed=closed,
                speed_factor=0.0 if closed else self.partial_speed_factor,
                metadata={"provider": "UTIC_INCIDENT", "control_type": control},
            ))
        return events


class JsonTrafficProvider:
    """Offline provider for tests/demos; accepts ``{"events": [...]}``."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def fetch_events(self) -> list[TrafficEvent]:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [
            TrafficEvent(
                event_id=str(row["event_id"]),
                link_ids=tuple(map(str, row["link_ids"])),
                description=str(row.get("description", "")),
                closed=bool(row.get("closed", False)),
                speed_factor=float(row.get("speed_factor", 1.0)),
                metadata=dict(row.get("metadata", {})),
            )
            for row in payload.get("events", [])
        ]
