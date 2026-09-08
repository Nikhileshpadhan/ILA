"""Analytics, detection, and correlation endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..analytics.correlator import CrossSourceCorrelator
from ..analytics.metrics import AnalyticsMetrics
from ..analytics.rules import RuleEngine
from ..database import get_db
from ..db_models import DBUser

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


def _run(operation: Any) -> Any:
    try:
        return operation()
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/summary")
def summary(hours: int = 24, db: Session = Depends(get_db), user: DBUser = Depends(get_current_user)) -> dict[str, Any]:
    return _run(lambda: AnalyticsMetrics(db, user.id).get_summary_stats(hours))


@router.get("/top-entities")
def top_entities(
    limit: int = 5,
    hours: int = 24,
    db: Session = Depends(get_db),
    user: DBUser = Depends(get_current_user),
) -> dict[str, Any]:
    return _run(lambda: AnalyticsMetrics(db, user.id).get_top_entities(limit, hours))


@router.get("/time-series")
def time_series(
    interval_minutes: int = 15,
    hours: int = 24,
    db: Session = Depends(get_db),
    user: DBUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    return _run(lambda: AnalyticsMetrics(db, user.id).get_time_series(interval_minutes, hours))


@router.get("/alerts")
def alerts(
    brute_force_threshold: int = 5,
    brute_force_window_minutes: int = 5,
    volume_threshold: int = 50,
    volume_window_minutes: int = 2,
    db: Session = Depends(get_db),
    user: DBUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    def detect() -> list[dict[str, Any]]:
        engine = RuleEngine()
        detections = engine.detect_brute_force(
            db, brute_force_threshold, brute_force_window_minutes, user.id
        )
        detections.extend(engine.detect_suspicious_ip(db, volume_window_minutes, user.id))
        return [alert.to_dict() for alert in detections]

    return _run(detect)


@router.get("/incidents")
def incidents(window_minutes: int = 15, db: Session = Depends(get_db), user: DBUser = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _run(lambda: CrossSourceCorrelator().correlate_by_ip(db, window_minutes, user.id))
