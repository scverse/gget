from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import urlopen

from .utils import set_up_logger

logger = set_up_logger()

from .constants import RCSB_PDB_API  # noqa: E402


def pdb(pdb_id: str, resource: str = "pdb", identifier: str | int | None = None, save: bool = False) -> Any:
    """Query RCSB PDB for the protein structutre/metadata of a given PDB ID.

    Args:
    - pdb_id        PDB ID to be queried (str), e.g. "7S7U".
    - resource      Defines type of information to be returned.
                    "pdb": Returns the protein structure in legacy PDB format (default).
                           Note: the legacy PDB format is being phased out by RCSB and is
                           not available for large structures. When the legacy PDB file does
                           not exist, gget automatically falls back to the PDBx/mmCIF format.
                    "mmcif": Returns the protein structure in PDBx/mmCIF format (.cif).
                    "entry": Information about PDB structures at the top level of PDB structure hierarchical data organization.
                    "pubmed": Get PubMed annotations (data integrated from PubMed) for a given entry's primary citation.
                    "assembly": Information about PDB structures at the quaternary structure level.
                    "branched_entity": Get branched entity description (define entity ID as "identifier").
                    "nonpolymer_entity": Get non-polymer entity data (define entity ID as "identifier").
                    "polymer_entity": Get polymer entity data (define entity ID as "identifier").
                    "uniprot": Get UniProt annotations for a given macromolecular entity (define entity ID as "identifier").
                    "branched_entity_instance": Get branched entity instance description (define chain ID as "identifier").
                    "polymer_entity_instance": Get polymer entity instance (a.k.a chain) data (define chain ID as "identifier").
                    "nonpolymer_entity_instance": Get non-polymer entity instance description (define chain ID as "identifier").
    -  identifier   Can be used to define assembly, entity or chain ID if applicable (default: None).
                    Assembly/entity IDs are numbers (e.g. 1), and chain IDs are letters (e.g. "A").
    - save          True/False wether to save JSON/PDB with query results in the current working directory (default: False).

    Returns requested information in JSON format (except for resource="pdb"/"mmcif" which
    return the protein structure in PDB/PDBx-mmCIF format).
    """
    # Resources that download a structure file (text), not JSON
    structure_resources = ["pdb", "mmcif"]

    # Check if resource argument is valid
    resources = [
        "pdb",
        "mmcif",
        "entry",
        "pubmed",
        "assembly",
        "branched_entity",
        "nonpolymer_entity",
        "polymer_entity",
        "uniprot",
        "branched_entity_instance",
        "polymer_entity_instance",
        "nonpolymer_entity_instance",
    ]
    if resource not in resources:
        raise ValueError(f"'resource' argument specified as {resource}. Expected one of: {', '.join(resources)}")

    # Check if required identifiers are present
    if resource == "assembly" and identifier is None:
        raise ValueError("Please define assembly ID (e.g. '1') as 'identifier'.")

    need_entity_id = [
        "branched_entity",
        "nonpolymer_entity",
        "polymer_entity",
        "uniprot",
    ]
    if resource in need_entity_id and identifier is None:
        raise ValueError("Please define entity ID (e.g. '1') as 'identifier'.")

    need_chain_id = [
        "branched_entity_instance",
        "nonpolymer_entity_instance",
        "polymer_entity_instance",
    ]
    if resource in need_chain_id and identifier is None:
        raise ValueError("Please define chain ID (e.g. 'A') as 'identifier'.")

    # Define URLs for HTTP request.
    # Each entry is (url, fetched_format) so we can track which structure format
    # was actually returned ("pdb"/"mmcif"/None for JSON resources).
    urls: list[tuple[str, str | None]]

    if resource not in structure_resources:
        # URLs to request resources other than a structure file
        if identifier is not None:
            url = f"{RCSB_PDB_API}{resource}/{pdb_id}/{identifier}"
        else:
            url = f"{RCSB_PDB_API}{resource}/{pdb_id}"

        urls = [(url, None)]  # only one option for JSON resources
    elif resource == "mmcif":
        # PDBx/mmCIF file
        urls = [(f"https://files.rcsb.org/download/{pdb_id}.cif", "mmcif")]
    else:
        # Legacy PDB format: try wwPDB first, then RCSB, then automatically
        # fall back to PDBx/mmCIF (legacy PDB is unavailable for large structures).
        urls = [
            (f"https://files.wwpdb.org/download/{pdb_id}.pdb", "pdb"),
            (f"https://files.rcsb.org/download/{pdb_id}.pdb", "pdb"),
            (f"https://files.rcsb.org/download/{pdb_id}.cif", "mmcif"),
        ]

    # Submit URL request with fallback logic
    r = None
    code = None
    fetched_format = None
    for url, fmt in urls:
        try:
            r = urlopen(url)

            # Get status code (in a way that is stable across Python versions)
            code = getattr(r, "status", None)
            if code is None:
                code = r.getcode()

            if code == 200:
                fetched_format = fmt
                break
        except HTTPError:
            continue

    if r is None or code != 200:
        if resource == "assembly":
            logger.error(
                f"{resource} for {pdb_id} assembly {identifier} was not found. Please double-check arguments and try again."
            )
        elif resource in need_entity_id:
            logger.error(
                f"{resource} for {pdb_id} entity {identifier} was not found. Please double-check arguments and try again."
            )
        elif resource in need_chain_id:
            logger.error(
                f"{resource} for {pdb_id} chain {identifier} was not found. Please double-check arguments and try again."
            )
        else:
            logger.error(f"{resource} for {pdb_id} was not found. Please double-check arguments and try again.")
        return

    if resource not in structure_resources:
        # Read json formatted results
        results = json.load(r)

        # Sort list-valued ID fields for deterministic output
        ids = (results.get("rcsb_assembly_container_identifiers") or {}).get("interface_ids")
        if ids is not None:
            ids.sort()
    else:
        # Read structure file (PDB or PDBx/mmCIF)
        results = r.read().decode()

        # Inform the user if a legacy PDB request was served as mmCIF instead
        if resource == "pdb" and fetched_format == "mmcif":
            logger.warning(
                f"The legacy PDB format is not available for {pdb_id} (it is being phased out "
                f"by RCSB). Returning the PDBx/mmCIF format instead. "
                f"Use resource='mmcif' to request it directly and silence this warning."
            )

    if save:
        if resource not in structure_resources:
            # Save the results in json format
            if identifier is not None:
                out_name = f"{pdb_id}_{identifier}_{resource}.json"
            else:
                out_name = f"{pdb_id}_{resource}.json"

            with open(out_name, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)

        else:
            # Save the structure file using the extension of the format actually fetched
            extension = "cif" if fetched_format == "mmcif" else "pdb"
            with open(f"{pdb_id}.{extension}", "w") as f:
                f.write(results)

    return results
