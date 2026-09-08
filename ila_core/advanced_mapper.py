import re

def flatten_dict(d: dict, parent_key: str = '', sep: str = '_') -> dict:
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

class HeuristicEvaluator:
    _IPV4_PATTERN = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    _STATUS_WORDS = {"success", "failed", "blocked", "error", "ok", "passed", "denied", "failure"}
    _SEVERITY_WORDS = {"low", "medium", "high", "critical", "info", "warn", "warning", "error", "fatal"}
    
    @staticmethod
    def is_ipv4(val: str) -> bool:
        return bool(HeuristicEvaluator._IPV4_PATTERN.match(str(val)))
        
    @staticmethod
    def is_status_keyword(val: str) -> bool:
        return str(val).lower() in HeuristicEvaluator._STATUS_WORDS

    @staticmethod
    def is_severity_keyword(val: str) -> bool:
        return str(val).lower() in HeuristicEvaluator._SEVERITY_WORDS

    @staticmethod
    def boost_scores(key: str, value: any, similarities: list[float], targets: list[str]) -> list[float]:
        boosted = list(similarities)
        val_str = str(value).strip() if value is not None else ""
        if not val_str:
            return boosted
            
        is_ip = HeuristicEvaluator.is_ipv4(val_str)
        is_status = HeuristicEvaluator.is_status_keyword(val_str)
        is_sev = HeuristicEvaluator.is_severity_keyword(val_str)
        
        for i, target in enumerate(targets):
            if is_ip and target in ("source_ip", "target_ip"):
                boosted[i] += 0.8
            if is_status and target == "status":
                boosted[i] += 0.8
            if is_sev and target == "severity":
                boosted[i] += 0.8
                
        return boosted
