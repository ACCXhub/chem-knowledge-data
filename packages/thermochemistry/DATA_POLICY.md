# Thermochemistry data policy

1. Every record carries `source_refs`; source registry entries pin URLs/commits and licensing notes.
2. Existing consolidated Species IDs are foreign keys. Formula/name matching is allowed only inside deterministic import tooling and must resolve to an explicit accepted mapping before publication.
3. Thermochemical values are never phase-agnostic. `H2O(l)` and `H2O(g)` are distinct records under the same Species identity.
4. Standard formation enthalpy is the primary educational reaction-enthalpy method when all participants have compatible phase-specific data.
5. Bond enthalpies are fallback estimates. They must carry `method = estimate_reference` or a more specific estimate method and a qualifier describing environment/averaging.
6. Source NASA polynomial values are evaluated deterministically at the recorded reference temperature. Raw source coefficients remain externally pinned rather than copied as a second canonical source corpus.
7. Unsupported or ambiguous source mappings are omitted and reported; they are not guessed from formula alone when isomers or allotropes make identity ambiguous.
8. Aqueous thermochemistry is outside the first release unless a source explicitly represents the aqueous species/standard state.
9. Phase-transition values are source/derivation specific and include transition temperature when used. No room-temperature phase difference is mislabeled as `ΔHvap`, `ΔHfus`, or `ΔHsub`.
10. Application code may cache/import these facts but does not change the data ownership or estimation hierarchy.
