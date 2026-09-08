"""Learned mapping inspection and human-approval endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..db_models import DBSourceMapping, DBUser
from ..schemas import MappingRuleResponse, MappingRuleUpdate

router = APIRouter(prefix="/api/v1/mappings", tags=["mappings"])


@router.get("/", response_model=list[MappingRuleResponse])
def list_mappings(db: Session = Depends(get_db), user: DBUser = Depends(get_current_user)) -> list[MappingRuleResponse]:
    rows = db.scalars(select(DBSourceMapping).where(DBSourceMapping.user_id == user.id).order_by(DBSourceMapping.updated_at.desc())).all()
    return [MappingRuleResponse.model_validate(row) for row in rows]


@router.put("/{signature_hash}", response_model=MappingRuleResponse)
def update_mapping(
    signature_hash: str,
    payload: MappingRuleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: DBUser = Depends(get_current_user),
) -> MappingRuleResponse:
    row = db.scalar(
        select(DBSourceMapping).where(DBSourceMapping.signature_hash == signature_hash, DBSourceMapping.user_id == user.id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Mapping not found")
    row.field_mapping = payload.field_mapping
    row.confidence = payload.confidence
    row.is_approved = payload.is_approved
    db.commit()
    db.refresh(row)
    request.app.state.mapping_store.update_mapping(
        signature_hash,
        payload.field_mapping,
        payload.confidence,
        payload.is_approved,
    )
    return MappingRuleResponse.model_validate(row)


@router.delete("/{signature_hash}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mapping(
    signature_hash: str,
    request: Request,
    db: Session = Depends(get_db),
    user: DBUser = Depends(get_current_user),
) -> None:
    row = db.scalar(
        select(DBSourceMapping).where(DBSourceMapping.signature_hash == signature_hash, DBSourceMapping.user_id == user.id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.delete(row)
    db.commit()
    request.app.state.mapping_store.delete_mapping(signature_hash)
