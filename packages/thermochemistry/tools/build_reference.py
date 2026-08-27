from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DATA = ROOT / "data"
SOURCES = ROOT / "sources"
CONSOLIDATED_SPECIES = REPO_ROOT / "packages" / "consolidated" / "generated" / "species.jsonl"
R = 8.31446261815324


class ChemistrySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that does not interpret chemical formula NO as YAML 1.1 false."""


ChemistrySafeLoader.yaml_implicit_resolvers = {
    key: [item for item in value if item[0] != "tag:yaml.org,2002:bool"]
    for key, value in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in records)
    path.write_text(text, encoding="utf-8")


def fetch_yaml(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "chem-knowledge-data-thermochemistry/0.1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = yaml.load(response.read(), Loader=ChemistrySafeLoader)
    if not isinstance(payload, dict):
        raise ValueError(f"source {url} did not return a mapping")
    return payload


def source_registry() -> dict[str, dict[str, Any]]:
    registry = load_json(SOURCES / "source_registry.json")
    return {row["key"]: row for row in registry["sources"]}


def index_species(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in payload.get("species", []):
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            continue
        output[row["name"]] = row
        output.setdefault(row["name"].upper(), row)
    return output


def pick(index: dict[str, dict[str, Any]], names: list[str]) -> dict[str, Any] | None:
    for name in names:
        if name in index:
            return index[name]
        if name.upper() in index:
            return index[name.upper()]
    return None


def nasa7_at(row: dict[str, Any], temperature_k: float) -> dict[str, float]:
    thermo = row.get("thermo")
    if not isinstance(thermo, dict) or thermo.get("model") != "NASA7":
        raise ValueError(f"{row.get('name')}: NASA7 required")
    ranges = thermo.get("temperature-ranges")
    coeff_sets = thermo.get("data")
    if not isinstance(ranges, list) or not isinstance(coeff_sets, list) or len(ranges) != len(coeff_sets) + 1:
        raise ValueError(f"{row.get('name')}: malformed NASA7 ranges")
    segment = None
    for idx in range(len(coeff_sets)):
        low, high = float(ranges[idx]), float(ranges[idx + 1])
        if low <= temperature_k <= high or (idx == len(coeff_sets) - 1 and math.isclose(temperature_k, high)):
            segment = idx
            break
    if segment is None:
        raise ValueError(f"{row.get('name')}: T={temperature_k} K outside NASA7 range {ranges}")
    coeff = [float(value) for value in coeff_sets[segment]]
    if len(coeff) != 7:
        raise ValueError(f"{row.get('name')}: NASA7 needs 7 coefficients")
    a1, a2, a3, a4, a5, a6, a7 = coeff
    t = temperature_k
    cp_r = a1 + a2*t + a3*t*t + a4*t**3 + a5*t**4
    h_rt = a1 + a2*t/2 + a3*t*t/3 + a4*t**3/4 + a5*t**4/5 + a6/t
    s_r = a1*math.log(t) + a2*t + a3*t*t/2 + a4*t**3/3 + a5*t**4/4 + a7
    cp = cp_r * R
    h = h_rt * R * t
    s = s_r * R
    return {"cp_j_mol_k": cp, "h_j_mol": h, "s_j_mol_k": s, "g_j_mol": h - t*s}


def round_value(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(value, digits)


def element_reference_g(
    gas: dict[str, dict[str, Any]], graphite: dict[str, dict[str, Any]], temperature_k: float
) -> dict[str, float]:
    refs: dict[str, float] = {}
    for element, source_name, divisor in [("H", "H2", 2), ("O", "O2", 2), ("N", "N2", 2), ("F", "F2", 2), ("Cl", "CL2", 2)]:
        row = pick(gas, [source_name, source_name.title()])
        if row is not None:
            refs[element] = nasa7_at(row, temperature_k)["g_j_mol"] / divisor
    carbon = pick(graphite, ["C(gr)"])
    if carbon is not None:
        refs["C"] = nasa7_at(carbon, temperature_k)["g_j_mol"]
    return refs


def formation_g(row: dict[str, Any], values: dict[str, float], element_g: dict[str, float]) -> float | None:
    composition = row.get("composition")
    if not isinstance(composition, dict):
        return None
    total = 0.0
    for symbol, amount in composition.items():
        if symbol not in element_g:
            return None
        total += float(amount) * element_g[symbol]
    return (values["g_j_mol"] - total) / 1000.0


def record_for(
    *,
    species_id: str,
    phase: str,
    source_key: str,
    source_row: dict[str, Any],
    temperature_k: float,
    pressure_bar: float,
    element_g: dict[str, float],
) -> dict[str, Any]:
    values = nasa7_at(source_row, temperature_k)
    return {
        "id": f"thermo:{species_id}:{phase}:{temperature_k:g}",
        "species_id": species_id,
        "phase": phase,
        "temperature_k": temperature_k,
        "standard_pressure_bar": pressure_bar,
        "delta_f_h_kj_mol": round_value(values["h_j_mol"] / 1000.0),
        "delta_f_g_kj_mol": round_value(formation_g(source_row, values, element_g)),
        "s_j_mol_k": round_value(values["s_j_mol_k"]),
        "cp_j_mol_k": round_value(values["cp_j_mol_k"]),
        "method": "NASA7_evaluated",
        "source_species_name": source_row["name"],
        "source_note": source_row.get("thermo", {}).get("note") or source_row.get("note"),
        "source_refs": [source_key],
        "status": "published"
    }


def try_reference_record(
    *, species_id: str, phase: str, source_key: str, source_row: dict[str, Any], temperature_k: float,
    pressure_bar: float, element_g: dict[str, float]
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return record_for(
            species_id=species_id, phase=phase, source_key=source_key, source_row=source_row,
            temperature_k=temperature_k, pressure_bar=pressure_bar, element_g=element_g
        ), None
    except ValueError as exc:
        if "outside NASA7 range" in str(exc):
            return None, str(exc)
        raise


def atomization_enthalpy(gas: dict[str, dict[str, Any]], molecule: str, atoms: dict[str, int], t: float) -> float:
    molecule_row = pick(gas, [molecule])
    if molecule_row is None:
        raise ValueError(f"bond reference molecule missing: {molecule}")
    h_products = 0.0
    for atom, count in atoms.items():
        atom_row = pick(gas, [atom])
        if atom_row is None:
            raise ValueError(f"atomic source missing: {atom}")
        h_products += count * nasa7_at(atom_row, t)["h_j_mol"]
    return (h_products - nasa7_at(molecule_row, t)["h_j_mol"]) / 1000.0


def build_bond_enthalpies(gas: dict[str, dict[str, Any]], t: float) -> list[dict[str, Any]]:
    values: dict[str, float] = {}
    values["H-H"] = atomization_enthalpy(gas, "H2", {"H": 2}, t)
    values["O=O"] = atomization_enthalpy(gas, "O2", {"O": 2}, t)
    values["N#N"] = atomization_enthalpy(gas, "N2", {"N": 2}, t)
    values["O-H"] = atomization_enthalpy(gas, "H2O", {"H": 2, "O": 1}, t) / 2
    values["N-H"] = atomization_enthalpy(gas, "NH3", {"N": 1, "H": 3}, t) / 3
    values["C-H"] = atomization_enthalpy(gas, "CH4", {"C": 1, "H": 4}, t) / 4
    values["C-C"] = atomization_enthalpy(gas, "C2H6", {"C": 2, "H": 6}, t) - 6 * values["C-H"]
    values["C=C"] = atomization_enthalpy(gas, "C2H4", {"C": 2, "H": 4}, t) - 4 * values["C-H"]
    values["C#C"] = atomization_enthalpy(gas, "C2H2,acetylene", {"C": 2, "H": 2}, t) - 2 * values["C-H"]
    values["C-O"] = atomization_enthalpy(gas, "CH3OH", {"C": 1, "H": 4, "O": 1}, t) - 3 * values["C-H"] - values["O-H"]
    values["O-O"] = atomization_enthalpy(gas, "H2O2", {"H": 2, "O": 2}, t) - 2 * values["O-H"]
    values["C=O:CO2"] = atomization_enthalpy(gas, "CO2", {"C": 1, "O": 2}, t) / 2
    values["C#O:CO"] = atomization_enthalpy(gas, "CO", {"C": 1, "O": 1}, t)
    values["N=O:NO"] = atomization_enthalpy(gas, "NO", {"N": 1, "O": 1}, t)

    specs = [
        ("H-H", "H", "H", 1.0, "general_diatomic"),
        ("O=O", "O", "O", 2.0, "general_diatomic"),
        ("N#N", "N", "N", 3.0, "general_diatomic"),
        ("O-H", "O", "H", 1.0, "average_from_H2O_atomization"),
        ("N-H", "N", "H", 1.0, "average_from_NH3_atomization"),
        ("C-H", "C", "H", 1.0, "average_from_CH4_atomization"),
        ("C-C", "C", "C", 1.0, "derived_with_CH4_C-H_reference_from_C2H6"),
        ("C=C", "C", "C", 2.0, "derived_with_CH4_C-H_reference_from_C2H4"),
        ("C#C", "C", "C", 3.0, "derived_with_CH4_C-H_reference_from_C2H2"),
        ("C-O", "C", "O", 1.0, "derived_from_CH3OH_with_C-H_and_O-H_references"),
        ("O-O", "O", "O", 1.0, "derived_from_H2O2_with_O-H_reference"),
        ("C=O:CO2", "C", "O", 2.0, "CO2_specific_average"),
        ("C#O:CO", "C", "O", 3.0, "CO_specific_diatomic"),
        ("N=O:NO", "N", "O", 2.0, "NO_specific_diatomic")
    ]
    output = []
    for key, atom1, atom2, order, environment in specs:
        output.append({
            "id": "bond-enthalpy:" + key.replace("#", "triple").replace("=", "double").replace(":", "-"),
            "atom1": atom1,
            "atom2": atom2,
            "bond_order": order,
            "environment_key": environment,
            "enthalpy_kj_mol": round_value(values[key], 3),
            "temperature_k": t,
            "phase_scope": "gas",
            "method": "thermochemical_atomization_estimate",
            "qualifier": "Educational fallback reference derived consistently from NASA gas-phase thermochemistry; not an exact universal bond dissociation enthalpy.",
            "source_refs": ["cantera_nasa_gas_2_6"],
            "status": "published"
        })
    return output


def main() -> int:
    registry = source_registry()
    mapping = load_json(DATA / "source_species_map.json")
    t = float(mapping["reference_temperature_k"])
    p_bar = float(mapping["standard_pressure_bar"])
    gas_payload = fetch_yaml(registry["cantera_nasa_gas_2_6"]["url"])
    condensed_payload = fetch_yaml(registry["cantera_nasa_condensed_2_6"]["url"])
    graphite_payload = fetch_yaml(registry["cantera_graphite_2_5"]["url"])
    gas = index_species(gas_payload)
    condensed = index_species(condensed_payload)
    graphite = index_species(graphite_payload)
    canonical = {row["id"]: row for row in load_jsonl(CONSOLIDATED_SPECIES)}
    element_g = element_reference_g(gas, graphite, t)

    phase_facts: list[dict[str, Any]] = []
    thermochemistry: list[dict[str, Any]] = []
    missing_sources: list[dict[str, Any]] = []

    for spec in mapping["species"]:
        species_id = spec["species_id"]
        if species_id not in canonical:
            raise ValueError(f"source map references missing canonical species: {species_id}")
        if canonical[species_id].get("formula") != spec["formula"]:
            raise ValueError(f"formula mismatch for {species_id}: map={spec['formula']} catalog={canonical[species_id].get('formula')}")
        available_phases: list[str] = []
        gas_row = pick(gas, spec.get("gas_names", []))
        if gas_row is not None:
            record, reason = try_reference_record(
                species_id=species_id, phase="g", source_key="cantera_nasa_gas_2_6", source_row=gas_row,
                temperature_k=t, pressure_bar=p_bar, element_g=element_g
            )
            if record is not None:
                thermochemistry.append(record)
                available_phases.append("g")
            else:
                missing_sources.append({"species_id": species_id, "phase": "g", "reason": reason, "candidates": spec.get("gas_names", [])})
        elif spec.get("gas_names"):
            missing_sources.append({"species_id": species_id, "phase": "g", "reason": "source_species_not_found", "candidates": spec["gas_names"]})

        for phase, names in spec.get("condensed", {}).items():
            row = pick(condensed, names)
            if row is None:
                missing_sources.append({"species_id": species_id, "phase": phase, "reason": "source_species_not_found", "candidates": names})
                continue
            record, reason = try_reference_record(
                species_id=species_id, phase=phase, source_key="cantera_nasa_condensed_2_6", source_row=row,
                temperature_k=t, pressure_bar=p_bar, element_g=element_g
            )
            if record is not None:
                thermochemistry.append(record)
                available_phases.append(phase)
            else:
                missing_sources.append({"species_id": species_id, "phase": phase, "reason": reason, "candidates": names})

        phase_facts.append({
            "id": f"phase-fact:{species_id}",
            "species_id": species_id,
            "standard_phase": spec["standard_phase"],
            "allowed_teaching_phases": spec["allowed_teaching_phases"],
            "thermochemistry_available_phases": sorted(set(available_phases)),
            "reference_conditions": {"temperature_k": t, "standard_pressure_bar": p_bar},
            "phase_conditions": [
                {
                    "phase": phase,
                    "use": "teaching_selectable",
                    "thermochemistry_available_at_reference": phase in available_phases
                }
                for phase in spec["allowed_teaching_phases"]
            ],
            "source_refs": ["internal_consolidated_1_0_0", "cantera_nasa_gas_2_6", "cantera_nasa_condensed_2_6"],
            "status": "published"
        })

    thermochemistry.sort(key=lambda row: (row["species_id"], row["phase"]))
    phase_facts.sort(key=lambda row: row["species_id"])

    transitions: list[dict[str, Any]] = []
    water_id = "species:inorganic:substance:water"
    water_g = pick(gas, ["H2O"])
    water_l = pick(condensed, ["H2O(L)"])
    water_s = pick(condensed, ["H2O(cr)", "H2O(s)"])
    if water_s is not None and water_l is not None:
        fusion_t = 273.15
        dh = (nasa7_at(water_l, fusion_t)["h_j_mol"] - nasa7_at(water_s, fusion_t)["h_j_mol"]) / 1000
        transitions.append({
            "id": "phase-transition:water:fusion", "species_id": water_id,
            "transition": "fusion", "from_phase": "s", "to_phase": "l",
            "transition_temperature_k": fusion_t, "enthalpy_kj_mol": round_value(dh, 4),
            "method": "NASA7_phase_enthalpy_difference_at_transition_temperature",
            "source_refs": ["cantera_nasa_condensed_2_6"], "status": "published"
        })
    if water_l is not None and water_g is not None:
        vapor_t = 373.15
        dh = (nasa7_at(water_g, vapor_t)["h_j_mol"] - nasa7_at(water_l, vapor_t)["h_j_mol"]) / 1000
        transitions.append({
            "id": "phase-transition:water:vaporization", "species_id": water_id,
            "transition": "vaporization", "from_phase": "l", "to_phase": "g",
            "transition_temperature_k": vapor_t, "enthalpy_kj_mol": round_value(dh, 4),
            "method": "NASA7_phase_enthalpy_difference_at_normal_boiling_reference",
            "source_refs": ["cantera_nasa_gas_2_6", "cantera_nasa_condensed_2_6"], "status": "published"
        })

    bonds = build_bond_enthalpies(gas, t)
    write_jsonl(DATA / "species_phase_facts.jsonl", phase_facts)
    write_jsonl(DATA / "species_thermochemistry.jsonl", thermochemistry)
    write_jsonl(DATA / "phase_transitions.jsonl", transitions)
    write_jsonl(DATA / "bond_enthalpies.jsonl", bonds)
    (DATA / "unresolved_source_mappings.json").write_text(
        json.dumps(missing_sources, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    manifest = {
        "package": "thermochemistry",
        "release": "thermochemistry-v0.1.0",
        "state": "READY_FOR_CONSOLIDATION",
        "reference_conditions": {"temperature_k": t, "standard_pressure_bar": p_bar},
        "records": {
            "species_phase_facts": len(phase_facts),
            "species_thermochemistry": len(thermochemistry),
            "phase_transitions": len(transitions),
            "bond_enthalpies": len(bonds)
        },
        "total_records": len(phase_facts) + len(thermochemistry) + len(transitions) + len(bonds),
        "unresolved_source_mappings": len(missing_sources),
        "canonical_boundary": {
            "owns": ["phase facts", "phase-specific thermochemistry", "phase-transition enthalpy facts", "bond-enthalpy estimate references"],
            "does_not_own": ["Substance identity", "Ion identity", "Structure identity", "Reaction identity", "Mechanism"]
        },
        "calculation_priority": ["phase_specific_standard_formation_enthalpy", "bond_enthalpy_estimate_fallback"]
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"records": manifest["records"], "unresolved": missing_sources}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
