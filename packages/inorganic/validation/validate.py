#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = ROOT / "sources" / "source_registry.json"
MANIFEST = ROOT / "manifest.json"

FILES = {
    "element_scope": DATA / "element_scope.jsonl",
    "ion": DATA / "ions.jsonl",
    "substance": DATA / "substances.jsonl",
    "reaction": DATA / "reactions.jsonl",
    "phenomenon": DATA / "phenomena.jsonl",
    "experiment": DATA / "experiments.jsonl",
    "concept": DATA / "concepts.jsonl",
}

PRIORITIES = {"core", "common", "extended"}
REVIEW = {"seed", "reviewed", "published"}

def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows

def aggregate(parts: list[dict], by_id: dict[str, dict]) -> tuple[dict[str, int], int]:
    atoms: dict[str, int] = {}
    charge = 0
    for p in parts:
        assert isinstance(p.get("coefficient"), int) and p["coefficient"] > 0, p
        sid = p["species_id"]
        assert sid in by_id, f"unknown species {sid}"
        species = by_id[sid]
        coeff = p["coefficient"]
        for element, count in species["composition"].items():
            atoms[element] = atoms.get(element, 0) + count * coeff
        charge += species.get("charge", 0) * coeff
    return atoms, charge

def main() -> None:
    source_registry = json.loads(SOURCES.read_text(encoding="utf-8"))
    source_ids = [s["id"] for s in source_registry["sources"]]
    assert len(source_ids) == len(set(source_ids)), "duplicate source id"
    source_set = set(source_ids)

    rows_by_kind = {kind: load_jsonl(path) for kind, path in FILES.items()}
    all_rows = [row for rows in rows_by_kind.values() for row in rows]
    ids = [row["id"] for row in all_rows]
    duplicates = [k for k, v in Counter(ids).items() if v > 1]
    assert not duplicates, f"duplicate ids: {duplicates}"
    by_id = {row["id"]: row for row in all_rows}

    for expected_kind, rows in rows_by_kind.items():
        for row in rows:
            assert row["kind"] == expected_kind, f"{row['id']}: kind mismatch"
            assert row.get("teaching_priority") in PRIORITIES, f"{row['id']}: invalid priority"
            assert row.get("review_status") in REVIEW, f"{row['id']}: invalid review status"
            assert row.get("sources"), f"{row['id']}: sources required"
            unknown = set(row["sources"]) - source_set
            assert not unknown, f"{row['id']}: unknown sources {unknown}"
            for target in row.get("verification_targets", []):
                assert target in source_set, f"{row['id']}: unknown verification target {target}"

    elems = rows_by_kind["element_scope"]
    assert len({r["symbol"] for r in elems}) == len(elems), "duplicate element symbol"
    assert len({r["atomic_number"] for r in elems}) == len(elems), "duplicate element atomic number"
    for row in elems:
        assert 1 <= row["atomic_number"] <= 118

    for row in rows_by_kind["ion"] + rows_by_kind["substance"]:
        assert row.get("composition"), f"{row['id']}: composition required"
        for element, count in row["composition"].items():
            assert element and isinstance(count, int) and count > 0, f"{row['id']}: invalid composition"

    for ion in rows_by_kind["ion"]:
        assert isinstance(ion["charge"], int) and ion["charge"] != 0, f"{ion['id']}: nonzero integer charge required"

    for substance in rows_by_kind["substance"]:
        ionic_projection = substance.get("ions", [])
        if ionic_projection:
            total_charge = 0
            for item in ionic_projection:
                iid = item["ion_id"]
                assert iid in by_id and by_id[iid]["kind"] == "ion", f"{substance['id']}: unknown ion {iid}"
                coeff = item["coefficient"]
                assert isinstance(coeff, int) and coeff > 0
                total_charge += by_id[iid]["charge"] * coeff
            assert total_charge == 0, f"{substance['id']}: ionic projection not neutral"

    for reaction in rows_by_kind["reaction"]:
        left_atoms, left_charge = aggregate(reaction["reactants"], by_id)
        right_atoms, right_charge = aggregate(reaction["products"], by_id)
        assert left_atoms == right_atoms, f"{reaction['id']}: atom conservation failed: {left_atoms} != {right_atoms}"
        assert left_charge == right_charge, f"{reaction['id']}: charge conservation failed"
        for pid in reaction.get("phenomenon_ids", []):
            assert pid in by_id and by_id[pid]["kind"] == "phenomenon", f"{reaction['id']}: unknown phenomenon {pid}"
        net = reaction.get("net_ionic")
        if net:
            n_left_atoms, n_left_charge = aggregate(net["reactants"], by_id)
            n_right_atoms, n_right_charge = aggregate(net["products"], by_id)
            assert n_left_atoms == n_right_atoms, f"{reaction['id']}: net ionic atom conservation failed"
            assert n_left_charge == n_right_charge, f"{reaction['id']}: net ionic charge conservation failed"

    for phenomenon in rows_by_kind["phenomenon"]:
        for rid in phenomenon.get("related_reaction_ids", []):
            assert rid in by_id and by_id[rid]["kind"] == "reaction", f"{phenomenon['id']}: unknown reaction {rid}"

    for experiment in rows_by_kind["experiment"]:
        for rid in experiment.get("reaction_ids", []):
            assert rid in by_id and by_id[rid]["kind"] == "reaction", f"{experiment['id']}: unknown reaction {rid}"
        for pid in experiment.get("expected_phenomenon_ids", []):
            assert pid in by_id and by_id[pid]["kind"] == "phenomenon", f"{experiment['id']}: unknown phenomenon {pid}"

    for concept in rows_by_kind["concept"]:
        for rid in concept.get("related_reaction_ids", []):
            assert rid in by_id and by_id[rid]["kind"] == "reaction", f"{concept['id']}: unknown reaction {rid}"
        for sid in concept.get("related_species_ids", []):
            assert sid in by_id and by_id[sid]["kind"] in {"ion", "substance"}, f"{concept['id']}: unknown species {sid}"

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    actual = {
        "element_scope": len(rows_by_kind["element_scope"]),
        "ions": len(rows_by_kind["ion"]),
        "substances": len(rows_by_kind["substance"]),
        "reactions": len(rows_by_kind["reaction"]),
        "phenomena": len(rows_by_kind["phenomenon"]),
        "experiments": len(rows_by_kind["experiment"]),
        "concepts": len(rows_by_kind["concept"]),
    }
    assert manifest["record_counts"] == actual, f"manifest count mismatch: {manifest['record_counts']} != {actual}"
    assert manifest["total_records"] == sum(actual.values())

    print("inorganic knowledge package validation: OK")
    for key, value in actual.items():
        print(f"  {key}: {value}")
    print(f"  total: {sum(actual.values())}")

if __name__ == "__main__":
    main()
