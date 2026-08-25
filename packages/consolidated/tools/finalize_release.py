from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

from build_release import (
    CONSOLIDATED,
    GENERATED,
    INORGANIC,
    ORGANIC,
    ORGANIC_KNOWLEDGE_DATASETS,
    ORGANIC_REACTION_FILES,
    ORGANIC_SUBSTANCE_FILES,
    SOURCE_INPUTS_FILE,
    STRUCTURAL_CHEMISTRY,
    STRUCTURE_REGISTRY,
    build_manifest,
    finding_id,
    load_json,
    load_jsonl,
    load_yaml,
    stable_knowledge_id,
    write_json,
    write_jsonl,
)

ALIAS_FILE = CONSOLIDATED / "data" / "source_reference_aliases.yaml"

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


def git_show_bytes(commit: str, repo_path: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "show", f"{commit}:{repo_path}"],
            cwd=CONSOLIDATED.parents[1],
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


def inorganic_paths() -> list[str]:
    manifest = load_json(INORGANIC / "manifest.json")
    paths = ["packages/inorganic/manifest.json"]
    for relatives in manifest.get("canonical_files", {}).values():
        paths.extend(f"packages/inorganic/{relative}" for relative in relatives)
    paths.extend(f"packages/inorganic/{relative}" for relative in manifest.get("rule_files", []))
    paths.append(f"packages/inorganic/{manifest['curriculum_file']}")
    return sorted(set(paths))


def organic_paths() -> list[str]:
    data_files = set(ORGANIC_SUBSTANCE_FILES + ORGANIC_REACTION_FILES)
    data_files.update(filename for _, filename, _ in ORGANIC_KNOWLEDGE_DATASETS)
    data_files.update({"identity_crossrefs.yaml", "curriculum_coverage.yaml"})
    return [
        "packages/organic/package.yaml",
        *(f"packages/organic/data/{name}" for name in sorted(data_files)),
    ]


def structure_registry_paths() -> list[str]:
    manifest = load_json(STRUCTURE_REGISTRY / "data" / "manifest.json")
    paths = ["packages/structure_registry/data/manifest.json"]
    paths.extend(
        f"packages/structure_registry/data/{relative}"
        for relative in manifest.get("files", {})
        if relative.startswith("canonical/") and relative.endswith(".jsonl")
    )
    paths.extend(
        [
            "packages/structure_registry/data/links/inorganic.jsonl",
            "packages/structure_registry/data/links/organic.jsonl",
            "packages/structure_registry/data/deferrals/organic.jsonl",
            "packages/structure_registry/sources/cross_track_targets.json",
        ]
    )
    return sorted(set(paths))


def structural_chemistry_paths() -> list[str]:
    paths = ["packages/structural_chemistry/manifest.json"]
    paths.extend(
        f"packages/structural_chemistry/data/{path.name}"
        for path in sorted((STRUCTURAL_CHEMISTRY / "data").glob("*.jsonl"))
    )
    paths.extend(
        [
            "packages/structural_chemistry/curriculum/coverage.json",
            "packages/structural_chemistry/curriculum/scope.json",
        ]
    )
    return sorted(set(paths))


def consumed_paths(package: str) -> list[str]:
    if package == "inorganic":
        return inorganic_paths()
    if package == "organic":
        return organic_paths()
    if package == "structure_registry":
        return structure_registry_paths()
    if package == "structural_chemistry":
        return structural_chemistry_paths()
    raise ValueError(f"unknown source package: {package}")


def verify_and_enrich_source_snapshot() -> None:
    pins = load_json(SOURCE_INPUTS_FILE)["inputs"]
    snapshot = load_json(GENERATED / "source_snapshot.json")

    for package, pin in pins.items():
        entry = snapshot["inputs"][package]
        expected_state = str(pin["state"]).casefold()
        observed_state = str(entry.get("state", "")).casefold()
        if expected_state != observed_state:
            raise RuntimeError(
                f"source state drift for {package}: expected {pin['state']!r}, got {entry.get('state')!r}"
            )

        commit = str(pin["release_commit"])
        paths = consumed_paths(package)
        current_items: list[tuple[str, bytes]] = []
        pinned_items: list[tuple[str, bytes]] = []
        for repo_path in paths:
            current_path = CONSOLIDATED.parents[1] / repo_path
            if not current_path.is_file():
                raise RuntimeError(f"current consumed input missing: {repo_path}")
            current_items.append((repo_path, current_path.read_bytes()))
            pinned_items.append((repo_path, git_show_bytes(commit, repo_path)))

        current_digest = aggregate_digest(current_items)
        pinned_digest = aggregate_digest(pinned_items)
        if current_digest != pinned_digest:
            raise RuntimeError(
                f"consumed input drift for {package}: current={current_digest}, pinned={pinned_digest}"
            )

        entry["release_commit"] = commit
        entry["input_sha256"] = current_digest
        entry["consumed_files"] = paths

    write_json(GENERATED / "source_snapshot.json", snapshot)


