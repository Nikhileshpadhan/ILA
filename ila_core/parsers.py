import json
import re

class ParsingDowngradeError(Exception):
    """Raised when a deterministic parser fails, triggering a downgrade to a lower tier."""
    pass

class BaseParser:
    def parse(self, raw_log: str) -> dict:
        raise NotImplementedError

class JSONParser(BaseParser):
    def parse(self, raw_log: str) -> dict:
        try:
            parsed = json.loads(raw_log)
            # Flatten parsed JSON mapping to the Essential 12
            # Since JSON could have any keys, we just return the flat dict.
            # We explicitly map standard keys.
            return {
                "source_name": parsed.get("source_name") or parsed.get("app") or parsed.get("source"),
                "source_type": parsed.get("source_type") or parsed.get("type"),
                "source_ip": parsed.get("source_ip") or parsed.get("ip"),
                "user": parsed.get("user") or parsed.get("username"),
                "action": parsed.get("action") or parsed.get("event_action"),
                "status": parsed.get("status") or parsed.get("event_status"),
                "severity": parsed.get("severity") or parsed.get("log_level")
            }
        except Exception as e:
            raise ParsingDowngradeError(f"JSON parsing failed: {e}")

class SyslogAuthParser(BaseParser):
    def parse(self, raw_log: str) -> dict:
        try:
            # sshd[1234]: Accepted publickey for alice from 192.168.1.100 port 50000 ssh2
            user_ip_regex = r"(?:for|user)\s+([a-zA-Z0-9_-]+)(?:\s+from\s+([0-9\.]+))?"
            status_regex = r"(Accepted|Failed|closed|session opened|session closed)"
            
            user_match = re.search(user_ip_regex, raw_log, re.IGNORECASE)
            status_match = re.search(status_regex, raw_log, re.IGNORECASE)
            
            user = user_match.group(1) if user_match else None
            ip = user_match.group(2) if (user_match and len(user_match.groups()) > 1) else None
            
            action = "auth"
            status = "unknown"
            if status_match:
                s = status_match.group(1).lower()
                if "accept" in s or "open" in s:
                    status = "success"
                elif "fail" in s:
                    status = "failed"
                elif "close" in s:
                    status = "success"
                    action = "logout"

            return {
                "user": user,
                "source_ip": ip,
                "action": action,
                "status": status,
                "source_type": "syslog",
                "source_name": "sshd"
            }
        except Exception as e:
            raise ParsingDowngradeError(f"SyslogAuth parsing failed: {e}")

class WebAccessParser(BaseParser):
    def parse(self, raw_log: str) -> dict:
        try:
            # ^(\S+)\s+\S+\s+(\S+)\s+\[(.*?)\]\s+"([A-Z]+)\s+(.*?)\s+(HTTP\/[\d\.]+)"\s+(\d{3})
            pattern = r'^(\S+)\s+\S+\s+(\S+)\s+\[(.*?)\]\s+"([A-Z]+)\s+(.*?)\s+(HTTP\/[\d\.]+)"\s+(\d{3})'
            match = re.search(pattern, raw_log)
            if not match:
                raise ValueError("Regex did not match web access pattern")
                
            ip = match.group(1)
            user = match.group(2) if match.group(2) != '-' else None
            method = match.group(4)
            path = match.group(5)
            status_code = int(match.group(7))
            
            status = "success" if 200 <= status_code < 400 else "failed"
            if status_code in (401, 403):
                status = "blocked"
                
            return {
                "source_ip": ip,
                "user": user,
                "action": f"{method} {path}",
                "status": status,
                "source_type": "web_access"
            }
        except Exception as e:
            raise ParsingDowngradeError(f"WebAccess parsing failed: {e}")

class DynamicKVParser(BaseParser):
    def parse(self, raw_log: str) -> dict:
        try:
            kv_pattern = r'([a-zA-Z0-9_]+)[=:]\s*([^\s,;]+)'
            matches = re.findall(kv_pattern, raw_log)
            if not matches:
                raise ValueError("No key-value pairs found")
                
            parsed = {k.lower(): v for k, v in matches}
            
            user = parsed.get("user") or parsed.get("actor") or parsed.get("username")
            ip = parsed.get("ip") or parsed.get("remote") or parsed.get("src") or parsed.get("source_ip")
            action = parsed.get("action") or parsed.get("task") or parsed.get("cmd")
            status = parsed.get("status") or parsed.get("outcome") or parsed.get("result")
            source_name = parsed.get("app") or parsed.get("source")
            
            # Map outcome -> status
            if status == "denied":
                status = "blocked"
            elif status == "ok":
                status = "success"
                
            return {
                "user": user,
                "source_ip": ip,
                "action": action,
                "status": status,
                "source_name": source_name,
                "source_type": "key_value"
            }
        except Exception as e:
            raise ParsingDowngradeError(f"KV parsing failed: {e}")

class FallbackParser(BaseParser):
    def parse(self, raw_log: str) -> dict:
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ip_match = re.search(ip_pattern, raw_log)
        ip = ip_match.group(0) if ip_match else None
        
        status = "unknown"
        raw_lower = raw_log.lower()
        if "fail" in raw_lower or "error" in raw_lower:
            status = "failed"
        elif "deny" in raw_lower or "denied" in raw_lower or "block" in raw_lower:
            status = "blocked"
        elif "success" in raw_lower or "accept" in raw_lower or "ok" in raw_lower:
            status = "success"
            
        action = "unknown"
        if "login" in raw_lower or "auth" in raw_lower:
            action = "login"
            
        return {
            "source_ip": ip,
            "action": action,
            "status": status,
            "source_type": "unstructured"
        }
