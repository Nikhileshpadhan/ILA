import json
import os
import re
from typing import Any

from groq import Groq
from .parsers import BaseParser, FallbackParser

class GroqParser(BaseParser):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=key) if key else None
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.fallback = FallbackParser()

    def pre_tag_text(self, raw_text: str) -> str:
        # Pre-tag IP addresses
        tagged = re.sub(r"\b((?:[0-9]{1,3}\.){3}[0-9]{1,3})\b", r"<IP: \1>", raw_text)
        # Pre-tag verbs
        tagged = re.sub(r"\b(GET|POST|PUT|DELETE|PATCH)\b", r"<VERB: \1>", tagged)
        # Pre-tag status
        tagged = re.sub(r"\b(failed|blocked|success|error|denied)\b", r"<STATUS: \1>", tagged, flags=re.IGNORECASE)
        return tagged

    def parse(self, raw_log: str) -> dict[str, Any]:
        if self.client is None:
            return self.fallback.parse(raw_log)
        
        tagged_log = self.pre_tag_text(raw_log)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Normalize the log into a flat JSON object strictly using only these keys: "
                            "timestamp, source_name, source_type, source_ip, user, action, status, severity. "
                            "Use null for unknown scalar values. Do not use nested objects. "
                            "status must be one of: success, failed, blocked, unknown. "
                            "severity must be one of: low, medium, high, critical. Return JSON only. "
                            "Use the <TAGS> as strong hints for your extraction."
                        ),
                    },
                    {"role": "user", "content": tagged_log},
                ],
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("Groq response must be a JSON object")
            return parsed
        except Exception:
            return self.fallback.parse(raw_log)

    def parse_with_feedback(self, extracted_data: dict, error_string: str) -> dict[str, Any]:
        if self.client is None:
            raise Exception("No client")
            
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are correcting a JSON log extraction. Return a flat JSON object."
                },
                {
                    "role": "user", 
                    "content": f"The following log was extracted as {json.dumps(extracted_data)}, but failed validation: {error_string}. Please correct the extraction to strictly match the schema."
                },
            ],
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("Groq response must be a JSON object")
        return parsed
