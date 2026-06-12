import io
import json as json_package

import pandas as pd
import requests

from .constants import DEFAULT_REQUESTS_TIMEOUT
from .utils import set_up_logger

logger = set_up_logger()

# ------------------------------
# Base URLs
# ------------------------------
BASE = "https://eightcubedb.onrender.com/"
SPECIFICITY_URL = BASE + "specificity"
PSI_BLOCK_URL = BASE + "psi_block"
GENE_EXPR_URL = BASE + "gene_expression"


# ------------------------------
# Utility
# ------------------------------
def _convert_to_df(response_text, endpoint_name):
    """Convert CSV response → DataFrame with error checking."""
    try:
        return pd.read_csv(io.StringIO(response_text))
    except Exception as e:
        raise RuntimeError(f"API '{endpoint_name}' returned non-CSV data: {e}\nResponse:\n{response_text}") from e


def _save_output(df_or_json, name, json=False, verbose=True):
    """Save to CSV or JSON."""
    if json:
        fname = name + ".json"
        with open(fname, "w", encoding="utf-8") as f:
            json_package.dump(df_or_json, f, ensure_ascii=False, indent=4)
    else:
        fname = name + ".csv"
        df_or_json.to_csv(fname, index=False)

    if verbose:
        logger.info(f"Saved results to {fname}")


def _normalize_gene_list(gene_list):
    """Normalize gene list (strip whitespace only; preserve Ensembl versions)."""
    return [g.strip() for g in gene_list]


# --------------------------------------------------------------------
# 1. SPECIFICITY
# --------------------------------------------------------------------
def specificity(
    gene_list,
    json=False,
    save=False,
    verbose=True,
):
    """Retrieve gene-level specificity statistics from the 8cubeDB.

    (https://eightcubedb.onrender.com/).

    This endpoint returns ψ (psi) and ζ (zeta) specificity metrics for one
    or more genes across all partitions of the dataset. Gene identifiers
    may be Entrez symbols or Ensembl IDs (any case; Ensembl version numbers
    are preserved).

    Args:
    - gene_list      List of gene identifiers (symbols or Ensembl IDs).
                     Example: ["Akr1c21"] or ["ENSMUSG00000021207.10"].
    - json           If True, return results as a JSON-compatible list of
                     dictionaries instead of a pandas DataFrame. Default: False.
    - save           If True, save results to the local directory as
                     gget_8cube_specificity.csv (or .json if json=True).
    - verbose        If True, print progress information. Default: True.

    Returns
    -------
    A pandas DataFrame or JSON list containing:
    - gene_name
    - ensembl_id
    - Analysis_level
    - Analysis_type
    - Psi_mean, Psi_std
    - Zeta_mean, Zeta_std

    Raises
    ------
    - ValueError     If gene_list is not a list.
    - RuntimeError   If the API request fails or returns invalid data.

    """
    if not isinstance(gene_list, (list, tuple)):
        raise ValueError("`gene_list` must be a list.")

    processed = _normalize_gene_list(gene_list)

    # Build query params
    params = [("gene_list", g) for g in processed]

    if verbose:
        logger.info(f"Fetching specificity for {len(processed)} genes…")

    r = requests.get(SPECIFICITY_URL, params=params, timeout=DEFAULT_REQUESTS_TIMEOUT)
    if not r.ok:
        raise RuntimeError(f"Specificity request failed ({r.status_code}): {r.text}")

    df = _convert_to_df(r.text, "specificity")

    if json:
        obj = json_package.loads(df.to_json(orient="records"))
        if save:
            _save_output(obj, "gget_8cube_specificity", json=True)
        return obj

    if save:
        _save_output(df, "gget_8cube_specificity")

    return df


