"""Semantic field mapping using sentence-transformers."""

from sentence_transformers import SentenceTransformer, util

from .models import MappingRule


class MLFieldMapper:
    def __init__(self) -> None:
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.canonical_targets: dict[str, str] = {
            "actor.user": "username user account uid principal",
            "actor.source_ip": "source ip client remote_host remote address",
            "event.action": "operation action command activity",
            "event.status": "result status outcome success failure",
            "event.severity": "severity priority risk level",
            "source.name": "hostname host device server application name",
            "source.type": "log source type format category",
            "timestamp": "timestamp time date occurred at",
        }
        self.canonical_embeddings = self.model.encode(
            list(self.canonical_targets.values()), convert_to_tensor=True
        )
        self.exact_aliases: dict[str, str] = {
            "username": "actor.user",
            "user": "actor.user",
            "user_name": "actor.user",
            "user.name": "actor.user",
            "user.id": "actor.user",
            "usr_id": "actor.user",
            "usr": "actor.user",
            "uid": "actor.user",
            "source_ip": "actor.source_ip",
            "src_ip": "actor.source_ip",
            "source.ip": "actor.source_ip",
            "source.address": "actor.source_ip",
            "client.ip": "actor.source_ip",
            "client.address": "actor.source_ip",
            "src": "actor.source_ip",
            "client_addr": "actor.source_ip",
            "client_address": "actor.source_ip",
            "client": "actor.source_ip",
            "action": "event.action",
            "event.action": "event.action",
            "op_code": "event.action",
            "op": "event.action",
            "operation": "event.action",
            "status": "event.status",
            "event.status": "event.status",
            "event.outcome": "event.status",
            "outcome": "event.status",
            "verdict": "event.status",
            "result": "event.status",
            "stat": "event.status",
            "severity": "event.severity",
            "log.level": "event.severity",
            "level": "event.severity",
            "sev": "event.severity",
            "pri": "event.severity",
            "hostname": "source.name",
            "host.name": "source.name",
            "device.name": "source.name",
            "observer.name": "source.name",
            "host": "source.name",
            "device": "source.name",
            "observer.type": "source.type",
            "timestamp": "timestamp",
            "@timestamp": "timestamp",
            "event.created": "timestamp",
        }

    def generate_mapping(self, unknown_keys: list[str], threshold: float = 0.28) -> MappingRule:
        if not unknown_keys:
            return MappingRule({}, 0.0)
        targets = list(self.canonical_targets)
        mapping: dict[str, str] = {}
        accepted_scores: list[float] = []
        unresolved_keys: list[str] = []
        for key in unknown_keys:
            exact_target = self.exact_aliases.get(key.lower().replace("-", "_"))
            if exact_target is not None:
                mapping[key] = exact_target
                accepted_scores.append(1.0)
                continue
            unresolved_keys.append(key)

        if unresolved_keys:
            key_embeddings = self.model.encode(unresolved_keys, convert_to_tensor=True)
            similarities = util.cos_sim(key_embeddings, self.canonical_embeddings)
        else:
            similarities = None

        for index, key in enumerate(unresolved_keys):
            assert similarities is not None
            best_index = int(similarities[index].argmax())
            score = float(similarities[index][best_index])
            if score >= threshold:
                mapping[key] = targets[best_index]
                accepted_scores.append(score)
        confidence = sum(accepted_scores) / len(accepted_scores) if accepted_scores else 0.0
        return MappingRule(mapping, confidence)