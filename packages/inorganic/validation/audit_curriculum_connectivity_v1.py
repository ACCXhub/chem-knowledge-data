#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
COVERAGE = ROOT / "curriculum" / "coverage.json"

CONCEPT_FILES = [DATA / "concepts.jsonl", DATA / "v1" / "concepts.ext.jsonl"]
TAG_FILES = [DATA / "v1" / "exam_tags.jsonl"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    concepts = [row for path in CONCEPT_FILES for row in load_jsonl(path)]
    tags = [row for path in TAG_FILES for row in load_jsonl(path)]
    coverage = load_json(COVERAGE)

    concept_by_id = {row["id"]: row for row in concepts}
    tag_by_id = {row["id"]: row for row in tags}
    concept_domains: Counter[str] = Counter()
    tag_domains: Counter[str] = Counter()
    concept_tags: Counter[str] = Counter()
    errors: list[str] = []

    for tag in tags:
        for concept_id in tag.get("related_concept_ids", []):
            concept_tags[concept_id] += 1

    for domain in coverage.get("domains", []):
        domain_id = domain["id"]
        concept_ids = domain.get("concept_ids", [])
        tag_ids = domain.get("exam_tag_ids", [])
        if domain.get("status") == "covered":
            if not concept_ids:
                errors.append(f"{domain_id}: covered domain has no concepts")
            if not tag_ids:
                errors.append(f"{domain_id}: covered domain has no exam tags")
        for concept_id in concept_ids:
            if concept_id not in concept_by_id:
                errors.append(f"{domain_id}: unknown concept {concept_id}")
            concept_domains[concept_id] += 1
        for tag_id in tag_ids:
            if tag_id not in tag_by_id:
                errors.append(f"{domain_id}: unknown exam tag {tag_id}")
            tag_domains[tag_id] += 1

    isolated_core: list[str] = []
    core_without_domain: list[str] = []
    for concept in concepts:
        cid = concept["id"]
        if concept.get("teaching_priority") != "core":
            continue
        if concept_domains[cid] == 0:
            core_without_domain.append(cid)
        has_chem_link = bool(concept.get("related_reaction_ids") or concept.get("related_species_ids"))
        has_teaching_link = concept_domains[cid] > 0 or concept_tags[cid] > 0
        if not has_chem_link and not has_teaching_link:
            isolated_core.append(cid)

    core_tags_without_domain = [
        tag["id"]
        for tag in tags
        if tag.get("teaching_priority") == "core" and tag_domains[tag["id"]] == 0
    ]

    if core_without_domain:
        errors.append("core concepts outside curriculum map: " + ",".join(core_without_domain))
    if isolated_core:
        errors.append("isolated core concepts: " + ",".join(isolated_core))
    if core_tags_without_domain:
        errors.append("core exam tags outside curriculum map: " + ",".join(core_tags_without_domain))

    theory_linked = [
        concept["id"]
        for concept in concepts
        if concept.get("teaching_priority") == "core"
        and not concept.get("related_reaction_ids")
        and not concept.get("related_species_ids")
        and (concept_domains[concept["id"]] > 0 or concept_tags[concept["id"]] > 0)
    ]

    print("inorganic v1 curriculum/connectivity audit")
    print(f"domains={len(coverage.get('domains', []))} concepts={len(concepts)} exam_tags={len(tags)}")
    print(f"core_theory_concepts_without_reaction_or_species_links={len(theory_linked)}")
    if theory_linked:
        print("core_theory_concept_ids=" + ",".join(theory_linked))
    if errors:
        print("ERRORS:")
        for error in errors:
            print("  " + error)
        raise SystemExit(1)
    print("curriculum/connectivity hard checks: OK")


if __name__ == "__main__":
    main()
