"""Natural-language SIEM query translation and event retrieval."""

import json
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from groq import Groq
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()
load_dotenv("ulpf/.env")

from ..auth import get_current_user
from ..database import get_db
from ..db_models import DBEvent, DBUser

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    message: str
    filters: dict[str, str | None]
    results: list[dict[str, Any]]


_ALLOWED_FILTERS = {"source_ip", "user", "action", "status", "severity"}
_SYSTEM_PROMPT = """You are a SIEM query translator. Translate the user's plain-English question into ONLY one JSON object with exactly these keys: source_ip, user, action, status, severity. Every value must be a string or null. Do not include markdown, explanations, SQL, or additional keys. Extract only explicit constraints from the question. Use null when a constraint is not present."""


def _translate_query(query: str) -> dict[str, str | None]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured")
    client = Groq(api_key=api_key)
    model = os.getenv("GROQ_CHAT_MODEL", os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise HTTPException(status_code=502, detail="Groq returned an invalid query translation") from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Groq query translation failed: {error}") from error
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=502, detail="Groq returned an invalid query translation")
    return {key: str(parsed[key]).strip() if parsed.get(key) is not None else None for key in _ALLOWED_FILTERS}


def _field(event: dict[str, Any], section: str, name: str) -> str | None:
    value = event.get(section, {})
    if not isinstance(value, dict) or value.get(name) is None:
        return None
    return str(value[name])


def _result(row: DBEvent) -> dict[str, Any]:
    normalized = row.normalized_event
    return {
        "event_id": row.event_id,
        "timestamp": row.timestamp,
        "source_type": row.source_type,
        "normalized_event": normalized,
        "raw_event": row.raw_event,
    }


def _analyze_logs(query: str, logs: list[dict[str, Any]]) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured")
    client = Groq(api_key=api_key)
    model = os.getenv("GROQ_CHAT_MODEL", os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))
    
    limited_logs = logs[:20]
    logs_json = json.dumps([{
        "timestamp": str(l.get("timestamp", "")),
        "source_type": l.get("source_type"),
        "normalized_event": l.get("normalized_event")
    } for l in limited_logs])

    system_prompt = (
        "You are a helpful, conversational cybersecurity AI assistant. "
        "The user has asked a question about their logs. "
        "I have provided a JSON dump of the relevant log events below. "
        "Read the logs and answer the user's question directly in a friendly, conversational tone. "
        "Do NOT output markdown tables, do NOT repeat the raw logs, and do NOT provide a generic summary unless asked. "
        "Just answer the specific question naturally based on the data."
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Logs:\n{logs_json}\n\nQuestion: {query}"},
            ],
        )
        return response.choices[0].message.content or "No response generated."
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Groq log analysis failed: {error}") from error


@router.post("/ask", response_model=ChatResponse)
def ask_chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: DBUser = Depends(get_current_user),
) -> ChatResponse:
    filters = _translate_query(payload.query)
    rows = db.scalars(
        select(DBEvent).where(DBEvent.user_id == user.id).order_by(DBEvent.timestamp.desc()).limit(1000)
    ).all()
    results: list[dict[str, Any]] = []
    for row in rows:
        normalized = row.normalized_event
        candidates = {
            "source_ip": _field(normalized, "actor", "source_ip"),
            "user": _field(normalized, "actor", "user"),
            "action": _field(normalized, "event", "action"),
            "status": _field(normalized, "event", "status"),
            "severity": _field(normalized, "event", "severity") or row.severity,
        }
        if all(not expected or (candidates[key] is not None and candidates[key].lower() == expected.lower()) for key, expected in filters.items()):
            results.append(_result(row))
    active = [f"{key.replace('_', ' ')} {value}" for key, value in filters.items() if value]
    description = ", ".join(active) if active else "your recent log activity"
    
    if results:
        message = _analyze_logs(payload.query, results)
    else:
        message = f"I couldn't find events matching {description}."
        
    return ChatResponse(
        message=message,
        filters=filters,
        results=[],
    )
