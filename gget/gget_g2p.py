from __future__ import annotations

import io
import pandas as pd
import requests

from .constants import G2P_API
from .utils import set_up_logger, DEFAULT_REQUESTS_TIMEOUT

logger = set_up_logger()


def g2p(
    gene: str,
    uniprot_id: str,
    resource: str = "features",
    isoform: str | None = None,
    save: bool = False,
    verbose: bool = True,
) -> pd.DataFrame | None:
    """
    Query the Genomics 2 Proteins (G2P) portal (https://g2p.broadinstitute.org/) to link
    genes/proteins to per-residue structural and functional annotations.

    Args:
    - gene          Gene symbol, e.g. "BRCA1" (str).
    - uniprot_id    UniProt accession, e.g. "P38398" (str). For resource="alignment" this is the
                    canonical isoform accession (e.g. "P01130-1").
                    Tip: find a gene's UniProt ID with 'gget info'.
    - resource      Type of information to return (default: "features"):
                    "features":  per-residue feature table (AlphaFold pLDDT, UniProt sites,
                                 secondary structure, predicted pockets, PTMs, etc.).
                    "map":       gene -> transcript -> protein isoform -> structure map
                                 (UniProt/Ensembl/RefSeq/PDB identifiers).
                    "alignment": residue-level alignment between two isoforms (requires 'isoform';
                                 'uniprot_id' is the canonical isoform).
    - isoform       Alternative isoform UniProt accession (e.g. "P01130-2"). Required when
                    resource="alignment" (default: None).
    - save          If True, save the result as a CSV in the current working directory (default: False).
    - verbose       True/False whether to print progress information (default: True).

    Returns a pandas DataFrame with the requested G2P information.
    """
    resources = ["features", "map", "alignment"]
    if resource not in resources:
        raise ValueError(
            f"'resource' argument specified as {resource}. Expected one of: {', '.join(resources)}"
        )

    if not uniprot_id:
        raise ValueError(
            "Please provide a UniProt accession as 'uniprot_id' (e.g. 'P38398'). "
            "You can find the UniProt ID for a gene using 'gget info'."
        )

    if resource == "alignment" and not isoform:
        raise ValueError(
            "resource='alignment' requires an alternative isoform UniProt accession as 'isoform' "
            "(e.g. 'P01130-2'). 'uniprot_id' is the canonical isoform (e.g. 'P01130-1')."
        )

    # The G2P REST API returns tab-separated values
    base = f"{G2P_API}/gene/{gene}/protein/{uniprot_id}"
    if resource == "features":
        url = f"{base}/protein-features"
    elif resource == "map":
        url = f"{base}/gene-transcript-protein-isoform-structure-map"
    else:  # alignment
        url = f"{base}/{isoform}/alignment"

    if verbose:
        logger.info(
            f"Querying the Genomics 2 Proteins portal ('{resource}') for {gene} / {uniprot_id}..."
        )

    try:
        r = requests.get(
            url,
            timeout=DEFAULT_REQUESTS_TIMEOUT,
            headers={"Accept": "text/tab-separated-values"},
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to the Genomics 2 Proteins portal failed: {e}")
        return

    if not r.ok:
        logger.error(
            f"G2P query (gene='{gene}', uniprot_id='{uniprot_id}', resource='{resource}') "
            f"returned status code {r.status_code}. Please double-check that the gene symbol "
            f"and UniProt accession match, then try again."
        )
        return

    if not r.text.strip():
        logger.warning(
            "The Genomics 2 Proteins portal returned an empty result for this query."
        )
        return pd.DataFrame()

    df = pd.read_csv(io.StringIO(r.text), sep="\t")

    if save:
        out_name = f"gget_g2p_{gene}_{uniprot_id}_{resource}.csv"
        df.to_csv(out_name, index=False)
        if verbose:
            logger.info(f"Results saved as {out_name}.")

    return df
