"""RDKit-backed normalization helpers for canonical structure records.

RDKit is a processing tool here, not an authority source.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

try:
    from rdkit import Chem, rdBase
    from rdkit.Chem import Descriptors, Lipinski, inchi
except ImportError as exc:
    raise RuntimeError("RDKit is required for structure normalization. Install the validation requirements.") from exc

from ids import structure_id_from_inchi, structure_id_from_fallback


@dataclass(frozen=True)
class NormalizedStructure:
    structure_id: str
    structure_scope: str
    molecular_formula: str
    formal_charge: int
    canonical_smiles: str
    isomeric_smiles: str
    standard_inchi: str
    standard_inchikey: str
    derived: dict[str, Any]


def hill_formula_no_charge(mol: "Chem.Mol") -> str:
    """Return Hill-ordered element counts with ionic charge omitted."""
    with_h = Chem.AddHs(mol)
    counts = Counter(atom.GetSymbol() for atom in with_h.GetAtoms())
    if "C" in counts:
        order = ["C"]
        if "H" in counts:
            order.append("H")
        order.extend(sorted(symbol for symbol in counts if symbol not in {"C", "H"}))
    else:
        order = sorted(counts)
    return "".join(symbol + (str(counts[symbol]) if counts[symbol] != 1 else "") for symbol in order)


def normalize_smiles(smiles: str, *, structure_scope: str) -> NormalizedStructure:
    mol = Chem.MolFromSmiles(smiles, sanitize=True)
    if mol is None:
        raise ValueError(f"RDKit could not parse/sanitize SMILES: {smiles!r}")

    canonical = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=False)
    isomeric = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)
    standard_inchi = inchi.MolToInchi(mol)
    if not standard_inchi.startswith("InChI=1S/"):
        raise ValueError("RDKit did not produce a Standard InChI")
    standard_inchikey = inchi.InchiToInchiKey(standard_inchi)
    formal_charge = sum(atom.GetFormalCharge() for atom in mol.GetAtoms())

    return NormalizedStructure(
        structure_id=structure_id_from_inchi(standard_inchi),
        structure_scope=structure_scope,
        molecular_formula=hill_formula_no_charge(mol),
        formal_charge=formal_charge,
        canonical_smiles=canonical,
        isomeric_smiles=isomeric,
        standard_inchi=standard_inchi,
        standard_inchikey=standard_inchikey,
        derived={
            "heavy_atom_count": int(Descriptors.HeavyAtomCount(mol)),
            "total_atom_count": int(Chem.AddHs(mol).GetNumAtoms()),
            "exact_mass": round(float(Descriptors.ExactMolWt(mol)), 6),
            "molecular_weight": round(float(Descriptors.MolWt(mol)), 6),
            "rotatable_bond_count": int(Lipinski.NumRotatableBonds(mol)),
            "hydrogen_bond_donor_count": int(Lipinski.NumHDonors(mol)),
            "hydrogen_bond_acceptor_count": int(Lipinski.NumHAcceptors(mol)),
            "toolkit": "RDKit",
            "toolkit_version": rdBase.rdkitVersion,
        },
    )


def identity_for_non_discrete(*, structure_scope: str, normalized_representation: str, formal_charge: int) -> str:
    return structure_id_from_fallback(structure_scope=structure_scope, normalized_representation=normalized_representation, formal_charge=formal_charge)
