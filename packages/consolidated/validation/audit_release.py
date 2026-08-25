from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[3]
CONSOLIDATED = ROOT / "packages" / "consolidated"
GENERATED = CONSOLIDATED / "generated"
SOURCE_INPUTS = CONSOLIDATED / "SOURCE_INPUTS.json"
ALIAS_FILE = CONSOLIDATED / "data" / "source_reference_aliases.yaml"

INORGANIC = ROOT / "packages" / "inorganic"
ORGANIC = ROOT / "packages" / "organic"
STRUCTURE_REGISTRY = ROOT / "packages" / "structure_registry"
STRUCTURAL_CHEMISTRY = ROOT / "packages" / "structural_chemistry"

STRUCTURAL_TYPES = {
    "atomic_configuration",
    "concept",
    "vsepr_model",
    "molecular_example",
    "bonding_example",
    "crystal_model",
    "coordination_example",
    "relation",
    "structure_property_rule",
    "exam_tag",
}

RUNTIME_KEYS = {
    "pinned",
    "favorite",
    "favorites",
    "recent",
    "recently_used",
    "usage_frequency",
    "usage_count",
    "hidden",
    "custom_order",
    "user_id",
}

REFERENCE_PATTERN = re.compile(
    r"^(ion|substance|reaction|phenomenon|experiment|concept|exam-tag):"
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected YAML mapping")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            output.append(value)
    return output


def git_show_bytes(commit: str, repo_path: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "show", f"{commit}:{repo_path}"],
            cwd=ROOT,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"cannot read pinned input {commit}:{repo_path}: {stderr}") from exc


