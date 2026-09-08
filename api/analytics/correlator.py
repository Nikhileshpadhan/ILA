"""Cross-source incident correlation."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db_models import DBEvent


def _event_time(row: DBEvent) -> datetime:
    timestamp = row.timestamp or row.ingested_at
    return timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp


class CrossSourceCorrelator:
    def correlate_by_ip(self, db: Session, window_minutes: int = 15, user_id: int | None = None) -> list[dict[str, Any]]:
        if window_minutes < 1:
            raise ValueError("window_minutes must be positive")
        start = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        filters = [DBEvent.timestamp >= start]
        if user_id is not None:
            filters.append(DBEvent.user_id == user_id)
        rows = db.scalars(select(DBEvent).where(*filters).order_by(DBEvent.timestamp.asc())).yield_per(1000)
        by_ip: dict[str, list[DBEvent]] = defaultdict(list)
        for row in rows:
            ip = row.source_ip
            if ip:
                by_ip[ip].append(row)

        incidents: list[dict[str, Any]] = []
        for ip, matches in by_ip.items():
            source_names = {row.source_name for row in matches if row.source_name}
            source_types = {row.source_type for row in matches if row.source_type}
            sources = sorted(source_names) if len(source_names) >= 2 else sorted(source_types)
            if len(source_types) < 2 and len(source_names) < 2:
                continue
            first_seen = min(_event_time(row) for row in matches)
            last_seen = max(_event_time(row) for row in matches)
            incidents.append(
                {
                    "incident_id": str(uuid4()),
                    "suspect_ip": ip,
                    "sources_involved": sources,
                    "events_count": len(matches),
                    "first_seen": first_seen,
                    "last_seen": last_seen,
                    "narrative": (
                        "Suspicious multi-vector reconnaissance: IP was observed across "
                        f"{len(sources)} distinct log sources."
                    ),
                    "severity": "high",
                }
            )
        return incidents
