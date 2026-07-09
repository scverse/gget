from __future__ import annotations

import json as json_package
from typing import Any, Literal, overload

import pandas as pd
import requests

from .constants import ALLIANCE_URL, DEFAULT_REQUESTS_TIMEOUT
from .utils import set_up_logger

logger = set_up_logger()

# Columns returned when fetching a single gene by its Alliance ID
_GENE_COLUMNS = [
    "id",
    "symbol",
    "name",
    "species",
    "taxon",
    "gene_type",
    "synonyms",
    "data_provider",
]
# Columns returned for a free-text search
_SEARCH_COLUMNS = [
    "id",
    "symbol",
    "name",
    "species",
    "category",
    "so_term_name",
]

# Friendly category names -> Alliance search API category values
_CATEGORY_MAP = {
    "gene": "gene_search_result",
    "allele": "allele_search_result",
    "disease": "disease_search_result",
    "go": "go_search_result",
    "variant": "variant_search_result",
    "model": "model",
}

# Recognized Alliance/model-organism-database gene ID (curie) prefixes
_GENE_ID_PREFIXES = {
    "HGNC",
    "MGI",
    "RGD",
    "ZFIN",
    "FB",
    "WB",
    "SGD",
    "ENSEMBL",
    "XENBASE",
    "WORMBASE",
    "FLYBASE",
}


def _is_gene_id(term: str) -> bool:
    """Return True if 'term' looks like an Alliance gene ID (e.g. HGNC:1101)."""
    if ":" not in term:
        return False
    prefix = term.split(":", 1)[0].upper()
    return prefix in _GENE_ID_PREFIXES


def _alliance_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """GET a JSON object from the Alliance of Genome Resources REST API."""
    url = f"{ALLIANCE_URL}{path}"
    try:
        response = requests.get(
            url,
            params=params,
            headers={"Accept": "application/json"},
            timeout=DEFAULT_REQUESTS_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"The Alliance server request failed: {exc}") from exc

    if response.status_code == 404:
        raise ValueError(f"Alliance returned 404 (not found) for '{path}'. Please double-check the gene ID.")
    if not response.ok:
        raise RuntimeError(
            f"The Alliance server returned error status code {response.status_code}. Please try again later."
        )

    return response.json()


def _text(value: Any) -> Any:
    """Extract display text from an Alliance {displayText/formatText} object."""
    if isinstance(value, dict):
        return value.get("displayText") or value.get("formatText")
    return value


def _gene_row(gene: dict[str, Any]) -> dict[str, Any]:
    """Flatten an Alliance gene object into a row of scalar values."""
    taxon = gene.get("taxon") or {}
    species = taxon.get("name") if isinstance(taxon, dict) else None
    taxon_curie = taxon.get("curie") if isinstance(taxon, dict) else None

    gene_type = gene.get("geneType")
    gene_type_name = gene_type.get("name") if isinstance(gene_type, dict) else gene_type

    data_provider = gene.get("dataProvider")
    provider = data_provider.get("abbreviation") if isinstance(data_provider, dict) else data_provider

    synonyms = [_text(s) for s in (gene.get("geneSynonyms") or [])]

    return {
        "id": gene.get("primaryExternalId"),
        "symbol": _text(gene.get("geneSymbol")),
        "name": _text(gene.get("geneFullName")),
        "species": species,
        "taxon": taxon_curie,
        "gene_type": gene_type_name,
        "synonyms": synonyms,
        "data_provider": provider,
    }


def _search_row(r: dict[str, Any]) -> dict[str, Any]:
    """Flatten an Alliance search result into a row of scalar values."""
    return {
        "id": r.get("id"),
        "symbol": r.get("symbol"),
        "name": r.get("name"),
        "species": r.get("species"),
        "category": r.get("category"),
        "so_term_name": r.get("soTermName"),
    }


@overload
def alliance(
    search_term: str,
    category: str = "gene",
    limit: int = 10,
    save: bool = False,
    verbose: bool = True,
    *,
    json: Literal[True],
) -> list[dict[str, Any]] | None: ...


@overload
def alliance(
    search_term: str,
    category: str = "gene",
    limit: int = 10,
    save: bool = False,
    verbose: bool = True,
    json: Literal[False] = False,
) -> pd.DataFrame | None: ...


def alliance(
    search_term: str,
    category: str = "gene",
    limit: int = 10,
    save: bool = False,
    verbose: bool = True,
    json: bool = False,
) -> pd.DataFrame | list[dict[str, Any]] | None:
    """Query the Alliance of Genome Resources (https://www.alliancegenome.org/).

    Two modes, chosen automatically from 'search_term':
      - If 'search_term' is an Alliance gene ID (e.g. "HGNC:1101", "MGI:109337",
        "RGD:2219", "ZFIN:...", "FB:...", "WB:...", "SGD:..."), the gene is fetched
        and its details are returned.
      - Otherwise, 'search_term' is used as a free-text query against the Alliance
        search endpoint and the matching objects of the given 'category' are returned.

    Args:
     - search_term  Alliance gene ID (curie) or a free-text search term.
     - category     Category for free-text searches: one of "gene", "allele",
                    "disease", "go", "variant", "model", or None/"all" for no filter.
                    Default: "gene".
     - limit        Maximum number of results for free-text searches. Default: 10.
     - save         If True, save the results table as csv/json in the working directory. Default: False.
     - verbose      True/False whether to print progress information. Default: True.
     - json         If True, returns results in json format instead of data frame. Default: False.

    Returns a data frame (or list of dicts if json=True) of gene details or search
    results. Returns None if no results are found.
    """
    if search_term is None or str(search_term).strip() == "":
        raise ValueError("Please provide a gene ID or search term in 'search_term'.")

    term = str(search_term).strip()
    source = "alliance_search"

    if _is_gene_id(term):
        if verbose:
            logger.info(f"Fetching Alliance gene {term}...")
        obj = _alliance_get(f"/gene/{term}")
        gene = obj.get("gene") if isinstance(obj, dict) else None
        if not gene:
            logger.warning(f"No Alliance gene found for '{term}'.")
            return None
        source = "alliance_gene"
        results_df = pd.DataFrame([_gene_row(gene)], columns=_GENE_COLUMNS)
    else:
        params: dict[str, Any] = {"q": term, "limit": limit}
        if category is not None and str(category).lower() not in ("all", ""):
            cat_key = str(category).lower()
            if cat_key not in _CATEGORY_MAP:
                logger.warning(
                    f"Unknown category '{category}'; expected one of {sorted(_CATEGORY_MAP)} (or 'all'). "
                    "Passing it to the Alliance API as-is, which may return no results."
                )
            params["category"] = _CATEGORY_MAP.get(cat_key, category)
        if verbose:
            logger.info(f"Searching Alliance for '{term}' (category={category})...")
        data = _alliance_get("/search", params=params)
        rows = [_search_row(r) for r in data.get("results", [])]
        results_df = pd.DataFrame(rows, columns=_SEARCH_COLUMNS)

    if len(results_df) == 0:
        logger.warning(f"No Alliance results found for '{term}'.")
        return None

    if json:
        results_dict = json_package.loads(results_df.to_json(orient="records"))
        if save:
            with open(f"gget_{source}_results.json", "w", encoding="utf-8") as f:
                json_package.dump(results_dict, f, ensure_ascii=False, indent=4)
        return results_dict

    if save:
        results_df.to_csv(f"gget_{source}_results.csv", index=False)

    return results_df
