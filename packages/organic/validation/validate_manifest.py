from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
SCHEMA_DIR = PACKAGE_ROOT / "schema"

DATA_FILES = {
    "substances": ["core_substances.yaml", "extended_substances.yaml", "polymer_substances.yaml", "lipid_substances.yaml"],
    "reactions": ["reactions.yaml", "property_reactions.yaml", "polymer_reactions.yaml", "lipid_reactions.yaml"],
    "concepts": ["concepts.yaml", "structure_concepts.yaml", "biomolecule_concepts.yaml", "applied_concepts.yaml"],
    "chemical_classes": ["classes.yaml", "biomolecule_classes.yaml"],
}


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def count_records(files: list[str], key: str) -> int:
    total = 0
    for filename in files:
        records = load_yaml(DATA_DIR / filename).get(key, [])
        if not isinstance(records, list):
            raise ValueError(f"{filename}: {key} must be a list")
        total += len(records)
    return total


def main() -> int:
    errors: list[str] = []
    manifest = load_yaml(PACKAGE_ROOT / "package.yaml")
    with (SCHEMA_DIR / "package_manifest.schema.json").open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    for issue in sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in issue.path)
        errors.append(f"package.yaml:{location}: {issue.message}")

    fg_doc = load_yaml(DATA_DIR / "functional_groups.yaml")
    curriculum = load_yaml(DATA_DIR / "curriculum_coverage.yaml")["coverage"]
    crossrefs = load_yaml(DATA_DIR / "identity_crossrefs.yaml").get("crossrefs", [])
    deferrals = load_yaml(DATA_DIR / "identity_deferrals.yaml").get("deferrals", [])

    actual = {
        "substances": count_records(DATA_FILES["substances"], "records"),
        "functional_groups": len(fg_doc.get("functional_groups", [])),
        "structural_features": len(fg_doc.get("structural_features", [])),
        "chemical_classes": count_records(DATA_FILES["chemical_classes"], "classes"),
        "reactions": count_records(DATA_FILES["reactions"], "reactions"),
        "concepts": count_records(DATA_FILES["concepts"], "concepts"),
        "phenomena": len(load_yaml(DATA_DIR / "phenomena.yaml").get("phenomena", [])),
        "experiments": len(load_yaml(DATA_DIR / "experiments.yaml").get("experiments", [])),
        "identity_crossrefs": len(crossrefs),
        "identity_deferrals": len(deferrals),
        "curriculum_topics": len({topic for block in curriculum.get("knowledge_blocks", []) for topic in block.get("required_topics", [])}),
        "curriculum_families": len({family for block in curriculum.get("knowledge_blocks", []) for family in block.get("required_families", [])}),
        "curriculum_reaction_classes": len({reaction_class for block in curriculum.get("knowledge_blocks", []) for reaction_class in block.get("required_reaction_classes", [])}),
        "curriculum_experiment_groups": len(set(curriculum.get("experiment_coverage", []))),
    }

    declared = manifest.get("validation", {}).get("counts", {})
    for key, actual_value in actual.items():
        declared_value = declared.get(key)
        if declared_value != actual_value:
            errors.append(
                f"package.yaml: count {key} declares {declared_value}, actual {actual_value}"
            )

    if manifest.get("status") == "complete":
        if curriculum.get("scope_status") != "complete_v0_2":
            errors.append(
                "package.yaml: complete package requires curriculum scope_status=complete_v0_2"
            )
        for gate, state in manifest.get("completion_gate", {}).items():
            if state not in {"passed", "passed_for_non_symbolic_balanced_seed", "required_green"}:
                errors.append(f"package.yaml: unexpected completion gate state {gate}={state}")

    if errors:
        print("Organic manifest validation FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Organic manifest validation PASSED")
    for key, value in actual.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
