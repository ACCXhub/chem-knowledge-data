from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[3]
PACKAGES = ROOT / "packages"
CONSOLIDATED = PACKAGES / "consolidated"
GENERATED = CONSOLIDATED / "generated"
SOURCE_INPUTS_FILE = CONSOLIDATED / "SOURCE_INPUTS.json"
IDENTITY_OVERRIDES_FILE = CONSOLIDATED / "data" / "identity_overrides.yaml"

INORGANIC = PACKAGES / "inorganic"
ORGANIC = PACKAGES / "organic"
STRUCTURE_REGISTRY = PACKAGES / "structure_registry"
STRUCTURAL_CHEMISTRY = PACKAGES / "structural_chemistry"
THERMOCHEMISTRY = PACKAGES / "thermochemistry"
STRUCTURAL_KNOWLEDGE_LINKS_FILE = CONSOLIDATED / "data" / "structural_knowledge_links.yaml"

STRUCTURAL_TYPE_MAP = {
    "atomic_configurations": "atomic_configuration",
    "concepts": "concept",
    "vsepr_models": "vsepr_model",
    "molecular_examples": "molecular_example",
    "bonding_examples": "bonding_example",
    "crystal_models": "crystal_model",
    "coordination_examples": "coordination_example",
    "relations": "relation",
    "structure_property_rules": "structure_property_rule",
    "exam_tags": "exam_tag",
}

ORGANIC_SUBSTANCE_FILES = [
    "core_substances.yaml",
    "extended_substances.yaml",
    "polymer_substances.yaml",
    "lipid_substances.yaml",
]
ORGANIC_REACTION_FILES = [
    "reactions.yaml",
    "property_reactions.yaml",
    "polymer_reactions.yaml",
    "lipid_reactions.yaml",
]
ORGANIC_KNOWLEDGE_DATASETS = [
    ("functional_group", "functional_groups.yaml", "functional_groups"),
    ("structural_feature", "functional_groups.yaml", "structural_features"),
    ("chemical_class", "classes.yaml", "classes"),
    ("chemical_class", "biomolecule_classes.yaml", "classes"),
    ("concept", "concepts.yaml", "concepts"),
    ("concept", "structure_concepts.yaml", "concepts"),
    ("concept", "biomolecule_concepts.yaml", "concepts"),
    ("concept", "applied_concepts.yaml", "concepts"),
    ("phenomenon", "phenomena.yaml", "phenomena"),
    ("experiment", "experiments.yaml", "experiments"),
]

