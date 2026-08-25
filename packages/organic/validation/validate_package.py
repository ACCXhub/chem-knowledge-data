from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
SCHEMA_DIR = PACKAGE_ROOT / "schema"
SOURCES_FILE = PACKAGE_ROOT / "sources" / "registry.yaml"
CURRICULUM_FILE = DATA_DIR / "curriculum_coverage.yaml"
COVERAGE_EVIDENCE_FILE = DATA_DIR / "coverage_evidence.yaml"
POLYMER_FORMULA_RE = re.compile(r"^\((.+)\)n$")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a mapping at document root")
    return data


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected an object at document root")
    return data


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)


def parse_formula(formula: str) -> Counter[str] | None:
    """Parse the package's simple molecular formula notation.

    Returns None for a syntactically valid symbolic repeat formula such as
    ``(C2H4)n``. The parser intentionally rejects charges, hydrate dots and other
    notations not owned by this organic Substance formula field.
    """

    polymer_match = POLYMER_FORMULA_RE.fullmatch(formula)
    if polymer_match:
        inner = parse_formula(polymer_match.group(1))
        if inner is None:
            raise ValueError("nested symbolic repeat formula is not supported")
        return None

    stack: list[Counter[str]] = [Counter()]
    index = 0
    while index < len(formula):
        char = formula[index]
        if char == "(":
            stack.append(Counter())
            index += 1
            continue
        if char == ")":
            if len(stack) == 1:
                raise ValueError("unmatched closing parenthesis")
            group = stack.pop()
            index += 1
            digit_start = index
            while index < len(formula) and formula[index].isdigit():
                index += 1
            multiplier = int(formula[digit_start:index] or "1")
            if multiplier < 1:
                raise ValueError("formula multiplier must be positive")
            for element, count in group.items():
                stack[-1][element] += count * multiplier
            continue
        if not char.isupper() or not char.isascii():
            raise ValueError(f"unexpected character {char!r}")

        element = char
        index += 1
        if index < len(formula) and formula[index].islower() and formula[index].isascii():
            element += formula[index]
            index += 1
        digit_start = index
        while index < len(formula) and formula[index].isdigit():
            index += 1
        count = int(formula[digit_start:index] or "1")
        if count < 1:
            raise ValueError("atom count must be positive")
        stack[-1][element] += count

    if len(stack) != 1:
        raise ValueError("unmatched opening parenthesis")
    if not stack[0]:
        raise ValueError("formula contains no elements")
    return stack[0]


def validate_schema_records(
    *,
    kind: str,
    path: Path,
    root_key: str,
    schema_path: Path,
    source_ids: set[str],
    records_by_kind: dict[str, list[dict[str, Any]]],
    source_path_by_record_id: dict[str, Path],
    errors: list[str],
) -> None:
    doc = load_yaml(path)
    records = doc.get(root_key, [])
    if not isinstance(records, list):
        errors.append(f"{path}: {root_key} must be a list")
        return

    validator = Draft202012Validator(load_json(schema_path))
    records_by_kind.setdefault(kind, []).extend(records)

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{path}:{index}: record must be a mapping")
            continue

        record_id = record.get("id", f"<index:{index}>")
        for validation_error in sorted(
            validator.iter_errors(record), key=lambda item: list(item.path)
        ):
            location = ".".join(str(part) for part in validation_error.path)
            errors.append(
                f"{path}:{record_id}:{location}: {validation_error.message}"
            )

        if isinstance(record_id, str):
            if record_id in source_path_by_record_id:
                errors.append(
                    f"duplicate id {record_id}: "
                    f"{source_path_by_record_id[record_id]} and {path}"
                )
            else:
                source_path_by_record_id[record_id] = path

        for provenance_ref in record.get("provenance_refs", []):
            if provenance_ref not in source_ids:
                errors.append(
                    f"{path}:{record_id}: unknown provenance ref {provenance_ref}"
                )