def aggregate_digest(items: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for repo_path, content in sorted(items):
        digest.update(repo_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(content).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def parse_formula(formula: str) -> Counter[str] | None:
    formula = formula.strip()
    if not formula or re.fullmatch(r"\(.+\)n", formula):
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
                return None
            group = stack.pop()
            index += 1
            start = index
            while index < len(formula) and formula[index].isdigit():
                index += 1
            multiplier = int(formula[start:index] or "1")
            for element, count in group.items():
                stack[-1][element] += count * multiplier
            continue
        if not char.isupper() or not char.isascii():
            return None
        element = char
        index += 1
        if index < len(formula) and formula[index].islower() and formula[index].isascii():
            element += formula[index]
            index += 1
        start = index
        while index < len(formula) and formula[index].isdigit():
            index += 1
        stack[-1][element] += int(formula[start:index] or "1")
    if len(stack) != 1 or not stack[0]:
        return None
    return stack[0]


def source_paths_from_snapshot(package: str, snapshot: dict[str, Any]) -> list[str]:
    paths = snapshot["inputs"][package].get("consumed_files")
    if not isinstance(paths, list) or not paths or not all(isinstance(item, str) for item in paths):
        raise RuntimeError(f"source snapshot has no consumed_files for {package}")
    return list(paths)


def audit_source_freeze(errors: list[str], stats: dict[str, Any]) -> None:
    pins = load_json(SOURCE_INPUTS)["inputs"]
    snapshot = load_json(GENERATED / "source_snapshot.json")
    for package, pin in pins.items():
        entry = snapshot.get("inputs", {}).get(package, {})
        if str(entry.get("release_commit")) != str(pin["release_commit"]):
            errors.append(f"{package}: source snapshot release_commit mismatch")
            continue
        if str(entry.get("state", "")).casefold() != str(pin["state"]).casefold():
            errors.append(
                f"{package}: source state mismatch: expected {pin['state']!r}, got {entry.get('state')!r}"
            )
        paths = source_paths_from_snapshot(package, snapshot)
        current_items = []
        pinned_items = []
        for repo_path in paths:
            current_path = ROOT / repo_path
            if not current_path.is_file():
                errors.append(f"{package}: consumed file missing from current tree: {repo_path}")
                continue
            current_items.append((repo_path, current_path.read_bytes()))
            try:
                pinned_items.append((repo_path, git_show_bytes(str(pin["release_commit"]), repo_path)))
            except RuntimeError as exc:
                errors.append(str(exc))
        if len(current_items) != len(paths) or len(pinned_items) != len(paths):
            continue
        current_digest = aggregate_digest(current_items)
        pinned_digest = aggregate_digest(pinned_items)
        if current_digest != pinned_digest:
            errors.append(
                f"{package}: consumed source drift: current={current_digest}, pinned={pinned_digest}"
            )
        if entry.get("input_sha256") != current_digest:
            errors.append(
                f"{package}: source_snapshot input_sha256 mismatch: "
                f"snapshot={entry.get('input_sha256')}, actual={current_digest}"
            )
        stats.setdefault("source_freeze", {})[package] = {
            "files": len(paths),
            "sha256": current_digest,
        }


def audit_expected_coverage(
    crosswalk: list[dict[str, Any]],
    reactions: list[dict[str, Any]],
    knowledge: list[dict[str, Any]],
    errors: list[str],
    stats: dict[str, Any],
) -> None:
    inorganic_manifest = load_json(INORGANIC / "manifest.json")
    organic_package = load_yaml(ORGANIC / "package.yaml")
    inorganic_counts = inorganic_manifest["record_counts"]
    organic_counts = organic_package["validation"]["counts"]

    expected_species = inorganic_counts["ions"] + inorganic_counts["substances"] + organic_counts["substances"]
    if len(crosswalk) != expected_species:
        errors.append(f"source species coverage mismatch: expected {expected_species}, got {len(crosswalk)}")

    reaction_counts = Counter(str(item["source_package"]) for item in reactions)
    expected_reactions = {
        "inorganic": inorganic_counts["reactions"],
        "organic": organic_counts["reactions"],
    }
    if dict(reaction_counts) != expected_reactions:
        errors.append(
            f"reaction source coverage mismatch: expected {expected_reactions}, got {dict(reaction_counts)}"
        )

    knowledge_counts = Counter(str(item["source_package"]) for item in knowledge)
    expected_inorganic_knowledge = sum(
        inorganic_counts[key]
        for key in ("element_scope", "phenomena", "experiments", "concepts", "exam_tags")
    )
    expected_organic_knowledge = sum(
        organic_counts[key]
        for key in (
            "functional_groups",
            "structural_features",
            "chemical_classes",
            "concepts",
            "phenomena",
            "experiments",
        )
    )
    expected_structural_knowledge = sum(
        1
        for path in (STRUCTURAL_CHEMISTRY / "data").glob("*.jsonl")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    expected_knowledge = {
        "inorganic": expected_inorganic_knowledge,
        "organic": expected_organic_knowledge,
        "structural_chemistry": expected_structural_knowledge,
    }
    if dict(knowledge_counts) != expected_knowledge:
        errors.append(
            f"knowledge source coverage mismatch: expected {expected_knowledge}, got {dict(knowledge_counts)}"
        )

    stats["coverage"] = {
        "species_source_records": len(crosswalk),
        "reactions": dict(reaction_counts),
        "knowledge": dict(knowledge_counts),
    }


def audit_structure_link_reconciliation(
    links: list[dict[str, Any]],
    species: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    errors: list[str],
    stats: dict[str, Any],
) -> None:
    accepted: dict[str, tuple[str, str]] = {}
    for package in ("inorganic", "organic"):
        for item in load_jsonl(STRUCTURE_REGISTRY / "data" / "links" / f"{package}.jsonl"):
            if item.get("status") == "accepted":
                accepted[str(item["link_id"])] = (package, str(item["entity_ref"]))

    normalized = {str(item["source_link_id"]) for item in links}
    if normalized != set(accepted):
        errors.append(
            "accepted Structure link reconciliation mismatch: "
            f"missing={sorted(set(accepted) - normalized)}, extra={sorted(normalized - set(accepted))}"
        )

    aliases = {
        (str(item["source_package"]), str(item["legacy_id"])): str(item["current_id"])
        for item in load_yaml(ALIAS_FILE).get("aliases", [])
        if isinstance(item, dict)
    }
    link_by_id = {str(item["source_link_id"]): item for item in links}
    for link_id, (package, legacy_or_current) in accepted.items():
        normalized_link = link_by_id.get(link_id)
        if normalized_link is None:
            continue
        expected_source_id = aliases.get((package, legacy_or_current), legacy_or_current)
        if normalized_link.get("source_package") != package or normalized_link.get("source_id") != expected_source_id:
            errors.append(
                f"Structure link {link_id} source bridge mismatch: expected "
                f"{package}:{expected_source_id}, got "
                f"{normalized_link.get('source_package')}:{normalized_link.get('source_id')}"
            )

    species_by_id = {str(item["id"]): item for item in species}
    structures_by_species: dict[str, set[str]] = {}
    for item in links:
        structures_by_species.setdefault(str(item["species_id"]), set()).add(str(item["structure_id"]))
    for species_id, item in species_by_id.items():
        preferred = item.get("preferred_structure_id")
        if preferred is not None and preferred not in structures_by_species.get(species_id, set()):
            errors.append(f"{species_id}: preferred Structure not represented by normalized link")

    historical_rebound = [
        item for item in findings if item.get("kind") == "historical_structure_link_rebound"
    ]
    if len(historical_rebound) != len(aliases):
        errors.append(
            f"historical Structure alias audit count mismatch: aliases={len(aliases)}, "
            f"rebound_findings={len(historical_rebound)}"
        )
    if any(item.get("kind") == "historical_structure_link_outside_snapshot" for item in findings):
        errors.append("historical Structure links are still being dropped instead of rebound")

    stats["structure_links"] = {
        "accepted_source_links": len(accepted),
        "normalized_links": len(links),
        "historical_rebounds": len(historical_rebound),
    }


def as_fraction(value: Any) -> Fraction | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, float):
        return Fraction(str(value))
    return None


def balance_of(
    participants: Iterable[dict[str, Any]],
    species_by_id: dict[str, dict[str, Any]],
) -> tuple[dict[str, Fraction], Fraction] | None:
    atoms: dict[str, Fraction] = {}
    charge = Fraction(0, 1)
    for participant in participants:
        coefficient = as_fraction(participant.get("coefficient"))
        species_id = participant.get("species_id")
        if coefficient is None or not isinstance(species_id, str) or participant.get("non_species_ref") is not None:
            return None
        species = species_by_id.get(species_id)
        if species is None or not isinstance(species.get("composition"), dict):
            return None
        for element, count in species["composition"].items():
            atoms[str(element)] = atoms.get(str(element), Fraction(0, 1)) + coefficient * int(count)
        charge += coefficient * int(species.get("charge", 0))
    return atoms, charge


def audit_reaction_semantics(
    reactions: list[dict[str, Any]],
    species: list[dict[str, Any]],
    knowledge: list[dict[str, Any]],
    errors: list[str],
    stats: dict[str, Any],
) -> None:
    species_by_id = {str(item["id"]): item for item in species}
    knowledge_keys = {
        (str(item["source_package"]), str(item["source_type"]), str(item["source_id"]))
        for item in knowledge
    }

    balanced_checked = 0
    balance_skipped = 0
    net_checked = 0
    formula_literal_checked = 0
    material_participants = 0

    ref_types = {
        "phenomenon_refs": "phenomenon",
        "experiment_refs": "experiment",
        "concept_refs": "concept",
    }

    for reaction in reactions:
        reaction_id = str(reaction["id"])

        for field, source_type in ref_types.items():
            for ref in reaction.get(field, []):
                package, separator, source_id = str(ref).partition(":")
                if not separator or (package, source_type, source_id) not in knowledge_keys:
                    errors.append(
                        f"{reaction_id}: generated {field} target missing from knowledge bundle: {ref}"
                    )

        for participant in reaction.get("participants", []):
            non_species = participant.get("non_species_ref")
            if non_species is not None:
                material_participants += 1
                if reaction.get("source_package") != "organic":
                    errors.append(f"{reaction_id}: non-species material is only valid for organic source relations")
                if reaction.get("equation_status") != "transformation_only":
                    errors.append(
                        f"{reaction_id}: non-species material requires equation_status=transformation_only"
                    )
                if not str(non_species).startswith("organic-material:"):
                    errors.append(f"{reaction_id}: invalid non-species material namespace {non_species}")
                if reaction.get("net_ionic") is not None:
                    errors.append(f"{reaction_id}: non-species material cannot appear in net-ionic relation")

            literal = participant.get("formula_literal")
            species_id = participant.get("species_id")
            if isinstance(literal, str) and isinstance(species_id, str):
                literal_comp = parse_formula(literal)
                target_comp = species_by_id.get(species_id, {}).get("composition")
                if literal_comp is not None and isinstance(target_comp, dict):
                    formula_literal_checked += 1
                    if dict(literal_comp) != {str(k): int(v) for k, v in target_comp.items()}:
                        errors.append(
                            f"{reaction_id}: formula_literal {literal} does not match resolved "
                            f"{species_id} composition {target_comp}"
                        )

        should_balance = (
            reaction.get("source_package") == "inorganic"
            or reaction.get("equation_status") == "balanced_seed"
        )
        if should_balance:
            reactants = [item for item in reaction["participants"] if item.get("role") == "reactant"]
            products = [item for item in reaction["participants"] if item.get("role") == "product"]
            left = balance_of(reactants, species_by_id)
            right = balance_of(products, species_by_id)
            if left is None or right is None:
                balance_skipped += 1
            else:
                balanced_checked += 1
                if left != right:
                    errors.append(
                        f"{reaction_id}: post-mapping atom/charge conservation failed: "
                        f"reactants={left}, products={right}"
                    )

        net = reaction.get("net_ionic")
        if isinstance(net, dict):
            reactants = [item for item in net.get("participants", []) if item.get("role") == "reactant"]
            products = [item for item in net.get("participants", []) if item.get("role") == "product"]
            left = balance_of(reactants, species_by_id)
            right = balance_of(products, species_by_id)
            if left is None or right is None:
                errors.append(f"{reaction_id}: net-ionic equation cannot be independently conserved")
            else:
                net_checked += 1
                if left != right:
                    errors.append(
                        f"{reaction_id}: net-ionic atom/charge conservation failed: "
                        f"reactants={left}, products={right}"
                    )

    stats["reaction_semantics"] = {
        "balanced_checked": balanced_checked,
        "balance_skipped": balance_skipped,
        "net_ionic_checked": net_checked,
        "formula_literal_checked": formula_literal_checked,
        "non_species_material_participants": material_participants,
    }


def find_runtime_keys(value: Any, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if str(key) in RUNTIME_KEYS:
                found.append(child_path)
            found.extend(find_runtime_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_runtime_keys(child, f"{path}[{index}]"))
    return found


def audit_teaching_projection(
    species: list[dict[str, Any]],
    teaching: list[dict[str, Any]],
    errors: list[str],
    stats: dict[str, Any],
) -> None:
    species_by_id = {str(item["id"]): item for item in species}
    ranks = [item.get("default_palette_rank") for item in teaching]
    if sorted(ranks) != list(range(len(teaching))):
        errors.append("teaching default_palette_rank is not a contiguous 0..N-1 permutation")

    for item in teaching:
        species_id = str(item["species_id"])
        source = species_by_id[species_id]
        category = str(item["primary_category"])
        if source["entity_kind"] == "ion":
            expected = "cation" if int(source["charge"]) > 0 else "anion" if int(source["charge"]) < 0 else "other"
            if category != expected:
                errors.append(
                    f"{species_id}: ion category mismatch: expected {expected}, got {category}"
                )
        tokens = set(str(value) for value in item.get("search_tokens", []))
        if source["name_zh"] not in tokens:
            errors.append(f"{species_id}: Chinese name missing from search tokens")
        if source["formula"] not in tokens:
            errors.append(f"{species_id}: formula missing from search tokens")
        leaked = find_runtime_keys(item)
        if leaked:
            errors.append(f"{species_id}: runtime user state leaked into teaching projection: {leaked}")

    stats["teaching_projection"] = {
        "records": len(teaching),
        "contiguous_ranks": True,
    }


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)


def audit_rule_references(
    crosswalk: list[dict[str, Any]],
    reactions: list[dict[str, Any]],
    knowledge: list[dict[str, Any]],
    errors: list[str],
    stats: dict[str, Any],
) -> None:
    inorganic_species = {
        str(item["source_id"])
        for item in crosswalk
        if item.get("source_package") == "inorganic"
    }
    inorganic_reactions = {
        str(item["source_id"])
        for item in reactions
        if item.get("source_package") == "inorganic"
    }
    knowledge_by_prefix = {
        "phenomenon": {
            str(item["source_id"])
            for item in knowledge
            if item.get("source_package") == "inorganic" and item.get("source_type") == "phenomenon"
        },
        "experiment": {
            str(item["source_id"])
            for item in knowledge
            if item.get("source_package") == "inorganic" and item.get("source_type") == "experiment"
        },
        "concept": {
            str(item["source_id"])
            for item in knowledge
            if item.get("source_package") == "inorganic" and item.get("source_type") == "concept"
        },
        "exam-tag": {
            str(item["source_id"])
            for item in knowledge
            if item.get("source_package") == "inorganic" and item.get("source_type") == "exam_tag"
        },
    }

    checked = 0
    for path in sorted((GENERATED / "rules").glob("*.json")):
        root = load_json(path)
        for value in iter_strings(root):
            match = REFERENCE_PATTERN.match(value)
            if not match:
                continue
            checked += 1
            prefix = match.group(1)
            if prefix in {"ion", "substance"}:
                valid = value in inorganic_species
            elif prefix == "reaction":
                valid = value in inorganic_reactions
            else:
                valid = value in knowledge_by_prefix[prefix]
            if not valid:
                errors.append(f"{path.name}: unresolved source-keyed rule reference {value}")

    stats["rule_references"] = {"checked": checked}


def audit_structural_types(
    knowledge: list[dict[str, Any]], errors: list[str], stats: dict[str, Any]
) -> None:
    observed = {
        str(item["source_type"])
        for item in knowledge
        if item.get("source_package") == "structural_chemistry"
    }
    if not observed.issubset(STRUCTURAL_TYPES):
        errors.append(
            f"structural chemistry consumer source_type not normalized: {sorted(observed - STRUCTURAL_TYPES)}"
        )
    stats["structural_source_types"] = sorted(observed)


def main() -> int:
    errors: list[str] = []
    stats: dict[str, Any] = {}

    species = load_jsonl(GENERATED / "species.jsonl")
    crosswalk = load_jsonl(GENERATED / "crosswalk.jsonl")
    links = load_jsonl(GENERATED / "structure_links.jsonl")
    teaching = load_jsonl(GENERATED / "teaching_projection.jsonl")
    reactions = load_jsonl(GENERATED / "reactions.jsonl")
    knowledge = load_jsonl(GENERATED / "knowledge_records.jsonl")
    findings = load_jsonl(GENERATED / "unresolved_findings.jsonl")
    manifest = load_json(GENERATED / "manifest.json")
    validation = load_json(GENERATED / "validation_report.json")

    audit_source_freeze(errors, stats)
    audit_expected_coverage(crosswalk, reactions, knowledge, errors, stats)
    audit_structure_link_reconciliation(links, species, findings, errors, stats)
    audit_reaction_semantics(reactions, species, knowledge, errors, stats)
    audit_teaching_projection(species, teaching, errors, stats)
    audit_rule_references(crosswalk, reactions, knowledge, errors, stats)
    audit_structural_types(knowledge, errors, stats)

    blocking = [item for item in findings if item.get("severity") == "blocking"]
    review = [item for item in findings if item.get("severity") == "review"]
    if blocking:
        errors.append(f"{len(blocking)} blocking integration finding(s) remain")
    if review:
        errors.append(f"{len(review)} review integration finding(s) remain before first release")

    if validation.get("status") != "passed" or validation.get("errors") or validation.get("warnings"):
        errors.append(f"base validator is not clean: {validation}")

    if manifest.get("release") != "consolidated-1.0.0":
        errors.append(f"unexpected release identity: {manifest.get('release')}")
    if manifest.get("state") != "READY_FOR_APP_IMPORT":
        errors.append(f"release state is not READY_FOR_APP_IMPORT: {manifest.get('state')}")
    if manifest.get("blocking_findings") != 0 or manifest.get("review_findings") != 0:
        errors.append("manifest still reports blocking/review findings")

    result = {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "stats": stats,
        "findings": {
            "blocking": len(blocking),
            "review": len(review),
            "info": sum(item.get("severity") == "info" for item in findings),
        },
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
