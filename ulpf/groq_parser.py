"""Optional Groq-assisted normalization for ambiguous log fields."""

import json
import os
import re
from datetime import datetime, timezone
from typing import Any

from groq import Groq


class GroqParser:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=key) if key else None
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def parse(self, raw_log: str) -> dict[str, Any]:
        if self.client is None:
            return self._regex_fallback(raw_log)
        try:
            response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Normalize the log into JSON with exactly these top-level objects: "
                        "timestamp, source, actor, event. Use null for unknown scalar values "
                        "and empty objects when no values are available. source keys are type "
                        "and name; actor keys are user and source_ip; event keys are action, "
                        "status, and severity. Return JSON only."
                    ),
                },
                {"role": "user", "content": raw_log},
            ],
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("Groq response must be a JSON object")
            return parsed
        except Exception:
            return self._regex_fallback(raw_log)

    @staticmethod
    def _regex_fallback(raw_log: str) -> dict[str, Any]:
        ip_match = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", raw_log)
        timestamp_match = re.search(
            r"(?:[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
            raw_log,
        )
        user_match = re.search(r"\b(?:user|for|by)\s+([a-zA-Z0-9_-]+)\b", raw_log, re.IGNORECASE)
        
        status = "unknown"
        lower_log = raw_log.lower()
        if any(w in lower_log for w in ("fail", "denied", "error")):
            status = "failed"
        elif any(w in lower_log for w in ("accept", "success", "allow")):
            status = "success"

        severity = "info"
        if "critical" in lower_log or "alert" in lower_log:
            severity = "critical"
        elif "error" in lower_log:
            severity = "error"
        elif "warn" in lower_log:
            severity = "warning"

        action = "unstructured_log"
        if status != "unknown":
            action = f"unstructured_{status}"

        actor = {}
        if ip_match:
            actor["source_ip"] = ip_match.group(0)
        if user_match:
            matched_user = user_match.group(1)
            if matched_user.lower() not in ("the", "a", "an", "this", "that"):
                actor["user"] = matched_user

        return {
            "timestamp": timestamp_match.group(0) if timestamp_match else datetime.now(timezone.utc).isoformat(),
            "source": {},
            "actor": actor,
            "event": {"action": action, "status": status, "severity": severity},
        }