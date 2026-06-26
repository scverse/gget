from __future__ import annotations

import io
import json
import time
from functools import lru_cache
from urllib.parse import quote

import pandas as pd
import requests

from .constants import G2P_API
from .utils import DEFAULT_REQUESTS_TIMEOUT, set_up_logger

logger = set_up_logger()

UNIPROT_ENTRY_URL = "https://rest.uniprot.org/uniprotkb/{accession}.json"
UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"


@lru_cache(maxsize=256)
def _resolve_gene_from_uniprot(uniprot_id: str) -> str | None:
    """Look up the primary gene symbol for a UniProt accession via the UniProt REST entry endpoint.

    Returns the gene symbol, or None if the accession is unknown or has no gene name.
    Cached so repeated `gget g2p` calls for the same protein don't re-query UniProt.
    """
    url = UNIPROT_ENTRY_URL.format(accession=quote(uniprot_id, safe=""))
    try:
        r = requests.get(url, timeout=DEFAULT_REQUESTS_TIMEOUT)
    except requests.exceptions.RequestException as e:
        logger.error(f"UniProt lookup for '{uniprot_id}' failed: {e}")
        return None
    if not r.ok:
        logger.error(
            f"UniProt lookup for '{uniprot_id}' returned HTTP {r.status_code}. "
            "Please check that this is a valid UniProt accession (e.g. 'P38398' or 'P01130-1')."
        )
        return None
    try:
        payload = r.json()
        gene = payload["genes"][0]["geneName"]["value"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        logger.error(f"UniProt returned an entry for '{uniprot_id}' but no primary gene symbol could be extracted.")
        return None
    return gene if isinstance(gene, str) and gene else None


@lru_cache(maxsize=256)
def _resolve_uniprot_from_gene(gene: str) -> tuple[str, int] | None:
    """Look up the canonical reviewed human Swiss-Prot accession for a gene symbol.

    Queries the UniProt REST search endpoint with
    `gene_exact:{gene} AND organism_id:9606 AND reviewed:true` and returns
    `(primary_accession, n_candidates)`. The candidate count lets the caller warn
    when more than one reviewed entry matched. Returns None if no reviewed entry
    was found.
    """
    params = {
        "query": f"gene_exact:{gene} AND organism_id:9606 AND reviewed:true",
        "format": "json",
        "fields": "accession",
        "size": 5,
    }
    try:
        r = requests.get(UNIPROT_SEARCH_URL, params=params, timeout=DEFAULT_REQUESTS_TIMEOUT)
    except requests.exceptions.RequestException as e:
        logger.error(f"UniProt lookup for gene '{gene}' failed: {e}")
        return None
    if not r.ok:
        logger.error(f"UniProt lookup for gene '{gene}' returned HTTP {r.status_code}.")
        return None
    try:
        results = r.json().get("results", [])
    except (json.JSONDecodeError, AttributeError):
        logger.error(f"UniProt lookup for gene '{gene}' returned invalid JSON.")
        return None
    if not results:
        return None
    first = results[0] if isinstance(results[0], dict) else {}
    accession = first.get("primaryAccession")
    if not isinstance(accession, str) or not accession:
        return None
    return accession, len(results)


def _normalize_residues(residues: object) -> set[int]:
    """Coerce a `residues` argument (int / iterable of ints / range) to a set of ints."""
    if isinstance(residues, bool):
        raise ValueError("'residues' must be an int or an iterable of ints, not a bool.")
    if isinstance(residues, int):
        return {residues}
    if isinstance(residues, (list, tuple, range, set, frozenset)):
        try:
            return {int(r) for r in residues}
        except (TypeError, ValueError) as e:
            raise ValueError(
                "'residues' must be an int or an iterable of ints "
                f"(e.g. [100, 200, 300] or range(100, 200)). Got: {residues!r}"
            ) from e
    raise ValueError(
        "'residues' must be an int or an iterable of ints "
        f"(e.g. [100, 200, 300] or range(100, 200)). Got: {residues!r}"
    )


def _g2p_get_tsv(
    url: str,
    label: str,
    retries: int = 3,
    backoff: float = 1.0,
) -> pd.DataFrame | None:
    """GET a G2P endpoint expected to return TSV. Returns a parsed DataFrame or None on any failure.

    Retries on transient failures (connection errors, timeouts, HTTP 5xx) with exponential
    backoff. Detects JSON-shaped error bodies that the G2P portal sometimes returns over
    the TSV channel with HTTP 200 (e.g. {"status":"failure","message":"No data for this gene."})
    and surfaces them as logged errors instead of letting pandas parse them as a single column.
    """
    attempts = retries + 1
    last_status: int | None = None
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            r = requests.get(url, timeout=DEFAULT_REQUESTS_TIMEOUT)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_exc = e
            last_status = None
        else:
            if r.ok:
                stripped = r.text.lstrip()
                if not stripped:
                    logger.warning(f"{label}: the Genomics 2 Proteins portal returned an empty response.")
                    return None
                if stripped[:1] in ("{", "["):
                    # JSON error body delivered over the TSV channel.
                    msg: str | None = None
                    try:
                        body = json.loads(stripped)
                    except json.JSONDecodeError:
                        body = None
                    if isinstance(body, dict):
                        m = body.get("message")
                        if isinstance(m, str):
                            msg = m
                    logger.error(
                        f"{label}: the Genomics 2 Proteins portal could not satisfy the request"
                        + (f": {msg}" if msg else ".")
                        + " Double-check that the gene symbol and UniProt accession match."
                    )
                    return None
                return pd.read_csv(io.StringIO(r.text), sep="\t")
            if r.status_code < 500:
                logger.error(
                    f"{label}: the Genomics 2 Proteins portal returned HTTP {r.status_code}. "
                    "Double-check that the gene symbol and UniProt accession match."
                )
                return None
            last_status = r.status_code
            last_exc = None

        if attempt < attempts - 1:
            delay = backoff * (2**attempt)
            reason = str(last_exc) if last_exc is not None else f"HTTP {last_status}"
            logger.warning(
                f"{label}: transient failure ({reason}); retrying in {delay:.1f}s (attempt {attempt + 2}/{attempts})."
            )
            time.sleep(delay)

    if last_exc is not None:
        logger.error(f"{label}: request failed after {attempts} attempts: {last_exc}")
    else:
        logger.error(f"{label}: returned HTTP {last_status} after {attempts} attempts.")
    return None


def g2p(
    gene: str | None = None,
    uniprot_id: str | None = None,
    resource: str = "features",
    isoform: str | None = None,
    residues: int | list[int] | tuple[int, ...] | range | set[int] | None = None,
    save: bool = False,
    out: str | None = None,
    verbose: bool = True,
) -> pd.DataFrame | None:
    """Query the Genomics 2 Proteins (G2P) portal to link genes/proteins to per-residue
    structural and functional annotations.

    Portal: https://g2p.broadinstitute.org/

    This module wraps the *public* G2P REST API (three endpoints: residue-level features,
    isoform/structure mapping, and isoform alignment). The variant overlays the portal
    shows in its web UI (gnomAD, ClinVar, HGMD) are not exposed by the public API and
    therefore not available here — query the portal directly for those.

    At least one of `gene` or `uniprot_id` is required. The other is resolved
    automatically via the UniProt REST API and cached. When resolution happens, the
    chosen pair is logged and prepended to the returned DataFrame as `Resolved Gene` /
    `Resolved UniProt` columns so it travels with the data.

    Args:
    - gene          Optional gene symbol, e.g. "BRCA1". If omitted, resolved from
                    `uniprot_id`. NOTE: gene-symbol → accession lookup is approximate
                    (gene symbols have synonyms and paralogues; the lookup picks the
                    *canonical reviewed human Swiss-Prot* entry — pass `uniprot_id`
                    explicitly for non-human organisms, unreviewed entries, or a
                    specific isoform).
    - uniprot_id    UniProt accession, e.g. "P38398". If omitted, resolved from `gene`.
                    For resource="alignment" this must be supplied explicitly as the
                    canonical isoform accession (e.g. "P01130-1"), because the
                    gene→UniProt path returns the base accession and cannot disambiguate
                    isoforms.
                    Tip: find a gene's UniProt ID with 'gget info'.
    - resource      Type of information to return (default: "features"):
                    "features":  per-residue feature table (~140 columns). Includes:
                                 AlphaFold pLDDT, DSSP secondary structure, accessible
                                 surface area, UniProt sites (active/binding/domain/...),
                                 PhosphoSitePlus PTMs, fpocket / af2bind / p2rank pocket
                                 predictions, intra/inter-chain hydrogen bonds, non-bonded
                                 interactions, disulfide bonds and salt bridges (from PDB
                                 and AlphaFold), PFES (Protein Feature Enrichment Score)
                                 and its sub-scores, and per-residue MaveDB experimental
                                 functional scores. See https://github.com/broadinstitute/g2p-bis
                                 for descriptions of each column.
                    "map":       gene -> transcript -> protein isoform -> structure map
                                 (UniProt/Ensembl/RefSeq/PDB identifiers). The
                                 comma-joined `PDB Ids` column is augmented with a
                                 parsed `PDB Ids List` column (list[str]) for direct
                                 consumption (e.g. with `gget pdb`).
                    "alignment": residue-level alignment between two isoforms (requires
                                 'isoform'; 'uniprot_id' is the canonical isoform).
    - isoform       Alternative isoform UniProt accession (e.g. "P01130-2"). Required when
                    resource="alignment" (default: None).
    - residues      Optional filter restricting the result to specific residue positions
                    (only applies to "features" and "alignment", which carry a
                    `residueId` column). Accepts an int, a list/tuple/set of ints, or a
                    range — e.g. `185`, `[185, 1775, 1812]`, `range(100, 200)`. Filtering
                    is performed client-side after fetching the full table.
    - save          If True, save the result as a CSV named
                    'gget_g2p_{gene}_{uniprot_id}_{resource}.csv' in the current working
                    directory (default: False).
    - out           Optional explicit path to write the result as CSV. Takes precedence
                    over `save` (default: None).
    - verbose       True/False whether to print progress information (default: True).

    Returns a pandas DataFrame with the requested G2P information, or None if the query
    failed (network error, invalid arguments, unknown gene/UniProt pair, or empty response).
    The resolved canonical pair is also stored on the DataFrame as
    `df.attrs["gene"]` / `df.attrs["uniprot_id"]`.
    """
    resources = ["features", "map", "alignment"]
    if resource not in resources:
        raise ValueError(f"'resource' argument specified as '{resource}'. Expected one of: {', '.join(resources)}")

    if not gene and not uniprot_id:
        raise ValueError(
            "Please provide at least one of 'gene' (e.g. 'BRCA1') or 'uniprot_id' "
            "(e.g. 'P38398'). You can find both with 'gget info'."
        )

    if resource == "alignment" and not uniprot_id:
        raise ValueError(
            "resource='alignment' requires 'uniprot_id' to be specified explicitly as the "
            "canonical isoform accession (e.g. 'P01130-1'). Gene→UniProt resolution returns "
            "the base accession and cannot disambiguate isoforms."
        )

    if resource == "alignment" and not isoform:
        raise ValueError(
            "resource='alignment' requires an alternative isoform UniProt accession as 'isoform' "
            "(e.g. 'P01130-2'). 'uniprot_id' is the canonical isoform (e.g. 'P01130-1')."
        )

    # Validate `residues` up-front (cheap, fails fast).
    residue_set: set[int] | None = _normalize_residues(residues) if residues is not None else None
    if residue_set is not None and resource == "map":
        raise ValueError(
            "The 'residues' filter does not apply to resource='map' (no per-residue table). "
            "Use it with 'features' or 'alignment'."
        )

    resolved_uniprot_from_gene = False
    resolved_gene_from_uniprot = False

    if not uniprot_id:
        if verbose:
            logger.info(f"Resolving UniProt accession for gene '{gene}' via UniProt...")
        lookup = _resolve_uniprot_from_gene(gene)  # type: ignore[arg-type]
        if not lookup:
            raise ValueError(
                f"No canonical reviewed human UniProt entry was found for gene '{gene}'. "
                "Please pass the UniProt accession explicitly via 'uniprot_id' (find it with 'gget info')."
            )
        uniprot_id, n_candidates = lookup
        resolved_uniprot_from_gene = True
        if verbose:
            extra = (
                f" ({n_candidates} reviewed candidates matched; the first was chosen)"
                if n_candidates > 1
                else ""
            )
            logger.info(
                f"Resolved gene '{gene}' → UniProt '{uniprot_id}' "
                f"(canonical reviewed human Swiss-Prot entry{extra}). "
                "Gene-symbol lookup is approximate — it picks the canonical human "
                "reviewed entry only. For non-human organisms, unreviewed entries, or "
                "a specific isoform, pass 'uniprot_id' explicitly."
            )

    if not gene:
        if verbose:
            logger.info(f"Resolving gene symbol for UniProt accession '{uniprot_id}' via UniProt...")
        gene = _resolve_gene_from_uniprot(uniprot_id)
        if not gene:
            raise ValueError(
                f"Could not resolve a gene symbol for UniProt accession '{uniprot_id}'. "
                "Please pass the gene symbol explicitly via the 'gene' argument."
            )
        resolved_gene_from_uniprot = True
        if verbose:
            logger.info(f"Resolved UniProt '{uniprot_id}' → gene '{gene}'.")

    # G2P REST API path templates:
    #   /api/gene/{gene}/protein/{uniprotId}/protein-features
    #   /api/gene/{gene}/protein/{uniprotId}/gene-transcript-protein-isoform-structure-map
    #   /api/gene/{gene}/protein/{canonicalIsoform}/{alignmentIsoform}/alignment
    gene_q = quote(gene, safe="")
    uniprot_q = quote(uniprot_id, safe="")
    base = f"{G2P_API}/gene/{gene_q}/protein/{uniprot_q}"
    if resource == "features":
        url = f"{base}/protein-features"
    elif resource == "map":
        url = f"{base}/gene-transcript-protein-isoform-structure-map"
    else:  # alignment
        assert isoform is not None  # validated above
        url = f"{base}/{quote(isoform, safe='')}/alignment"

    label = f"G2P {resource} ({gene} / {uniprot_id})"
    if verbose:
        logger.info(f"Querying the Genomics 2 Proteins portal: {label}...")

    df = _g2p_get_tsv(url, label=label)
    if df is None:
        return None

    # Augment the `map` resource with a parsed list of PDB IDs alongside the
    # comma-joined string column (so callers can pipe straight into `gget pdb`).
    if resource == "map" and "PDB Ids" in df.columns:
        pdb_lists = df["PDB Ids"].fillna("").map(
            lambda s: [p for p in str(s).split(",") if p]
        )
        df.insert(df.columns.get_loc("PDB Ids") + 1, "PDB Ids List", pdb_lists)

    # Apply the residues filter (validated above; resource is features or alignment).
    if residue_set is not None:
        if "residueId" not in df.columns:
            logger.warning(
                f"{label}: 'residues' filter requested but the response has no 'residueId' "
                "column; returning unfiltered result."
            )
        else:
            df = df[df["residueId"].isin(residue_set)].reset_index(drop=True)
            missing = sorted(residue_set - set(df["residueId"].tolist()))
            if missing and verbose:
                logger.warning(
                    f"{label}: {len(missing)} requested residue(s) not present in the response: "
                    f"{missing[:10]}{'...' if len(missing) > 10 else ''}"
                )

    # Surface the canonical pair both as pandas metadata and (when we resolved
    # something) as visible leading columns so it travels with saved files too.
    df.attrs["gene"] = gene
    df.attrs["uniprot_id"] = uniprot_id
    if resolved_uniprot_from_gene or resolved_gene_from_uniprot:
        df.insert(0, "Resolved UniProt", uniprot_id)
        df.insert(0, "Resolved Gene", gene)

    out_path: str | None = out if out else (f"gget_g2p_{gene}_{uniprot_id}_{resource}.csv" if save else None)
    if out_path:
        df.to_csv(out_path, index=False)
        if verbose:
            logger.info(f"Results saved as {out_path}.")

    return df
