"""Core data models for normalized events and learned mappings."""

from dataclasses import asdict, dataclass, field
import json
from typing import Any


@dataclass
class UniversalEvent:
    event_id: str
    timestamp: str
    source: dict[str, Any] = field(default_factory=dict)
    actor: dict[str, Any] = field(default_factory=dict)
    event: dict[str, Any] = field(default_factory=dict)
    raw_event: str = ""
    processing: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass(frozen=True)
class LogSignature:
    format_type: str
    signature_hash: str


@dataclass
class MappingRule:
    source_fields_to_universal_fields: dict[str, str]
    confidence: float