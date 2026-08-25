#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

JSONL_FILES = [
    DATA / "element_scope.jsonl",
    DATA / "v1" / "element_scope.ext.jsonl",
    DATA / "ions.jsonl",
    DATA / "v1" / "ions.ext.jsonl",
    DATA / "substances.jsonl",
    DATA / "v1" / "substances.01.ext.jsonl",
    DATA / "v1" / "substances.02.ext.jsonl",
    DATA / "v1" / "substances.03.ext.jsonl",
    DATA / "reactions.jsonl",
    DATA / "v1" / "reactions.01.ext.jsonl",
    DATA / "v1" / "reactions.02.ext.jsonl",
    DATA / "v1" / "reactions.03.ext.jsonl",
    DATA / "phenomena.jsonl",
    DATA / "v1" / "phenomena.ext.jsonl",
    DATA / "experiments.jsonl",
    DATA / "v1" / "experiments.ext.jsonl",
    DATA / "concepts.jsonl",
    DATA / "v1" / "concepts.ext.jsonl",
    DATA / "v1" / "exam_tags.jsonl",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n",
        encoding="utf-8",
    )


def add_alias(row: dict[str, Any], value: str) -> None:
    aliases = row.setdefault("aliases", [])
    if value not in aliases:
        aliases.append(value)


def add_reaction_type(row: dict[str, Any], value: str) -> None:
    types = row.setdefault("reaction_types", [])
    if value not in types:
        types.append(value)


def add_related_reaction(row: dict[str, Any], value: str) -> None:
    ids = row.setdefault("related_reaction_ids", [])
    if value not in ids:
        ids.append(value)


def patch_record(row: dict[str, Any]) -> None:
    rid = row.get("id")

    if rid == "substance:phosphorus":
        row["name_zh"] = "白磷（四原子磷）"
        row["name_en"] = "tetraphosphorus"
        add_alias(row, "磷（P4）")
        add_alias(row, "白磷")
        row["notes"] = "本记录对应高中方程式中以 P4 表示的四原子磷/白磷教学物种，不代表磷的全部同素异形体。"

    elif rid == "substance:silicic-acid":
        row["name_en"] = "metasilicic acid"
        add_alias(row, "silicic acid")
        row["notes"] = "高中教学常以 H2SiO3 表示硅酸，本记录对应 metasilicic acid 教学表示；实际水溶液硅酸体系可更复杂。"

    elif rid == "substance:phosphorus-pentoxide":
        row["name_en"] = "tetraphosphorus decaoxide"
        add_alias(row, "phosphorus pentoxide")
        add_alias(row, "phosphorus(V) oxide")
        row["notes"] = "P4O10 为分子式；P2O5 是常用经验式。高中中文传统名称“五氧化二磷”保留为教学别名。"

    elif rid == "substance:ammonium-phosphate":
        row["name_en"] = "triammonium phosphate"
        add_alias(row, "ammonium phosphate, tribasic")
        row["notes"] = "本记录明确对应 (NH4)3PO4；泛称 ammonium phosphate 可能指不同酸式铵盐。"

    elif rid == "substance:hydrogen-chromate":
        row["aqueous_behavior"] = "acid_equilibrium"
        row["notes"] = "H2CrO4 水溶液存在酸解离及铬酸根/重铬酸根平衡；不发布单一固定离子拆写投影。"

    elif rid == "substance:hydrogen-dichromate":
        row["aqueous_behavior"] = "acid_equilibrium"
        row["notes"] = "H2Cr2O7/重铬酸体系在水溶液中与铬酸根物种存在条件相关平衡；不发布单一固定离子拆写投影。"

    elif rid == "substance:iron-iii-thiocyanate":
        row["teaching_priority"] = "extended"
        row["notes"] = "Fe(SCN)3 仅保留为历史高中分子式简化表示；Fe3+ 与 SCN- 的显色教学默认使用 [FeSCN]2+ 平衡反应，不将本记录作为主要水溶液真实物种。"

    elif rid == "ion:thiosulfate":
        row["name_en"] = "thiosulfate ion"
        add_alias(row, "thiosulfate(2-)")

    elif rid == "ion:peroxide":
        row["name_en"] = "peroxide ion"
        add_alias(row, "peroxide(2-)")

    elif rid == "ion:silicate":
        row["name_en"] = "metasilicate teaching ion"
        add_alias(row, "metasilicate")
        add_alias(row, "偏硅酸根")
        row["notes"] = "高中教学中常以 SiO3^2- 表示偏硅酸根/硅酸盐单元；真实硅酸盐可具有聚合结构，本记录是教学级离子表示。"

    elif rid in {
        "reaction:chlorine-water",
        "reaction:haber-ammonia",
        "reaction:sulfur-dioxide-oxidation",
    }:
        add_reaction_type(row, "equilibrium")

    elif rid == "reaction:fecl3-kscn":
        row["name_zh"] = "铁(III)离子与硫氰酸根显色平衡"
        row["reactants"] = [
            {"species_id": "ion:iron-iii", "coefficient": 1, "phase": "aq"},
            {"species_id": "ion:thiocyanate", "coefficient": 1, "phase": "aq"},
        ]
        row["products"] = [
            {"species_id": "ion:thiocyanatoiron-iii", "coefficient": 1, "phase": "aq"},
        ]
        row["reaction_types"] = ["complex_formation", "qualitative_test", "equilibrium"]
        row["conditions"] = []
        row["net_ionic"] = {
            "reactants": [
                {"species_id": "ion:iron-iii", "coefficient": 1, "phase": "aq"},
                {"species_id": "ion:thiocyanate", "coefficient": 1, "phase": "aq"},
            ],
            "products": [
                {"species_id": "ion:thiocyanatoiron-iii", "coefficient": 1, "phase": "aq"},
            ],
        }
        row["reversible"] = True
        row["notes"] = "采用高中定性分析常用的 Fe3+ + SCN- ⇌ [FeSCN]2+ 教学简化；实际溶液可含多种硫氰酸根配合物。"

    elif rid == "experiment:halogen-displacement-series":
        row["delivery_mode"] = "teacher_demo"
        row["safety_notes_zh"] = [
            "涉及氯/溴体系，按教师微量演示与通风要求执行；避免学生直接接触或吸入卤素。"
        ]

    elif rid == "phenomenon:baso4-precipitate":
        add_related_reaction(row, "reaction:baoh2-h2so4")

    elif rid in {"concept:precipitation", "concept:ionic-reaction", "concept:neutralization"}:
        add_related_reaction(row, "reaction:baoh2-h2so4")