def published_structure_ids() -> set[str]:
    manifest = load_json(STRUCTURE_REGISTRY / "data" / "manifest.json")
    output: set[str] = set()
    for relative in manifest.get("files", {}):
        if not relative.startswith("canonical/") or not relative.endswith(".jsonl"):
            continue
        for record in load_jsonl(STRUCTURE_REGISTRY / "data" / relative):
            validation = record.get("validation", {})
            if (
                validation.get("status") == "valid"
                and validation.get("review_status") == "published"
            ):
                output.add(str(record["structure_id"]))
    return output


def load_aliases() -> list[dict[str, Any]]:
    root = load_yaml(ALIAS_FILE)
    aliases = root.get("aliases", [])
    if not isinstance(aliases, list):
        raise RuntimeError("source_reference_aliases.yaml: aliases must be a list")
    return [item for item in aliases if isinstance(item, dict)]


def rebind_historical_structure_links() -> None:
    aliases = load_aliases()
    if not aliases:
        return

    species = load_jsonl(GENERATED / "species.jsonl")
    crosswalk = load_jsonl(GENERATED / "crosswalk.jsonl")
    links = load_jsonl(GENERATED / "structure_links.jsonl")
    findings = load_jsonl(GENERATED / "unresolved_findings.jsonl")

    species_by_id = {str(item["id"]): item for item in species}
    crosswalk_by_source = {
        (str(item["source_package"]), str(item["source_id"])): str(item["consolidated_id"])
        for item in crosswalk
        if item.get("mapping_status") == "resolved"
    }
    accepted_links: dict[tuple[str, str], dict[str, Any]] = {}
    for package in ("inorganic", "organic"):
        for item in load_jsonl(STRUCTURE_REGISTRY / "data" / "links" / f"{package}.jsonl"):
            if item.get("status") == "accepted":
                accepted_links[(package, str(item["entity_ref"]))] = item

    cross_targets = load_json(STRUCTURE_REGISTRY / "sources" / "cross_track_targets.json")
    legacy_targets = {
        str(item["entity_ref"]): item
        for item in cross_targets.get("inorganic", {}).get("accepted", [])
        if isinstance(item, dict) and item.get("entity_ref")
    }
    published = published_structure_ids()
    existing_link_ids = {str(item["source_link_id"]) for item in links}

    rebound_legacy_ids: set[str] = set()

    for alias in aliases:
        package = str(alias.get("source_package"))
        legacy_id = str(alias.get("legacy_id"))
        current_id = str(alias.get("current_id"))
        if package != "inorganic":
            raise RuntimeError(f"unsupported historical alias package: {package}")

        target_species_id = crosswalk_by_source.get((package, current_id))
        if target_species_id is None:
            raise RuntimeError(f"historical alias target missing from crosswalk: {package}:{current_id}")
        target_species = species_by_id[target_species_id]

        expected_formula = str(alias.get("expected_formula"))
        expected_charge = int(alias.get("expected_charge"))
        if target_species.get("formula") != expected_formula or target_species.get("charge") != expected_charge:
            raise RuntimeError(
                f"historical alias chemistry mismatch for {legacy_id} -> {current_id}: "
                f"expected {expected_formula}/{expected_charge}, got "
                f"{target_species.get('formula')}/{target_species.get('charge')}"
            )

        registry_target = legacy_targets.get(legacy_id)
        if registry_target is None:
            raise RuntimeError(f"historical alias lacks Structure Registry target evidence: {legacy_id}")
        expected_cid = int(alias.get("pubchem_cid"))
        if int(registry_target.get("pubchem_cid")) != expected_cid:
            raise RuntimeError(
                f"historical alias PubChem evidence mismatch for {legacy_id}: "
                f"expected {expected_cid}, got {registry_target.get('pubchem_cid')}"
            )

        registry_link = accepted_links.get((package, legacy_id))
        if registry_link is None:
            raise RuntimeError(f"historical alias lacks accepted Structure Registry link: {legacy_id}")
        structure_id = str(registry_link["structure_id"])
        if structure_id not in published:
            raise RuntimeError(f"historical alias points to unpublished Structure: {structure_id}")

        source_link_id = str(registry_link["link_id"])
        if source_link_id not in existing_link_ids:
            evidence_refs = {
                f"structure_registry:{value}"
                for value in registry_link.get("evidence", [])
            }
            evidence_refs.add("consolidated:data/source_reference_aliases.yaml")
            links.append(
                {
                    "species_id": target_species_id,
                    "source_package": package,
                    "source_id": current_id,
                    "structure_id": structure_id,
                    "relation": str(registry_link["relation"]),
                    "source_link_id": source_link_id,
                    "evidence_refs": sorted(evidence_refs),
                }
            )
            existing_link_ids.add(source_link_id)

        preferred = target_species.get("preferred_structure_id")
        if preferred not in (None, structure_id):
            raise RuntimeError(
                f"historical alias conflicts with preferred Structure for {current_id}: "
                f"{preferred} vs {structure_id}"
            )
        target_species["preferred_structure_id"] = structure_id
        rebound_legacy_ids.add(legacy_id)

        refs = [f"{package}:{legacy_id}", f"structure_registry:{source_link_id}"]
        findings.append(
            {
                "id": finding_id("historical_structure_link_rebound", refs),
                "severity": "info",
                "kind": "historical_structure_link_rebound",
                "message": (
                    "Accepted Structure Registry link used a historical source ID; "
                    "consolidation rebound it to the reviewed current inorganic ID."
                ),
                "source_refs": refs,
                "details": {
                    "legacy_id": legacy_id,
                    "current_id": current_id,
                    "formula": expected_formula,
                    "charge": expected_charge,
                    "pubchem_cid": expected_cid,
                    "structure_id": structure_id,
                },
            }
        )

    findings = [
        item
        for item in findings
        if not (
            item.get("kind") == "historical_structure_link_outside_snapshot"
            and any(
                ref == f"inorganic:{legacy_id}"
                for legacy_id in rebound_legacy_ids
                for ref in item.get("source_refs", [])
            )
        )
    ]

    links.sort(key=lambda item: (item["species_id"], item["relation"], item["structure_id"]))
    species.sort(key=lambda item: item["id"])
    findings.sort(key=lambda item: (item["severity"], item["kind"], item["id"]))
    write_jsonl(GENERATED / "species.jsonl", species)
    write_jsonl(GENERATED / "structure_links.jsonl", links)
    write_jsonl(GENERATED / "unresolved_findings.jsonl", findings)


