"""Lightweight rule-based security detections."""

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db_models import DBEvent


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
    timestamp = row.timestamp or row.ingested_at
    return timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp


class RuleEngine:
    def detect_brute_force(
        self, db: Session, threshold: int = 5, window_minutes: int = 5, user_id: int | None = None
    ) -> list[SecurityAlert]:
        if threshold < 1 or window_minutes < 1:
            raise ValueError("threshold and window_minutes must be positive")
        rows = _event_rows(db, datetime.now(timezone.utc) - timedelta(minutes=window_minutes), user_id)
        failed = [
            row for row in rows 
            if (row.status or "").lower() in {"failure", "failed", "fail", "error", "denied"}
        ]
        by_entity: dict[tuple[str | None, str | None], list[DBEvent]] = defaultdict(list)
        for row in failed:
            ip = row.source_ip
            user = row.user
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

    def detect_success_after_failures(self, db: Session, threshold: int = 3, window_minutes: int = 15, user_id: int | None = None) -> list[SecurityAlert]:
        rows = _event_rows(db, datetime.now(timezone.utc) - timedelta(minutes=window_minutes), user_id)
        by_ip: dict[str, list[DBEvent]] = defaultdict(list)
        for row in rows:
            ip = row.source_ip
            if ip:
                by_ip[ip].append(row)
        
        alerts: list[SecurityAlert] = []
        for ip, matches in by_ip.items():
            matches.sort(key=lambda x: x.timestamp or x.ingested_at)
            failures = 0
            for row in matches:
                status = (row.status or "").lower()
                if status in {"failure", "failed", "fail", "error", "denied"}:
                    failures += 1
                elif status in {"success", "succeeded", "ok", "passed"}:
                    if failures >= threshold:
                        alerts.append(
                            SecurityAlert(
                                alert_id=str(uuid4()),
                                rule_name="success_after_failures",
                                severity="critical",
                                entity_ip=ip,
                                entity_user=row.user,
                                matched_events_count=failures + 1,
                                details=f"{failures} failures followed by a success from {ip}.",
                                timestamp=_event_time(row),
                            )
                        )
                        break
                    failures = 0
        return alerts

    def detect_suspicious_ip(self, db: Session, window_minutes: int = 60, user_id: int | None = None) -> list[SecurityAlert]:
        rows = _event_rows(db, datetime.now(timezone.utc) - timedelta(minutes=window_minutes), user_id)
        high_sev = [row for row in rows if row.severity == "high"]
        by_ip: dict[str, set[str]] = defaultdict(set)
        for row in high_sev:
            ip = row.source_ip
            system = row.source_name
            if ip and system:
                by_ip[ip].add(system)
        
        return [
            SecurityAlert(
                alert_id=str(uuid4()),
                rule_name="suspicious_ip_multiple_systems",
                severity="critical",
                entity_ip=ip,
                entity_user=None,
                matched_events_count=len(systems),
                details=f"IP {ip} triggered high-severity events across {len(systems)} distinct systems.",
                timestamp=datetime.now(timezone.utc),
            )
            for ip, systems in by_ip.items() if len(systems) >= 2
        ]

    def geo_ip_analysis_placeholder(self, ip: str) -> dict[str, str]:
        """Mock function for Geo-IP mapping."""
        mock_db = {
            "10.0.0.1": "US-East",
            "192.168.1.100": "Internal",
            "185.15.59.224": "RU-Moscow",
            "8.8.8.8": "US-Global",
        }
        return {"ip": ip, "region": mock_db.get(ip, "Unknown")}

    def generate_attack_timeline(self, db: Session, ip: str, window_minutes: int = 60, user_id: int | None = None) -> list[dict[str, Any]]:
        rows = _event_rows(db, datetime.now(timezone.utc) - timedelta(minutes=window_minutes), user_id)
        ip_events = [row for row in rows if row.source_ip == ip]
        ip_events.sort(key=lambda x: x.timestamp or x.ingested_at)
        
        timeline = []
        for row in ip_events:
            timeline.append({
                "time": (row.timestamp or row.ingested_at).isoformat(),
                "action": row.action or "unknown",
                "status": row.status or "unknown",
                "system": row.source_name or "unknown",
                "severity": row.severity
            })
        return timeline
