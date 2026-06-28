from __future__ import annotations

import json as json_package
from typing import Any, Literal, overload

import pandas as pd
import requests

from .constants import (
    DEFAULT_REQUESTS_TIMEOUT,
    RUMMAGENE_GRAPHQL_URL,
    RUMMAGEO_GRAPHQL_URL,
)
from .utils import set_up_logger

logger = set_up_logger()

# Column order for the returned data frames
_RUMMAGENE_COLUMNS = [
    "rank",
    "term",
    "n_overlap",
    "n_genes_in_set",
    "odds_ratio",
    "pval",
    "adj_pval",
]
_RUMMAGEO_COLUMNS = [
    "rank",
    "term",
    "species",
    "n_overlap",
    "n_genes_in_set",
    "odds_ratio",
    "pval",
    "adj_pval",
]


def _clean_genes(genes: str | list[Any]) -> list[str]:
    """Normalize the genes argument into a clean list of gene symbol strings."""
    if isinstance(genes, str):
        genes = [genes]

    genes_clean = []
    for gene in genes:
        # Skip NaNs/Nones/empty strings
        if gene is None or (isinstance(gene, float)):
            continue
        gene_str = str(gene).strip()
        if gene_str == "" or gene_str.lower() == "nan":
            continue
        genes_clean.append(gene_str)

    if len(genes_clean) == 0:
        raise ValueError("Please provide at least one gene symbol in the 'genes' argument.")

    return genes_clean


def _rummage_enrich(
    source: str,
    url: str,
    genes: str | list[Any],
    limit: int = 50,
    filter_term: str | None = None,
    json: bool = False,
    save: bool = False,
    verbose: bool = True,
) -> pd.DataFrame | list[dict[str, Any]] | None:
    """Shared enrichment helper for the Rummagene and RummaGEO GraphQL APIs.

    Both services expose the same `currentBackground { enrich(...) }` entry point;
    they differ only in the per-result gene set selection (Rummagene returns a
    `geneSets` connection, RummaGEO a single `geneSet` with a `species` field).
    """
    genes_clean = _clean_genes(genes)

    # The two APIs differ in how each enrichment result exposes its gene set(s)
    if source == "rummagene":
        result_selection = "geneSets { nodes { term nGeneIds } }"
        columns = _RUMMAGENE_COLUMNS
    else:
        result_selection = "geneSet { term nGeneIds species }"
        columns = _RUMMAGEO_COLUMNS

    query = (
        "query ($genes: [String]!, $first: Int, $filterTerm: String) {"
        "  currentBackground {"
        "    enrich(genes: $genes, first: $first, filterTerm: $filterTerm) {"
        "      totalCount"
        f"      nodes {{ pvalue adjPvalue oddsRatio nOverlap {result_selection} }}"
        "    }"
        "  }"
        "}"
    )
    variables: dict[str, Any] = {"genes": genes_clean}
    if limit is not None:
        variables["first"] = int(limit)
    if filter_term is not None and str(filter_term).strip() != "":
        variables["filterTerm"] = str(filter_term)

    if verbose:
        logger.info(f"Querying {source} with {len(genes_clean)} genes...")

    try:
        response = requests.post(
            url,
            json={"query": query, "variables": variables},
            timeout=DEFAULT_REQUESTS_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"The {source} server request failed: {exc}") from exc

    if not response.ok:
        raise RuntimeError(
            f"The {source} server returned error status code {response.status_code}. "
            "Please try again later and/or report this issue if it persists."
        )

    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(f"The {source} GraphQL API returned an error: {payload['errors']}")

    enrich = ((payload.get("data") or {}).get("currentBackground") or {}).get("enrich") or {}
    nodes = enrich.get("nodes") or []

    rows = []
    for node in nodes:
        base = {
            "n_overlap": node.get("nOverlap"),
            "odds_ratio": node.get("oddsRatio"),
            "pval": node.get("pvalue"),
            "adj_pval": node.get("adjPvalue"),
        }
        if source == "rummagene":
            gene_sets = (node.get("geneSets") or {}).get("nodes") or []
            for gene_set in gene_sets:
                rows.append(
                    {
                        "term": gene_set.get("term"),
                        "n_genes_in_set": gene_set.get("nGeneIds"),
                        **base,
                    }
                )
        else:
            gene_set = node.get("geneSet") or {}
            rows.append(
                {
                    "term": gene_set.get("term"),
                    "species": gene_set.get("species"),
                    "n_genes_in_set": gene_set.get("nGeneIds"),
                    **base,
                }
            )

    if len(rows) == 0:
        logger.warning(
            f"No {source} gene sets found for the provided genes. "
            "Please double-check the gene symbols (HGNC symbols are expected)."
        )
        return None

    # Honor 'limit' as the number of returned results
    if limit is not None:
        rows = rows[: int(limit)]

    results_df = pd.DataFrame(rows)
    # Add 1-based rank and enforce column order
    results_df.insert(0, "rank", range(1, len(results_df) + 1))
    results_df = results_df[columns]

    if json:
        results_dict = json_package.loads(results_df.to_json(orient="records"))
        if save:
            with open(f"gget_{source}_results.json", "w", encoding="utf-8") as f:
                json_package.dump(results_dict, f, ensure_ascii=False, indent=4)
        return results_dict

    if save:
        results_df.to_csv(f"gget_{source}_results.csv", index=False)

    return results_df


