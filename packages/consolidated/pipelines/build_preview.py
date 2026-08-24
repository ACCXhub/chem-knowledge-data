from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
ORGANIC_DATA = REPO_ROOT / "packages" / "organic" / "data"
DATA_DIR = PACKAGE_ROOT / "data"

SUBSTANCE_FILES = (
    "core_substances.yaml",
    "extended_substances.yaml",
    "lipid_substances.yaml",
    "polymer_substances.yaml",
)

FORMULA_TOKEN = re.compile(r"([A-Z][a-z]?)([0-9]*)")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected mapping")
    return data


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected object")
            records.append(value)
    return records


def dump_jsonl(records: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
        for record in records
    )


def parse_formula(formula: str) -> tuple[str, dict[str, int] | None]:
    basis = "whole_species"
    source = formula
    repeat_match = re.fullmatch(r"\(([^()]+)\)n", formula)
    if repeat_match:
        basis = "repeat_unit"
        source = repeat_match.group(1)

    position = 0
    composition: dict[str, int] = {}
    for match in FORMULA_TOKEN.finditer(source):
        if match.start() != position:
            return "not_applicable", None
        element, count_text = match.groups()
        composition[element] = composition.get(element, 0) + (
            int(count_text) if count_text else 1
        )
        position = match.end()

    if position != len(source) or not composition:
        return "not_applicable", None
    return basis, composition


def normalized_external_ids(
    record: dict[str, Any], crossref: dict[str, Any] | None
) -> list[dict[str, str]]:
    result: dict[tuple[str, str], dict[str, str]] = {}

    source_external = record.get("external_ids")
    if isinstance(source_external, dict):
        for namespace, value in source_external.items():
            if value is None:
                continue
            canonical_namespace = "chebi" if namespace == "chebi" else namespace
            result[(canonical_namespace, str(value))] = {
                "namespace": canonical_namespace,
                "value": str(value),
            }

    if crossref:
        if crossref.get("pubchem_cid") is not None:
            value = str(crossref["pubchem_cid"])
            result[("pubchem_cid", value)] = {
                "namespace": "pubchem_cid",
                "value": value,
            }
        if crossref.get("chebi_id"):
            value = str(crossref["chebi_id"])
            result[("chebi", value)] = {"namespace": "chebi", "value": value}

    return sorted(result.values(), key=lambda item: (item["namespace"], item["value"]))


def source_provenance(refs: list[str]) -> list[dict[str, str]]:
    return [
        {"package": "organic", "ref": ref, "granularity": "record"}
        for ref in refs
    ]


