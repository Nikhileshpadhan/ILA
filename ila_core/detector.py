import re
import json
import hashlib

class LogDetector:
    @staticmethod
    def detect(raw_log: str) -> tuple[str, str]:
        """
        Takes a single log string and strictly routes it.
        Returns a tuple: (format_type, signature_hash)
        """
        raw_log = raw_log.strip()
        if not raw_log:
            return ("Unstructured", "empty")

        # 1. JSON
        if raw_log.startswith('{') and raw_log.endswith('}'):
            try:
                parsed = json.loads(raw_log)
                if isinstance(parsed, dict):
                    keys_str = ",".join(sorted(parsed.keys()))
                    sig = hashlib.sha256(keys_str.encode()).hexdigest()[:16]
                    return ("JSON", sig)
            except json.JSONDecodeError:
                pass

        # 2. CEF
        if "CEF:0" in raw_log:
            parts = raw_log.split('|')
            if len(parts) >= 3:
                vendor = parts[1].strip()
                product = parts[2].strip()
                sig = hashlib.sha256(f"{vendor}_{product}".encode()).hexdigest()[:16]
                return ("CEF", sig)
            return ("CEF", "cef_generic")

        # 3. Web_Access
        web_pattern = r'^(\S+)\s+\S+\s+(\S+)\s+\[(.*?)\]\s+"([A-Z]+)\s+.*?'
        if re.search(web_pattern, raw_log):
            return ("Web_Access", "common_log_format_v1")

        # 4. Syslog_Auth
        syslog_auth_pattern = r'^(?:[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2}).*(sshd|sudo)'
        if re.search(syslog_auth_pattern, raw_log, re.IGNORECASE):
            return ("Syslog_Auth", "linux_auth_v1")

        # 5. KeyValue
        # Look for instances of key=value or key: value
        kv_pattern = r'([a-zA-Z0-9_]+)[=:]\s*([^\s,;]+)'
        matches = re.findall(kv_pattern, raw_log)
        if len(matches) >= 2:
            keys_str = ",".join(sorted([m[0] for m in matches]))
            sig = hashlib.sha256(keys_str.encode()).hexdigest()[:16]
            return ("KeyValue", sig)

        # 6. Unstructured
        return ("Unstructured", "unstructured_fallback")
