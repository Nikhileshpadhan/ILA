"""Log ingestion endpoints."""

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from ulpf.models import UniversalEvent

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
    normalized = event.to_dict()
    timestamp = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
    processing = event.processing
    severity = str(event.event.get("severity") or "info")
    return DBEvent(
        user_id=user_id,
        event_id=event.event_id,
        timestamp=timestamp,
        source_type=str(processing.get("parser", "Unstructured")),
        severity=severity,
        raw_event=event.raw_event,
        normalized_event=normalized,
        processing_method=str(processing.get("method", "unknown")),
        mapping_version=str(processing.get("mapping_version", "")),
    )


def _response(event: UniversalEvent) -> EventResponse:
    return EventResponse(**event.to_dict())


def _pipeline(request: Request, user_id: int) -> Any:
    return request.app.state.get_pipeline(user_id)


def _process_one(pipeline: Any, raw_log: str) -> UniversalEvent:
    if not raw_log.strip():
        raise ValueError("Log cannot be empty")
    return pipeline.process(raw_log)


@router.post("/single", status_code=status.HTTP_201_CREATED)
def ingest_single(
    payload: SingleLogIngestRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: DBUser = Depends(get_current_user),
) -> Any:
    lines = [line for line in payload.log.splitlines() if line.strip()]
    if len(lines) > 1:
        return ingest_batch(BatchLogIngestRequest(logs=lines), request, db, user)

    try:
        event = _process_one(_pipeline(request, user.id), lines[0] if lines else payload.log)
        db.add(_event_row(event, user.id))
        db.commit()
        return _response(event)
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Unable to process log: {error}") from error


def _batch_events(pipeline: Any, logs: Iterable[str], user_id: int) -> tuple[list[DBEvent], list[str]]:
    rows: list[DBEvent] = []
    event_ids: list[str] = []
    for raw_log in logs:
        try:
            event = _process_one(pipeline, raw_log)
            rows.append(_event_row(event, user_id))
            event_ids.append(event.event_id)
        except Exception:
            continue
    return rows, event_ids


@router.post("/batch", response_model=BatchIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_batch(
    payload: BatchLogIngestRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: DBUser = Depends(get_current_user),
) -> BatchIngestResponse:
    rows, event_ids = _batch_events(_pipeline(request, user.id), payload.logs, user.id)
    if rows:
        db.add_all(rows)
        db.commit()
    return BatchIngestResponse(
        processed=len(rows),
        failed=len(payload.logs) - len(rows),
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
    logs = [content] if filename.endswith(".json") else [line for line in content.splitlines() if line.strip()]
    rows, event_ids = _batch_events(_pipeline(request, user.id), logs, user.id)
    if rows:
        db.add_all(rows)
        db.commit()
    return BatchIngestResponse(
        processed=len(rows),
        failed=len(logs) - len(rows),
        sample_event_ids=event_ids[:10],
    )
