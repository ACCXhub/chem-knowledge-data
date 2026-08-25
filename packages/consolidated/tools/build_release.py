from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
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
PRIMARY_STRUCTURE_RELATIONS = {"primary_structure", "ion_structure", "formula_unit"}


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
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: expected object")
            records.append(value)
    return records


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


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def source_ref(package: str, raw: str) -> str:
    return f"{package}:{raw}"


def stable_species_id(package: str, source_id: str) -> str:
    return f"species:{package}:{source_id}"


def stable_reaction_id(package: str, source_id: str) -> str:
    return f"reaction:{package}:{source_id}"


def stable_knowledge_id(package: str, source_type: str, source_id: str) -> str:
    return f"knowledge:{package}:{source_type}:{source_id}"


def finding_id(kind: str, refs: list[str], ordinal: int = 0) -> str:
    key = "|".join([kind, *sorted(refs), str(ordinal)])
    return "finding:" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def normalize_text(value: str) -> str:
    return re.sub(r"[\s\-_(),，（）]+", "", value).casefold()


def parse_formula(formula: str) -> dict[str, int] | None:
    # Organic package permits symbolic polymer repeat formulas such as (C2H4)n.
    if re.fullmatch(r"\(.+\)n", formula):
        return None
    stack: list[dict[str, int]] = [defaultdict(int)]
    i = 0
    while i < len(formula):
        char = formula[i]
        if char == "(":
            stack.append(defaultdict(int))
            i += 1
            continue
        if char == ")":
            if len(stack) == 1:
                return None
            group = stack.pop()
            i += 1
            start = i
            while i < len(formula) and formula[i].isdigit():
                i += 1
            mul = int(formula[start:i] or "1")
            for element, count in group.items():
                stack[-1][element] += count * mul
            continue
        if not char.isupper() or not char.isascii():
            return None
        element = char
        i += 1
        if i < len(formula) and formula[i].islower() and formula[i].isascii():
            element += formula[i]
            i += 1
        start = i
        while i < len(formula) and formula[i].isdigit():
            i += 1
        count = int(formula[start:i] or "1")
        stack[-1][element] += count
    if len(stack) != 1 or not stack[0]:
        return None
    return dict(stack[0])


def provenance_from(record: dict[str, Any], package: str) -> list[str]:
    values: list[str] = []
    for key in ("sources", "provenance_refs", "source_refs"):
        raw = record.get(key)
        if isinstance(raw, list):
            values.extend(str(item) for item in raw if isinstance(item, (str, int)))
    raw_provenance = record.get("provenance")
    if isinstance(raw_provenance, list):
        for item in raw_provenance:
            if isinstance(item, dict):
                source_id = item.get("source_id")
                locator = item.get("record_locator")
                if source_id:
                    values.append(str(source_id))
                if locator:
                    values.append(f"locator:{locator}")
    normalized = sorted({source_ref(package, value) for value in values if value})
    return normalized or [f"{package}:package-release"]


