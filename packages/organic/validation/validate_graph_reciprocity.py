from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"

REACTION_FILES = [
    DATA_DIR / "reactions.yaml",
    DATA_DIR / "property_reactions.yaml",
    DATA_DIR / "polymer_reactions.yaml",
    DATA_DIR / "lipid_reactions.yaml",
]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a mapping at document root")
    return data


def index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["id"]: record for record in records}


def require_backlink(
    *,
    owner_kind: str,
    owner_id: str,
    target_kind: str,
    target_id: str,
    target_records: dict[str, dict[str, Any]],
    backlink_field: str,
    errors: list[str],
) -> None:
    target = target_records.get(target_id)
    if target is None:
        errors.append(f"{owner_kind}:{owner_id}: unknown {target_kind} {target_id}")
        return
    backlinks = target.get(backlink_field, [])
    if owner_id not in backlinks:
        errors.append(
            f"{owner_kind}:{owner_id} -> {target_kind}:{target_id} lacks reciprocal "
            f"{backlink_field}"
        )


def validate_relation_pair(
    *,
    left_kind: str,
    left_records: dict[str, dict[str, Any]],
    left_field: str,
    right_kind: str,
    right_records: dict[str, dict[str, Any]],
    right_field: str,
    errors: list[str],
) -> None:
    for left_id, record in left_records.items():
        for right_id in record.get(left_field, []):
            require_backlink(
                owner_kind=left_kind,
                owner_id=left_id,
                target_kind=right_kind,
                target_id=right_id,
                target_records=right_records,
                backlink_field=right_field,
                errors=errors,
            )
    for right_id, record in right_records.items():
        for left_id in record.get(right_field, []):
            require_backlink(
                owner_kind=right_kind,
                owner_id=right_id,
                target_kind=left_kind,
                target_id=left_id,
                target_records=left_records,
                backlink_field=left_field,
                errors=errors,
            )


def main() -> int:
    errors: list[str] = []

    reactions: list[dict[str, Any]] = []
    for path in REACTION_FILES:
        reactions.extend(load_yaml(path).get("reactions", []))
    experiments = load_yaml(DATA_DIR / "experiments.yaml").get("experiments", [])
    phenomena = load_yaml(DATA_DIR / "phenomena.yaml").get("phenomena", [])

    reaction_index = index(reactions)
    experiment_index = index(experiments)
    phenomenon_index = index(phenomena)

    validate_relation_pair(
        left_kind="reaction",
        left_records=reaction_index,
        left_field="experiment_refs",
        right_kind="experiment",
        right_records=experiment_index,
        right_field="reaction_refs",
        errors=errors,
    )
    validate_relation_pair(
        left_kind="reaction",
        left_records=reaction_index,
        left_field="phenomenon_refs",
        right_kind="phenomenon",
        right_records=phenomenon_index,
        right_field="reaction_refs",
        errors=errors,
    )
    validate_relation_pair(
        left_kind="experiment",
        left_records=experiment_index,
        left_field="phenomenon_refs",
        right_kind="phenomenon",
        right_records=phenomenon_index,
        right_field="experiment_refs",
        errors=errors,
    )

    if errors:
        print("Organic relation graph reciprocity FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Organic relation graph reciprocity PASSED")
    print(f"reactions: {len(reaction_index)}")
    print(f"experiments: {len(experiment_index)}")
    print(f"phenomena: {len(phenomenon_index)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
