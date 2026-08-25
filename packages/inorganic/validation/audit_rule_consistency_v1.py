#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOLUBILITY = ROOT / "rules" / "solubility.json"

ION_FILES = [DATA / "ions.jsonl", DATA / "v1" / "ions.ext.jsonl"]
SUBSTANCE_FILES = [
    DATA / "substances.jsonl",
    DATA / "v1" / "substances.01.ext.jsonl",
    DATA / "v1" / "substances.02.ext.jsonl",
    DATA / "v1" / "substances.03.ext.jsonl",
]

# aqueous_behavior is a consumer projection for ionic-equation handling, not a pure
# solubility field. A sparingly soluble strong electrolyte such as Ca(OH)2 may therefore
# be strong_electrolyte while the solubility rule says sparingly_soluble.
ALLOWED_RULE_RESULTS = {
    "strong_electrolyte": {"soluble", "sparingly_soluble"},
    "insoluble": {"insoluble"},
    "sparingly_soluble": {"sparingly_soluble"},
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def ionic_pair(
    substance: dict[str, Any],
    ions_by_id: dict[str, dict[str, Any]],
) -> tuple[str, str] | None:
    components = substance.get("ions", [])
    if len(components) != 2:
        return None
    positive: list[str] = []
    negative: list[str] = []
    for component in components:
        ion_id = component.get("ion_id")
        ion = ions_by_id.get(ion_id)
        if ion is None:
            return None
        charge = ion["charge"]
        if charge > 0:
            positive.append(ion_id)
        elif charge < 0:
            negative.append(ion_id)
    if len(positive) != 1 or len(negative) != 1:
        return None
    return positive[0], negative[0]


def matches(match: dict[str, Any], cation: str, anion: str) -> bool:
    if "cation" in match and match["cation"] != cation:
        return False
    if "anion" in match and match["anion"] != anion:
        return False
    if "cation_any" in match and cation not in match["cation_any"]:
        return False
    if "anion_any" in match and anion not in match["anion_any"]:
        return False
    return bool(match)


def specificity(match: dict[str, Any]) -> int:
    score = 0
    if "cation" in match:
        score += 2
    elif "cation_any" in match:
        score += 1
    if "anion" in match:
        score += 2
    elif "anion_any" in match:
        score += 1
    return score


def apply_exceptions(
    rule: dict[str, Any],
    substance_id: str,
    cation: str,
    default_result: str,
) -> str:
    for item in rule.get("exceptions", []):
        if item.get("substance_id") == substance_id:
            return item["result"]
    for item in rule.get("exceptions_by_cation", []):
        if item.get("cation") == cation or cation in item.get("cation_any", []):
            return item["result"]
    return default_result


def predict(
    substance: dict[str, Any],
    cation: str,
    anion: str,
    rules: list[dict[str, Any]],
) -> tuple[str, str] | None:
    candidates: list[tuple[int, int, str, str]] = []
    for index, rule in enumerate(rules):
        match = rule.get("match", {})
        if not matches(match, cation, anion):
            continue
        result = apply_exceptions(rule, substance["id"], cation, rule["result"])
        candidates.append((specificity(match), index, result, rule["id"]))
    if not candidates:
        return None
    _, _, result, rule_id = max(candidates)
    return result, rule_id


def main() -> None:
    ions = [row for path in ION_FILES for row in load_jsonl(path)]
    substances = [row for path in SUBSTANCE_FILES for row in load_jsonl(path)]
    ions_by_id = {row["id"]: row for row in ions}
    rule_doc = load_json(SOLUBILITY)
    rules = rule_doc["rules"]

    errors: list[str] = []
    warnings: list[str] = []
    outcomes: Counter[str] = Counter()
    unknown_relevant: list[str] = []

    for substance in substances:
        pair = ionic_pair(substance, ions_by_id)
        if pair is None:
            outcomes["not_binary_ionic_pair"] += 1
            continue
        cation, anion = pair
        behavior = substance.get("aqueous_behavior")
        prediction = predict(substance, cation, anion, rules)
        if prediction is None:
            outcomes["unknown"] += 1
            if behavior in ALLOWED_RULE_RESULTS:
                unknown_relevant.append(
                    f"{substance['id']}: {cation} + {anion}; canonical={behavior}"
                )
            continue

        result, rule_id = prediction
        outcomes[result] += 1
        allowed = ALLOWED_RULE_RESULTS.get(behavior)
        if allowed is not None and result not in allowed:
            errors.append(
                f"{substance['id']}: canonical={behavior} is incompatible with "
                f"rule={rule_id} predicting {result} for {cation} + {anion}"
            )

    if unknown_relevant:
        warnings.append(
            f"{len(unknown_relevant)} canonical ionic substances have no explicit solubility-rule result"
        )

    print("inorganic v1 solubility-rule consistency audit")
    print(f"substances={len(substances)} outcomes={dict(outcomes)}")
    print(f"unknown_relevant={len(unknown_relevant)}")
    if unknown_relevant:
        print("UNKNOWN_RELEVANT:")
        for item in unknown_relevant:
            print("  " + item)
    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print("  " + warning)
    if errors:
        print("ERRORS:")
        for error in errors:
            print("  " + error)
        raise SystemExit(1)
    print("solubility rule consistency hard checks: OK")


if __name__ == "__main__":
    main()
