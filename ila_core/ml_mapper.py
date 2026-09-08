from sentence_transformers import SentenceTransformer, util
from .advanced_mapper import HeuristicEvaluator

class MLFieldMapper:
    def __init__(self) -> None:
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.canonical_targets: dict[str, str] = {
            "source_name": "hostname host device server application name app source",
            "source_type": "log source type format category",
            "source_ip": "source ip client remote_host remote address src remote_ip",
            "user": "username user account uid principal actor",
            "action": "operation action command activity task event_action",
            "status": "result status outcome success failure blocked verdict event_status",
            "severity": "severity priority risk level log_level",
            "timestamp": "timestamp time date occurred at",
        }
        self.canonical_embeddings = self.model.encode(
            list(self.canonical_targets.values()), convert_to_tensor=True
        )
        self.exact_aliases: dict[str, str] = {
            "username": "user",
            "actor": "user",
            "user_name": "user",
            "user.name": "user",
            "uid": "user",
            "src_ip": "source_ip",
            "client.ip": "source_ip",
            "remote": "source_ip",
            "src": "source_ip",
            "client": "source_ip",
            "ip": "source_ip",
            "task": "action",
            "operation": "action",
            "cmd": "action",
            "outcome": "status",
            "result": "status",
            "level": "severity",
            "app": "source_name",
            "hostname": "source_name",
            "host": "source_name",
            "@timestamp": "timestamp",
            "time": "timestamp",
        }

    def generate_mapping(self, parsed_dict: dict, threshold: float = 0.28) -> tuple[dict[str, str], float]:
        if not parsed_dict:
            return {}, 0.0
        targets = list(self.canonical_targets)
        mapping: dict[str, str] = {}
        accepted_scores: list[float] = []
        unresolved_keys: list[str] = []
        unresolved_values: list[any] = []
        for key, val in parsed_dict.items():
            exact_target = self.exact_aliases.get(key.lower().replace("-", "_"))
            if exact_target is not None:
                mapping[key] = exact_target
                accepted_scores.append(1.0)
                continue
            unresolved_keys.append(key)
            unresolved_values.append(val)

        if unresolved_keys:
            key_embeddings = self.model.encode(unresolved_keys, convert_to_tensor=True)
            similarities = util.cos_sim(key_embeddings, self.canonical_embeddings)
        else:
            similarities = None

        for index, key in enumerate(unresolved_keys):
            assert similarities is not None
            # Extract basic similarities
            raw_scores = [float(similarities[index][i]) for i in range(len(targets))]
            # Apply heuristics
            boosted_scores = HeuristicEvaluator.boost_scores(key, unresolved_values[index], raw_scores, targets)
            
            best_index = int(max(range(len(boosted_scores)), key=boosted_scores.__getitem__))
            score = boosted_scores[best_index]
            
            if score >= threshold:
                mapping[key] = targets[best_index]
                accepted_scores.append(score)
        confidence = sum(accepted_scores) / len(accepted_scores) if accepted_scores else 0.0
        return mapping, confidence
