"""Log ingestion endpoints."""

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from ila_core.schema import UniversalEvent
from ila_core.pipeline import LogPipeline

from ..auth import get_current_user
from ..database import get_db
from ..db_models import DBEvent, DBUser
from ..schemas import (
    BatchIngestResponse,
    BatchLogIngestRequest,
    EventResponse,
    SingleLogIngestRequest,
)

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])

def _event_row(event: UniversalEvent, user_id: int) -> DBEvent:
    timestamp = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00")) if event.timestamp else None
    return DBEvent(
        user_id=user_id,
        event_id=event.event_id,
        timestamp=timestamp,
        source_name=event.source_name,
        source_type=event.source_type,
        source_ip=event.source_ip,
        user=event.user,
        action=event.action,
        status=event.status,
        severity=event.severity,
        raw_event=event.raw_event,
        processing_method=event.processing_method,
        mapping_version=""
    )

def _response(event: UniversalEvent) -> EventResponse:
    return EventResponse(**event.to_dict())

def _pipeline(request: Request, user_id: int) -> LogPipeline:
    return request.app.state.get_pipeline(user_id)


@router.post("/single", status_code=status.HTTP_201_CREATED)
def ingest_single(
    payload: SingleLogIngestRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: DBUser = Depends(get_current_user),
) -> Any:
    if not payload.log.strip():
        raise HTTPException(status_code=400, detail="Log cannot be empty")
        
    try:
        pipeline = _pipeline(request, user.id)
        events = pipeline.process_payload(payload.log)
        
        if not events:
            raise ValueError("No events parsed")
            
        # Single log might chunk into multiple
        if len(events) > 1:
            rows = []
            event_ids = []
            for event in events:
                rows.append(_event_row(event, user.id))
                event_ids.append(event.event_id)
            db.add_all(rows)
            db.commit()
            return BatchIngestResponse(
                processed=len(rows),
                failed=0,
                sample_event_ids=event_ids[:10],
            )

        event = events[0]
        db.add(_event_row(event, user.id))
        db.commit()
        return _response(event)
    except Exception as error:
        db.rollback()
        import traceback; err = traceback.format_exc()
        raise HTTPException(status_code=422, detail=f"Unable to process log: {error}\n{err}") from error


@router.post("/batch", response_model=BatchIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_batch(
    payload: BatchLogIngestRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: DBUser = Depends(get_current_user),
) -> BatchIngestResponse:
    pipeline = _pipeline(request, user.id)
    rows = []
    event_ids = []
    failed_count = 0
    
    for raw_log in payload.logs:
        try:
            events = pipeline.process_payload(raw_log)
            for event in events:
                rows.append(_event_row(event, user.id))
                event_ids.append(event.event_id)
        except Exception:
            failed_count += 1
            
    if rows:
        db.add_all(rows)
        db.commit()
        
    return BatchIngestResponse(
        processed=len(rows),
        failed=failed_count,
        sample_event_ids=event_ids[:10],
    )


@router.post("/upload", response_model=BatchIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_upload(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: DBUser = Depends(get_current_user),
) -> BatchIngestResponse:
    filename = (file.filename or "").lower()
    if not filename.endswith((".log", ".txt", ".json", ".csv")):
        raise HTTPException(status_code=415, detail="Supported files: .log, .txt, .json, .csv")
        
    content = (await file.read()).decode("utf-8", errors="replace")
    
    pipeline = _pipeline(request, user.id)
    rows = []
    event_ids = []
    failed_count = 0
    
    try:
        events = pipeline.process_payload(content)
        for event in events:
            rows.append(_event_row(event, user.id))
            event_ids.append(event.event_id)
    except Exception:
        failed_count += 1
        
    if rows:
        db.add_all(rows)
        db.commit()
        
    return BatchIngestResponse(
        processed=len(rows),
        failed=failed_count,
        sample_event_ids=event_ids[:10],
    )
