#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SCHEMA = ROOT / "schema" / "catalog-v1.schema.json"

DATA_FILES = [
    DATA / "element_scope.jsonl",
    DATA / "v1" / "element_scope.ext.jsonl",
    DATA / "ions.jsonl",
    DATA / "v1" / "ions.ext.jsonl",
    DATA / "substances.jsonl",
    DATA / "v1" / "substances.01.ext.jsonl",
    DATA / "v1" / "substances.02.ext.jsonl",
    DATA / "v1" / "substances.03.ext.jsonl",
    DATA / "reactions.jsonl",
    DATA / "v1" / "reactions.01.ext.jsonl",
    DATA / "v1" / "reactions.02.ext.jsonl",
    DATA / "v1" / "reactions.03.ext.jsonl",
    DATA / "v1" / "reactions.04.ext.jsonl",
    DATA / "phenomena.jsonl",
    DATA / "v1" / "phenomena.ext.jsonl",
    DATA / "experiments.jsonl",
    DATA / "v1" / "experiments.ext.jsonl",
    DATA / "concepts.jsonl",
    DATA / "v1" / "concepts.ext.jsonl",
    DATA / "v1" / "exam_tags.jsonl",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    count = 0
    for path in DATA_FILES:
        for lineno, row in enumerate(load_jsonl(path), 1):
            count += 1
            for error in validator.iter_errors(row):
                location = ".".join(str(part) for part in error.absolute_path)
                errors.append(f"{path.relative_to(ROOT)}:{lineno}:{location}: {error.message}")
    if errors:
        print("JSON_SCHEMA_ERRORS:")
        for error in errors:
            print("  " + error)
        raise SystemExit(1)
    print(f"JSON Schema conformance: OK ({count} canonical records)")


if __name__ == "__main__":
    main()
