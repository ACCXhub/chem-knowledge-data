# Source → consolidated mapping

本文件记录当前五个源包到 consumer release 的具体映射。源包 schema 保持不变；统一发生在 generated artifacts 中。

当前稳定发布：`consolidated-1.1.0`。

## 1. Species

| Consumer field | Inorganic | Organic | Structure Registry | Rule |
|---|---|---|---|---|
| source identity | `id` | `id` | n/a | 保留 package + source ID |
| entity kind | `kind=ion/substance` | substance | `structure_scope` | species source 决定；Structure 不重新分类 species |
| name_zh | `name_zh` | `name_zh` | n/a | 保留 reviewed/source label |
| name_en | `name_en` | `name_en` | n/a | 可空 |
| formula | `formula` | `formula` | `molecular_formula` | source species value 为主；linked Structure 用于一致性核验 |
| charge | ion `charge`；substance 默认 0 | 默认 0 | `formal_charge` | linked Structure 仅作核验 |
| composition | `composition` | generator 解析普通分子式；symbolic polymer 可空 | 可派生 | source-supported 优先 |
| aliases | `aliases` | `aliases` | n/a | 统一为去重数组 |
| classification | `category` + `aqueous_behavior` | `category` | n/a | chemical classification 与 teaching projection 分离 |
| teaching priority | `teaching_priority` | `teaching_priority` | n/a | `core/common/extended` |
| verification | `review_status` | `verification_status` | `validation.*` | source state 与 integration state 分开 |
| provenance | `sources` | `provenance_refs` | `provenance[]` | 加 package namespace 后聚合 |
| external IDs | 暂无统一 canonical 字段 | `identity_crossrefs.yaml` | `external_ids[]` | 归一为 namespace/value |
| structure link | accepted `links/inorganic.jsonl` | accepted `links/organic.jsonl` | owns target | 复用 accepted link；历史 source ID 迁移只走 reviewed bridge |

## 2. Consumer ID 与 crosswalk

默认 consumer species ID 由 source package + source ID 稳定生成。跨包重复不会因为 formula/name 相同自动 merge。

`identity_overrides.yaml` 只用于 reviewed merge/deprecation。若未来两个已发布 consumer IDs 被确认同一实体：

- 选一个既有 ID 作为 survivor；
- 另一个 source ID crosswalk 改指 survivor；
- 旧 consumer ID 进入迁移/弃用记录；
- provenance 不丢失。

## 3. Structure links

输入只来自：

- `packages/structure_registry/data/links/inorganic.jsonl`
- `packages/structure_registry/data/links/organic.jsonl`

仅 `status=accepted` 可进入 consumer `structure_links.jsonl`，且 target 必须是 published Structure。

若 accepted link 的 `entity_ref` 属于 Structure Registry 冻结输入中的历史 source ID，而当前冻结业务包已经完成稳定 ID 迁移，允许在 reviewed historical bridge 下映射到当前 source ID。当前 release 有且仅有三条该类桥接：

- `ion:copper-2` → `ion:copper-ii`
- `ion:iron-2` → `ion:iron-ii`
- `ion:iron-3` → `ion:iron-iii`

桥接通过相同 Structure target、对应 formal charge/价态、formula/composition 与原 cross-track evidence 核验，原 `source_link_id` 保留。因此当前 release 对 Structure Registry 的 **69/69 accepted links** 完整对账，没有静默跳过 accepted link。

Organic v0.2 中仍残留的历史说明字符串 `packages/structure` 被视为旧 owner 名称，不作为有效 target path；当前 canonical owner 始终是 `packages/structure_registry/`。

## 4. Teaching projection

### Primary category

Inorganic：

- ion charge > 0 → `cation`
- ion charge < 0 → `anion`
- `simple_substance` → `elemental_substance`
- `acid` → `acid`
- `base` → `base`
- `salt` → `salt`
- `oxide` → `oxide`
- 其他 → `other`

Organic substance → `organic`。

### Tags

可从 source-supported 字段生成：

- inorganic `category`
- `aqueous_behavior`
- `ambient_phase`
- organic detailed category / functional-group refs

`gas`、`strong_electrolyte`、`insoluble` 等只作为 tags。

### Equation mode

