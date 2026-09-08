"""Event search and forensic traceability endpoints."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..db_models import DBEvent, DBSourceMapping, DBUser
from ..schemas import EventDetailResponse, EventResponse, PaginatedEventsResponse

router = APIRouter(prefix="/api/v1/events", tags=["events"])


def _event_response(row: DBEvent) -> EventResponse:
    return EventResponse(
        event_id=row.event_id,
        timestamp=row.timestamp.isoformat() if row.timestamp else None,
        ingested_at=row.ingested_at.isoformat() if row.ingested_at else None,
        source_name=row.source_name,
        source_type=row.source_type,
        source_ip=row.source_ip,
        user=row.user,
        action=row.action,
        status=row.status,
        severity=row.severity,
        processing_method=row.processing_method,
        raw_event=row.raw_event
    )


@router.get("/", response_model=PaginatedEventsResponse)
def list_events(
    page: int = 1,
    limit: int = 50,
    source_type: str | None = None,
    severity: str | None = None,
    user_query: str | None = Query(default=None, alias="user"),
    ip: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
) -> PaginatedEventsResponse:
    if page < 1 or limit < 1 or limit > 500:
        raise HTTPException(status_code=422, detail="page must be >= 1 and limit must be 1-500")
    query = select(DBEvent)
    filters: list[Any] = [DBEvent.user_id == current_user.id]
    if source_type:
        filters.append(DBEvent.source_type == source_type)
    if severity:
        filters.append(DBEvent.severity == severity)
        
    if user_query and ip and user_query == ip:
        filters.append(
            or_(
                DBEvent.user == user_query,
                DBEvent.source_ip == ip
            )
        )
    else:
        if user_query:
            filters.append(DBEvent.user == user_query)
        if ip:
            filters.append(DBEvent.source_ip == ip)
            
    if start_time:
        filters.append(DBEvent.timestamp >= start_time)
    if end_time:
        filters.append(DBEvent.timestamp <= end_time)
    query = query.where(*filters).order_by(DBEvent.created_at.desc())
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.offset((page - 1) * limit).limit(limit)).all()
    return PaginatedEventsResponse(
        total=total,
        page=page,
        limit=limit,
        items=[_event_response(row) for row in rows],
    )


@router.get("/{event_id}", response_model=EventDetailResponse)
def get_event(event_id: str, db: Session = Depends(get_db), user: DBUser = Depends(get_current_user)) -> EventDetailResponse:
    row = db.scalar(select(DBEvent).where(DBEvent.event_id == event_id, DBEvent.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventDetailResponse(
        event_id=row.event_id,
        timestamp=row.timestamp.isoformat() if row.timestamp else None,
        ingested_at=row.ingested_at.isoformat() if row.ingested_at else None,
        source_name=row.source_name,
        source_type=row.source_type,
        source_ip=row.source_ip,
        user=row.user,
        action=row.action,
        status=row.status,
        severity=row.severity,
        processing_method=row.processing_method,
        raw_event=row.raw_event,
        id=row.id,
        mapping_version=row.mapping_version,
        created_at=row.created_at,
    )


@router.get("/{event_id}/trace")
def trace_event(event_id: str, db: Session = Depends(get_db), user: DBUser = Depends(get_current_user)) -> dict[str, Any]:
    row = db.scalar(select(DBEvent).where(DBEvent.event_id == event_id, DBEvent.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    mapping = db.scalar(
        select(DBSourceMapping).where(
            DBSourceMapping.signature_hash == f"{user.id}:{row.mapping_version}",
            DBSourceMapping.user_id == user.id,
        )
    )
    return {
        "event_id": row.event_id,
        "raw_log": row.raw_event,
        "parser": row.source_type,
        "processing_method": row.processing_method,
        "mapping_version": row.mapping_version,
        "mapping_rule": mapping.field_mapping if mapping else {},
        "confidence": mapping.confidence if mapping else None,
        "transformation": {
            source_field: f"{source_field} -> {target_field}"
            for source_field, target_field in (mapping.field_mapping.items() if mapping else [])
        },
    }
