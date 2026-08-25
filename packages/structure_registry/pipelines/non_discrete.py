"""Normalization helpers for non-molecular Structure scopes."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from rdkit import Chem, rdBase
from rdkit.Chem import inchi

from ids import structure_id_from_fallback, structure_id_from_inchi
from normalize_rdkit import hill_formula_no_charge


@dataclass(frozen=True)
class NonDiscreteStructure:
    structure_id: str
    structure_scope: str
    molecular_formula: str
    formal_charge: int
    standard_inchi: str | None = None
    standard_inchikey: str | None = None
    repeat_unit_smiles: str | None = None
    attachment_point_count: int | None = None
    toolkit_version: str = rdBase.rdkitVersion


def normalize_formula_unit(source_smiles: str) -> NonDiscreteStructure:
    mol = Chem.MolFromSmiles(source_smiles, sanitize=True)
    if mol is None:
        raise ValueError(f"invalid formula-unit source SMILES: {source_smiles!r}")
    standard_inchi = inchi.MolToInchi(mol)
    if not standard_inchi.startswith("InChI=1S/"):
        raise ValueError("formula unit did not produce Standard InChI")
    return NonDiscreteStructure(
        structure_id=structure_id_from_inchi(standard_inchi),
        structure_scope="formula_unit",
        molecular_formula=hill_formula_no_charge(mol),
        formal_charge=sum(atom.GetFormalCharge() for atom in mol.GetAtoms()),
        standard_inchi=standard_inchi,
        standard_inchikey=inchi.InchiToInchiKey(standard_inchi),
    )


def _repeat_unit_formula(mol: "Chem.Mol") -> str:
    """Return a Hill formula for the chemical repeat unit, excluding dummy attachment atoms."""
    with_h = Chem.AddHs(mol)
    counts = Counter(atom.GetSymbol() for atom in with_h.GetAtoms() if atom.GetAtomicNum() != 0)
    if "C" in counts:
        order = ["C"]
        if "H" in counts:
            order.append("H")
        order.extend(sorted(symbol for symbol in counts if symbol not in {"C", "H"}))
    else:
        order = sorted(counts)
    return "".join(symbol + (str(counts[symbol]) if counts[symbol] != 1 else "") for symbol in order)


def normalize_repeat_unit(repeat_unit_smiles: str) -> NonDiscreteStructure:
    mol = Chem.MolFromSmiles(repeat_unit_smiles, sanitize=True)
    if mol is None:
        raise ValueError(f"invalid repeat-unit SMILES: {repeat_unit_smiles!r}")
    attachment_points = sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() == 0)
    if attachment_points != 2:
        raise ValueError("polymer repeat unit requires exactly two attachment points")
    normalized = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)
    charge = sum(atom.GetFormalCharge() for atom in mol.GetAtoms())
    return NonDiscreteStructure(
        structure_id=structure_id_from_fallback(
            structure_scope="polymer_repeat_unit",
            normalized_representation=normalized,
            formal_charge=charge,
        ),
        structure_scope="polymer_repeat_unit",
        molecular_formula=_repeat_unit_formula(mol),
        formal_charge=charge,
        repeat_unit_smiles=normalized,
        attachment_point_count=attachment_points,
    )