- neutral inorganic/organic substances：molecular 优先；ionic/net-ionic available/deemphasized 由 aqueous behavior 决定；
- ions：ionic / net-ionic 优先，molecular deemphasized；
- strong aqueous electrolytes：molecular available，同时允许 importer 根据无机规则产生 ionic projection；
- weak/insoluble/equilibrium species 不因 `ions` 字段被自动拆写。

默认 Palette rank 由 `teaching_priority` + primary category + source stable order 生成；运行时使用频率不写入数据包。

## 5. Reaction

### Inorganic

- `reactants/products[].species_id` → inorganic source crosswalk
- `net_ionic` 同样解析
- `reaction_types`、phase、conditions、phenomenon IDs、reversible、teaching priority、sources 保留

### Organic

- `substance_ref` → organic source crosswalk
- `external_species_key=inorganic:<slug>` → 优先 `substance:<slug>`，若不存在再检查 `ion:<slug>`
- `formula_literal` 仅用于 display/evidence
- `reaction_class` 映射为 consumer `reaction_types`
- symbolic coefficient（如聚合反应中的 `n`）原样保留

任何必需 participant 无法解析时写入 `unresolved_findings.jsonl`，该 Reaction 不进入 ready-for-import gate。

发布审计进一步在映射完成后复核可数值反应的元素与总电荷守恒；net ionic 独立复核。Symbolic polymer、transformation-only 与明确 non-discrete material 场景单独分类，不强行套普通 fixed-coefficient 守恒器。

## 6. Non-species knowledge

不同领域不强行压成一个业务 schema，而是使用统一 envelope：

```text
consumer_id
source_package
source_type
source_id
name_zh/title_zh
teaching_priority
provenance_refs
payload
```

`payload` 保存源包 reviewed record；因此 Concept、Phenomenon、Experiment、FunctionalGroup、ChemicalClass、ExamTag 和 structural chemistry 的教学模型/关系都能在单一 release 中消费，同时不丢领域字段。

## 7. Resolved knowledge links

`knowledge_links.jsonl` 从 Structural Chemistry reviewed records 生成 bounded navigation projection：原子排布以 atomic number + symbol 链接 element；显式 relation/model/concept refs 链接 knowledge；`data/structural_knowledge_links.yaml` 中人工审核且唯一可辩护的 identity resolution 链接 consumer species，并在该 species 已有 accepted Structure 时增加 Structure target。Formula-only、同分异构体、多晶型、水合物、配位实体与 polymer cases 不做猜测式链接。

当前 176 条 link 包含 36 element、125 knowledge、10 species 与 5 Structure targets。

## 8. Thermochemistry

`thermochemistry-v0.1.0` 只经 pinned consolidated input 消费，映射为四个 typed artifacts：

- `species_phase_facts.jsonl`：species identity、standard phase、allowed teaching phases、reference conditions；
- `species_thermochemistry.jsonl`：species + phase + temperature + standard pressure 唯一键及 nullable thermochemical quantities；
- `phase_transitions.jsonl`：species、transition、from/to phase、enthalpy、conditions/provenance；
- `bond_enthalpies.jsonl`：教育用途 bond/environment/order reference 与 estimate qualifier。

所有 species refs 必须解析到现有 consumer species。Phase 不生成新 species；例如 H2O(g) 与 H2O(l) 是同一 water species 的两条 phase-specific records。

## 9. Rules 与 curriculum

- Inorganic 7 个 rule sets 复制到 consumer release 的 `rules/`，保持原 JSON 语义；其中 `equation_composer.json` 是 Equation Lab 候选/组合基础。
- Inorganic curriculum coverage、Organic curriculum coverage、Structural Chemistry curriculum coverage 统一打包到 `curriculum/`，但保留 source package namespace。
- 发布审计验证 rule 中的 species / reaction / experiment / phenomenon 引用均能解析到冻结源包的 published records。

## 10. Findings policy

以下项目允许进入 informational/review finding，但不会被自动“修掉”：

- formula/name 相同但缺少强 identity evidence 的跨包 duplicate candidate；
- Structure Registry 明确 deferral 的 organic entity；
- 新源包字段尚未进入 consumer mapping；
- source provenance 出现互相矛盾的值。

必需 Reaction participant 未解析、accepted Structure target 不存在、accepted link 无法解释、crosswalk 冲突、source freeze 漂移、守恒失败或引用悬空属于 blocking error。

`consolidated-1.1.0` 最终为 13 informational findings、0 review findings、0 blocking findings。
