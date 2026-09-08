import json

class PayloadPreProcessor:
    @staticmethod
    def chunk_payload(raw_input: str) -> list[str]:
        """
        Chunks the raw input payload into individual log string representations.
        Resolves multi-line JSON pretty-print bugs.
        """
        raw_input = raw_input.strip()
        if not raw_input:
            return []

        try:
            parsed = json.loads(raw_input)
            # Rule 1: JSON Array
            if isinstance(parsed, list):
                return [json.dumps(item) for item in parsed]
            # Rule 2: JSON Object
            elif isinstance(parsed, dict):
                return [json.dumps(parsed)]
        except json.JSONDecodeError:
            # Not valid standard JSON, proceed to Rule 3
            pass

        # Rule 3: Plain Text / NDJSON
        chunks = []
        for line in raw_input.split('\n'):
            line = line.strip()
            if line:
                chunks.append(line)
        return chunks
