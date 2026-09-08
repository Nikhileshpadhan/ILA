"""Database-backed mapping store with an in-memory hot cache."""

from collections.abc import Callable
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .db_models import DBSourceMapping


class DatabaseMappingStore:
    def __init__(self, session_factory: Callable[[], Session], user_id: int | None = None) -> None:
        self.session_factory = session_factory
        self.user_id = user_id
        self._cache: dict[str, dict[str, str]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        with self.session_factory() as db:
            query = select(DBSourceMapping)
            if self.user_id is not None:
                query = query.where(DBSourceMapping.user_id == self.user_id)
            rows = db.scalars(query).all()
            self._cache = {
                row.signature_hash: dict(row.field_mapping)
                for row in rows
                if row.is_approved
            }

    def get_mapping(self, signature: str) -> dict[str, str] | None:
        return self._cache.get(self._storage_signature(signature))

    def save_mapping(self, signature: str, format_type: str, mapping: dict[str, str], confidence: float) -> None:
        with self.session_factory() as db:
            storage_signature = self._storage_signature(signature)
            row = db.scalar(select(DBSourceMapping).where(DBSourceMapping.signature_hash == storage_signature))
            if row is None:
                row = DBSourceMapping(
                    signature_hash=storage_signature,
                    format_type=format_type,
                    field_mapping=dict(mapping),
                    confidence=confidence,
                    is_approved=True,
                    user_id=self.user_id,
                )
                db.add(row)
            else:
                row.format_type = format_type
                row.field_mapping = dict(mapping)
                row.confidence = confidence
                row.is_approved = True
                row.user_id = self.user_id
            db.commit()
        self._cache[storage_signature] = dict(mapping)

    def _storage_signature(self, signature_hash: str) -> str:
        return f"{self.user_id}:{signature_hash}" if self.user_id is not None else signature_hash

    def update_mapping(
        self,
        signature_hash: str,
        field_mapping: dict[str, str],
        confidence: float,
        is_approved: bool,
    ) -> DBSourceMapping | None:
        with self.session_factory() as db:
            row = db.scalar(select(DBSourceMapping).where(DBSourceMapping.signature_hash == signature_hash))
            if row is None:
                return None
            row.field_mapping = dict(field_mapping)
            row.confidence = confidence
            row.is_approved = is_approved
            db.commit()
            db.refresh(row)
            
            # The cache key needs to be the base signature without user_id prefix if we strip it, 
            # but wait, the signature passed here might be the storage signature?
            # Actually, `self._cache` uses the original signature without prefix if we look at `_load_cache`.
            # Wait, `_load_cache` uses `row.signature_hash` which includes the prefix!
            # So `self._cache` key is `row.signature_hash`.
            
            if is_approved:
                self._cache[row.signature_hash] = dict(field_mapping)
            else:
                self._cache.pop(row.signature_hash, None)
            return row

    def delete_mapping(self, signature_hash: str) -> bool:
        with self.session_factory() as db:
            row = db.scalar(
                select(DBSourceMapping).where(DBSourceMapping.signature_hash == signature_hash)
            )
            if row is None:
                return False
                
            db.execute(delete(DBSourceMapping).where(DBSourceMapping.id == row.id))
            db.commit()
        self._cache.pop(row.signature_hash, None)
        return True
