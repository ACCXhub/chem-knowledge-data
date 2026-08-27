# Thermochemistry package contract

## Owns

- phase facts attached to an existing consolidated species identity;
- standard thermochemical quantities for an existing species in a specified phase;
- phase-transition enthalpy records;
- bond-enthalpy reference values with explicit estimation semantics;
- provenance and reference conditions for those facts.

## References, but does not own

- `species_id`: `packages/consolidated/` / application `knowledge_catalog`;
- `structure_id`: `packages/structure_registry/`;
- Reaction identity and participants: consolidated Reaction data / application reaction owners.

## Stable consumer keys

- phase fact: `species_id`;
- thermochemistry: `(species_id, phase, temperature_k, standard_pressure_bar)`;
- phase transition: `(species_id, transition, from_phase, to_phase)`;
- bond enthalpy: `(atom1, atom2, bond_order, environment_key)`.

## Phases

Canonical phase codes in this package are `s`, `l`, `g`, `aq`.

`standard_phase` means the preferred standard-state phase near the record's stated reference conditions. `allowed_teaching_phases` is a presentation/composition capability, not a claim that all listed phases are stable at every temperature and pressure.

## Thermochemistry semantics

`delta_f_h_kj_mol`, `delta_f_g_kj_mol`, `s_j_mol_k`, and `cp_j_mol_k` are phase-specific. Missing values remain null/absent rather than being silently replaced by a different phase or an estimate.

## Bond energetics semantics

Bond-enthalpy records are educational gas-phase/atomization reference estimates. Consumers may use them only as a fallback when a phase-specific formation-enthalpy calculation is unavailable. Results must be labeled estimated.
