# Source-to-consolidated mapping

This matrix tracks how current source-package fields converge into the future consumer release. It is intentionally source-aware: source schemas stay unchanged and unresolved gaps remain explicit until the owning package publishes a stable boundary.

## Species mapping

| Consolidated responsibility | Inorganic source | Organic source | Structure source | Consolidation rule |
|---|---|---|---|---|
| source identity | `species.id` | `substance.id` | n/a | preserve as source ID in crosswalk |
| global identity | n/a | n/a | n/a | assign one persistent consolidated ID after duplicate resolution |
| entity kind | `entity_type` = ion/substance | implicit substance | `structure_scope` is structure semantics, not species kind | source species kind wins; Structure never reclassifies species |
| Chinese name | `name_zh` | `name_zh` | n/a | preserve preferred reviewed label plus source variants |
| English name | `name_en` | `name_en` | n/a | same |
| formula | `formula` | `formula` | `molecular_formula` | species package value remains species fact; Structure is strong consistency evidence when linked |
| charge | `charge` | neutral unless later source field says otherwise | `formal_charge` | ions require explicit charge; Structure charge is validation/link evidence |
| elemental composition | `composition` | not currently required | derivable for supported published structures | keep source composition; derive only in generated projection with method provenance |
| chemistry category | `category` | organic `category` enum | n/a | map into chemical classification + separate high-school teaching projection |
| aliases | `aliases_zh` | `aliases` | n/a | normalize for search projection without replacing canonical label |
| teaching priority | `teaching_priority` | `teaching_priority` | n/a | preserve `core/common/extended` |
| verification | `status` | `verification_status` | `validation.status/review_status` | retain source-specific status; derive integration status separately |
| provenance | `source_refs` | `provenance_refs` | `provenance[]` | aggregate additively; never collapse to one generic source string |
| external IDs | future/source-specific | `external_ids` | `external_ids[]` | normalize to namespace/value pairs and use as matching evidence |
| structure link | future explicit link or consolidation match | `structure_ref` placeholder | `structure-link` | accepted Structure link is authoritative relation; do not copy Structure identity into species ID |

## Structure-link resolution

Resolution order:

1. accepted explicit `structure-link` or an explicit package cross-reference;
2. exact authoritative external ID match with compatible entity semantics;
3. exact published Standard InChIKey for molecular entities;
4. reviewed formula + charge + structure-scope match for simple ions/formula units;
5. otherwise unresolved.

Formula-only matching is not used for organic molecules because structural isomers can share formulas.

## High-school teaching projection

Source chemistry categories are not used directly as the final UI taxonomy.

The generated consumer projection maps species to one primary high-school category:

- `elemental_substance`
- `cation`
- `anion`
- `acid`
- `base`
- `salt`
- `oxide`
- `organic`
- `other`

Orthogonal facts such as `gas`, `precipitate`, `sparingly_soluble`, `strong_electrolyte`, `weak_electrolyte`, and `volatile` stay tags/behavioral data rather than becoming competing primary categories.

The initial Equation Lab palette order is generated from teaching priority + primary category + mode suitability. User pinning, manual order, recency, and usage frequency remain application preferences outside this repository.

## Search projection

Generated search tokens include only normalized projections of source facts:

- Chinese name;
- Chinese aliases;
- English name/aliases when available;
- plain formula tokens;
- stable external IDs where useful;
- teaching category/tags.

Rendered typography (`SO₄²⁻`) is UI output. Canonical data remains formula `SO4` + charge `-2`.

## Reaction mapping

Organic Reaction remains a first-class entity.

Participant resolution:

- `substance_ref` resolves through the organic-source crosswalk;
- `external_species_key` must resolve to a consolidated species before publication;
- `formula_literal` is temporary evidence only and must not become a new species implicitly when identity is ambiguous;
- reactant/product/catalyst roles and coefficients are retained;
- symbolic coefficients such as `n` remain valid for polymerization where source semantics require them;
- conditions, Phenomenon, Experiment, and Concept references remain typed references.

A consolidated reaction is publishable only when every required participant has a resolved species identity or an explicitly supported non-species role. Reaction is never converted into pairwise species edges.

## Current open integration gaps

These remain intentionally open while `packages/inorganic/` is active:

- final inorganic substance/reaction coverage;
- authoritative inorganic category vocabulary beyond the current free-form `category` field;
- aqueous dissociation/solubility/electrolyte rules needed for ionic-equation mode-aware ranking;
- cross-package duplicate set between inorganic and organic edge cases (for example salts with organic anions);
- final set of accepted `structure-link` records for source species;
- serialization details for the first consumer release.

These gaps do not block contract work. They block only the first published consolidated release.
