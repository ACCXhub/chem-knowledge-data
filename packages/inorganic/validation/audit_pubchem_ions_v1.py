#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ION_FILES = [DATA / "ions.jsonl", DATA / "v1" / "ions.ext.jsonl"]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_formula(formula: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for symbol, digits in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        counts[symbol] = counts.get(symbol, 0) + (int(digits) if digits else 1)
    return counts


def fetch_properties(name: str) -> tuple[str, int] | None:
    encoded = urllib.parse.quote(name, safe="")
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded}/property/MolecularFormula,Charge/JSON"
    request = urllib.request.Request(url, headers={"User-Agent": "chem-knowledge-data-v1-audit/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.load(response)
            props = payload.get("PropertyTable", {}).get("Properties", [])
            if not props:
                return None
            formula = props[0].get("MolecularFormula")
            charge = props[0].get("Charge")
            if isinstance(formula, str) and isinstance(charge, int):
                return formula, charge
            return None
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code in {429, 500, 502, 503, 504} and attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            return None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            return None
    return None


def main() -> None:
    ions = [row for path in ION_FILES for row in load_jsonl(path)]
    outcomes: Counter[str] = Counter()
    mismatches: list[str] = []
    unresolved: list[str] = []
    for index, row in enumerate(ions, 1):
        name = row.get("name_en")
        if not isinstance(name, str) or not name:
            outcomes["missing_name"] += 1
            unresolved.append(f"{row['id']}: missing name_en")
            continue
        external = fetch_properties(name)
        if external is None:
            outcomes["unresolved"] += 1
            unresolved.append(f"{row['id']}: {name}")
        else:
            formula, charge = external
            formula_ok = parse_formula(formula) == row.get("composition")
            charge_ok = charge == row.get("charge")
            if formula_ok and charge_ok:
                outcomes["match"] += 1
            else:
                outcomes["mismatch"] += 1
                mismatches.append(
                    f"{row['id']}: name={name!r} local={row.get('formula')} charge={row.get('charge')} "
                    f"pubchem={formula} charge={charge} formula_ok={formula_ok} charge_ok={charge_ok}"
                )
        if index != len(ions):
            time.sleep(0.24)

    print("PubChem ion cross-check (diagnostic; name resolution can be ambiguous)")
    print(f"total={len(ions)} outcomes={dict(outcomes)}")
    if mismatches:
        print("MISMATCHES_REQUIRING_REVIEW:")
        for item in mismatches:
            print("  " + item)
    if unresolved:
        print("UNRESOLVED:")
        for item in unresolved:
            print("  " + item)


if __name__ == "__main__":
    main()