def display_name(record: dict[str, Any]) -> str:
    for key in ("name_zh", "title_zh", "term_zh", "label_zh", "name", "title", "id"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "未命名记录"


def load_inorganic_manifest_records(manifest: dict[str, Any], key: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative in manifest["canonical_files"].get(key, []):
        records.extend(load_jsonl(INORGANIC / relative))
    return records


def load_organic_records(files: list[str], root_key: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for filename in files:
        root = load_yaml(ORGANIC / "data" / filename)
        value = root.get(root_key, [])
        if not isinstance(value, list):
            raise ValueError(f"{filename}: {root_key} must be a list")
        records.extend(item for item in value if isinstance(item, dict))
    return records


def actual_source_snapshot(findings: list[dict[str, Any]]) -> dict[str, Any]:
    pins = load_json(SOURCE_INPUTS_FILE)
    inorganic_manifest = load_json(INORGANIC / "manifest.json")
    organic_package = load_yaml(ORGANIC / "package.yaml")
    registry_manifest = load_json(STRUCTURE_REGISTRY / "data" / "manifest.json")
    structural_manifest = load_json(STRUCTURAL_CHEMISTRY / "manifest.json")

    actual = {
        "repository_commit": git_head(),
        "inputs": {
            "inorganic": {
                "release": inorganic_manifest.get("version"),
                "state": inorganic_manifest.get("status"),
                "total_records": inorganic_manifest.get("total_records"),
            },
            "organic": {
                "release": str(organic_package.get("version")),
                "state": organic_package.get("status"),
                "substances": organic_package.get("validation", {}).get("counts", {}).get("substances"),
                "reactions": organic_package.get("validation", {}).get("counts", {}).get("reactions"),
            },
            "structure_registry": {
                "release": registry_manifest.get("dataset_version"),
                "state": "PUBLISHED",
                "structures": registry_manifest.get("counts", {}).get("total"),
                "inorganic_links": registry_manifest.get("cross_track", {}).get("inorganic_accepted_links"),
                "organic_links": registry_manifest.get("cross_track", {}).get("organic_accepted_links"),
                "organic_deferrals": registry_manifest.get("cross_track", {}).get("organic_deferrals"),
            },
            "structural_chemistry": {
                "release": structural_manifest.get("release"),
                "state": structural_manifest.get("state"),
                "total_records": structural_manifest.get("total_records"),
            },
        },
    }

    expected = pins["inputs"]
    checks = [
        ("inorganic", "release", expected["inorganic"]["release"], actual["inputs"]["inorganic"]["release"]),
        ("inorganic", "total_records", expected["inorganic"]["expected_total_records"], actual["inputs"]["inorganic"]["total_records"]),
        ("organic", "release", expected["organic"]["release"], actual["inputs"]["organic"]["release"]),
        ("organic", "substances", expected["organic"]["expected_substances"], actual["inputs"]["organic"]["substances"]),
        ("organic", "reactions", expected["organic"]["expected_reactions"], actual["inputs"]["organic"]["reactions"]),
        ("structure_registry", "release", expected["structure_registry"]["release"], actual["inputs"]["structure_registry"]["release"]),
        ("structure_registry", "structures", expected["structure_registry"]["expected_structures"], actual["inputs"]["structure_registry"]["structures"]),
        ("structure_registry", "inorganic_links", expected["structure_registry"]["expected_inorganic_links"], actual["inputs"]["structure_registry"]["inorganic_links"]),
        ("structure_registry", "organic_links", expected["structure_registry"]["expected_organic_links"], actual["inputs"]["structure_registry"]["organic_links"]),
        ("structure_registry", "organic_deferrals", expected["structure_registry"]["expected_organic_deferrals"], actual["inputs"]["structure_registry"]["organic_deferrals"]),
        ("structural_chemistry", "release", expected["structural_chemistry"]["release"], actual["inputs"]["structural_chemistry"]["release"]),
        ("structural_chemistry", "total_records", expected["structural_chemistry"]["expected_total_records"], actual["inputs"]["structural_chemistry"]["total_records"]),
    ]
    for package, field, wanted, got in checks:
        if wanted != got:
            refs = [f"{package}:{field}"]
            findings.append({
                "id": finding_id("source_snapshot_mismatch", refs),
                "severity": "blocking",
                "kind": "source_snapshot_mismatch",
                "message": f"Pinned {package}.{field}={wanted!r}, current source has {got!r}",
                "source_refs": refs,
                "details": {"expected": wanted, "actual": got},
            })
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
            continue
        survivor_key = (str(survivor.get("package")), str(survivor.get("id")))
        if survivor_key not in source_species:
            refs = [f"{survivor_key[0]}:{survivor_key[1]}"]
            findings.append({
                "id": finding_id("invalid_identity_override", refs, index),
                "severity": "blocking",
                "kind": "invalid_identity_override",
                "message": "Identity override survivor does not exist in current source snapshot",
                "source_refs": refs,
                "details": merge,
            })
            continue
        target = stable_species_id(*survivor_key)
        for member in members:
            if not isinstance(member, dict):
                continue
            key = (str(member.get("package")), str(member.get("id")))
            if key not in source_species:
                refs = [f"{key[0]}:{key[1]}"]
                findings.append({
                    "id": finding_id("invalid_identity_override", refs, index + 1000),
                    "severity": "blocking",
                    "kind": "invalid_identity_override",
                    "message": "Identity override member does not exist in current source snapshot",
                    "source_refs": refs,
                    "details": merge,
                })
                continue
            mapping[key] = target
            methods[key] = "reviewed_manual"
            evidence[key] = [str(item) for item in merge.get("evidence_refs", [])] or ["packages/consolidated/data/identity_overrides.yaml"]

    crosswalk = []
    for key in sorted(source_species):
        package, source_id = key
        record = source_species[key]
        crosswalk.append({
            "source_package": package,
            "source_entity_type": "ion" if record.get("kind") == "ion" else "substance",
            "source_id": source_id,
            "consolidated_id": mapping[key],
            "mapping_status": "resolved",
            "resolution_method": methods[key],
            "evidence_refs": evidence[key],
            "notes": None,
        })
    return mapping, crosswalk


def load_structure_registry(
    crosswalk: dict[tuple[str, str], str], findings: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], str]]:
    manifest = load_json(STRUCTURE_REGISTRY / "data" / "manifest.json")
    structure_ids: set[str] = set()
    for relative, meta in manifest.get("files", {}).items():
        if not relative.startswith("canonical/") or not relative.endswith(".jsonl"):
            continue
        for record in load_jsonl(STRUCTURE_REGISTRY / "data" / relative):
            if record.get("validation", {}).get("status") == "valid" and record.get("validation", {}).get("review_status") == "published":
                structure_ids.add(str(record["structure_id"]))

    normalized: list[dict[str, Any]] = []
    preferred_by_source: dict[tuple[str, str], str] = {}
    for package in ("inorganic", "organic"):
        for link in load_jsonl(STRUCTURE_REGISTRY / "data" / "links" / f"{package}.jsonl"):
            if link.get("status") != "accepted":
                continue
            source_id = str(link.get("entity_ref"))
            key = (package, source_id)
            refs = [f"{package}:{source_id}", f"structure_registry:{link.get('link_id')}"]
            if key not in crosswalk:
                findings.append({
                    "id": finding_id("stale_structure_link_source", refs),
                    "severity": "blocking",
                    "kind": "stale_structure_link_source",
                    "message": "Accepted Structure Registry link points to a source species absent from the pinned release",
                    "source_refs": refs,
                    "details": link,
                })
                continue
            structure_id = str(link.get("structure_id"))
            if structure_id not in structure_ids:
                findings.append({
                    "id": finding_id("missing_structure_target", refs),
                    "severity": "blocking",
                    "kind": "missing_structure_target",
                    "message": "Accepted Structure Registry link points to a non-published Structure",
                    "source_refs": refs,
                    "details": {"structure_id": structure_id},
                })
                continue
            normalized.append({
                "species_id": crosswalk[key],
                "source_package": package,
                "source_id": source_id,
                "structure_id": structure_id,
                "relation": str(link.get("relation")),
                "source_link_id": str(link.get("link_id")),
                "evidence_refs": sorted({source_ref("structure_registry", str(item)) for item in link.get("evidence", [])}),
            })
            if link.get("relation") in PRIMARY_STRUCTURE_RELATIONS:
                existing = preferred_by_source.get(key)
                if existing and existing != structure_id:
                    findings.append({
                        "id": finding_id("multiple_preferred_structures", refs),
                        "severity": "review",
                        "kind": "multiple_preferred_structures",
                        "message": "One source species has multiple candidate preferred Structure targets",
                        "source_refs": refs,
                        "details": {"existing": existing, "candidate": structure_id},
                    })
                else:
                    preferred_by_source[key] = structure_id

    deferrals_path = STRUCTURE_REGISTRY / "data" / "deferrals" / "organic.jsonl"
    if deferrals_path.exists():
        for item in load_jsonl(deferrals_path):
            source_id = str(item.get("entity_ref"))
            refs = [f"organic:{source_id}", f"structure_registry:{item.get('deferral_id')}"]
            findings.append({
                "id": finding_id("structure_identity_deferred", refs),
                "severity": "info",
                "kind": "structure_identity_deferred",
                "message": "Structure Registry explicitly defers full structure identity for this organic species",
                "source_refs": refs,
                "details": {"reason": item.get("reason"), "notes": item.get("notes")},
            })

    normalized.sort(key=lambda item: (item["species_id"], item["relation"], item["structure_id"]))
    return normalized, preferred_by_source


def organic_external_ids() -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = defaultdict(list)
    path = ORGANIC / "data" / "identity_crossrefs.yaml"
    if not path.exists():
        return result
    for item in load_yaml(path).get("crossrefs", []):
        if not isinstance(item, dict) or not item.get("substance_ref"):
            continue
        source_id = str(item["substance_ref"])
        if item.get("pubchem_cid"):
            result[source_id].append({"namespace": "pubchem_cid", "value": str(item["pubchem_cid"])})
        if item.get("chebi_id"):
            result[source_id].append({"namespace": "chebi", "value": str(item["chebi_id"])})
    return result


def merge_species_group(
    consolidated_id: str,
    members: list[tuple[str, dict[str, Any]]],
    preferred_by_source: dict[tuple[str, str], str],
    external_by_organic: dict[str, list[dict[str, str]]],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    members = sorted(members, key=lambda item: (0 if item[0] == "inorganic" else 1, str(item[1]["id"])))
    primary_package, primary = members[0]
    source_ids = [{"package": package, "id": str(record["id"])} for package, record in members]
    formulas = {str(record.get("formula")) for _, record in members if record.get("formula")}
    charges = {int(record.get("charge", 0)) for _, record in members}
    if len(formulas) > 1 or len(charges) > 1:
        refs = [f"{package}:{record['id']}" for package, record in members]
        findings.append({
            "id": finding_id("merged_identity_conflict", refs),
            "severity": "blocking",
            "kind": "merged_identity_conflict",
            "message": "Reviewed identity merge has conflicting formula or charge",
            "source_refs": refs,
            "details": {"formulas": sorted(formulas), "charges": sorted(charges)},
        })

    aliases: set[str] = set()
    classifications: set[str] = set()
    provenance: set[str] = set()
    external_ids: dict[tuple[str, str], dict[str, str]] = {}
    review_states: list[dict[str, str]] = []
    structure_candidates: set[str] = set()
    priorities: list[str] = []

    for package, record in members:
        aliases.update(str(item) for item in record.get("aliases", []) if item)
        if package == "inorganic":
            if record.get("category"):
                classifications.add(str(record["category"]))
            if record.get("aqueous_behavior"):
                classifications.add(str(record["aqueous_behavior"]))
            review_states.append({"package": package, "state": str(record.get("review_status", "unknown"))})
        else:
            if record.get("category"):
                classifications.add(str(record["category"]))
            for fg in record.get("functional_group_refs", []):
                classifications.add(f"functional_group:{fg}")
            review_states.append({"package": package, "state": str(record.get("verification_status", "unknown"))})
            for external in external_by_organic.get(str(record["id"]), []):
                external_ids[(external["namespace"], external["value"])] = external
        provenance.update(provenance_from(record, package))
        priorities.append(str(record.get("teaching_priority", "extended")))
        structure_id = preferred_by_source.get((package, str(record["id"])))
        if structure_id:
            structure_candidates.add(structure_id)

    preferred_structure_id: str | None = None
    if len(structure_candidates) == 1:
        preferred_structure_id = next(iter(structure_candidates))
    elif len(structure_candidates) > 1:
        refs = [f"{package}:{record['id']}" for package, record in members]
        findings.append({
            "id": finding_id("merged_structure_conflict", refs),
            "severity": "review",
            "kind": "merged_structure_conflict",
            "message": "Merged source identities point to different preferred Structure records",
            "source_refs": refs,
            "details": {"structure_ids": sorted(structure_candidates)},
        })

    priority = min(priorities, key=lambda item: PRIORITY_ORDER.get(item, 99))
    composition = primary.get("composition")
    if composition is None and primary_package == "organic":
        composition = parse_formula(str(primary.get("formula", "")))

    return {
        "id": consolidated_id,
        "entity_kind": "ion" if primary.get("kind") == "ion" else "substance",
        "source_ids": source_ids,
        "name_zh": str(primary.get("name_zh") or display_name(primary)),
        "name_en": primary.get("name_en"),
        "formula": str(primary.get("formula")),
        "charge": int(primary.get("charge", 0)),
        "composition": composition,
        "aliases": sorted(aliases),
        "chemical_classifications": sorted(classifications),
        "teaching_priority": priority,
        "source_review_states": review_states,
        "preferred_structure_id": preferred_structure_id,
        "external_ids": sorted(external_ids.values(), key=lambda item: (item["namespace"], item["value"])),
        "integration_status": "resolved",
        "provenance_refs": sorted(provenance),
    }


def duplicate_candidates(species: list[dict[str, Any]], findings: list[dict[str, Any]]) -> None:
    inorganic = [item for item in species if any(src["package"] == "inorganic" for src in item["source_ids"]) and item["entity_kind"] == "substance"]
    organic = [item for item in species if any(src["package"] == "organic" for src in item["source_ids"]) and item["entity_kind"] == "substance"]
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
            shared_structure = left.get("preferred_structure_id") and left.get("preferred_structure_id") == right.get("preferred_structure_id")
            if left_names.intersection(right_names) or shared_structure:
                refs = [left["id"], right["id"]]
                findings.append({
                    "id": finding_id("cross_package_duplicate_candidate", refs),
                    "severity": "review",
                    "kind": "cross_package_duplicate_candidate",
                    "message": "Two source species may represent the same chemical identity; they remain separate until reviewed",
                    "source_refs": refs,
                    "details": {"formula": left["formula"], "shared_name": bool(left_names.intersection(right_names)), "shared_structure": bool(shared_structure)},
                })


def primary_category(species: dict[str, Any]) -> str:
    if species["entity_kind"] == "ion":
        if species["charge"] > 0:
            return "cation"
        if species["charge"] < 0:
            return "anion"
        return "other"
    source_packages = {item["package"] for item in species["source_ids"]}
    if "organic" in source_packages and "inorganic" not in source_packages:
        return "organic"
    classes = set(species["chemical_classifications"])
    mapping = {
        "simple_substance": "elemental_substance",
        "acid": "acid",
        "base": "base",
        "salt": "salt",
        "oxide": "oxide",
    }
    for source_class, category in mapping.items():
        if source_class in classes:
            return category
    if "organic" in source_packages:
        return "organic"
    return "other"


def teaching_projection(species: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        species,
        key=lambda item: (
            PRIORITY_ORDER.get(item["teaching_priority"], 99),
            CATEGORY_ORDER.get(primary_category(item), 99),
            item["name_zh"],
            item["id"],
        ),
    )
    result: list[dict[str, Any]] = []
    for rank, item in enumerate(ordered):
        category = primary_category(item)
        tags = set(item["chemical_classifications"])
        for source in item["source_ids"]:
            tags.add(f"source:{source['package']}")
        tokens = {item["name_zh"], item["formula"]}
        if item.get("name_en"):
            tokens.add(str(item["name_en"]))
        tokens.update(item["aliases"])
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

        result.append({
            "species_id": item["id"],
            "primary_category": category,
            "tags": sorted(tags),
            "search_tokens": sorted(token for token in tokens if isinstance(token, str) and token.strip()),
            "default_priority": item["teaching_priority"],
            "default_palette_rank": rank,
            "equation_modes": modes,
        })
    return result


def resolve_organic_external_key(raw: str, crosswalk: dict[tuple[str, str], str]) -> tuple[str | None, str]:
    if not raw.startswith("inorganic:"):
        return None, raw
    slug = raw.split(":", 1)[1]
    for source_id in (f"substance:{slug}", f"ion:{slug}"):
        key = ("inorganic", source_id)
        if key in crosswalk:
            return crosswalk[key], source_id
    return None, raw


def normalize_reactions(
    inorganic_records: list[dict[str, Any]],
    organic_records: list[dict[str, Any]],
    crosswalk: dict[tuple[str, str], str],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    def participant(package: str, source_reaction_id: str, raw: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        actual_role = role or str(raw.get("role"))
        consolidated: str | None = None
        source_species_ref = ""
        if package == "inorganic":
            source_id = str(raw.get("species_id"))
            source_species_ref = f"inorganic:{source_id}"
            consolidated = crosswalk.get(("inorganic", source_id))
        elif raw.get("substance_ref"):
            source_id = str(raw["substance_ref"])
            source_species_ref = f"organic:{source_id}"
            consolidated = crosswalk.get(("organic", source_id))
        elif raw.get("external_species_key"):
            external = str(raw["external_species_key"])
            consolidated, resolved_source = resolve_organic_external_key(external, crosswalk)
            source_species_ref = f"inorganic:{resolved_source}" if consolidated else external
        else:
            source_species_ref = str(raw.get("formula_literal") or "unresolved")

        if consolidated is None and actual_role in {"reactant", "product"}:
            refs = [f"{package}:{source_reaction_id}", source_species_ref]
            findings.append({
                "id": finding_id("unresolved_reaction_participant", refs),
                "severity": "blocking",
                "kind": "unresolved_reaction_participant",
                "message": "Required Reaction participant cannot be resolved to a consolidated species",
                "source_refs": refs,
                "details": raw,
            })
        return {
            "role": actual_role,
            "coefficient": raw.get("coefficient", 1),
            "species_id": consolidated,
            "source_species_ref": source_species_ref,
            "formula_literal": raw.get("formula_literal"),
            "phase": raw.get("phase"),
        }

    for record in inorganic_records:
        source_id = str(record["id"])
        parts = [participant("inorganic", source_id, item, "reactant") for item in record.get("reactants", [])]
        parts.extend(participant("inorganic", source_id, item, "product") for item in record.get("products", []))
        net_ionic = None
        if isinstance(record.get("net_ionic"), dict):
            net_parts = [participant("inorganic", source_id, item, "reactant") for item in record["net_ionic"].get("reactants", [])]
            net_parts.extend(participant("inorganic", source_id, item, "product") for item in record["net_ionic"].get("products", []))
            net_ionic = {"participants": net_parts}
        resolved = all(item["species_id"] is not None for item in parts)
        if net_ionic:
            resolved = resolved and all(item["species_id"] is not None for item in net_ionic["participants"])
        output.append({
            "id": stable_reaction_id("inorganic", source_id),
            "source_package": "inorganic",
            "source_id": source_id,
            "name_zh": str(record.get("name_zh") or source_id),
            "participants": parts,
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
        })

    for record in organic_records:
        source_id = str(record["id"])
        parts = [participant("organic", source_id, item) for item in record.get("participants", [])]
        resolved = all(item["species_id"] is not None for item in parts if item["role"] in {"reactant", "product"})
        output.append({
            "id": stable_reaction_id("organic", source_id),
            "source_package": "organic",
            "source_id": source_id,
            "name_zh": str(record.get("name_zh") or source_id),
            "participants": parts,
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
        })

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
        for record in load_inorganic_manifest_records(inorganic_manifest, source_type):
            source_id = str(record["id"])
            output.append({
                "id": stable_knowledge_id("inorganic", singular, source_id),
                "source_package": "inorganic",
                "source_type": singular,
                "source_id": source_id,
                "display_name_zh": display_name(record),
                "teaching_priority": record.get("teaching_priority"),
                "provenance_refs": provenance_from(record, "inorganic"),
                "payload": record,
            })

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
            output.append({
                "id": stable_knowledge_id("organic", source_type, source_id),
                "source_package": "organic",
                "source_type": source_type,
                "source_id": source_id,
                "display_name_zh": display_name(record),
                "teaching_priority": record.get("teaching_priority"),
                "provenance_refs": provenance_from(record, "organic"),
                "payload": record,
            })

    for path in sorted((STRUCTURAL_CHEMISTRY / "data").glob("*.jsonl")):
        source_type = path.stem
        for record in load_jsonl(path):
            source_id = str(record.get("id") or record.get(f"{source_type.rstrip('s')}_id") or "")
            if not source_id:
                source_id = hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:24]
            output.append({
                "id": stable_knowledge_id("structural_chemistry", source_type, source_id),
                "source_package": "structural_chemistry",
                "source_type": source_type,
                "source_id": source_id,
                "display_name_zh": display_name(record),
                "teaching_priority": record.get("teaching_priority"),
                "provenance_refs": provenance_from(record, "structural_chemistry"),
                "payload": record,
            })

    output.sort(key=lambda item: item["id"])
    return output


def copy_rules_and_curriculum(inorganic_manifest: dict[str, Any]) -> None:
    rules_dir = GENERATED / "rules"
    curriculum_dir = GENERATED / "curriculum"
    rules_dir.mkdir(parents=True, exist_ok=True)
    curriculum_dir.mkdir(parents=True, exist_ok=True)

    for relative in inorganic_manifest.get("rule_files", []):
        source = INORGANIC / relative
        shutil.copyfile(source, rules_dir / source.name)

    shutil.copyfile(INORGANIC / inorganic_manifest["curriculum_file"], curriculum_dir / "inorganic.json")
    organic_curriculum = load_yaml(ORGANIC / "data" / "curriculum_coverage.yaml")
    write_json(curriculum_dir / "organic.json", organic_curriculum)
    shutil.copyfile(STRUCTURAL_CHEMISTRY / "curriculum" / "coverage.json", curriculum_dir / "structural_chemistry_coverage.json")
    shutil.copyfile(STRUCTURAL_CHEMISTRY / "curriculum" / "scope.json", curriculum_dir / "structural_chemistry_scope.json")


def build_manifest(counts: dict[str, int], findings: list[dict[str, Any]]) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    for path in sorted(GENERATED.rglob("*")):
        if not path.is_file() or path.name in {"manifest.json", "validation_report.json"}:
            continue
        relative = path.relative_to(GENERATED).as_posix()
        meta: dict[str, Any] = {"sha256": sha256_file(path)}
        if path.suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                meta["records"] = sum(1 for line in handle if line.strip())
        files[relative] = meta
    blocking = sum(1 for item in findings if item["severity"] == "blocking")
    return {
        "package": "consolidated",
        "release": "consolidated-draft-1",
        "state": "generated_candidate",
        "source_snapshot_file": "source_snapshot.json",
        "counts": counts,
        "blocking_findings": blocking,
        "review_findings": sum(1 for item in findings if item["severity"] == "review"),
        "info_findings": sum(1 for item in findings if item["severity"] == "info"),
        "files": files,
    }


def main() -> int:
    if GENERATED.exists():
        shutil.rmtree(GENERATED)
    GENERATED.mkdir(parents=True, exist_ok=True)

    findings: list[dict[str, Any]] = []
    snapshot = actual_source_snapshot(findings)
    inorganic_manifest = load_json(INORGANIC / "manifest.json")

    inorganic_ions = load_inorganic_manifest_records(inorganic_manifest, "ions")
    inorganic_substances = load_inorganic_manifest_records(inorganic_manifest, "substances")
    inorganic_reactions = load_inorganic_manifest_records(inorganic_manifest, "reactions")
    organic_substances = load_organic_records(ORGANIC_SUBSTANCE_FILES, "records")
    organic_reactions = load_organic_records(ORGANIC_REACTION_FILES, "reactions")

    source_species: dict[tuple[str, str], dict[str, Any]] = {}
    for record in [*inorganic_ions, *inorganic_substances]:
        source_species[("inorganic", str(record["id"]))] = record
    for record in organic_substances:
        normalized = dict(record)
        normalized["kind"] = "substance"
        source_species[("organic", str(record["id"]))] = normalized

    crosswalk_map, crosswalk_records = build_crosswalk(source_species, findings)
    structure_links, preferred_by_source = load_structure_registry(crosswalk_map, findings)
    external_by_organic = organic_external_ids()

    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for key, record in source_species.items():
        grouped[crosswalk_map[key]].append((key[0], record))

    species = [
        merge_species_group(consolidated_id, members, preferred_by_source, external_by_organic, findings)
        for consolidated_id, members in sorted(grouped.items())
    ]
    duplicate_candidates(species, findings)
    teaching = teaching_projection(species)
    reactions = normalize_reactions(inorganic_reactions, organic_reactions, crosswalk_map, findings)
    knowledge = build_knowledge_records(inorganic_manifest)

    findings.sort(key=lambda item: (item["severity"], item["kind"], item["id"]))
    write_jsonl(GENERATED / "species.jsonl", species)
    write_jsonl(GENERATED / "crosswalk.jsonl", crosswalk_records)
    write_jsonl(GENERATED / "structure_links.jsonl", structure_links)
    write_jsonl(GENERATED / "teaching_projection.jsonl", teaching)
    write_jsonl(GENERATED / "reactions.jsonl", reactions)
    write_jsonl(GENERATED / "knowledge_records.jsonl", knowledge)
    write_jsonl(GENERATED / "unresolved_findings.jsonl", findings)
    write_json(GENERATED / "source_snapshot.json", snapshot)
    copy_rules_and_curriculum(inorganic_manifest)

    counts = {
        "species": len(species),
        "source_crosswalks": len(crosswalk_records),
        "structure_links": len(structure_links),
        "teaching_projections": len(teaching),
        "reactions": len(reactions),
        "knowledge_records": len(knowledge),
        "findings": len(findings),
    }
    manifest = build_manifest(counts, findings)
    write_json(GENERATED / "manifest.json", manifest)

    print(json.dumps({"counts": counts, "blocking_findings": manifest["blocking_findings"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