def build_species() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    identities = {
        item["source_refs"][0]["local_id"]: item
        for item in load_jsonl(DATA_DIR / "identity-map.jsonl")
        if item.get("entity_kind") == "species"
        and item.get("source_refs")
        and item["source_refs"][0].get("package") == "organic"
    }
    links = {
        item["source_ref"]["local_id"]: item
        for item in load_jsonl(DATA_DIR / "organic-structure-links.jsonl")
    }
    crossrefs = {
        item["substance_ref"]: item
        for item in load_yaml(ORGANIC_DATA / "identity_crossrefs.yaml").get(
            "crossrefs", []
        )
    }

    source_records: list[dict[str, Any]] = []
    for filename in SUBSTANCE_FILES:
        records = load_yaml(ORGANIC_DATA / filename).get("records", [])
        if not isinstance(records, list):
            raise ValueError(f"{filename}: records must be a list")
        source_records.extend(records)

    if set(identities) != {record["id"] for record in source_records}:
        missing = sorted({record["id"] for record in source_records} - set(identities))
        extra = sorted(set(identities) - {record["id"] for record in source_records})
        raise ValueError(f"organic identity map mismatch: missing={missing}, extra={extra}")

    species: list[dict[str, Any]] = []
    projections: list[dict[str, Any]] = []
    priority_base = {"core": 0, "common": 1000, "extended": 2000}

    for ordinal, record in enumerate(source_records):
        local_id = record["id"]
        identity = identities[local_id]
        provenance_refs = [str(item) for item in record.get("provenance_refs", [])]
        provenance = source_provenance(provenance_refs)
        basis, composition = parse_formula(record["formula"])
        composition_provenance = [
            {
                "package": "consolidation",
                "ref": "formula_parser_v1",
                "granularity": "derived",
            }
        ]

        structure_links: list[dict[str, Any]] = []
        link = links.get(local_id)
        if link:
            structure_links.append(
                {
                    "structure_id": link["structure_id"],
                    "relation": link["relation"],
                    "evidence": [
                        f"{evidence['kind']}:{evidence.get('namespace') or ''}:{evidence['value']}"
                        for evidence in link["evidence"]
                    ],
                }
            )

        crossref = crossrefs.get(local_id)
        fields = {
            "name_zh": provenance,
            "formula": provenance,
            "charge": provenance,
            "composition": composition_provenance,
            "aliases": provenance,
        }
        if record.get("name_en"):
            fields["name_en"] = provenance
        if crossref:
            fields["external_ids"] = [
                {
                    "package": "organic",
                    "ref": ref,
                    "granularity": "record",
                }
                for ref in crossref.get("provenance_refs", [])
            ] or provenance
        if structure_links:
            fields["structure_links"] = [
                {
                    "package": "consolidation",
                    "ref": "organic-structure-links.jsonl",
                    "granularity": "link",
                }
            ]

        species.append(
            {
                "species_id": identity["canonical_id"],
                "entity_type": "substance",
                "name_zh": record["name_zh"],
                "name_en": record.get("name_en"),
                "formula": record["formula"],
                "charge": 0,
                "composition_basis": basis,
                "composition": composition,
                "aliases": record.get("aliases", []),
                "structure_links": structure_links,
                "external_ids": normalized_external_ids(record, crossref),
                "source_refs": [{"package": "organic", "local_id": local_id}],
                "source_states": [
                    {
                        "package": "organic",
                        "local_id": local_id,
                        "status": record["verification_status"],
                    }
                ],
                "field_provenance": fields,
                "review_status": "reviewed",
            }
        )

        category = record["category"]
        tags = [f"organic_{category}"]
        palette_groups = ["organic"]
        if record["teaching_priority"] in {"core", "common"}:
            palette_groups.insert(0, "common")
        if category == "carboxylic_acid":
            tags.append("acid")
            palette_groups.append("acids")
        elif category == "carboxylate_salt":
            tags.append("salt")
            palette_groups.append("salts")

        terms: list[str] = []
        for value in [
            record["name_zh"],
            record.get("name_en"),
            record["formula"],
            *record.get("aliases", []),
        ]:
            if isinstance(value, str) and value and value not in terms:
                terms.append(value)
        for external_id in normalized_external_ids(record, crossref):
            for value in (
                f"{external_id['namespace']}:{external_id['value']}",
                external_id["value"],
            ):
                if value not in terms:
                    terms.append(value)

        projections.append(
            {
                "target": {"kind": "species", "id": identity["canonical_id"]},
                "curriculum_scope": "senior_high_school_cn",
                "priority": record["teaching_priority"],
                "primary_category": "organic",
                "tags": sorted(set(tags)),
                "palette_groups": list(dict.fromkeys(palette_groups)),
                "default_rank": priority_base[record["teaching_priority"]] + ordinal,
                "search_terms": terms,
            }
        )

    species.sort(key=lambda item: item["species_id"])
    projections.sort(key=lambda item: item["target"]["id"])
    return species, projections


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR / "generated")
    args = parser.parse_args()

    species, projections = build_species()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "species.jsonl").write_text(
        dump_jsonl(species), encoding="utf-8"
    )
    (args.output_dir / "teaching-projections.jsonl").write_text(
        dump_jsonl(projections), encoding="utf-8"
    )
    summary = {
        "status": "organic_structure_preview",
        "consumer_release": False,
        "species": len(species),
        "teaching_projections": len(projections),
        "inorganic_pending": True,
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
