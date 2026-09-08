"""Deterministic parsers and mapping application."""

from abc import ABC, abstractmethod
import json
import re
from typing import Any
from datetime import datetime, timezone

from .models import MappingRule


def _normalize_timestamp(ts_str: str) -> str:
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).isoformat()
    except ValueError:
        pass
    try:
        dt = datetime.strptime(ts_str, "%d/%b/%Y:%H:%M:%S %z")
        return dt.isoformat()
    except ValueError:
        pass
    try:
        year = datetime.now(timezone.utc).year
        ts_clean = re.sub(r'\s+', ' ', ts_str)
        dt = datetime.strptime(f"{year} {ts_clean}", "%Y %b %d %H:%M:%S")
        return dt.isoformat() + "Z"
    except ValueError:
        pass
    return datetime.now(timezone.utc).isoformat()


class BaseParser(ABC):
    @abstractmethod
    def parse(self, raw_log: str) -> dict[str, Any]:
        """Parse a raw log into extracted fields."""


class JSONParser(BaseParser):
    def parse(self, raw_log: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_log)
        except json.JSONDecodeError as error:
            raise ValueError("Invalid JSON log") from error
        if not isinstance(parsed, dict):
            raise ValueError("JSON log must contain an object")
        normalized: dict[str, Any] = {"source": {}, "actor": {}, "event": {}}
        for section in ("source", "actor", "event"):
            if isinstance(parsed.get(section), dict):
                normalized[section].update(parsed[section])
        aliases = {
            "username": ("actor", "user"), "user": ("actor", "user"),
            "source_ip": ("actor", "source_ip"), "src_ip": ("actor", "source_ip"),
            "action": ("event", "action"), "status": ("event", "status"),
            "severity": ("event", "severity"), "hostname": ("source", "name"),
            "source_type": ("source", "type"), "timestamp": (None, None),
        }
        for key, (section, name) in aliases.items():
            if key in parsed and section is not None:
                normalized[section][name] = parsed[key]
        if "timestamp" in parsed:
            normalized["timestamp"] = _normalize_timestamp(str(parsed["timestamp"]))
        normalized["raw_fields"] = parsed
        return normalized


class CEFParser(BaseParser):
    def parse(self, raw_log: str) -> dict[str, Any]:
        if "CEF:" not in raw_log:
            raise ValueError("CEF header not found")
        parts = raw_log.split("CEF:", 1)[1].split("|", 7)
        header_names = (
            "cef_version",
            "device_vendor",
            "device_product",
            "device_version",
            "signature_id",
            "name",
            "severity",
        )
        fields: dict[str, Any] = {
            name: value.strip() for name, value in zip(header_names, parts[:7])
        }
        extension_text = parts[7] if len(parts) > 7 else ""
        matches = re.finditer(r"([^=\s]+)=([^=]+)(?=\s+[^=\s]+=|$)", extension_text)
        for match in matches:
            key, value = match.groups()
            fields[key.strip()] = value.strip()
        return fields


class SyslogAuthParser(BaseParser):
    _header = re.compile(
        r"^(?P<timestamp>(?:[A-Z][a-z]{2}\s+[0-9]{1,2}\s+\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}))\s+"
        r"(?P<hostname>\S+)\s+(?P<process>[\w.-]+)(?:\[(?P<pid>\d+)\])?:\s*(?P<message>.*)$"
    )
    _auth = re.compile(
        r"\b(Accepted|Failed|Invalid)\s+(password|publickey|none)\s+for\s+"
        r"(?:invalid user\s+)?(\S+)\s+from\s+([0-9a-fA-F.:]+)",
        re.IGNORECASE,
    )

    def parse(self, raw_log: str) -> dict[str, Any]:
        header = self._header.match(raw_log.strip())
        if not header:
            raise ValueError("Invalid Syslog auth line")
        values = header.groupdict()
        result: dict[str, Any] = {
            "timestamp": _normalize_timestamp(values["timestamp"]),
            "source": {"name": values["hostname"], "type": values["process"]},
            "actor": {},
            "event": {},
        }
        match = self._auth.search(values["message"])
        if match:
            outcome = match.group(1).lower()
            result["actor"] = {"user": match.group(3), "source_ip": match.group(4)}
            result["event"] = {
                "action": "ssh_login",
                "auth_method": match.group(2).lower(),
                "status": "success" if outcome == "accepted" else "failed",
                "severity": "low" if outcome == "accepted" else "high",
            }
        return result


class DynamicMappedParser(BaseParser):
    def __init__(self, mapping_rule: MappingRule) -> None:
        self.mapping_rule = mapping_rule

    def parse(self, raw_log: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(raw_log, str):
            raise TypeError("DynamicMappedParser.parse expects extracted fields, not raw text")
        return self.parse_fields(raw_log)

    def parse_fields(self, fields: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {"source": {}, "actor": {}, "event": {}}
        for source_field, universal_field in self.mapping_rule.source_fields_to_universal_fields.items():
            if source_field not in fields:
                continue
            target = normalized
            parts = universal_field.split(".")
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            if parts:
                target[parts[-1]] = fields[source_field]
        return normalized


class WebAccessParser(BaseParser):
    _pattern = re.compile(
        r'^(?P<ip>\S+)\s+(?P<ident>\S+)\s+(?P<user>\S+)\s+\[(?P<timestamp>[^]]+)\]\s+'
        r'"(?P<method>[A-Z]+)\s+(?P<path>\S+)(?:\s+HTTP/\d\.\d)?"\s+(?P<status>\d{3})\s+(?P<bytes>\S+)'
    )

    def parse(self, raw_log: str) -> dict[str, Any]:
        match = self._pattern.search(raw_log.strip())
        if not match:
            raise ValueError("Invalid Web Access log line")
        values = match.groupdict()
        user = values["user"] if values["user"] != "-" else "anonymous"
        status_code = int(values["status"])
        return {
            "timestamp": _normalize_timestamp(values["timestamp"]),
            "source": {},
            "actor": {"user": user, "source_ip": values["ip"]},
            "event": {
                "action": f"http_{values['method'].lower()}",
                "status": "success" if 200 <= status_code < 400 else "failed",
            },
        }


class SyslogGenericParser(BaseParser):
    _header = re.compile(
        r"^(?P<timestamp>(?:[A-Z][a-z]{2}\s+[0-9]{1,2}\s+\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}))\s+"
        r"(?P<hostname>\S+)\s+(?P<process>[\w.-]+)(?:\[(?P<pid>\d+)\])?:\s*(?P<message>.*)$"
    )

    def parse(self, raw_log: str) -> dict[str, Any]:
        header = self._header.match(raw_log.strip())
        if not header:
            raise ValueError("Invalid Syslog line")
        values = header.groupdict()
        return {
            "timestamp": _normalize_timestamp(values["timestamp"]),
            "source": {"name": values["hostname"], "type": values["process"]},
            "actor": {},
            "event": {"action": "syslog_message"},
        }