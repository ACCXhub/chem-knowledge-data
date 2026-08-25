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
SUBSTANCE_FILES = [
    DATA / "substances.jsonl",
    DATA / "v1" / "substances.01.ext.jsonl",
    DATA / "v1" / "substances.02.ext.jsonl",
    DATA / "v1" / "substances.03.ext.jsonl",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_formula(formula: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for symbol, digits in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        counts[symbol] = counts.get(symbol, 0) + (int(digits) if digits else 1)
    return counts


def fetch_formula(name: str) -> str | None:
    encoded = urllib.parse.quote(name, safe="")
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded}/property/MolecularFormula/JSON"
    request = urllib.request.Request(url, headers={"User-Agent": "chem-knowledge-data-v1-audit/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.load(response)
            props = payload.get("PropertyTable", {}).get("Properties", [])
            if not props:
                return None
            return props[0].get("MolecularFormula")
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
    substances = [row for path in SUBSTANCE_FILES for row in load_jsonl(path)]
    outcomes: Counter[str] = Counter()
    mismatches: list[str] = []
    unresolved: list[str] = []

    for index, row in enumerate(substances, 1):
        name = row.get("name_en")
        if not isinstance(name, str) or not name:
            outcomes["missing_name"] += 1
            unresolved.append(f"{row['id']}: missing name_en")
            continue
        external_formula = fetch_formula(name)
        if external_formula is None:
            outcomes["unresolved"] += 1
            unresolved.append(f"{row['id']}: {name}")
        else:
            external_composition = parse_formula(external_formula)
            if external_composition == row.get("composition"):
                outcomes["composition_match"] += 1
            else:
                outcomes["composition_mismatch"] += 1
                mismatches.append(
                    f"{row['id']}: name={name!r} local={row.get('formula')} composition={row.get('composition')} "
                    f"pubchem={external_formula} composition={external_composition}"
                )
        # Keep comfortably below PubChem's interactive request rate.
        if index != len(substances):
            time.sleep(0.24)

    print("PubChem substance cross-check (diagnostic; name resolution can be ambiguous)")
    print(f"total={len(substances)} outcomes={dict(outcomes)}")
    if mismatches:
        print("MISMATCHES_REQUIRING_REVIEW:")
        for item in mismatches:
            print("  " + item)
    if unresolved:
        print("UNRESOLVED:")
        for item in unresolved:
            print("  " + item)

    # Diagnostic only: mismatches must be reviewed manually because PubChem name resolution
    # may resolve another allotrope, hydration state, or mixture. Never auto-rewrite canonical data.


if __name__ == "__main__":
    main()
