from datetime import datetime, timezone
import uuid
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

class UniversalEvent(BaseModel):
    model_config = ConfigDict(extra='ignore')

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: Optional[str] = None
    ingested_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    source_ip: Optional[str] = None
    user: Optional[str] = None
    action: Optional[str] = None
    status: Optional[Literal["success", "failed", "blocked", "unknown"]] = None
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None
    
    processing_method: Literal["deterministic", "ml_assisted", "llm_fallback"]
    raw_event: str

    def to_dict(self) -> dict:
        return self.model_dump(exclude_none=True)

def cast_to_universal(parsed_dict: dict, raw_string: str) -> UniversalEvent:
    """
    Safely maps extracted dictionary to UniversalEvent model.
    """
    # ensure raw_event is always present
    parsed_dict['raw_event'] = raw_string
    
    # default processing_method if missing
    if 'processing_method' not in parsed_dict:
        parsed_dict['processing_method'] = "deterministic"

    # handle nested dicts if they are accidentally passed in, flattening them
    flat_dict = {}
    for k, v in parsed_dict.items():
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                flat_dict[sub_k] = sub_v
        else:
            flat_dict[k] = v

    return UniversalEvent(**flat_dict)
