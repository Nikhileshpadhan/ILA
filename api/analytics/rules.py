"""Lightweight rule-based security detections."""

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db_models import DBEvent
from .metrics import _event_value


@dataclass
class SecurityAlert:
    alert_id: str
    rule_name: str
    severity: str
    entity_ip: str | None
    entity_user: str | None
    matched_events_count: int
    details: str
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _event_rows(db: Session, start: datetime, user_id: int | None = None) -> list[DBEvent]:
    filters = [DBEvent.timestamp >= start]
    if user_id is not None:
        filters.append(DBEvent.user_id == user_id)
    return list(db.scalars(select(DBEvent).where(*filters).order_by(DBEvent.timestamp.asc())).yield_per(1000))


def _event_time(row: DBEvent) -> datetime:
    timestamp = row.timestamp
    return timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp


class RuleEngine:
    def detect_brute_force(
        self, db: Session, threshold: int = 5, window_minutes: int = 5, user_id: int | None = None
    ) -> list[SecurityAlert]:
        if threshold < 1 or window_minutes < 1:
            raise ValueError("threshold and window_minutes must be positive")
        rows = _event_rows(db, datetime.now(timezone.utc) - timedelta(minutes=window_minutes), user_id)
        failed = [
            row
            for row in rows
            if (_event_value(row.normalized_event, "event", "status") or "").lower()
            in {"failure", "failed", "fail", "error", "denied"}
        ]
        by_entity: dict[tuple[str | None, str | None], list[DBEvent]] = defaultdict(list)
        for row in failed:
            ip = _event_value(row.normalized_event, "actor", "source_ip")
            user = _event_value(row.normalized_event, "actor", "user")
            if ip or user:
                by_entity[(ip, user)].append(row)
        alerts: list[SecurityAlert] = []
        for (ip, user), matches in by_entity.items():
            if len(matches) >= threshold:
                alerts.append(
                    SecurityAlert(
                        alert_id=str(uuid4()),
                        rule_name="brute_force",
                        severity="high",
                        entity_ip=ip,
                        entity_user=user,
                        matched_events_count=len(matches),
                        details=f"{len(matches)} failed events in {window_minutes} minutes.",
                        timestamp=max(_event_time(row) for row in matches),
                    )
                )
        return alerts

    def detect_suspicious_volume(
        self, db: Session, threshold: int = 50, window_minutes: int = 2, user_id: int | None = None
    ) -> list[SecurityAlert]:
        if threshold < 1 or window_minutes < 1:
            raise ValueError("threshold and window_minutes must be positive")
        rows = _event_rows(db, datetime.now(timezone.utc) - timedelta(minutes=window_minutes), user_id)
        by_ip: dict[str, list[DBEvent]] = defaultdict(list)
        for row in rows:
            ip = _event_value(row.normalized_event, "actor", "source_ip")
            if ip:
                by_ip[ip].append(row)
        return [
            SecurityAlert(
                alert_id=str(uuid4()),
                rule_name="suspicious_volume",
                severity="high",
                entity_ip=ip,
                entity_user=None,
                matched_events_count=len(matches),
                details=f"{len(matches)} events from one IP in {window_minutes} minutes.",
                timestamp=max(_event_time(row) for row in matches),
            )
            for ip, matches in by_ip.items()
            if len(matches) >= threshold
        ]