def main() -> None:
    found: set[str] = set()
    for path in JSONL_FILES:
        rows = read_jsonl(path)
        before = json.dumps(rows, ensure_ascii=False, sort_keys=True)
        for row in rows:
            rid = row.get("id")
            patch_record(row)
            if rid in {
                "substance:phosphorus",
                "substance:silicic-acid",
                "substance:phosphorus-pentoxide",
                "substance:ammonium-phosphate",
                "substance:hydrogen-chromate",
                "substance:hydrogen-dichromate",
                "substance:iron-iii-thiocyanate",
                "ion:thiosulfate",
                "ion:peroxide",
                "ion:silicate",
                "reaction:chlorine-water",
                "reaction:haber-ammonia",
                "reaction:sulfur-dioxide-oxidation",
                "reaction:fecl3-kscn",
                "experiment:halogen-displacement-series",
                "phenomenon:baso4-precipitate",
                "concept:precipitation",
                "concept:ionic-reaction",
                "concept:neutralization",
            }:
                found.add(rid)
        after = json.dumps(rows, ensure_ascii=False, sort_keys=True)
        if before != after:
            write_jsonl(path, rows)

    required = {
        "substance:phosphorus",
        "substance:silicic-acid",
        "substance:phosphorus-pentoxide",
        "substance:ammonium-phosphate",
        "substance:hydrogen-chromate",
        "substance:hydrogen-dichromate",
        "substance:iron-iii-thiocyanate",
        "ion:thiosulfate",
        "ion:peroxide",
        "ion:silicate",
        "reaction:chlorine-water",
        "reaction:haber-ammonia",
        "reaction:sulfur-dioxide-oxidation",
        "reaction:fecl3-kscn",
        "experiment:halogen-displacement-series",
        "phenomenon:baso4-precipitate",
    }
    missing = sorted(required - found)
    if missing:
        raise SystemExit("missing expected records: " + ", ".join(missing))

    print("v1.0.1 record corrections applied")


if __name__ == "__main__":
    main()
