"""Strict three-tier log processing waterfall."""

from datetime import datetime, timezone
import json
import re
from typing import Any
from uuid import uuid4

from .detector import SourceDetector
from .groq_parser import GroqParser
from .mapping_store import InMemoryMappingStore
from .ml_mapper import MLFieldMapper
from .models import LogSignature, MappingRule, UniversalEvent
from .parsers import CEFParser, DynamicMappedParser, JSONParser, SyslogAuthParser, WebAccessParser, SyslogGenericParser


class LogProcessingPipeline:
    def __init__(self) -> None:
        self.detector = SourceDetector()
        self.mapping_store = InMemoryMappingStore()
        self.ml_mapper = MLFieldMapper()
        self.groq_parser = GroqParser()

    def process(self, raw_log: str) -> UniversalEvent:
        clean_log = raw_log.strip().replace("\r", "")
        signature = self.detector.detect(clean_log)

        # Tier 1: formats with a deterministic parser and no learned mapping.
        if signature.format_type == "Syslog_Auth":
            normalized = SyslogAuthParser().parse(clean_log)
            return self._build_event(raw_log, normalized, "deterministic", signature)
        if signature.format_type == "CEF":
            fields = CEFParser().parse(clean_log)
            normalized = self._parse_cef(fields)
            return self._build_event(raw_log, normalized, "deterministic", signature)
        if signature.format_type == "Web_Access":
            normalized = WebAccessParser().parse(clean_log)
            return self._build_event(raw_log, normalized, "deterministic", signature)
        if signature.format_type == "Syslog_Generic":
            normalized = SyslogGenericParser().parse(clean_log)
            return self._build_event(raw_log, normalized, "deterministic", signature)

        # Tier 2: JSON and key-value structures learn a reusable field mapping.
        if signature.format_type in {"JSON", "KeyValue"}:
            fields, direct = self._tier_two_fields(raw_log, signature)
            if direct is not None:
                return self._build_event(raw_log, direct, "deterministic", signature)
            if fields:
                rule = self.mapping_store.get_mapping(signature)
                method = "deterministic_cached"
                if rule is None:
                    rule = self.ml_mapper.generate_mapping(list(fields))
                    self.mapping_store.save_mapping(signature, rule)
                    method = "ml_assisted"
                normalized = DynamicMappedParser(rule).parse(fields)
                return self._build_event(raw_log, normalized, method, signature)

        # Tier 3: genuinely unstructured logs use Groq, or its regex fallback.
        normalized = self.groq_parser.parse(raw_log)
        return self._build_event(raw_log, normalized, "llm_fallback", signature)

    def _tier_two_fields(
        self, raw_log: str, signature: LogSignature
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        if signature.format_type == "JSON":
            parsed = JSONParser().parse(raw_log)
            raw_fields = parsed.get("raw_fields", {})
            has_nested_schema = any(
                isinstance(raw_fields.get(section), dict) and bool(raw_fields[section])
                for section in ("source", "actor", "event")
            )
            if has_nested_schema:
                return {}, parsed
            return raw_fields if isinstance(raw_fields, dict) else {}, None
        return self._extract_key_values(raw_log), None

    @staticmethod
    def _extract_key_values(raw_log: str) -> dict[str, Any]:
        return {
            key: value
            for key, value in re.findall(r"([A-Za-z_][\w.-]*)[=:]\s*([^\s,;]+)", raw_log)
        }

    @staticmethod
    def _parse_cef(fields: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {"source": {}, "actor": {}, "event": {}}
        aliases = {
            "device_vendor": "source.name",
            "device_product": "source.type",
            "src": "actor.source_ip",
            "sourceAddress": "actor.source_ip",
            "suser": "actor.user",
            "user": "actor.user",
            "act": "event.action",
            "action": "event.action",
            "outcome": "event.status",
            "status": "event.status",
            "severity": "event.severity",
        }
        return DynamicMappedParser(
            MappingRule({key: target for key, target in aliases.items() if key in fields}, 1.0)
        ).parse(fields)

    @staticmethod
    def _build_event(
        raw_log: str,
        normalized: dict[str, Any],
        method: str,
        signature: LogSignature,
    ) -> UniversalEvent:
        return UniversalEvent(
            event_id=str(uuid4()),
            timestamp=str(normalized.get("timestamp") or datetime.now(timezone.utc).isoformat()),
            source=normalized.get("source", {}),
            actor=normalized.get("actor", {}),
            event=normalized.get("event", {}),
            raw_event=raw_log,
            processing={
                "method": method,
                "parser": signature.format_type,
                "mapping_version": signature.signature_hash,
            },
        )
