"""Database-backed mapping store with an in-memory hot cache."""

from collections.abc import Callable
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ulpf.models import LogSignature, MappingRule

from .db_models import DBSourceMapping


class DatabaseMappingStore:
    def __init__(self, session_factory: Callable[[], Session], user_id: int | None = None) -> None:
        self.session_factory = session_factory
        self.user_id = user_id
        self._cache: dict[LogSignature, MappingRule] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        with self.session_factory() as db:
            query = select(DBSourceMapping)
            if self.user_id is not None:
                query = query.where(DBSourceMapping.user_id == self.user_id)
            rows = db.scalars(query).all()
            self._cache = {
                LogSignature(row.format_type, row.signature_hash): MappingRule(
                    dict(row.field_mapping), row.confidence
                )
                for row in rows
                if row.is_approved
            }

    def get_mapping(self, signature: LogSignature) -> MappingRule | None:
        return self._cache.get(signature)

    def save_mapping(self, signature: LogSignature, rule: MappingRule) -> None:
        with self.session_factory() as db:
            storage_signature = self._storage_signature(signature.signature_hash)
            row = db.scalar(select(DBSourceMapping).where(DBSourceMapping.signature_hash == storage_signature))
            if row is None:
                row = DBSourceMapping(
                    signature_hash=storage_signature,
                    format_type=signature.format_type,
                    field_mapping=dict(rule.source_fields_to_universal_fields),
                    confidence=rule.confidence,
                    is_approved=True,
                    user_id=self.user_id,
                )
                db.add(row)
            else:
                row.format_type = signature.format_type
                row.field_mapping = dict(rule.source_fields_to_universal_fields)
                row.confidence = rule.confidence
                row.is_approved = True
                row.user_id = self.user_id
            db.commit()
        self._cache[signature] = MappingRule(
            dict(rule.source_fields_to_universal_fields), rule.confidence
        )

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
            signature = LogSignature(row.format_type, row.signature_hash)
            if is_approved:
                self._cache[signature] = MappingRule(dict(field_mapping), confidence)
            else:
                self._cache.pop(signature, None)
            return row

    def delete_mapping(self, signature_hash: str) -> bool:
        with self.session_factory() as db:
            row = db.scalar(
                select(DBSourceMapping).where(DBSourceMapping.signature_hash == signature_hash)
            )
            if row is None:
                return False
            signature = LogSignature(row.format_type, row.signature_hash)
            db.execute(delete(DBSourceMapping).where(DBSourceMapping.id == row.id))
            db.commit()
        self._cache.pop(signature, None)
        return True
