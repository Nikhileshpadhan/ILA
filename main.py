"""Interactive entry point for the ULPF core engine."""

import sys

from ulpf import LogProcessingPipeline


def read_log() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return input("Paste a log to process (press Enter to exit): ").strip()


def main() -> None:
    raw_log = read_log()
    if not raw_log:
        print("No log provided.")
        return

    pipeline = LogProcessingPipeline()
    event = pipeline.process(raw_log)
    print("Processed output:")
    print(event.to_json())


if __name__ == "__main__":
    main()