PRIORITY_ORDER = {"core": 0, "common": 1, "extended": 2}
CATEGORY_ORDER = {
    "elemental_substance": 0,
    "cation": 1,
    "anion": 2,
    "acid": 3,
    "base": 4,
    "salt": 5,
    "oxide": 6,
    "organic": 7,
    "other": 8,
}
PREFERRED_STRUCTURE_RELATIONS = {"primary_structure", "ion_structure", "formula_unit"}


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
                raise ValueError(f"{path}:{line_no}: expected object")
            output.append(value)
    return output


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    materialized = list(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in materialized:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
    return len(materialized)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_ref(package: str, raw: str) -> str:
    return f"{package}:{raw}"


def stable_species_id(package: str, source_id: str) -> str:
    return f"species:{package}:{source_id}"


def stable_reaction_id(package: str, source_id: str) -> str:
    return f"reaction:{package}:{source_id}"


def stable_knowledge_id(package: str, source_type: str, source_id: str) -> str:
    return f"knowledge:{package}:{source_type}:{source_id}"


def stable_knowledge_link_id(source_id: str, relation: str, target_kind: str, target_id: str) -> str:
    raw = "|".join((source_id, relation, target_kind, target_id))
    return "knowledge-link:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def finding_id(kind: str, refs: list[str], ordinal: int = 0) -> str:
    raw = "|".join([kind, *sorted(refs), str(ordinal)])
    return "finding:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def normalize_text(value: str) -> str:
    return re.sub(r"[\s\-_(),，（）]+", "", value).casefold()


def parse_formula(formula: str) -> dict[str, int] | None:
    if re.fullmatch(r"\(.+\)n", formula):
        return None
    stack: list[dict[str, int]] = [defaultdict(int)]
    index = 0
    while index < len(formula):
        char = formula[index]
        if char == "(":
            stack.append(defaultdict(int))
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
    return dict(stack[0])


def provenance_from(record: dict[str, Any], package: str) -> list[str]:
    values: list[str] = []
    for key in ("sources", "provenance_refs", "source_refs"):
        raw = record.get(key)
        if isinstance(raw, list):
            values.extend(str(item) for item in raw if isinstance(item, (str, int)))
    if isinstance(record.get("provenance"), list):
        for item in record["provenance"]:
            if not isinstance(item, dict):
                continue
            if item.get("source_id"):
                values.append(str(item["source_id"]))
            if item.get("record_locator"):
                values.append(f"locator:{item['record_locator']}")
    result = sorted({source_ref(package, value) for value in values if value})
    return result or [f"{package}:package-release"]


def display_name(record: dict[str, Any]) -> str:
    for key in ("name_zh", "title_zh", "term_zh", "label_zh", "name", "title", "id"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "未命名记录"


def load_inorganic_records(manifest: dict[str, Any], key: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for relative in manifest["canonical_files"].get(key, []):
        output.extend(load_jsonl(INORGANIC / relative))
    return output


def load_organic_records(files: list[str], root_key: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for filename in files:
        records = load_yaml(ORGANIC / "data" / filename).get(root_key, [])
        if not isinstance(records, list):
            raise ValueError(f"{filename}: {root_key} must be a list")
        output.extend(item for item in records if isinstance(item, dict))
    return output


def add_finding(
    findings: list[dict[str, Any]],
    *,
    severity: str,
    kind: str,
    message: str,
    refs: list[str],
    details: dict[str, Any] | None = None,
    ordinal: int = 0,
) -> None:
    findings.append(
        {
            "id": finding_id(kind, refs, ordinal),
            "severity": severity,
            "kind": kind,
            "message": message,
            "source_refs": refs,
            "details": details,
        }
    )


def source_snapshot(findings: list[dict[str, Any]]) -> dict[str, Any]:
    pins = load_json(SOURCE_INPUTS_FILE)["inputs"]
    inorganic = load_json(INORGANIC / "manifest.json")
    organic = load_yaml(ORGANIC / "package.yaml")
    registry = load_json(STRUCTURE_REGISTRY / "data" / "manifest.json")
    structural = load_json(STRUCTURAL_CHEMISTRY / "manifest.json")
    thermochemistry = load_json(THERMOCHEMISTRY / "manifest.json")
    actual = {
        "inputs": {
            "inorganic": {
                "release": inorganic.get("version"),
                "state": inorganic.get("status"),
                "total_records": inorganic.get("total_records"),
            },
            "organic": {
                "release": str(organic.get("version")),
                "state": organic.get("status"),
                "substances": organic.get("validation", {}).get("counts", {}).get("substances"),
                "reactions": organic.get("validation", {}).get("counts", {}).get("reactions"),
            },
            "structure_registry": {
                "release": registry.get("dataset_version"),
                "state": "PUBLISHED",
                "structures": registry.get("counts", {}).get("total"),
                "inorganic_links": registry.get("cross_track", {}).get("inorganic_accepted_links"),
                "organic_links": registry.get("cross_track", {}).get("organic_accepted_links"),
                "organic_deferrals": registry.get("cross_track", {}).get("organic_deferrals"),
            },
            "structural_chemistry": {
                "release": structural.get("release"),
                "state": structural.get("state"),
                "total_records": structural.get("total_records"),
            },
            "thermochemistry": {
                "release": thermochemistry.get("release"),
                "state": thermochemistry.get("state"),
                "species_phase_facts": thermochemistry.get("records", {}).get("species_phase_facts"),
                "species_thermochemistry": thermochemistry.get("records", {}).get("species_thermochemistry"),
                "phase_transitions": thermochemistry.get("records", {}).get("phase_transitions"),
                "bond_enthalpies": thermochemistry.get("records", {}).get("bond_enthalpies"),
                "unresolved_source_mappings": thermochemistry.get("unresolved_source_mappings"),
            },
        }
    }
    checks = [
        ("inorganic", "release", pins["inorganic"]["release"], actual["inputs"]["inorganic"]["release"]),
        ("inorganic", "total_records", pins["inorganic"]["expected_total_records"], actual["inputs"]["inorganic"]["total_records"]),
        ("organic", "release", pins["organic"]["release"], actual["inputs"]["organic"]["release"]),
        ("organic", "substances", pins["organic"]["expected_substances"], actual["inputs"]["organic"]["substances"]),
        ("organic", "reactions", pins["organic"]["expected_reactions"], actual["inputs"]["organic"]["reactions"]),
        ("structure_registry", "release", pins["structure_registry"]["release"], actual["inputs"]["structure_registry"]["release"]),
        ("structure_registry", "structures", pins["structure_registry"]["expected_structures"], actual["inputs"]["structure_registry"]["structures"]),
        ("structure_registry", "inorganic_links", pins["structure_registry"]["expected_inorganic_links"], actual["inputs"]["structure_registry"]["inorganic_links"]),
        ("structure_registry", "organic_links", pins["structure_registry"]["expected_organic_links"], actual["inputs"]["structure_registry"]["organic_links"]),
        ("structure_registry", "organic_deferrals", pins["structure_registry"]["expected_organic_deferrals"], actual["inputs"]["structure_registry"]["organic_deferrals"]),
        ("structural_chemistry", "release", pins["structural_chemistry"]["release"], actual["inputs"]["structural_chemistry"]["release"]),
        ("structural_chemistry", "total_records", pins["structural_chemistry"]["expected_total_records"], actual["inputs"]["structural_chemistry"]["total_records"]),
        ("thermochemistry", "release", pins["thermochemistry"]["release"], actual["inputs"]["thermochemistry"]["release"]),
        ("thermochemistry", "species_phase_facts", pins["thermochemistry"]["expected_species_phase_facts"], actual["inputs"]["thermochemistry"]["species_phase_facts"]),
        ("thermochemistry", "species_thermochemistry", pins["thermochemistry"]["expected_species_thermochemistry"], actual["inputs"]["thermochemistry"]["species_thermochemistry"]),
        ("thermochemistry", "phase_transitions", pins["thermochemistry"]["expected_phase_transitions"], actual["inputs"]["thermochemistry"]["phase_transitions"]),
        ("thermochemistry", "bond_enthalpies", pins["thermochemistry"]["expected_bond_enthalpies"], actual["inputs"]["thermochemistry"]["bond_enthalpies"]),
        ("thermochemistry", "unresolved_source_mappings", pins["thermochemistry"]["expected_unresolved_source_mappings"], actual["inputs"]["thermochemistry"]["unresolved_source_mappings"]),
    ]
    for package, field, expected, observed in checks:
        if expected != observed:
            add_finding(
                findings,
                severity="blocking",
                kind="source_snapshot_mismatch",
                message=f"Pinned {package}.{field}={expected!r}, current source has {observed!r}",
                refs=[f"{package}:{field}"],
                details={"expected": expected, "actual": observed},
            )
    return actual


def build_crosswalk(
    source_species: dict[tuple[str, str], dict[str, Any]],
    findings: list[dict[str, Any]],
) -> tuple[dict[tuple[str, str], str], list[dict[str, Any]]]:
    mapping = {key: stable_species_id(*key) for key in source_species}
    methods = {key: "source_anchor" for key in source_species}
    evidence = {key: [f"packages/{key[0]}"] for key in source_species}

    overrides = load_yaml(IDENTITY_OVERRIDES_FILE) if IDENTITY_OVERRIDES_FILE.exists() else {"merges": []}
    for index, merge in enumerate(overrides.get("merges", [])):
        if not isinstance(merge, dict):
            continue
        survivor = merge.get("survivor")
        members = merge.get("members", [])
        if not isinstance(survivor, dict) or not isinstance(members, list):
            add_finding(
                findings,
                severity="blocking",
                kind="invalid_identity_override",
                message="Identity override must define survivor and members",
                refs=["consolidated:identity_overrides"],
                details=merge,
                ordinal=index,
            )
            continue
        survivor_key = (str(survivor.get("package")), str(survivor.get("id")))
        if survivor_key not in source_species:
            add_finding(
                findings,
                severity="blocking",
                kind="invalid_identity_override",
                message="Identity override survivor is absent from the pinned source snapshot",
                refs=[f"{survivor_key[0]}:{survivor_key[1]}"],
                details=merge,
                ordinal=index,
            )
            continue
        target = stable_species_id(*survivor_key)
        for member_index, member in enumerate(members):
            if not isinstance(member, dict):
                continue
            key = (str(member.get("package")), str(member.get("id")))
            if key not in source_species:
                add_finding(
                    findings,
                    severity="blocking",
                    kind="invalid_identity_override",
                    message="Identity override member is absent from the pinned source snapshot",
                    refs=[f"{key[0]}:{key[1]}"],
                    details=merge,
                    ordinal=index * 100 + member_index,
                )
                continue
            mapping[key] = target
            methods[key] = "reviewed_manual"
            evidence[key] = [str(item) for item in merge.get("evidence_refs", [])] or [
                "packages/consolidated/data/identity_overrides.yaml"
            ]

    records = []
    for key in sorted(source_species):
        package, source_id = key
        records.append(
            {
                "source_package": package,
                "source_entity_type": "ion" if source_species[key].get("kind") == "ion" else "substance",
                "source_id": source_id,
                "consolidated_id": mapping[key],
                "mapping_status": "resolved",
                "resolution_method": methods[key],
                "evidence_refs": evidence[key],
                "notes": None,
            }
        )
    return mapping, records


def load_structure_registry(
    crosswalk: dict[tuple[str, str], str], findings: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], str]]:
    registry_manifest = load_json(STRUCTURE_REGISTRY / "data" / "manifest.json")
    published_ids: set[str] = set()
    for relative in registry_manifest.get("files", {}):
        if not relative.startswith("canonical/") or not relative.endswith(".jsonl"):
            continue
        for record in load_jsonl(STRUCTURE_REGISTRY / "data" / relative):
            validation = record.get("validation", {})
            if validation.get("status") == "valid" and validation.get("review_status") == "published":
                published_ids.add(str(record["structure_id"]))

    links: list[dict[str, Any]] = []
    preferred: dict[tuple[str, str], str] = {}
    for package in ("inorganic", "organic"):
        path = STRUCTURE_REGISTRY / "data" / "links" / f"{package}.jsonl"
        for link in load_jsonl(path):
            if link.get("status") != "accepted":
                continue
            source_id = str(link.get("entity_ref"))
            key = (package, source_id)
            refs = [f"{package}:{source_id}", f"structure_registry:{link.get('link_id')}"]
            if key not in crosswalk:
                add_finding(
                    findings,
                    severity="info",
                    kind="historical_structure_link_outside_snapshot",
                    message="Accepted Structure Registry link belongs to its frozen source snapshot but the source entity is not present in the current pinned package release; consumer link is skipped",
                    refs=refs,
                    details={"relation": link.get("relation"), "structure_id": link.get("structure_id")},
                )
                continue
            structure_id = str(link.get("structure_id"))
            if structure_id not in published_ids:
                add_finding(
                    findings,
                    severity="blocking",
                    kind="missing_structure_target",
                    message="Accepted Structure Registry link points to a non-published Structure",
                    refs=refs,
                    details={"structure_id": structure_id},
                )
                continue
            links.append(
                {
                    "species_id": crosswalk[key],
                    "source_package": package,
                    "source_id": source_id,
                    "structure_id": structure_id,
                    "relation": str(link.get("relation")),
                    "source_link_id": str(link.get("link_id")),
                    "evidence_refs": sorted(
                        {source_ref("structure_registry", str(item)) for item in link.get("evidence", [])}
                    ),
                }
            )
            if link.get("relation") in PREFERRED_STRUCTURE_RELATIONS:
                existing = preferred.get(key)
                if existing and existing != structure_id:
                    add_finding(
                        findings,
                        severity="review",
                        kind="multiple_preferred_structures",
                        message="One source species has multiple candidate preferred Structure targets",
                        refs=refs,
                        details={"existing": existing, "candidate": structure_id},
                    )
                else:
                    preferred[key] = structure_id

    deferrals = STRUCTURE_REGISTRY / "data" / "deferrals" / "organic.jsonl"
    if deferrals.exists():
        for item in load_jsonl(deferrals):
            source_id = str(item.get("entity_ref"))
            add_finding(
                findings,
                severity="info",
                kind="structure_identity_deferred",
                message="Structure Registry explicitly defers full structure identity for this organic species/material",
                refs=[f"organic:{source_id}", f"structure_registry:{item.get('deferral_id')}"],
                details={
                    "reason": item.get("reason"),
                    "available_abstraction_structure_ids": item.get("available_abstraction_structure_ids", []),
                    "notes": item.get("notes"),
                },
            )

    links.sort(key=lambda item: (item["species_id"], item["relation"], item["structure_id"]))
    return links, preferred


def organic_external_ids() -> dict[str, list[dict[str, str]]]:
    output: dict[str, list[dict[str, str]]] = defaultdict(list)
    path = ORGANIC / "data" / "identity_crossrefs.yaml"
    if not path.exists():
        return output
    for item in load_yaml(path).get("crossrefs", []):
        if not isinstance(item, dict) or not item.get("substance_ref"):
            continue
        source_id = str(item["substance_ref"])
        if item.get("pubchem_cid"):
            output[source_id].append({"namespace": "pubchem_cid", "value": str(item["pubchem_cid"])})
        if item.get("chebi_id"):
            output[source_id].append({"namespace": "chebi", "value": str(item["chebi_id"])})
    return output


def merge_species(
    consolidated_id: str,
    members: list[tuple[str, dict[str, Any]]],
    preferred_by_source: dict[tuple[str, str], str],
    external_by_organic: dict[str, list[dict[str, str]]],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    members = sorted(members, key=lambda item: (0 if item[0] == "inorganic" else 1, str(item[1]["id"])))
    primary_package, primary = members[0]
    formulas = {str(record.get("formula")) for _, record in members if record.get("formula")}
    charges = {int(record.get("charge", 0)) for _, record in members}
    refs = [f"{package}:{record['id']}" for package, record in members]
    if len(formulas) > 1 or len(charges) > 1:
        add_finding(
            findings,
            severity="blocking",
            kind="merged_identity_conflict",
            message="Reviewed identity merge has conflicting formula or charge",
            refs=refs,
            details={"formulas": sorted(formulas), "charges": sorted(charges)},
        )

    aliases: set[str] = set()
    classifications: set[str] = set()
    provenance: set[str] = set()
    review_states: list[dict[str, str]] = []
    priorities: list[str] = []
    structures: set[str] = set()
    external: dict[tuple[str, str], dict[str, str]] = {}

    for package, record in members:
        aliases.update(str(value) for value in record.get("aliases", []) if value)
        if record.get("category"):
            classifications.add(str(record["category"]))
        if package == "inorganic" and record.get("aqueous_behavior"):
            classifications.add(str(record["aqueous_behavior"]))
        for fg in record.get("functional_group_refs", []) if package == "organic" else []:
            classifications.add(f"functional_group:{fg}")
        state_key = "review_status" if package == "inorganic" else "verification_status"
        review_states.append({"package": package, "state": str(record.get(state_key, "unknown"))})
        priorities.append(str(record.get("teaching_priority", "extended")))
        provenance.update(provenance_from(record, package))
        structure_id = preferred_by_source.get((package, str(record["id"])))
        if structure_id:
            structures.add(structure_id)
        if package == "organic":
            for item in external_by_organic.get(str(record["id"]), []):
                external[(item["namespace"], item["value"])] = item

    preferred_structure_id: str | None = None
    if len(structures) == 1:
        preferred_structure_id = next(iter(structures))
    elif len(structures) > 1:
        add_finding(
            findings,
            severity="review",
            kind="merged_structure_conflict",
            message="Merged source identities point to different preferred Structure records",
            refs=refs,
            details={"structure_ids": sorted(structures)},
        )

    composition = primary.get("composition")
    if composition is None and primary_package == "organic":
        composition = parse_formula(str(primary.get("formula", "")))

    return {
        "id": consolidated_id,
        "entity_kind": "ion" if primary.get("kind") == "ion" else "substance",
        "source_ids": [{"package": package, "id": str(record["id"])} for package, record in members],
        "name_zh": str(primary.get("name_zh") or display_name(primary)),
        "name_en": primary.get("name_en"),
        "formula": str(primary.get("formula")),
        "charge": int(primary.get("charge", 0)),
        "composition": composition,
        "aliases": sorted(aliases),
        "chemical_classifications": sorted(classifications),
        "teaching_priority": min(priorities, key=lambda value: PRIORITY_ORDER.get(value, 99)),
        "source_review_states": review_states,
        "preferred_structure_id": preferred_structure_id,
        "external_ids": sorted(external.values(), key=lambda item: (item["namespace"], item["value"])),
        "integration_status": "resolved",
        "provenance_refs": sorted(provenance),
    }


def find_duplicate_candidates(species: list[dict[str, Any]], findings: list[dict[str, Any]]) -> None:
    inorganic = [
        item for item in species
        if item["entity_kind"] == "substance" and any(src["package"] == "inorganic" for src in item["source_ids"])
    ]
    organic = [
        item for item in species
        if item["entity_kind"] == "substance" and any(src["package"] == "organic" for src in item["source_ids"])
    ]
    for left in inorganic:
        left_names = {normalize_text(left["name_zh"]), normalize_text(left.get("name_en") or "")}
        left_names.update(normalize_text(alias) for alias in left["aliases"])
        left_names.discard("")
        for right in organic:
            if left["id"] == right["id"] or left["formula"] != right["formula"]:
                continue
            right_names = {normalize_text(right["name_zh"]), normalize_text(right.get("name_en") or "")}
            right_names.update(normalize_text(alias) for alias in right["aliases"])
            right_names.discard("")
            shared_structure = bool(
                left.get("preferred_structure_id")
                and left.get("preferred_structure_id") == right.get("preferred_structure_id")
            )
            if left_names.intersection(right_names) or shared_structure:
                add_finding(
                    findings,
                    severity="review",
                    kind="cross_package_duplicate_candidate",
                    message="Two source species may represent the same chemical identity; they remain separate until reviewed",
                    refs=[left["id"], right["id"]],
                    details={
                        "formula": left["formula"],
                        "shared_name": bool(left_names.intersection(right_names)),
                        "shared_structure": shared_structure,
                    },
                )


def primary_category(species: dict[str, Any]) -> str:
    if species["entity_kind"] == "ion":
        return "cation" if species["charge"] > 0 else "anion" if species["charge"] < 0 else "other"
    packages = {item["package"] for item in species["source_ids"]}
    if packages == {"organic"}:
        return "organic"
    classes = set(species["chemical_classifications"])
    for source_class, category in {
        "simple_substance": "elemental_substance",
        "acid": "acid",
        "base": "base",
        "salt": "salt",
        "oxide": "oxide",
    }.items():
        if source_class in classes:
            return category
    return "organic" if "organic" in packages else "other"


def build_teaching_projection(species: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        species,
        key=lambda item: (
            PRIORITY_ORDER.get(item["teaching_priority"], 99),
            CATEGORY_ORDER.get(primary_category(item), 99),
            item["name_zh"],
            item["id"],
        ),
    )
    output: list[dict[str, Any]] = []
    for rank, item in enumerate(ordered):
        category = primary_category(item)
        tags = set(item["chemical_classifications"])
        tags.update(f"source:{source['package']}" for source in item["source_ids"])
        tokens = {item["name_zh"], item["formula"], *item["aliases"]}
        if item.get("name_en"):
            tokens.add(str(item["name_en"]))
        tokens.update(f"{external['namespace']}:{external['value']}" for external in item["external_ids"])

        if item["entity_kind"] == "ion":
            modes = {"molecular": "deemphasized", "ionic": "recommended", "net_ionic": "recommended"}
        elif category == "organic":
            modes = {"molecular": "recommended", "ionic": "deemphasized", "net_ionic": "deemphasized"}
        elif "strong_electrolyte" in tags:
            modes = {"molecular": "recommended", "ionic": "available", "net_ionic": "available"}
        elif tags.intersection({"weak_electrolyte", "weak_base", "acid_equilibrium", "insoluble", "sparingly_soluble"}):
            modes = {"molecular": "recommended", "ionic": "available", "net_ionic": "deemphasized"}
        else:
            modes = {"molecular": "recommended", "ionic": "deemphasized", "net_ionic": "deemphasized"}

        output.append(
            {
                "species_id": item["id"],
                "primary_category": category,
                "tags": sorted(tags),
                "search_tokens": sorted(value for value in tokens if isinstance(value, str) and value.strip()),
                "default_priority": item["teaching_priority"],
                "default_palette_rank": rank,
                "equation_modes": modes,
            }
        )
    return output


def resolve_inorganic_external(raw: str, crosswalk: dict[tuple[str, str], str]) -> tuple[str | None, str]:
    if not raw.startswith("inorganic:"):
        return None, raw
    slug = raw.split(":", 1)[1]
    for source_id in (f"substance:{slug}", f"ion:{slug}"):
        target = crosswalk.get(("inorganic", source_id))
        if target:
            return target, source_id
    return None, raw


def build_reactions(
    inorganic_records: list[dict[str, Any]],
    organic_records: list[dict[str, Any]],
    crosswalk: dict[tuple[str, str], str],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    def normalize_participant(
        package: str,
        reaction_source_id: str,
        raw: dict[str, Any],
        forced_role: str | None = None,
    ) -> dict[str, Any]:
        role = forced_role or str(raw.get("role"))
        species_id: str | None = None
        non_species_ref: str | None = None
        source_species_ref = ""

        if package == "inorganic":
            source_id = str(raw.get("species_id"))
            source_species_ref = f"inorganic:{source_id}"
            species_id = crosswalk.get(("inorganic", source_id))
        elif raw.get("substance_ref"):
            source_id = str(raw["substance_ref"])
            source_species_ref = f"organic:{source_id}"
            species_id = crosswalk.get(("organic", source_id))
        elif raw.get("external_species_key"):
            external = str(raw["external_species_key"])
            if external.startswith("organic-material:"):
                source_species_ref = external
                non_species_ref = external
                add_finding(
                    findings,
                    severity="info",
                    kind="non_species_material_participant",
                    message="Reaction intentionally references a non-discrete teaching material rather than inventing a Substance identity",
                    refs=[f"organic:{reaction_source_id}", external],
                    details={"role": role},
                )
            else:
                species_id, resolved_source = resolve_inorganic_external(external, crosswalk)
                source_species_ref = f"inorganic:{resolved_source}" if species_id else external
        else:
            source_species_ref = str(raw.get("formula_literal") or "unresolved")

        if role in {"reactant", "product"} and species_id is None and non_species_ref is None:
            add_finding(
                findings,
                severity="blocking",
                kind="unresolved_reaction_participant",
                message="Required Reaction participant cannot be resolved to a consolidated species or an explicitly modeled non-species teaching material",
                refs=[f"{package}:{reaction_source_id}", source_species_ref],
                details=raw,
            )

        return {
            "role": role,
            "coefficient": raw.get("coefficient", 1),
            "species_id": species_id,
            "non_species_ref": non_species_ref,
            "source_species_ref": source_species_ref,
            "formula_literal": raw.get("formula_literal"),
            "phase": raw.get("phase"),
        }

    def required_resolved(item: dict[str, Any]) -> bool:
        return item["role"] not in {"reactant", "product"} or bool(item["species_id"] or item["non_species_ref"])

    for record in inorganic_records:
        source_id = str(record["id"])
        participants = [
            normalize_participant("inorganic", source_id, item, "reactant")
            for item in record.get("reactants", [])
        ]
        participants.extend(
            normalize_participant("inorganic", source_id, item, "product")
            for item in record.get("products", [])
        )
        net_ionic = None
        if isinstance(record.get("net_ionic"), dict):
            net_parts = [
                normalize_participant("inorganic", source_id, item, "reactant")
                for item in record["net_ionic"].get("reactants", [])
            ]
            net_parts.extend(
                normalize_participant("inorganic", source_id, item, "product")
                for item in record["net_ionic"].get("products", [])
            )
            net_ionic = {"participants": net_parts}
        resolved = all(required_resolved(item) for item in participants)
        if net_ionic:
            resolved = resolved and all(item["species_id"] is not None for item in net_ionic["participants"])
        output.append(
            {
                "id": stable_reaction_id("inorganic", source_id),
                "source_package": "inorganic",
                "source_id": source_id,
                "name_zh": str(record.get("name_zh") or source_id),
                "participants": participants,
                "reaction_types": list(record.get("reaction_types", [])),
                "conditions": list(record.get("conditions", [])),
                "equation": record.get("equation"),
                "equation_status": record.get("equation_status"),
                "phenomenon_refs": [source_ref("inorganic", str(item)) for item in record.get("phenomenon_ids", [])],
                "experiment_refs": [source_ref("inorganic", str(item)) for item in record.get("experiment_ids", [])],
                "concept_refs": [source_ref("inorganic", str(item)) for item in record.get("concept_ids", [])],
                "net_ionic": net_ionic,
                "reversible": record.get("reversible"),
                "teaching_priority": str(record.get("teaching_priority", "extended")),
                "source_review_state": str(record.get("review_status", "unknown")),
                "integration_status": "resolved" if resolved else "review_required",
                "provenance_refs": provenance_from(record, "inorganic"),
                "notes": record.get("notes"),
            }
        )

    for record in organic_records:
        source_id = str(record["id"])
        participants = [normalize_participant("organic", source_id, item) for item in record.get("participants", [])]
        resolved = all(required_resolved(item) for item in participants)
        output.append(
            {
                "id": stable_reaction_id("organic", source_id),
                "source_package": "organic",
                "source_id": source_id,
                "name_zh": str(record.get("name_zh") or source_id),
                "participants": participants,
                "reaction_types": list(record.get("reaction_class", [])),
                "conditions": list(record.get("conditions", [])),
                "equation": record.get("equation"),
                "equation_status": record.get("equation_status"),
                "phenomenon_refs": [source_ref("organic", str(item)) for item in record.get("phenomenon_refs", [])],
                "experiment_refs": [source_ref("organic", str(item)) for item in record.get("experiment_refs", [])],
                "concept_refs": [source_ref("organic", str(item)) for item in record.get("concept_refs", [])],
                "net_ionic": None,
                "reversible": record.get("reversible"),
                "teaching_priority": str(record.get("teaching_priority", "extended")),
                "source_review_state": str(record.get("verification_status", "unknown")),
                "integration_status": "resolved" if resolved else "review_required",
                "provenance_refs": provenance_from(record, "organic"),
                "notes": record.get("notes"),
            }
        )

    output.sort(key=lambda item: item["id"])
    return output


def build_knowledge_records(inorganic_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for source_type in ("element_scope", "phenomena", "experiments", "concepts", "exam_tags"):
        singular = {
            "phenomena": "phenomenon",
            "experiments": "experiment",
            "concepts": "concept",
            "exam_tags": "exam_tag",
        }.get(source_type, source_type)
        for record in load_inorganic_records(inorganic_manifest, source_type):
            source_id = str(record["id"])
            output.append(
                {
                    "id": stable_knowledge_id("inorganic", singular, source_id),
                    "source_package": "inorganic",
                    "source_type": singular,
                    "source_id": source_id,
                    "display_name_zh": display_name(record),
                    "teaching_priority": record.get("teaching_priority"),
                    "provenance_refs": provenance_from(record, "inorganic"),
                    "payload": record,
                }
            )

    seen_organic: set[tuple[str, str]] = set()
    for source_type, filename, root_key in ORGANIC_KNOWLEDGE_DATASETS:
        records = load_yaml(ORGANIC / "data" / filename).get(root_key, [])
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict) or not record.get("id"):
                continue
            source_id = str(record["id"])
            key = (source_type, source_id)
            if key in seen_organic:
                continue
            seen_organic.add(key)
            output.append(
                {
                    "id": stable_knowledge_id("organic", source_type, source_id),
                    "source_package": "organic",
                    "source_type": source_type,
                    "source_id": source_id,
                    "display_name_zh": display_name(record),
                    "teaching_priority": record.get("teaching_priority"),
                    "provenance_refs": provenance_from(record, "organic"),
                    "payload": record,
                }
            )

    for path in sorted((STRUCTURAL_CHEMISTRY / "data").glob("*.jsonl")):
        source_type = path.stem
        for record in load_jsonl(path):
            source_id = str(record.get("id") or "")
            if not source_id:
                source_id = hashlib.sha256(
                    json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest()[:24]
            output.append(
                {
                    "id": stable_knowledge_id("structural_chemistry", source_type, source_id),
                    "source_package": "structural_chemistry",
                    "source_type": source_type,
                    "source_id": source_id,
                    "display_name_zh": display_name(record),
                    "teaching_priority": record.get("teaching_priority"),
                    "provenance_refs": provenance_from(record, "structural_chemistry"),
                    "payload": record,
                }
            )

    output.sort(key=lambda item: item["id"])
    return output


def build_knowledge_links(
    knowledge: list[dict[str, Any]],
    species: list[dict[str, Any]],
    structure_links: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    structural_by_source = {
        str(item["source_id"]): item
        for item in knowledge
        if item.get("source_package") == "structural_chemistry"
    }
    species_ids = {str(item["id"]) for item in species}
    structures_by_species: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in structure_links:
        structures_by_species[str(item["species_id"])].append(item)

    def knowledge_id(item: dict[str, Any]) -> str:
        source_type = STRUCTURAL_TYPE_MAP.get(str(item["source_type"]), str(item["source_type"]))
        return stable_knowledge_id("structural_chemistry", source_type, str(item["source_id"]))

    output: list[dict[str, Any]] = []

    def add_link(
        source_knowledge_id: str,
        relation: str,
        target_kind: str,
        target_id: str,
        resolution_method: str,
        evidence_refs: list[str],
    ) -> None:
        output.append(
            {
                "id": stable_knowledge_link_id(source_knowledge_id, relation, target_kind, target_id),
                "source_knowledge_id": source_knowledge_id,
                "relation": relation,
                "target_kind": target_kind,
                "target_id": target_id,
                "resolution_method": resolution_method,
                "evidence_refs": sorted(set(evidence_refs)),
            }
        )

    for item in structural_by_source.values():
        payload = item["payload"]
        source_id = knowledge_id(item)
        source_type = str(item["source_type"])
        if source_type == "atomic_configurations":
            atomic_number = int(payload["atomic_number"])
            add_link(
                source_id,
                "describes_element",
                "element",
                f"element:{atomic_number}:{payload['symbol']}",
                "atomic_number_and_symbol",
                ["structural_chemistry:atomic-configuration", *item["provenance_refs"]],
            )

        if source_type == "molecular_examples" and isinstance(payload.get("vsepr_pattern"), str):
            pattern = str(payload["vsepr_pattern"])
            model = next(
                (
                    candidate
                    for candidate in structural_by_source.values()
                    if candidate.get("source_type") == "vsepr_models"
                    and candidate["payload"].get("ax_e_notation") == pattern
                ),
                None,
            )
            if model is not None:
                add_link(
                    source_id,
                    "uses_teaching_model",
                    "knowledge",
                    knowledge_id(model),
                    "reviewed_field_reference",
                    [f"structural_chemistry:vsepr-pattern:{pattern}"],
                )

        if source_type == "bonding_examples":
            for interaction in payload.get("interactions", []):
                concept_ref = str(interaction.get("concept_ref", ""))
                target = structural_by_source.get(concept_ref)
                if target is None:
                    add_finding(
                        findings,
                        severity="blocking",
                        kind="dangling_structural_knowledge_reference",
                        message="Bonding example references missing structural chemistry concept",
                        refs=[str(item["source_id"]), concept_ref],
                    )
                    continue
                add_link(
                    source_id,
                    "uses_bonding_concept",
                    "knowledge",
                    knowledge_id(target),
                    "reviewed_field_reference",
                    [f"structural_chemistry:{item['source_id']}"],
                )

        if source_type == "relations":
            source_ref = str(payload.get("source_ref", ""))
            target_ref = str(payload.get("target_ref", ""))
            source = structural_by_source.get(source_ref)
            target = structural_by_source.get(target_ref)
            if source is None or target is None:
                add_finding(
                    findings,
                    severity="blocking",
                    kind="dangling_structural_knowledge_reference",
                    message="Structural chemistry relation has a missing endpoint",
                    refs=[str(item["source_id"]), source_ref, target_ref],
                )
                continue
            add_link(
                knowledge_id(source),
                str(payload["relation_type"]),
                "knowledge",
                knowledge_id(target),
                "reviewed_relation_record",
                [source_id],
            )

    reviewed = load_yaml(STRUCTURAL_KNOWLEDGE_LINKS_FILE).get("reviewed_species_links", [])
    for index, link in enumerate(reviewed):
        if not isinstance(link, dict):
            continue
        source_record = structural_by_source.get(str(link.get("source_id")))
        target_species_id = str(link.get("species_id"))
        refs = ["consolidated:data/structural_knowledge_links.yaml", *link.get("evidence_refs", [])]
        if source_record is None or target_species_id not in species_ids:
            add_finding(
                findings,
                severity="blocking",
                kind="invalid_reviewed_knowledge_link",
                message="Reviewed structural knowledge link has a missing source or species target",
                refs=[str(link.get("source_id")), target_species_id],
                details=link,
                ordinal=index,
            )
            continue
        source_knowledge_id = knowledge_id(source_record)
        add_link(
            source_knowledge_id,
            "describes_species",
            "species",
            target_species_id,
            "reviewed_identity_resolution",
            refs,
        )
        for structure_link in structures_by_species.get(target_species_id, []):
            add_link(
                source_knowledge_id,
                "describes_structure",
                "structure",
                str(structure_link["structure_id"]),
                "accepted_structure_link",
                [*refs, f"structure_registry:{structure_link['source_link_id']}"],
            )

    deduplicated = {item["id"]: item for item in output}
    return sorted(deduplicated.values(), key=lambda item: item["id"])


def build_thermochemistry(
    species: list[dict[str, Any]], findings: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    species_ids = {str(item["id"]) for item in species}
    artifacts = {
        "species_phase_facts": load_jsonl(THERMOCHEMISTRY / "data" / "species_phase_facts.jsonl"),
        "species_thermochemistry": load_jsonl(THERMOCHEMISTRY / "data" / "species_thermochemistry.jsonl"),
        "phase_transitions": load_jsonl(THERMOCHEMISTRY / "data" / "phase_transitions.jsonl"),
        "bond_enthalpies": load_jsonl(THERMOCHEMISTRY / "data" / "bond_enthalpies.jsonl"),
    }
    for family in ("species_phase_facts", "species_thermochemistry", "phase_transitions"):
        for item in artifacts[family]:
            species_id = str(item.get("species_id"))
            if species_id not in species_ids:
                add_finding(
                    findings,
                    severity="blocking",
                    kind="unresolved_thermochemistry_species",
                    message="Thermochemistry record references a missing consolidated species",
                    refs=[f"thermochemistry:{item.get('id')}", species_id],
                )
    for records in artifacts.values():
        records.sort(key=lambda item: str(item["id"]))
    return artifacts


def copy_rules_and_curriculum(inorganic_manifest: dict[str, Any]) -> None:
    rules_dir = GENERATED / "rules"
    curriculum_dir = GENERATED / "curriculum"
    rules_dir.mkdir(parents=True, exist_ok=True)
    curriculum_dir.mkdir(parents=True, exist_ok=True)
    for relative in inorganic_manifest.get("rule_files", []):
        source = INORGANIC / relative
        shutil.copyfile(source, rules_dir / source.name)
    shutil.copyfile(INORGANIC / inorganic_manifest["curriculum_file"], curriculum_dir / "inorganic.json")
    write_json(curriculum_dir / "organic.json", load_yaml(ORGANIC / "data" / "curriculum_coverage.yaml"))
    shutil.copyfile(
        STRUCTURAL_CHEMISTRY / "curriculum" / "coverage.json",
        curriculum_dir / "structural_chemistry_coverage.json",
    )
    shutil.copyfile(
        STRUCTURAL_CHEMISTRY / "curriculum" / "scope.json",
        curriculum_dir / "structural_chemistry_scope.json",
    )


def build_manifest(counts: dict[str, int], findings: list[dict[str, Any]]) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    for path in sorted(GENERATED.rglob("*")):
        if not path.is_file() or path.name in {"manifest.json", "validation_report.json"}:
            continue
        relative = path.relative_to(GENERATED).as_posix()
        meta: dict[str, Any] = {"sha256": sha256_file(path)}
        if path.suffix == ".jsonl":
            meta["records"] = len(load_jsonl(path))
        files[relative] = meta
    return {
        "package": "consolidated",
        "release": "consolidated-draft-1",
        "state": "generated_candidate",
        "source_snapshot_file": "source_snapshot.json",
        "counts": counts,
        "blocking_findings": sum(item["severity"] == "blocking" for item in findings),
        "review_findings": sum(item["severity"] == "review" for item in findings),
        "info_findings": sum(item["severity"] == "info" for item in findings),
        "files": files,
    }


def main() -> int:
    if GENERATED.exists():
        shutil.rmtree(GENERATED)
    GENERATED.mkdir(parents=True, exist_ok=True)

    findings: list[dict[str, Any]] = []
    snapshot = source_snapshot(findings)
    inorganic_manifest = load_json(INORGANIC / "manifest.json")

    inorganic_ions = load_inorganic_records(inorganic_manifest, "ions")
    inorganic_substances = load_inorganic_records(inorganic_manifest, "substances")
    inorganic_reactions = load_inorganic_records(inorganic_manifest, "reactions")
    organic_substances = load_organic_records(ORGANIC_SUBSTANCE_FILES, "records")
    organic_reactions = load_organic_records(ORGANIC_REACTION_FILES, "reactions")

    source_species: dict[tuple[str, str], dict[str, Any]] = {}
    for record in [*inorganic_ions, *inorganic_substances]:
        source_species[("inorganic", str(record["id"]))] = record
    for record in organic_substances:
        normalized = dict(record)
        normalized["kind"] = "substance"
        source_species[("organic", str(record["id"]))] = normalized

    crosswalk_map, crosswalk = build_crosswalk(source_species, findings)
    structure_links, preferred_by_source = load_structure_registry(crosswalk_map, findings)
    external_by_organic = organic_external_ids()

    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for key, record in source_species.items():
        grouped[crosswalk_map[key]].append((key[0], record))
    species = [
        merge_species(consolidated_id, members, preferred_by_source, external_by_organic, findings)
        for consolidated_id, members in sorted(grouped.items())
    ]
    find_duplicate_candidates(species, findings)
    teaching = build_teaching_projection(species)
    reactions = build_reactions(inorganic_reactions, organic_reactions, crosswalk_map, findings)
    knowledge = build_knowledge_records(inorganic_manifest)
    knowledge_links = build_knowledge_links(knowledge, species, structure_links, findings)
    thermochemistry = build_thermochemistry(species, findings)

    findings.sort(key=lambda item: (item["severity"], item["kind"], item["id"]))
    write_jsonl(GENERATED / "species.jsonl", species)
    write_jsonl(GENERATED / "crosswalk.jsonl", crosswalk)
    write_jsonl(GENERATED / "structure_links.jsonl", structure_links)
    write_jsonl(GENERATED / "teaching_projection.jsonl", teaching)
    write_jsonl(GENERATED / "reactions.jsonl", reactions)
    write_jsonl(GENERATED / "knowledge_records.jsonl", knowledge)
    write_jsonl(GENERATED / "knowledge_links.jsonl", knowledge_links)
    write_jsonl(GENERATED / "species_phase_facts.jsonl", thermochemistry["species_phase_facts"])
    write_jsonl(GENERATED / "species_thermochemistry.jsonl", thermochemistry["species_thermochemistry"])
    write_jsonl(GENERATED / "phase_transitions.jsonl", thermochemistry["phase_transitions"])
    write_jsonl(GENERATED / "bond_enthalpies.jsonl", thermochemistry["bond_enthalpies"])
    write_jsonl(GENERATED / "unresolved_findings.jsonl", findings)
    write_json(GENERATED / "source_snapshot.json", snapshot)
    copy_rules_and_curriculum(inorganic_manifest)

    counts = {
        "species": len(species),
        "source_crosswalks": len(crosswalk),
        "structure_links": len(structure_links),
        "teaching_projections": len(teaching),
        "reactions": len(reactions),
        "knowledge_records": len(knowledge),
        "knowledge_links": len(knowledge_links),
        "species_phase_facts": len(thermochemistry["species_phase_facts"]),
        "species_thermochemistry": len(thermochemistry["species_thermochemistry"]),
        "phase_transitions": len(thermochemistry["phase_transitions"]),
        "bond_enthalpies": len(thermochemistry["bond_enthalpies"]),
        "findings": len(findings),
    }
    manifest = build_manifest(counts, findings)
    write_json(GENERATED / "manifest.json", manifest)
    print(json.dumps({"counts": counts, "blocking_findings": manifest["blocking_findings"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
