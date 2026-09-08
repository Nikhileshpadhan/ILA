"""Read-only aggregation metrics over persisted events."""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..db_models import DBEvent


def _window_start(hours: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=hours)


class AnalyticsMetrics:
    def __init__(self, db: Session, user_id: int | None = None) -> None:
        self.db = db
        self.user_id = user_id

    def _base_filters(self, start: datetime) -> list:
        filters = [DBEvent.ingested_at >= start]
        if self.user_id is not None:
            filters.append(DBEvent.user_id == self.user_id)
        return filters

    def get_summary_stats(self, hours: int = 24) -> dict[str, Any]:
        if hours < 1:
            raise ValueError("hours must be at least 1")
        start = _window_start(hours)
        filters = self._base_filters(start)
        
        total_events = self.db.scalar(select(func.count(DBEvent.id)).where(*filters)) or 0
        
        source_distribution = dict(self.db.execute(
            select(DBEvent.source_type, func.count(DBEvent.id))
            .where(*filters)
            .group_by(DBEvent.source_type)
        ).all())
        
        severity_distribution = dict(self.db.execute(
            select(DBEvent.severity, func.count(DBEvent.id))
            .where(*filters)
            .group_by(DBEvent.severity)
        ).all())
        
        success = self.db.scalar(
            select(func.count(DBEvent.id))
            .where(*filters, DBEvent.status.in_(["success", "succeeded", "ok", "passed"]))
        ) or 0
        
        failure = self.db.scalar(
            select(func.count(DBEvent.id))
            .where(*filters, DBEvent.status.in_(["failure", "failed", "fail", "error", "denied"]))
        ) or 0
        
        error_rate = (failure / total_events * 100) if total_events > 0 else 0.0
        
        duration_seconds = (datetime.now(timezone.utc) - start).total_seconds()
        duration_minutes = duration_seconds / 60
        duration_hours = duration_seconds / 3600
        
        return {
            "hours": hours,
            "total_events": total_events,
            "error_rate_percent": round(error_rate, 2),
            "throughput": {
                "logs_per_second": round(total_events / duration_seconds, 2) if duration_seconds > 0 else 0,
                "logs_per_minute": round(total_events / duration_minutes, 2) if duration_minutes > 0 else 0,
                "logs_per_hour": round(total_events / duration_hours, 2) if duration_hours > 0 else 0,
            },
            "by_source_type": source_distribution,
            "by_severity": severity_distribution,
            "success_failure": {
                "success": success,
                "failure": failure,
            },
        }

    def get_top_entities(self, limit: int = 5, hours: int = 24) -> dict[str, Any]:
        if limit < 1 or limit > 100 or hours < 1:
            raise ValueError("limit must be 1-100 and hours must be at least 1")
        filters = self._base_filters(_window_start(hours))
        
        ips = self.db.execute(
            select(DBEvent.source_ip, func.count(DBEvent.id))
            .where(*filters, DBEvent.source_ip != None)
            .group_by(DBEvent.source_ip)
            .order_by(func.count(DBEvent.id).desc())
            .limit(limit)
        ).all()
        
        users = self.db.execute(
            select(DBEvent.user, func.count(DBEvent.id))
            .where(*filters, DBEvent.user != None)
            .group_by(DBEvent.user)
            .order_by(func.count(DBEvent.id).desc())
            .limit(limit)
        ).all()
        
        systems = self.db.execute(
            select(DBEvent.source_name, func.count(DBEvent.id))
            .where(*filters, DBEvent.source_name != None)
            .group_by(DBEvent.source_name)
            .order_by(func.count(DBEvent.id).desc())
            .limit(limit)
        ).all()
        
        actions = self.db.execute(
            select(DBEvent.action, func.count(DBEvent.id))
            .where(*filters, DBEvent.action != None)
            .group_by(DBEvent.action)
            .order_by(func.count(DBEvent.id).desc())
            .limit(limit)
        ).all()

        return {
            "hours": hours,
            "limit": limit,
            "top_source_ips": [{"entity": e, "count": c} for e, c in ips],
            "top_users": [{"entity": e, "count": c} for e, c in users],
            "most_active_systems": [{"entity": e, "count": c} for e, c in systems],
            "top_actions": [{"entity": e, "count": c} for e, c in actions],
        }

    def get_time_series(self, interval_minutes: int = 15, hours: int = 24) -> list[dict[str, Any]]:
        if interval_minutes < 1 or interval_minutes > 1440 or hours < 1:
            raise ValueError("interval_minutes must be 1-1440 and hours must be at least 1")
        start = _window_start(hours)
        filters = self._base_filters(start)
        
        rows = list(self.db.scalars(
            select(DBEvent.timestamp).where(*filters)
        ))
        
        interval = interval_minutes * 60
        buckets = {}
        for ts in rows:
            if not ts:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            bucket_epoch = int(ts.timestamp()) // interval * interval
            buckets[bucket_epoch] = buckets.get(bucket_epoch, 0) + 1
            
        bucket_start = int(start.timestamp()) // interval * interval
        bucket_end = int(datetime.now(timezone.utc).timestamp()) // interval * interval
        return [
            {
                "timestamp": datetime.fromtimestamp(epoch, timezone.utc),
                "count": buckets.get(epoch, 0),
            }
            for epoch in range(bucket_start, bucket_end + interval, interval)
        ]
