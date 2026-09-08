import pytest
from datetime import datetime
from ulpf.models import UniversalEvent, EventInfo, ActorInfo
from ulpf.parsers import _normalize_timestamp

def test_normalize_timestamp():
    # Valid timestamp
    ts = _normalize_timestamp("2023-10-27T10:00:00Z")
    assert ts is not None
    assert isinstance(ts, str)

    # Missing timestamp
    ts_none = _normalize_timestamp(None)
    assert ts_none is None

    # Invalid timestamp
    ts_invalid = _normalize_timestamp("invalid-date")
    assert ts_invalid is None

def test_canonical_schema_compliance():
    # Test valid event
    event = UniversalEvent(
        event_id="123",
        timestamp=None, # explicit null
        ingested_at=datetime.now().isoformat(),
        actor=ActorInfo(user="root"),
        event=EventInfo(action="login", status="failed"),
        raw_event='{"user": "root", "action": "login", "status": "failed"}'
    )
    assert event.timestamp is None
    assert event.ingested_at is not None
    assert event.actor.user == "root"
    assert event.event.status == "failed"

    # Test auto-generation of ingested_at
    event_auto = UniversalEvent(
        event_id="123",
        actor=ActorInfo(),
        event=EventInfo(),
        raw_event="{}"
    )
    assert event_auto.ingested_at is not None
    assert event_auto.timestamp is None
