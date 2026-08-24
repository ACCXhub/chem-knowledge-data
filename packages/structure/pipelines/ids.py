"""Deterministic source-neutral identifiers for the Structure track."""

from __future__ import annotations

import uuid

STRUCTURE_NAMESPACE = uuid.UUID("c9d2c469-8557-5661-ae35-950cde95e61f")


def _uuid5(name: str) -> str:
    return str(uuid.uuid5(STRUCTURE_NAMESPACE, name))


def structure_id_from_inchi(standard_inchi: str) -> str:
    if not standard_inchi.startswith("InChI=1S/"):
        raise ValueError("Structure identity requires a Standard InChI beginning with InChI=1S/")
    return "str_" + _uuid5("inchi:" + standard_inchi)


def structure_id_from_fallback(*, structure_scope: str, normalized_representation: str, formal_charge: int) -> str:
    if not structure_scope.strip():
        raise ValueError("structure_scope is required")
    if not normalized_representation.strip():
        raise ValueError("normalized_representation is required")
    key = f"fallback:{structure_scope.strip()}|{normalized_representation.strip()}|charge:{formal_charge}"
    return "str_" + _uuid5(key)


def link_id(*, requester_track: str, substance_ref: str, structure_id: str, relation: str) -> str:
    key = f"link:{requester_track}|{substance_ref}|{structure_id}|{relation}"
    return "slink_" + _uuid5(key)


def request_id(*, requester_track: str, local_entity_ref: str) -> str:
    key = f"request:{requester_track}|{local_entity_ref}"
    return "sreq_" + _uuid5(key)
