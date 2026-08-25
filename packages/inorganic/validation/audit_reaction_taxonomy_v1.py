#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

REACTION_FILES = [
    DATA / "reactions.jsonl",
    DATA / "v1" / "reactions.01.ext.jsonl",
    DATA / "v1" / "reactions.02.ext.jsonl",
    DATA / "v1" / "reactions.03.ext.jsonl",
    DATA / "v1" / "reactions.04.ext.jsonl",
]
PHENOMENON_FILES = [DATA / "phenomena.jsonl", DATA / "v1" / "phenomena.ext.jsonl"]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def has_product(reaction: dict[str, Any], species_id: str | None = None, phase: str | None = None) -> bool:
    return any(
        (species_id is None or part["species_id"] == species_id)
        and (phase is None or part["phase"] == phase)
        for part in reaction["products"]
    )


def has_reactant(reaction: dict[str, Any], species_id: str | None = None, phase: str | None = None) -> bool:
    return any(
        (species_id is None or part["species_id"] == species_id)
        and (phase is None or part["phase"] == phase)
        for part in reaction["reactants"]
    )


def main() -> None:
    reactions = [row for path in REACTION_FILES for row in load_jsonl(path)]
    phenomena = [row for path in PHENOMENON_FILES for row in load_jsonl(path)]
    by_reaction = {row["id"]: row for row in reactions}

    errors: list[str] = []

    for reaction in reactions:
        rid = reaction["id"]
        types = set(reaction["reaction_types"])

        if "precipitation" in types and not has_product(reaction, phase="s"):
            errors.append(f"{rid}: precipitation has no solid product")
        if types.intersection({"gas_evolution", "gas_preparation"}) and not has_product(reaction, phase="g"):
            errors.append(f"{rid}: gas-generation classification has no gaseous product")
        if "combustion" in types and not has_reactant(reaction, species_id="substance:oxygen"):
            errors.append(f"{rid}: combustion has no O2 reactant")
        if "neutralization" in types and not has_product(reaction, species_id="substance:water"):
            errors.append(f"{rid}: neutralization has no water product")
        if "acid_carbonate" in types and not has_product(reaction, species_id="substance:carbon-dioxide"):
            errors.append(f"{rid}: acid_carbonate has no CO2 product")
        if "decomposition" in types and len(reaction["reactants"]) != 1:
            errors.append(f"{rid}: decomposition should have one canonical reactant")
        if "double_displacement" in types and (len(reaction["reactants"]) < 2 or len(reaction["products"]) < 2):
            errors.append(f"{rid}: double_displacement lacks two-sided species exchange")
        if "qualitative_test" in types and not reaction.get("phenomenon_ids"):
            errors.append(f"{rid}: qualitative_test has no linked observable phenomenon")

    for phenomenon in phenomena:
        if phenomenon.get("category") != "precipitate":
            continue
        for rid in phenomenon.get("related_reaction_ids", []):
            reaction = by_reaction[rid]
            if not has_product(reaction, phase="s"):
                errors.append(f"{phenomenon['id']}: precipitate phenomenon links reaction without solid product {rid}")

    print("inorganic v1 reaction-taxonomy semantic audit")
    print(f"reactions={len(reactions)} phenomena={len(phenomena)}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print("  " + error)
        raise SystemExit(1)
    print("reaction taxonomy hard checks: OK")


if __name__ == "__main__":
    main()