@overload
def rummagene(
    genes: str | list[str],
    limit: int = 50,
    filter_term: str | None = None,
    save: bool = False,
    verbose: bool = True,
    *,
    json: Literal[True],
) -> list[dict[str, Any]] | None: ...


@overload
def rummagene(
    genes: str | list[str],
    limit: int = 50,
    filter_term: str | None = None,
    save: bool = False,
    verbose: bool = True,
    json: Literal[False] = False,
) -> pd.DataFrame | None: ...


def rummagene(
    genes: str | list[str],
    limit: int = 50,
    filter_term: str | None = None,
    save: bool = False,
    verbose: bool = True,
    json: bool = False,
) -> pd.DataFrame | list[dict[str, Any]] | None:
    """Find gene sets from PMC supplementary tables that overlap a query gene set using Rummagene.

    Performs gene set enrichment against the ~1M gene sets that Rummagene
    automatically extracted from supplementary tables of PubMed Central (PMC)
    articles (https://rummagene.com/).

    Args:
     - genes        List of gene symbols (HGNC) to query, e.g. ["STAT1", "IRF1"].
                    A single gene may be passed as a string.
     - limit        Maximum number of enriched gene sets to return. Default: 50.
     - filter_term  If provided, only return gene sets whose term contains this
                    (case-insensitive) substring. Default: None.
     - save         If True, save the results in the current working directory. Default: False.
     - verbose      True/False whether to print progress information. Default: True.
     - json         If True, returns results in json format instead of data frame. Default: False.

    Returns a data frame (or list of dicts if json=True) with the matching gene sets
    ranked by p-value, including the gene set term, overlap size, odds ratio, and
    (adjusted) p-values from a Fisher's exact test. Returns None if no overlap is found.
    """
    return _rummage_enrich(
        source="rummagene",
        url=RUMMAGENE_GRAPHQL_URL,
        genes=genes,
        limit=limit,
        filter_term=filter_term,
        json=json,
        save=save,
        verbose=verbose,
    )


@overload
def rummageo(
    genes: str | list[str],
    limit: int = 50,
    filter_term: str | None = None,
    save: bool = False,
    verbose: bool = True,
    *,
    json: Literal[True],
) -> list[dict[str, Any]] | None: ...


@overload
def rummageo(
    genes: str | list[str],
    limit: int = 50,
    filter_term: str | None = None,
    save: bool = False,
    verbose: bool = True,
    json: Literal[False] = False,
) -> pd.DataFrame | None: ...


def rummageo(
    genes: str | list[str],
    limit: int = 50,
    filter_term: str | None = None,
    save: bool = False,
    verbose: bool = True,
    json: bool = False,
) -> pd.DataFrame | list[dict[str, Any]] | None:
    """Find gene sets from GEO studies that overlap a query gene set using RummaGEO.

    Performs gene set enrichment against the gene sets that RummaGEO automatically
    extracted from differential-expression signatures of Gene Expression Omnibus
    (GEO) studies (https://rummageo.com/).

    Args:
     - genes        List of gene symbols (HGNC/MGI) to query, e.g. ["STAT1", "IRF1"].
                    A single gene may be passed as a string.
     - limit        Maximum number of enriched gene sets to return. Default: 50.
     - filter_term  If provided, only return gene sets whose term contains this
                    (case-insensitive) substring. Default: None.
     - save         If True, save the results in the current working directory. Default: False.
     - verbose      True/False whether to print progress information. Default: True.
     - json         If True, returns results in json format instead of data frame. Default: False.

    Returns a data frame (or list of dicts if json=True) with the matching gene sets
    ranked by p-value, including the gene set term, the species, overlap size, odds
    ratio, and (adjusted) p-values from a Fisher's exact test. Returns None if no
    overlap is found.
    """
    return _rummage_enrich(
        source="rummageo",
        url=RUMMAGEO_GRAPHQL_URL,
        genes=genes,
        limit=limit,
        filter_term=filter_term,
        json=json,
        save=save,
        verbose=verbose,
    )
