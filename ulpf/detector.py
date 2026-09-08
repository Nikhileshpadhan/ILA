"""Heuristic source format detection."""

import hashlib
import re

from .models import LogSignature


class SourceDetector:
    def detect(self, raw_log: str) -> LogSignature:
        value = raw_log.strip().replace("\r", "")
        if value.startswith("{") and value.endswith("}"):
            return LogSignature("JSON", self._hash_shape(value))
        if "CEF:" in raw_log:
            header = raw_log.split("CEF:", 1)[1].split("|", 5)
            vendor = header[1].strip() if len(header) > 1 else ""
            product = header[2].strip() if len(header) > 2 else ""
            return LogSignature("CEF", f"{vendor}:{product}")
        if "LEEF:" in raw_log:
            return LogSignature("LEEF", "leef_v1")
        web_pattern = r'^\S+\s+\S+\s+\S+\s+\[[^]]+\]\s+"[A-Z]+\s+[^\"]+"\s+\d{3}\s+\S+'
        if re.search(web_pattern, value, re.MULTILINE):
            return LogSignature("Web_Access", "common_log_format_v1")
        syslog_pattern = r"^(?:[A-Z][a-z]{2}\s+[0-9]{1,2}\s+\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
        if re.search(syslog_pattern, value, re.MULTILINE):
            if re.search(r"sshd|sudo|systemd-logind|auth", value, re.IGNORECASE):
                return LogSignature("Syslog_Auth", "linux_auth_v1")
            return LogSignature("Syslog_Generic", "syslog_generic_v1")
        if len(re.findall(r"(\w+)[=:]\s*([^\s,;]+)", raw_log)) >= 2:
            return LogSignature("KeyValue", self._hash_shape(raw_log))
        return LogSignature("Unstructured", self._hash_shape(raw_log))

    @staticmethod
    def _hash_shape(raw_log: str) -> str:
        format_hint = re.sub(r"[A-Za-z0-9]+", "<value>", raw_log.strip())
        return hashlib.sha256(format_hint.encode("utf-8")).hexdigest()