"""Read-only aggregation metrics over persisted events."""

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db_models import DBEvent


def _window_start(hours: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=hours)


def _event_value(event: dict[str, Any], section: str, key: str) -> str | None:
    value = event.get(section, {})
    if not isinstance(value, dict):
        return None
    result = value.get(key)
    return str(result) if result is not None and str(result) else None


class AnalyticsMetrics:
    def __init__(self, db: Session, user_id: int | None = None) -> None:
        self.db = db
        self.user_id = user_id

    def _events_since(self, start: datetime) -> list[DBEvent]:
        filters = [DBEvent.timestamp >= start]
        if self.user_id is not None:
            filters.append(DBEvent.user_id == self.user_id)
        return list(self.db.scalars(select(DBEvent).where(*filters).order_by(DBEvent.timestamp.asc())).yield_per(1000))

    def get_summary_stats(self, hours: int = 24) -> dict[str, Any]:
        if hours < 1:
            raise ValueError("hours must be at least 1")
        rows = self._events_since(_window_start(hours))
        source_distribution = Counter(row.source_type for row in rows)
        severity_distribution = Counter(row.severity for row in rows)
        success = 0
        failure = 0
        for row in rows:
            status = (_event_value(row.normalized_event, "event", "status") or "").lower()
            if status in {"success", "succeeded", "ok", "passed"}:
                success += 1
            elif status in {"failure", "failed", "fail", "error", "denied"}:
                failure += 1
        resolved = success + failure
        return {
            "hours": hours,
            "total_events": len(rows),
            "by_source_type": dict(source_distribution),
            "by_severity": dict(severity_distribution),
            "success_failure": {
                "success": success,
                "failure": failure,
                "ratio": success / resolved if resolved else None,
            },
        }

    def get_top_entities(self, limit: int = 5, hours: int = 24) -> dict[str, Any]:
        if limit < 1 or limit > 100 or hours < 1:
            raise ValueError("limit must be 1-100 and hours must be at least 1")
        rows = self._events_since(_window_start(hours))
        ips = Counter(
            value
            for row in rows
            if (value := _event_value(row.normalized_event, "actor", "source_ip"))
        )
        users = Counter(
            value
            for row in rows
            if (value := _event_value(row.normalized_event, "actor", "user"))
        )
        actions = Counter(
            value
            for row in rows
            if (value := _event_value(row.normalized_event, "event", "action"))
        )
        return {
            "hours": hours,
            "limit": limit,
            "top_source_ips": [
                {"entity": entity, "count": count} for entity, count in ips.most_common(limit)
            ],
            "top_users": [
                {"entity": entity, "count": count} for entity, count in users.most_common(limit)
            ],
            "top_actions": [
                {"entity": entity, "count": count} for entity, count in actions.most_common(limit)
            ],
        }

    def get_time_series(self, interval_minutes: int = 15, hours: int = 24) -> list[dict[str, Any]]:
        if interval_minutes < 1 or interval_minutes > 1440 or hours < 1:
            raise ValueError("interval_minutes must be 1-1440 and hours must be at least 1")
        start = _window_start(hours)
        rows = self._events_since(start)
        interval = interval_minutes * 60
        buckets: Counter[int] = Counter()
        for row in rows:
            timestamp = row.timestamp
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            bucket_epoch = int(timestamp.timestamp()) // interval * interval
            buckets[bucket_epoch] += 1
        bucket_start = int(start.timestamp()) // interval * interval
        bucket_end = int(datetime.now(timezone.utc).timestamp()) // interval * interval
        return [
            {
                "timestamp": datetime.fromtimestamp(epoch, timezone.utc),
                "count": buckets.get(epoch, 0),
            }
            for epoch in range(bucket_start, bucket_end + interval, interval)
        ]
