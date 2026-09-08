"""In-memory storage for learned field mappings."""

from .models import LogSignature, MappingRule


class InMemoryMappingStore:
    def __init__(self) -> None:
        self._mappings: dict[LogSignature, MappingRule] = {}

    def get_mapping(self, signature: LogSignature) -> MappingRule | None:
        return self._mappings.get(signature)

    def save_mapping(self, signature: LogSignature, rule: MappingRule) -> None:
        self._mappings[signature] = rule