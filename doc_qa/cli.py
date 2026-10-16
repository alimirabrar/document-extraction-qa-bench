"""Command-line interface for document extraction evaluation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .evaluator import evaluate, load_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare extracted JSON fields with ground truth in JSONL.")
    parser.add_argument("data_file", help="Path to evaluation JSONL")
    parser.add_argument("--out", help="Optional path for a JSON report")
    args = parser.parse_args()
    try:
        report = evaluate(load_jsonl(args.data_file))
        rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.out:
            Path(args.out).write_text(rendered, encoding="utf-8")
        sys.stdout.write(rendered)
        return 0
    except (OSError, ValueError) as exc:
        print(f"doc-qa: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
