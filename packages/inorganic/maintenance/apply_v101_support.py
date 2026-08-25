#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n",
        encoding="utf-8",
    )


def ensure_reaction_link(path: Path, concept_ids: set[str], reaction_id: str) -> None:
    rows = read_jsonl(path)
    changed = False
    for row in rows:
        if row.get("id") in concept_ids:
            links = row.setdefault("related_reaction_ids", [])
            if reaction_id not in links:
                links.append(reaction_id)
                changed = True
    if changed:
        write_jsonl(path, rows)


def patch_solubility() -> None:
    path = ROOT / "rules" / "solubility.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = "1.0.1"
    rules = data["rules"]

    # The generic v1 alkali shortcut was too broad for Li2CO3. Keep Na/K as the
    # high-school broad soluble shortcut and represent lithium carbonate explicitly.
    for rule in rules:
        if rule.get("id") == "sol:alkali":
            rule["match"]["cation_any"] = ["ion:sodium", "ion:potassium"]
            rule["summary_zh"] = "高中常见钠盐、钾盐通常可溶；锂盐按具体阴离子规则判断。"
        elif rule.get("id") == "sol:carbonate":
            for exception in rule.get("exceptions_by_cation", []):
                exception["cation_any"] = [
                    item for item in exception.get("cation_any", []) if item != "ion:lithium"
                ]
            rule["summary_zh"] = "多数碳酸盐难溶；Na+、K+、NH4+ 的常见碳酸盐可溶，Li2CO3 溶解度较低，单独按微溶规则处理。"

    if not any(rule.get("id") == "sol:lithium-carbonate" for rule in rules):
        lithium_rule = {
            "id": "sol:lithium-carbonate",
            "match": {"cation": "ion:lithium", "anion": "ion:carbonate"},
            "result": "sparingly_soluble",
            "summary_zh": "Li2CO3 在水中的溶解度较低，不套用一般碱金属盐可溶的简化结论。",
        }
        carbonate_index = next(i for i, rule in enumerate(rules) if rule.get("id") == "sol:carbonate")
        rules.insert(carbonate_index, lithium_rule)

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_manifest() -> None:
    path = ROOT / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = "1.0.1-rc1"
    data["status"] = "audit_candidate"
    data["record_counts"]["reactions"] = 152
    data["total_records"] = 641
    reaction_files = data["canonical_files"]["reactions"]
    new_file = "data/v1/reactions.04.ext.jsonl"
    if new_file not in reaction_files:
        reaction_files.append(new_file)
    notes = data.setdefault("notes", [])
    audit_note = "v1.0.1 audit candidate adds independent schema/semantic/formula audits and targeted chemistry corrections before final consolidation release."
    if audit_note not in notes:
        notes.append(audit_note)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_validation_file_lists() -> None:
    paths = [
        ROOT / "validation" / "validate_v1.py",
        ROOT / "validation" / "audit_v1.py",
        ROOT / "validation" / "audit_semantics_v1.py",
    ]
    needle = '        DATA / "v1" / "reactions.03.ext.jsonl",\n'
    replacement = needle + '        DATA / "v1" / "reactions.04.ext.jsonl",\n'
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if 'reactions.04.ext.jsonl' not in text:
            if needle not in text:
                raise SystemExit(f"could not patch reaction file list in {path}")
            text = text.replace(needle, replacement, 1)
            path.write_text(text, encoding="utf-8")

    schema_audit = ROOT / "validation" / "audit_jsonschema_v1.py"
    text = schema_audit.read_text(encoding="utf-8")
    needle2 = '    DATA / "v1" / "reactions.03.ext.jsonl",\n'
    replacement2 = needle2 + '    DATA / "v1" / "reactions.04.ext.jsonl",\n'
    if 'reactions.04.ext.jsonl' not in text:
        if needle2 not in text:
            raise SystemExit("could not patch reaction file list in audit_jsonschema_v1.py")
        schema_audit.write_text(text.replace(needle2, replacement2, 1), encoding="utf-8")


def patch_status() -> None:
    path = ROOT / "STATUS.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("**State:** `READY_FOR_CONSOLIDATION`", "**State:** `AUDIT_CANDIDATE`")
    text = text.replace("**Release:** `1.0.0`", "**Release:** `1.0.1-rc1`")
    text = text.replace("- 151 first-class reactions", "- 152 first-class reactions")
    text = text.replace("- **640 canonical records total**", "- **641 canonical records total**")
    if "## Post-release audit" not in text:
        text += (
            "\n## Post-release audit\n\n"
            "v1.0.0 之后执行了独立公式/组成、最简计量系数、JSON Schema、语义覆盖和 PubChem 诊断交叉检查。"
            "当前 rc1 在 audit 分支收敛命名歧义、平衡分类、一个非最简系数问题、Li2CO3 溶解性规则和核心 Ba(OH)2 反应覆盖。"
            "通过最终 CI 与人工复核后再恢复 READY_FOR_CONSOLIDATION。\n"
        )
    path.write_text(text, encoding="utf-8")


def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("151", "152") if "151" in text else text
    text = text.replace("640", "641") if "640" in text else text
    path.write_text(text, encoding="utf-8")


def main() -> None:
    ensure_reaction_link(
        DATA / "concepts.jsonl",
        {"concept:acid-base-neutralization", "concept:ionic-reaction", "concept:net-ionic-equation", "concept:precipitation"},
        "reaction:baoh2-h2so4",
    )
    patch_solubility()
    patch_manifest()
    patch_validation_file_lists()
    patch_status()
    patch_readme()
    print("v1.0.1 support updates applied")


if __name__ == "__main__":
    main()
