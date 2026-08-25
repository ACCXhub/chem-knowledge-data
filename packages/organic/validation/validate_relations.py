from __future__ import annotations

from pathlib import Path

import yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
REACTION_FILES = [
    "reactions.yaml",
    "property_reactions.yaml",
    "polymer_reactions.yaml",
    "lipid_reactions.yaml",
]


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def index_records(files: list[str], key: str) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for filename in files:
        records = load_yaml(DATA_DIR / filename).get(key, [])
        for record in records:
            record_id = record["id"]
            if record_id in result:
                raise ValueError(f"duplicate id {record_id}")
            result[record_id] = record
    return result


def require_reverse(
    *,
    source_kind: str,
    source_id: str,
    target_ids: list[str],
    target_index: dict[str, dict],
    reverse_field: str,
    errors: list[str],
) -> None:
    for target_id in target_ids:
        target = target_index.get(target_id)
        if target is None:
            errors.append(f"{source_kind}:{source_id}: missing target {target_id}")
            continue
        reverse_refs = target.get(reverse_field, [])
        if source_id not in reverse_refs:
            errors.append(
                f"{source_kind}:{source_id} -> {target_id} is not reciprocated in {reverse_field}"
            )


def main() -> int:
    errors: list[str] = []
    reactions = index_records(REACTION_FILES, "reactions")
    experiments = index_records(["experiments.yaml"], "experiments")
    phenomena = index_records(["phenomena.yaml"], "phenomena")

    for reaction_id, reaction in reactions.items():
        require_reverse(
            source_kind="reaction",
            source_id=reaction_id,
            target_ids=reaction.get("experiment_refs", []),
            target_index=experiments,
            reverse_field="reaction_refs",
            errors=errors,
        )
        require_reverse(
            source_kind="reaction",
            source_id=reaction_id,
            target_ids=reaction.get("phenomenon_refs", []),
            target_index=phenomena,
            reverse_field="reaction_refs",
            errors=errors,
        )

    for experiment_id, experiment in experiments.items():
        require_reverse(
            source_kind="experiment",
            source_id=experiment_id,
            target_ids=experiment.get("reaction_refs", []),
            target_index=reactions,
            reverse_field="experiment_refs",
            errors=errors,
        )
        require_reverse(
            source_kind="experiment",
            source_id=experiment_id,
            target_ids=experiment.get("phenomenon_refs", []),
            target_index=phenomena,
            reverse_field="experiment_refs",
            errors=errors,
        )

    for phenomenon_id, phenomenon in phenomena.items():
        require_reverse(
            source_kind="phenomenon",
            source_id=phenomenon_id,
            target_ids=phenomenon.get("reaction_refs", []),
            target_index=reactions,
            reverse_field="phenomenon_refs",
            errors=errors,
        )
        require_reverse(
            source_kind="phenomenon",
            source_id=phenomenon_id,
            target_ids=phenomenon.get("experiment_refs", []),
            target_index=experiments,
            reverse_field="phenomenon_refs",
            errors=errors,
        )

    if errors:
        print("Organic relation validation FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Organic relation validation PASSED")
    print(f"reactions: {len(reactions)}")
    print(f"experiments: {len(experiments)}")
    print(f"phenomena: {len(phenomena)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