def normalize_structural_knowledge_types() -> None:
    records = load_jsonl(GENERATED / "knowledge_records.jsonl")
    for item in records:
        if item.get("source_package") != "structural_chemistry":
            continue
        old_type = str(item["source_type"])
        new_type = STRUCTURAL_TYPE_MAP.get(old_type)
        if new_type is None:
            raise RuntimeError(f"unknown structural chemistry source_type: {old_type}")
        item["source_type"] = new_type
        item["id"] = stable_knowledge_id(
            "structural_chemistry", new_type, str(item["source_id"])
        )
    records.sort(key=lambda item: item["id"])
    write_jsonl(GENERATED / "knowledge_records.jsonl", records)


def rewrite_manifest_as_release() -> None:
    artifact_files = [
        "species.jsonl",
        "crosswalk.jsonl",
        "structure_links.jsonl",
        "teaching_projection.jsonl",
        "reactions.jsonl",
        "knowledge_records.jsonl",
        "unresolved_findings.jsonl",
    ]
    counts = {
        "species": len(load_jsonl(GENERATED / "species.jsonl")),
        "source_crosswalks": len(load_jsonl(GENERATED / "crosswalk.jsonl")),
        "structure_links": len(load_jsonl(GENERATED / "structure_links.jsonl")),
        "teaching_projections": len(load_jsonl(GENERATED / "teaching_projection.jsonl")),
        "reactions": len(load_jsonl(GENERATED / "reactions.jsonl")),
        "knowledge_records": len(load_jsonl(GENERATED / "knowledge_records.jsonl")),
        "findings": len(load_jsonl(GENERATED / "unresolved_findings.jsonl")),
    }
    findings = load_jsonl(GENERATED / "unresolved_findings.jsonl")
    manifest = build_manifest(counts, findings)
    manifest["release"] = "consolidated-1.0.0"
    manifest["state"] = "READY_FOR_APP_IMPORT"
    manifest["audit_gate"] = "independent-pre-release-v1"
    manifest["artifact_contract"] = artifact_files
    write_json(GENERATED / "manifest.json", manifest)


def main() -> int:
    verify_and_enrich_source_snapshot()
    rebind_historical_structure_links()
    normalize_structural_knowledge_types()
    rewrite_manifest_as_release()
    manifest = load_json(GENERATED / "manifest.json")
    print(
        json.dumps(
            {
                "release": manifest["release"],
                "state": manifest["state"],
                "counts": manifest["counts"],
                "blocking_findings": manifest["blocking_findings"],
                "review_findings": manifest["review_findings"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
