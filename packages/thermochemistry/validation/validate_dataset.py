from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DATA = ROOT / "data"
CONSOLIDATED = REPO_ROOT / "packages" / "consolidated" / "generated" / "species.jsonl"
PHASES = {"s", "l", "g", "aq"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def between(value: float, low: float, high: float, label: str) -> None:
    assert low <= value <= high, f"{label}: expected {low}..{high}, got {value}"


def main() -> None:
    required = [
        DATA / "source_species_map.json",
        DATA / "species_phase_facts.jsonl",
        DATA / "species_thermochemistry.jsonl",
        DATA / "phase_transitions.jsonl",
        DATA / "bond_enthalpies.jsonl",
        DATA / "unresolved_source_mappings.json",
        ROOT / "manifest.json",
        ROOT / "sources" / "source_registry.json"
    ]
    for path in required:
        assert path.is_file(), f"missing {path.relative_to(ROOT)}"

    canonical = {row["id"]: row for row in load_jsonl(CONSOLIDATED)}
    source_keys = {row["key"] for row in load_json(ROOT / "sources" / "source_registry.json")["sources"]}
    mapping = load_json(DATA / "source_species_map.json")
    mapped_ids = {row["species_id"] for row in mapping["species"]}
    assert len(mapped_ids) == len(mapping["species"]), "duplicate source species mapping"
    assert mapped_ids <= set(canonical), f"unknown mapped species: {sorted(mapped_ids - set(canonical))}"

    phase_facts = load_jsonl(DATA / "species_phase_facts.jsonl")
    thermo = load_jsonl(DATA / "species_thermochemistry.jsonl")
    transitions = load_jsonl(DATA / "phase_transitions.jsonl")
    bonds = load_jsonl(DATA / "bond_enthalpies.jsonl")
    unresolved = load_json(DATA / "unresolved_source_mappings.json")
    manifest = load_json(ROOT / "manifest.json")

    assert len(phase_facts) == len(mapping["species"]), "every mapped teaching species needs one phase fact"
    assert len({row["species_id"] for row in phase_facts}) == len(phase_facts), "duplicate phase fact"
    thermo_keys = set()
    thermo_by_key = {}
    for row in thermo:
        assert row["species_id"] in canonical, f"unknown thermo species {row['species_id']}"
        assert row["phase"] in PHASES
        key = (row["species_id"], row["phase"], row["temperature_k"], row["standard_pressure_bar"])
        assert key not in thermo_keys, f"duplicate thermochemistry key {key}"
        thermo_keys.add(key)
        thermo_by_key[(row["species_id"], row["phase"])] = row
        assert row["method"] == "NASA7_evaluated"
        assert row["source_refs"] and set(row["source_refs"]) <= source_keys
        assert row["status"] == "published"
        assert row["cp_j_mol_k"] > 0
        assert row["s_j_mol_k"] >= 0

    for row in phase_facts:
        assert row["species_id"] in canonical
        assert row["standard_phase"] in PHASES
        allowed = row["allowed_teaching_phases"]
        assert allowed and set(allowed) <= PHASES
        assert row["standard_phase"] in allowed
        assert set(row["thermochemistry_available_phases"]) <= set(allowed)
        assert (row["species_id"], row["standard_phase"]) in thermo_by_key, (
            f"standard phase lacks thermochemistry: {row['species_id']}({row['standard_phase']})"
        )
        assert set(row["source_refs"]) <= source_keys

    water = "species:inorganic:substance:water"
    water_l = thermo_by_key[(water, "l")]
    water_g = thermo_by_key[(water, "g")]
    between(water_l["delta_f_h_kj_mol"], -288.0, -283.0, "H2O(l) delta_f_h")
    between(water_g["delta_f_h_kj_mol"], -244.0, -239.0, "H2O(g) delta_f_h")
    assert water_l["delta_f_h_kj_mol"] < water_g["delta_f_h_kj_mol"], "liquid water must be lower enthalpy than vapor"
    if water_l["delta_f_g_kj_mol"] is not None:
        between(water_l["delta_f_g_kj_mol"], -240.0, -235.0, "H2O(l) delta_f_g")

    transition_by_id = {row["id"]: row for row in transitions}
    assert "phase-transition:water:fusion" in transition_by_id
    assert "phase-transition:water:vaporization" in transition_by_id
    between(transition_by_id["phase-transition:water:fusion"]["enthalpy_kj_mol"], 5.0, 7.5, "water fusion enthalpy")
    between(transition_by_id["phase-transition:water:vaporization"]["enthalpy_kj_mol"], 38.0, 43.0, "water vaporization enthalpy")

    bond_by_id = {row["id"]: row for row in bonds}
    assert len(bond_by_id) == len(bonds) >= 12
    for row in bonds:
        assert row["method"] == "thermochemical_atomization_estimate"
        assert row["phase_scope"] == "gas"
        assert row["qualifier"]
        assert set(row["source_refs"]) <= source_keys
        between(row["enthalpy_kj_mol"], 50.0, 1500.0, row["id"])
    between(bond_by_id["bond-enthalpy:H-H"]["enthalpy_kj_mol"], 420.0, 450.0, "H-H")
    between(bond_by_id["bond-enthalpy:OdoubleO"]["enthalpy_kj_mol"], 480.0, 510.0, "O=O")
    between(bond_by_id["bond-enthalpy:O-H"]["enthalpy_kj_mol"], 450.0, 510.0, "O-H average")

    standard_missing = []
    standard_by_species = {row["species_id"]: row["standard_phase"] for row in phase_facts}
    for item in unresolved:
        if item.get("phase") == standard_by_species.get(item.get("species_id")):
            standard_missing.append(item)
    assert not standard_missing, f"standard-phase source mappings unresolved: {standard_missing}"

    counts = {
        "species_phase_facts": len(phase_facts),
        "species_thermochemistry": len(thermo),
        "phase_transitions": len(transitions),
        "bond_enthalpies": len(bonds)
    }
    assert manifest["records"] == counts, f"manifest count mismatch: {manifest['records']} vs {counts}"
    assert manifest["total_records"] == sum(counts.values())
    assert manifest["calculation_priority"] == ["phase_specific_standard_formation_enthalpy", "bond_enthalpy_estimate_fallback"]
    assert manifest["state"] == "READY_FOR_CONSOLIDATION"

    print(json.dumps({
        "status": "passed",
        "records": counts,
        "optional_unresolved_source_mappings": len(unresolved),
        "water_default_phase": "l",
        "formation_enthalpy_priority": True,
        "bond_enthalpy_fallback_only": True
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
