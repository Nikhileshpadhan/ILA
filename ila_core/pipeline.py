from typing import Any
from pydantic import ValidationError

from .schema import UniversalEvent
from .preprocessor import PayloadPreProcessor
from .detector import LogDetector
from .parsers import (
    ParsingDowngradeError,
    JSONParser,
    SyslogAuthParser,
    WebAccessParser,
    DynamicKVParser,
    FallbackParser
)
from .ml_mapper import MLFieldMapper
from .groq_parser import GroqParser
from .advanced_mapper import flatten_dict

class LogPipeline:
    def __init__(self, mapping_store=None):
        """
        mapping_store should provide methods:
          - get_mapping(signature_hash) -> dict or None
          - save_mapping(signature_hash, format_type, mapping, confidence)
        """
        self.store = mapping_store
        
        self.json_parser = JSONParser()
        self.syslog_parser = SyslogAuthParser()
        self.web_parser = WebAccessParser()
        self.kv_parser = DynamicKVParser()
        
        self.ml_mapper = MLFieldMapper()
        self.groq_parser = GroqParser()
        self.fallback_parser = FallbackParser()

    def _apply_mapping(self, parsed: dict, mapping: dict[str, str]) -> dict:
        """
        Applies a semantic field mapping to a flat parsed dict.
        """
        result = {}
        
        # Flatten parsed temporarily just in case
        flat_parsed = flatten_dict(parsed)

        for source_field, dest_field in mapping.items():
            val = flat_parsed.get(source_field)
            if val is not None:
                # the mapping now maps directly to flat top-level keys like "user" or "source_ip"
                result[dest_field] = val
                    
        return result

    def process_payload(self, raw_payload: str) -> list[UniversalEvent]:
        chunks = PayloadPreProcessor.chunk_payload(raw_payload)
        events = []

        for chunk in chunks:
            format_type, signature = LogDetector.detect(chunk)
            
            parsed_dict = None
            processing_method = "deterministic"

            try:
                # TIER 1 & TIER 2 logic
                if format_type == "JSON":
                    raw_parsed = self.json_parser.parse(chunk)
                    parsed_dict = self._handle_tier2(raw_parsed, format_type, signature)
                elif format_type == "KeyValue":
                    raw_parsed = self.kv_parser.parse(chunk)
                    parsed_dict = self._handle_tier2(raw_parsed, format_type, signature)
                elif format_type == "Syslog_Auth":
                    parsed_dict = self.syslog_parser.parse(chunk)
                elif format_type == "Web_Access":
                    parsed_dict = self.web_parser.parse(chunk)
                elif format_type == "CEF":
                    raise ParsingDowngradeError("CEF Parser not implemented, falling back")
                else: 
                    raise ParsingDowngradeError("Unstructured format")
                    
            except ParsingDowngradeError:
                # TIER 3 Fallback
                processing_method = "llm_fallback"
                parsed_dict = self.groq_parser.parse(chunk)

            # Build UniversalEvent directly from the flat dictionary with feedback loop
            try:
                event = UniversalEvent(
                    **parsed_dict, 
                    raw_event=chunk, 
                    processing_method=processing_method
                )
            except ValidationError as e:
                # Feedback loop
                error_str = str(e)
                try:
                    corrected = self.groq_parser.parse_with_feedback(parsed_dict, error_str)
                    event = UniversalEvent(
                        **corrected,
                        raw_event=chunk,
                        processing_method="llm_feedback_correction"
                    )
                except Exception:
                    # Drop invalid keys if second pass fails
                    valid_keys = UniversalEvent.model_fields.keys()
                    safe_dict = {k: v for k, v in parsed_dict.items() if k in valid_keys}
                    event = UniversalEvent.model_construct(
                        **safe_dict,
                        raw_event=chunk,
                        processing_method="fallback_partial"
                    )
            events.append(event)

        return events

    def _handle_tier2(self, parsed: dict, format_type: str, signature: str) -> dict:
        """Handles MappingStore check and ML Map generation for JSON/KV."""
        if not self.store:
            return parsed

        mapping = self.store.get_mapping(signature)
        if mapping:
            return self._apply_mapping(parsed, mapping)

        # Flat keys for ML mapper
        flat_parsed = flatten_dict(parsed)

        mapping, confidence = self.ml_mapper.generate_mapping(flat_parsed)
        
        # Save mapping for future
        self.store.save_mapping(signature, format_type, mapping, confidence)
        
        return self._apply_mapping(parsed, mapping)