def collect_curriculum_requirements(curriculum: dict[str, Any]) -> dict[str, set[str]]:
    coverage = curriculum.get("coverage", {})
    blocks = coverage.get("knowledge_blocks", [])
    required_topics: set[str] = set()
    required_families: set[str] = set()
    required_reaction_classes: set[str] = set()

    for block in blocks:
        if not isinstance(block, dict):
            continue
        required_topics.update(block.get("required_topics", []))
        required_families.update(block.get("required_families", []))
        required_reaction_classes.update(block.get("required_reaction_classes", []))

    return {
        "topics": required_topics,
        "families": required_families,
        "reaction_classes": required_reaction_classes,
        "experiments": set(coverage.get("experiment_coverage", [])),
    }


def validate_balanced_reactions(
    reactions: list[dict[str, Any]],
    substance_formula_by_id: dict[str, str],
    errors: list[str],
    warnings: list[str],
) -> None:
    for reaction in reactions:
        if reaction.get("equation_status") != "balanced_seed":
            continue

        reaction_id = reaction.get("id", "<unknown>")
        if not reaction.get("equation"):
            errors.append(f"reaction:{reaction_id}: balanced_seed requires equation text")

        left: Counter[str] = Counter()
        right: Counter[str] = Counter()
        symbolic = False

        for participant in reaction.get("participants", []):
            role = participant.get("role")
            if role == "catalyst":
                continue
            coefficient = participant.get("coefficient")
            if not isinstance(coefficient, int):
                symbolic = True
                break

            substance_ref = participant.get("substance_ref")
            if substance_ref:
                formula = substance_formula_by_id.get(substance_ref)
                if not formula:
                    errors.append(
                        f"reaction:{reaction_id}: missing formula for {substance_ref}"
                    )
                    continue
            else:
                formula = participant.get("formula_literal")
                if not formula:
                    errors.append(
                        f"reaction:{reaction_id}: external participant "
                        f"{participant.get('external_species_key')} needs formula_literal "
                        "for atom-balance validation"
                    )
                    continue

            try:
                atoms = parse_formula(formula)
            except ValueError as exc:
                errors.append(
                    f"reaction:{reaction_id}: invalid participant formula {formula}: {exc}"
                )
                continue
            if atoms is None:
                symbolic = True
                break

            destination = left if role == "reactant" else right
            for element, count in atoms.items():
                destination[element] += count * coefficient

        if symbolic:
            warnings.append(
                f"reaction:{reaction_id}: atom-balance check skipped for symbolic polymer notation"
            )
            continue
        if left != right:
            errors.append(
                f"reaction:{reaction_id}: atom balance mismatch "
                f"reactants={dict(sorted(left.items()))} products={dict(sorted(right.items()))}"
            )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    source_doc = load_yaml(SOURCES_FILE)
    sources = source_doc.get("sources", [])
    source_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("id"), str):
            errors.append("sources/registry.yaml: each source must have a string id")
            continue
        source_id = source["id"]
        if source_id in source_ids:
            errors.append(f"sources/registry.yaml: duplicate source id {source_id}")
        source_ids.add(source_id)

    dataset_specs = [
        ("substance", DATA_DIR / "core_substances.yaml", "records", SCHEMA_DIR / "substance.schema.json"),
        ("substance", DATA_DIR / "extended_substances.yaml", "records", SCHEMA_DIR / "substance.schema.json"),
        ("substance", DATA_DIR / "polymer_substances.yaml", "records", SCHEMA_DIR / "substance.schema.json"),
        ("substance", DATA_DIR / "lipid_substances.yaml", "records", SCHEMA_DIR / "substance.schema.json"),
        ("functional_group", DATA_DIR / "functional_groups.yaml", "functional_groups", SCHEMA_DIR / "functional_group.schema.json"),
        ("reaction", DATA_DIR / "reactions.yaml", "reactions", SCHEMA_DIR / "reaction.schema.json"),
        ("reaction", DATA_DIR / "polymer_reactions.yaml", "reactions", SCHEMA_DIR / "reaction.schema.json"),
        ("reaction", DATA_DIR / "lipid_reactions.yaml", "reactions", SCHEMA_DIR / "reaction.schema.json"),
        ("concept", DATA_DIR / "concepts.yaml", "concepts", SCHEMA_DIR / "concept.schema.json"),
        ("concept", DATA_DIR / "structure_concepts.yaml", "concepts", SCHEMA_DIR / "concept.schema.json"),
        ("concept", DATA_DIR / "biomolecule_concepts.yaml", "concepts", SCHEMA_DIR / "concept.schema.json"),
        ("phenomenon", DATA_DIR / "phenomena.yaml", "phenomena", SCHEMA_DIR / "phenomenon.schema.json"),
        ("experiment", DATA_DIR / "experiments.yaml", "experiments", SCHEMA_DIR / "experiment.schema.json"),
        ("chemical_class", DATA_DIR / "classes.yaml", "classes", SCHEMA_DIR / "chemical_class.schema.json"),
        ("chemical_class", DATA_DIR / "biomolecule_classes.yaml", "classes", SCHEMA_DIR / "chemical_class.schema.json"),
    ]

    records_by_kind: dict[str, list[dict[str, Any]]] = {}
    source_path_by_record_id: dict[str, Path] = {}

    for kind, path, root_key, schema_path in dataset_specs:
        validate_schema_records(
            kind=kind,
            path=path,
            root_key=root_key,
            schema_path=schema_path,
            source_ids=source_ids,
            records_by_kind=records_by_kind,
            source_path_by_record_id=source_path_by_record_id,
            errors=errors,
        )

    feature_doc = load_yaml(DATA_DIR / "functional_groups.yaml")
    feature_records = feature_doc.get("structural_features", [])
    if not isinstance(feature_records, list):
        errors.append("functional_groups.yaml: structural_features must be a list")
        feature_records = []
    feature_validator = Draft202012Validator(
        load_json(SCHEMA_DIR / "structural_feature.schema.json")
    )
    feature_ids: set[str] = set()
    for index, record in enumerate(feature_records):
        if not isinstance(record, dict):
            errors.append(f"structural_feature:{index}: record must be a mapping")
            continue
        record_id = record.get("id", f"<index:{index}>")
        for validation_error in sorted(
            feature_validator.iter_errors(record), key=lambda item: list(item.path)
        ):
            location = ".".join(str(part) for part in validation_error.path)
            errors.append(
                f"structural_feature:{record_id}:{location}: {validation_error.message}"
            )
        if isinstance(record_id, str):
            if record_id in feature_ids or record_id in source_path_by_record_id:
                errors.append(f"duplicate id {record_id}")
            feature_ids.add(record_id)

    id_sets = {
        "org-substance:": {
            record["id"] for record in records_by_kind.get("substance", [])
        },
        "org-fg:": {
            record["id"] for record in records_by_kind.get("functional_group", [])
        },
        "org-reaction:": {
            record["id"] for record in records_by_kind.get("reaction", [])
        },
        "org-concept:": {
            record["id"] for record in records_by_kind.get("concept", [])
        },
        "org-phenomenon:": {
            record["id"] for record in records_by_kind.get("phenomenon", [])
        },
        "org-experiment:": {
            record["id"] for record in records_by_kind.get("experiment", [])
        },
        "org-class:": {
            record["id"] for record in records_by_kind.get("chemical_class", [])
        },
        "org-feature:": feature_ids,
    }

    def validate_local_refs(context: str, value: Any) -> None:
        for string_value in iter_strings(value):
            for prefix, known_ids in id_sets.items():
                if string_value.startswith(prefix) and string_value not in known_ids:
                    errors.append(
                        f"{context}: unresolved local reference {string_value}"
                    )
                    break

    for kind, records in records_by_kind.items():
        for record in records:
            validate_local_refs(f"{kind}:{record.get('id', '<unknown>')}", record)

    crossref_doc = load_yaml(DATA_DIR / "identity_crossrefs.yaml")
    crossrefs = crossref_doc.get("crossrefs", [])
    crossref_validator = Draft202012Validator(
        load_json(SCHEMA_DIR / "identity_crossref.schema.json")
    )
    seen_crossref_substances: set[str] = set()
    for index, crossref in enumerate(crossrefs):
        label = (
            crossref.get("substance_ref", f"<index:{index}>")
            if isinstance(crossref, dict)
            else f"<index:{index}>"
        )
        if not isinstance(crossref, dict):
            errors.append(f"identity_crossrefs:{label}: record must be a mapping")
            continue
        for validation_error in sorted(
            crossref_validator.iter_errors(crossref), key=lambda item: list(item.path)
        ):
            location = ".".join(str(part) for part in validation_error.path)
            errors.append(
                f"identity_crossrefs:{label}:{location}: {validation_error.message}"
            )
        substance_ref = crossref.get("substance_ref")
        if substance_ref not in id_sets["org-substance:"]:
            errors.append(
                f"identity_crossrefs:{label}: unresolved local reference {substance_ref}"
            )
        if substance_ref in seen_crossref_substances:
            errors.append(
                f"identity_crossrefs:{label}: duplicate crossref for substance"
            )
        if isinstance(substance_ref, str):
            seen_crossref_substances.add(substance_ref)
        for provenance_ref in crossref.get("provenance_refs", []):
            if provenance_ref not in source_ids:
                errors.append(
                    f"identity_crossrefs:{label}: unknown provenance ref {provenance_ref}"
                )

    substance_records = records_by_kind.get("substance", [])
    formula_index: dict[str, list[str]] = {}
    substance_formula_by_id: dict[str, str] = {}
    for record in substance_records:
        formula = record["formula"]
        record_id = record["id"]
        formula_index.setdefault(formula, []).append(record_id)
        substance_formula_by_id[record_id] = formula
        try:
            parse_formula(formula)
        except ValueError as exc:
            errors.append(f"substance:{record_id}: invalid formula {formula}: {exc}")
        if "external_ids" in record:
            errors.append(
                f"substance:{record_id}: external_ids must live only in identity_crossrefs.yaml"
            )

    for formula, ids in sorted(formula_index.items()):
        if len(ids) > 1:
            warnings.append(
                f"shared formula {formula}: {', '.join(ids)} "
                "(allowed; verify these are distinct identities)"
            )

    validate_balanced_reactions(
        records_by_kind.get("reaction", []),
        substance_formula_by_id,
        errors,
        warnings,
    )

    curriculum = load_yaml(CURRICULUM_FILE)
    evidence_doc = load_yaml(COVERAGE_EVIDENCE_FILE)
    evidence = evidence_doc.get("coverage_evidence", {})
    requirements = collect_curriculum_requirements(curriculum)

    for section, required_items in requirements.items():
        provided = evidence.get(section, {})
        if not isinstance(provided, dict):
            errors.append(f"coverage_evidence:{section}: must be a mapping")
            continue
        missing = sorted(required_items - set(provided))
        for item in missing:
            errors.append(f"coverage_evidence:{section}: missing required item {item}")
        for item in sorted(required_items):
            entry = provided.get(item)
            if not isinstance(entry, dict):
                errors.append(f"coverage_evidence:{section}:{item}: must be a mapping")
                continue
            if entry.get("status") != "covered":
                errors.append(
                    f"coverage_evidence:{section}:{item}: status must be covered"
                )
            refs = entry.get("refs", [])
            if not isinstance(refs, list) or not refs:
                errors.append(
                    f"coverage_evidence:{section}:{item}: refs must be a non-empty list"
                )
            else:
                validate_local_refs(f"coverage_evidence:{section}:{item}", refs)

    curriculum_source_refs = curriculum.get("coverage", {}).get("source_refs", [])
    for source_ref in curriculum_source_refs:
        if source_ref not in source_ids:
            errors.append(f"curriculum_coverage: unknown source ref {source_ref}")

    if errors:
        print("Organic package validation FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARN: {warning}")
        return 1

    print("Organic package validation PASSED")
    for kind, records in sorted(records_by_kind.items()):
        print(f"{kind}: {len(records)}")
    print(f"identity_crossref: {len(crossrefs)}")
    print(f"structural_feature: {len(feature_ids)}")
    print(f"sources: {len(source_ids)}")
    print(
        "coverage: "
        + ", ".join(
            f"{section}={len(items)}" for section, items in sorted(requirements.items())
        )
    )
    print("chemistry_balance: checked for all non-symbolic balanced_seed reactions")
    for warning in warnings:
        print(f"WARN: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
