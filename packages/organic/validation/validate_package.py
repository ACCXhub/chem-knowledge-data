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

DATASET_SPECS = [
    ("substance", "core_substances.yaml", "records", "substance.schema.json"),
    ("substance", "extended_substances.yaml", "records", "substance.schema.json"),
    ("substance", "polymer_substances.yaml", "records", "substance.schema.json"),
    ("substance", "lipid_substances.yaml", "records", "substance.schema.json"),
    ("functional_group", "functional_groups.yaml", "functional_groups", "functional_group.schema.json"),
    ("reaction", "reactions.yaml", "reactions", "reaction.schema.json"),
    ("reaction", "property_reactions.yaml", "reactions", "reaction.schema.json"),
    ("reaction", "polymer_reactions.yaml", "reactions", "reaction.schema.json"),
    ("reaction", "lipid_reactions.yaml", "reactions", "reaction.schema.json"),
    ("concept", "concepts.yaml", "concepts", "concept.schema.json"),
    ("concept", "structure_concepts.yaml", "concepts", "concept.schema.json"),
    ("concept", "biomolecule_concepts.yaml", "concepts", "concept.schema.json"),
    ("concept", "applied_concepts.yaml", "concepts", "concept.schema.json"),
    ("phenomenon", "phenomena.yaml", "phenomena", "phenomenon.schema.json"),
    ("experiment", "experiments.yaml", "experiments", "experiment.schema.json"),
    ("chemical_class", "classes.yaml", "classes", "chemical_class.schema.json"),
    ("chemical_class", "biomolecule_classes.yaml", "classes", "chemical_class.schema.json"),
]


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
    """Parse the package's molecular-formula notation.

    Returns ``None`` for a valid symbolic repeat formula such as ``(C2H4)n``.
    Charges, hydrate dots and ionic formula syntax belong to other packages and
    are intentionally not accepted in the organic Substance formula field.
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


def validate_records(
    kind: str,
    data_file: str,
    root_key: str,
    schema_file: str,
    source_ids: set[str],
    records_by_kind: dict[str, list[dict[str, Any]]],
    record_locations: dict[str, str],
    errors: list[str],
) -> None:
    path = DATA_DIR / data_file
    records = load_yaml(path).get(root_key, [])
    if not isinstance(records, list):
        errors.append(f"{data_file}: {root_key} must be a list")
        return

    validator = Draft202012Validator(load_json(SCHEMA_DIR / schema_file))
    records_by_kind.setdefault(kind, []).extend(records)

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{data_file}:{index}: record must be a mapping")
            continue
        record_id = record.get("id", f"<index:{index}>")
        for issue in sorted(validator.iter_errors(record), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in issue.path)
            errors.append(f"{data_file}:{record_id}:{location}: {issue.message}")
        if isinstance(record_id, str):
            if record_id in record_locations:
                errors.append(
                    f"duplicate id {record_id}: {record_locations[record_id]} and {data_file}"
                )
            else:
                record_locations[record_id] = data_file
        for source_ref in record.get("provenance_refs", []):
            if source_ref not in source_ids:
                errors.append(f"{data_file}:{record_id}: unknown provenance ref {source_ref}")


def collect_curriculum_requirements(curriculum: dict[str, Any]) -> dict[str, set[str]]:
    coverage = curriculum.get("coverage", {})
    topics: set[str] = set()
    families: set[str] = set()
    reaction_classes: set[str] = set()
    for block in coverage.get("knowledge_blocks", []):
        if not isinstance(block, dict):
            continue
        topics.update(block.get("required_topics", []))
        families.update(block.get("required_families", []))
        reaction_classes.update(block.get("required_reaction_classes", []))
    return {
        "topics": topics,
        "families": families,
        "reaction_classes": reaction_classes,
        "experiments": set(coverage.get("experiment_coverage", [])),
    }


def validate_balanced_reactions(
    reactions: list[dict[str, Any]],
    formula_by_substance: dict[str, str],
    errors: list[str],
    warnings: list[str],
) -> tuple[int, int]:
    checked = 0
    symbolic_skipped = 0
    for reaction in reactions:
        if reaction.get("equation_status") != "balanced_seed":
            continue
        reaction_id = reaction.get("id", "<unknown>")
        if not reaction.get("equation"):
            errors.append(f"reaction:{reaction_id}: balanced_seed requires equation text")

        left: Counter[str] = Counter()
        right: Counter[str] = Counter()
        symbolic = False
        participant_error = False

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
                formula = formula_by_substance.get(substance_ref)
                if not formula:
                    errors.append(f"reaction:{reaction_id}: missing formula for {substance_ref}")
                    participant_error = True
                    continue
            else:
                formula = participant.get("formula_literal")
                if not formula:
                    errors.append(
                        f"reaction:{reaction_id}: external participant "
                        f"{participant.get('external_species_key')} needs formula_literal "
                        "for atom-balance validation"
                    )
                    participant_error = True
                    continue

            try:
                atoms = parse_formula(formula)
            except ValueError as exc:
                errors.append(f"reaction:{reaction_id}: invalid formula {formula}: {exc}")
                participant_error = True
                continue
            if atoms is None:
                symbolic = True
                break

            destination = left if role == "reactant" else right
            for element, count in atoms.items():
                destination[element] += count * coefficient

        if participant_error:
            continue
        if symbolic:
            symbolic_skipped += 1
            warnings.append(
                f"reaction:{reaction_id}: atom-balance check skipped for symbolic polymer notation"
            )
            continue
        checked += 1
        if left != right:
            errors.append(
                f"reaction:{reaction_id}: atom balance mismatch "
                f"reactants={dict(sorted(left.items()))} products={dict(sorted(right.items()))}"
            )
    return checked, symbolic_skipped


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    source_doc = load_yaml(SOURCES_FILE)
    sources = source_doc.get("sources", [])
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict) or not isinstance(source.get("id"), str):
            errors.append(f"sources/registry.yaml:{index}: source requires string id")
            continue
        source_id = source["id"]
        if source_id in source_ids:
            errors.append(f"sources/registry.yaml: duplicate source id {source_id}")
        source_ids.add(source_id)

    records_by_kind: dict[str, list[dict[str, Any]]] = {}
    record_locations: dict[str, str] = {}
    for spec in DATASET_SPECS:
        validate_records(*spec, source_ids, records_by_kind, record_locations, errors)

    feature_doc = load_yaml(DATA_DIR / "functional_groups.yaml")
    features = feature_doc.get("structural_features", [])
    if not isinstance(features, list):
        errors.append("functional_groups.yaml: structural_features must be a list")
        features = []
    feature_validator = Draft202012Validator(
        load_json(SCHEMA_DIR / "structural_feature.schema.json")
    )
    feature_ids: set[str] = set()
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            errors.append(f"structural_feature:{index}: record must be a mapping")
            continue
        feature_id = feature.get("id", f"<index:{index}>")
        for issue in sorted(feature_validator.iter_errors(feature), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in issue.path)
            errors.append(f"structural_feature:{feature_id}:{location}: {issue.message}")
        if isinstance(feature_id, str):
            if feature_id in feature_ids or feature_id in record_locations:
                errors.append(f"duplicate id {feature_id}")
            feature_ids.add(feature_id)

    id_sets = {
        "org-substance:": {record["id"] for record in records_by_kind.get("substance", [])},
        "org-fg:": {record["id"] for record in records_by_kind.get("functional_group", [])},
        "org-reaction:": {record["id"] for record in records_by_kind.get("reaction", [])},
        "org-concept:": {record["id"] for record in records_by_kind.get("concept", [])},
        "org-phenomenon:": {record["id"] for record in records_by_kind.get("phenomenon", [])},
        "org-experiment:": {record["id"] for record in records_by_kind.get("experiment", [])},
        "org-class:": {record["id"] for record in records_by_kind.get("chemical_class", [])},
        "org-feature:": feature_ids,
    }

    def validate_local_refs(context: str, value: Any) -> None:
        for string_value in iter_strings(value):
            for prefix, known_ids in id_sets.items():
                if string_value.startswith(prefix) and string_value not in known_ids:
                    errors.append(f"{context}: unresolved local reference {string_value}")
                    break

    for kind, records in records_by_kind.items():
        for record in records:
            validate_local_refs(f"{kind}:{record.get('id', '<unknown>')}", record)

    crossrefs = load_yaml(DATA_DIR / "identity_crossrefs.yaml").get("crossrefs", [])
    crossref_validator = Draft202012Validator(
        load_json(SCHEMA_DIR / "identity_crossref.schema.json")
    )
    crossref_substances: set[str] = set()
    pubchem_owners: dict[int, str] = {}
    chebi_owners: dict[str, str] = {}
    for index, crossref in enumerate(crossrefs):
        label = (
            crossref.get("substance_ref", f"<index:{index}>")
            if isinstance(crossref, dict)
            else f"<index:{index}>"
        )
        if not isinstance(crossref, dict):
            errors.append(f"identity_crossrefs:{label}: record must be a mapping")
            continue
        for issue in sorted(crossref_validator.iter_errors(crossref), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in issue.path)
            errors.append(f"identity_crossrefs:{label}:{location}: {issue.message}")
        substance_ref = crossref.get("substance_ref")
        if substance_ref not in id_sets["org-substance:"]:
            errors.append(f"identity_crossrefs:{label}: unresolved substance {substance_ref}")
        if substance_ref in crossref_substances:
            errors.append(f"identity_crossrefs:{label}: duplicate crossref for substance")
        if isinstance(substance_ref, str):
            crossref_substances.add(substance_ref)

        pubchem_cid = crossref.get("pubchem_cid")
        if isinstance(pubchem_cid, int):
            previous = pubchem_owners.get(pubchem_cid)
            if previous and previous != substance_ref:
                errors.append(
                    f"identity_crossrefs: PubChem CID {pubchem_cid} belongs to both "
                    f"{previous} and {substance_ref}"
                )
            pubchem_owners[pubchem_cid] = substance_ref
        chebi_id = crossref.get("chebi_id")
        if isinstance(chebi_id, str):
            previous = chebi_owners.get(chebi_id)
            if previous and previous != substance_ref:
                errors.append(
                    f"identity_crossrefs: {chebi_id} belongs to both {previous} and {substance_ref}"
                )
            chebi_owners[chebi_id] = substance_ref
        for source_ref in crossref.get("provenance_refs", []):
            if source_ref not in source_ids:
                errors.append(f"identity_crossrefs:{label}: unknown provenance ref {source_ref}")

    substance_records = records_by_kind.get("substance", [])
    formula_index: dict[str, list[str]] = {}
    formula_by_substance: dict[str, str] = {}
    for record in substance_records:
        record_id = record["id"]
        formula = record["formula"]
        formula_index.setdefault(formula, []).append(record_id)
        formula_by_substance[record_id] = formula
        try:
            parse_formula(formula)
        except ValueError as exc:
            errors.append(f"substance:{record_id}: invalid formula {formula}: {exc}")
        if "external_ids" in record:
            errors.append(
                f"substance:{record_id}: external_ids must live only in identity_crossrefs.yaml"
            )
        if record.get("verification_status") == "source_crosschecked" and record_id not in crossref_substances:
            errors.append(
                f"substance:{record_id}: source_crosschecked requires identity_crossrefs entry"
            )

    for formula, ids in sorted(formula_index.items()):
        if len(ids) > 1:
            warnings.append(
                f"shared formula {formula}: {', '.join(ids)} "
                "(allowed; formula is not chemical identity)"
            )

    balance_checked, symbolic_skipped = validate_balanced_reactions(
        records_by_kind.get("reaction", []), formula_by_substance, errors, warnings
    )

    curriculum = load_yaml(CURRICULUM_FILE)
    evidence = load_yaml(COVERAGE_EVIDENCE_FILE).get("coverage_evidence", {})
    requirements = collect_curriculum_requirements(curriculum)
    for section, required_items in requirements.items():
        provided = evidence.get(section, {})
        if not isinstance(provided, dict):
            errors.append(f"coverage_evidence:{section}: must be a mapping")
            continue
        for item in sorted(required_items - set(provided)):
            errors.append(f"coverage_evidence:{section}: missing required item {item}")
        for item in sorted(required_items):
            entry = provided.get(item)
            if not isinstance(entry, dict):
                errors.append(f"coverage_evidence:{section}:{item}: must be a mapping")
                continue
            if entry.get("status") != "covered":
                errors.append(f"coverage_evidence:{section}:{item}: status must be covered")
            refs = entry.get("refs", [])
            if not isinstance(refs, list) or not refs:
                errors.append(
                    f"coverage_evidence:{section}:{item}: refs must be a non-empty list"
                )
            else:
                validate_local_refs(f"coverage_evidence:{section}:{item}", refs)

    for source_ref in curriculum.get("coverage", {}).get("source_refs", []):
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
    print(
        f"chemistry_balance: checked={balance_checked}, "
        f"symbolic_skipped={symbolic_skipped}"
    )
    for warning in warnings:
        print(f"WARN: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
