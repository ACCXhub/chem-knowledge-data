"""Small PubChem PUG REST fetcher for evidence staging.

This script never writes canonical records. It only emits source evidence JSON.
Respect PubChem throttling and keep request rate conservative.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request

PROPERTY_LIST = "MolecularFormula,Charge,ConnectivitySMILES,SMILES,InChI,InChIKey"


def fetch_cid(cid: str, *, retries: int = 4, min_interval: float = 0.25) -> dict:
    cid = str(cid).strip()
    if not cid.isdigit():
        raise ValueError("CID must be numeric")
    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
        + urllib.parse.quote(cid, safe="")
        + "/property/"
        + PROPERTY_LIST
        + "/JSON"
    )
    delay = min_interval
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "chem-knowledge-data/structure-evidence"})
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.load(response)
                props = payload["PropertyTable"]["Properties"]
                if len(props) != 1:
                    raise RuntimeError(f"Expected exactly one property record for CID {cid}")
                time.sleep(min_interval)
                return {
                    "source_id": "pubchem",
                    "record_locator": f"CID {cid}",
                    "source_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
                    "payload": props[0],
                }
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 503} or attempt >= retries:
                raise
            retry_after = exc.headers.get("Retry-After")
            if retry_after:
                try:
                    delay = max(delay, float(retry_after))
                except ValueError:
                    pass
            time.sleep(delay)
            delay = min(delay * 2, 8.0)
    raise RuntimeError("unreachable")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cid", nargs="+", help="One or more PubChem CIDs")
    args = parser.parse_args()
    for cid in args.cid:
        print(json.dumps(fetch_cid(cid), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