# --------------------------------------------------------------------
# 2. PSI BLOCK
# --------------------------------------------------------------------
def psi_block(
    gene_list,
    analysis_level,
    analysis_type,
    json=False,
    save=False,
    verbose=True,
):
    """Retrieve ψ_block (psi-block) specificity scores from the 8cubeDB.

    ψ_block quantifies the specificity of a gene to a particular block
    within a partition. This endpoint supports block-wise
    retrieval for individual genes.

    Args:
    - gene_list      List of genes to query (symbols or Ensembl IDs).
    - analysis_level Biological level (e.g., "Across_tissues", "Kidney").
    - analysis_type  Partition design (e.g., "Sex:Strain", "Sex:Celltype").
    - json           If True, return JSON-compatible output instead of DataFrame.
    - save           If True, save output locally as gget_8cube_psiblock.csv
                     or .json if json=True.
    - verbose        If True, print progress information. Default: True.

    Returns
    -------
    A pandas DataFrame or JSON list containing ψ_block scores for each block
    label in the partition (e.g., "Male:NZOJ", "Female:B6J", etc.).

    Raises
    ------
    - ValueError     If gene_list is not a list.
    - RuntimeError   If the API request fails.

    """
    if not isinstance(gene_list, (list, tuple)):
        raise ValueError("`gene_list` must be a list.")

    processed = _normalize_gene_list(gene_list)

    params = [
        ("analysis_level", analysis_level),
        ("analysis_type", analysis_type),
    ] + [("gene_list", g) for g in processed]

    if verbose:
        logger.info(f"Fetching ψ-block scores for {len(processed)} genes ({analysis_level}, {analysis_type})…")

    r = requests.get(PSI_BLOCK_URL, params=params, timeout=DEFAULT_REQUESTS_TIMEOUT)
    if not r.ok:
        raise RuntimeError(f"ψ-block request failed ({r.status_code}): {r.text}")

    df = _convert_to_df(r.text, "psi_block")

    if json:
        obj = json_package.loads(df.to_json(orient="records"))
        if save:
            _save_output(obj, "gget_8cube_psiblock", json=True)
        return obj

    if save:
        _save_output(df, "gget_8cube_psiblock")

    return df


# --------------------------------------------------------------------
# 3. GENE EXPRESSION
# --------------------------------------------------------------------
def gene_expression(
    gene_list,
    analysis_level,
    analysis_type,
    json=False,
    save=False,
    verbose=True,
):
    """Retrieve normalized gene expression values from 8cubeDB.

    This endpoint returns mean and variance of normalized expression for the
    specified gene(s), computed over the selected partition. For example:
    Kidney × Sex:Celltype, Across_tissues × Strain, etc.

    Args:
    - gene_list      List of gene symbols or Ensembl IDs to retrieve.
                     Example: ["ENSMUSG00000030945.18"].
    - analysis_level Biological level (e.g., "Across_tissues", "Kidney").
    - analysis_type  Partition design (e.g., "Sex:Strain", "Sex:Celltype").
    - json           If True, return JSON-compatible structure instead of DataFrame.
    - save           If True, save results as gget_8cube_expression.csv
                     or .json if json=True.
    - verbose        If True, print progress information.

    Returns
    -------
    A pandas DataFrame or JSON list with expression values and metadata for
    each partition block (columns vary depending on analysis_type).

    Raises
    ------
    - ValueError     If gene_list is not a list.
    - RuntimeError   If the API request fails or returns invalid/empty data.

    """
    if not isinstance(gene_list, (list, tuple)):
        raise ValueError("`gene_list` must be a list.")

    processed = _normalize_gene_list(gene_list)

    params = [
        ("analysis_level", analysis_level),
        ("analysis_type", analysis_type),
    ] + [("gene_list", g) for g in processed]

    if verbose:
        logger.info(f"Fetching expression data for {len(processed)} genes ({analysis_level}, {analysis_type})…")

    r = requests.get(GENE_EXPR_URL, params=params, timeout=DEFAULT_REQUESTS_TIMEOUT)
    if not r.ok:
        raise RuntimeError(f"Gene expression request failed ({r.status_code}): {r.text}")

    df = _convert_to_df(r.text, "gene_expression")

    if json:
        obj = json_package.loads(df.to_json(orient="records"))
        if save:
            _save_output(obj, "gget_8cube_expression", json=True)
        return obj

    if save:
        _save_output(df, "gget_8cube_expression")

    return df
