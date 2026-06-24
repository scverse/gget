from __future__ import annotations

import json as json_
import re
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import pandas as pd

from .utils import http_json, set_up_logger

logger = set_up_logger()

try:
    _GGET_VERSION = version("gget")
except PackageNotFoundError:
    _GGET_VERSION = "unknown"

# Reactome ContentService REST API (https://reactome.org/dev/content-service)
REACTOME_CONTENT_API = "https://reactome.org/ContentService"

_REACTOME_HEADERS = {
    "User-Agent": f"gget/{_GGET_VERSION} (+https://github.com/scverse/gget)",
    "Accept": "application/json",
}

# Supported values for the 'resource' argument
REACTOME_RESOURCES = ("pathways", "search", "entity")

# Regex to strip the <span class="highlighting">...</span> tags Reactome wraps around
# matched search terms.
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: Any) -> Any:
    """Remove HTML highlight tags returned by the Reactome search endpoint."""
    if isinstance(text, str):
        return _HTML_TAG_RE.sub("", text)
    return text


def _is_http_status(error: Exception, status: int) -> bool:
    """True if the RuntimeError raised by http_json corresponds to the given HTTP status."""
    return f"HTTP {status}" in str(error)


def _reactome_pathways(
    query: str,
    source: str = "UniProt",
    species: str | None = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """Map an identifier to the Reactome pathways it participates in.

    Uses the ContentService '/data/mapping/{source}/{identifier}/pathways' endpoint.
    """
    if verbose:
        logger.info(f"Querying Reactome for pathways containing {source} identifier '{query}'.")

    params = {}
    if species is not None:
        params["species"] = species

    try:
        payload = http_json(
            "GET",
            f"{REACTOME_CONTENT_API}/data/mapping/{source}/{query}/pathways",
            context="Reactome ContentService (pathways)",
            headers=_REACTOME_HEADERS,
            params=params,
        )
    except RuntimeError as e:
        # Reactome returns 404 when the identifier is not found / has no mapped pathways.
        if _is_http_status(e, 404):
            logger.warning(f"No Reactome pathways found for {source} identifier '{query}'.")
            return pd.DataFrame(columns=["stable_id", "name", "species", "schema_class", "in_disease"])
        raise

    rows = [
        {
            "stable_id": entry.get("stId"),
            "name": entry.get("displayName"),
            "species": entry.get("speciesName"),
            "schema_class": entry.get("schemaClass"),
            "in_disease": entry.get("isInDisease"),
        }
        for entry in payload
    ]
    return pd.DataFrame(rows, columns=["stable_id", "name", "species", "schema_class", "in_disease"])


def _reactome_search(
    query: str,
    species: str | None = None,
    types: str | None = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """Full-text search of the Reactome knowledgebase.

    Uses the ContentService '/search/query' endpoint and flattens the grouped results.
    """
    if verbose:
        logger.info(f"Searching Reactome for '{query}'.")

    params: dict[str, Any] = {"query": query, "cluster": "true"}
    if species is not None:
        params["species"] = species
    if types is not None:
        params["types"] = types

    try:
        payload = http_json(
            "GET",
            f"{REACTOME_CONTENT_API}/search/query",
            context="Reactome ContentService (search)",
            headers=_REACTOME_HEADERS,
            params=params,
        )
    except RuntimeError as e:
        # Reactome returns 404 when the search yields no results.
        if _is_http_status(e, 404):
            logger.warning(f"No Reactome search results found for '{query}'.")
            return pd.DataFrame(columns=["stable_id", "name", "type", "species", "reactome_id"])
        raise

    rows = []
    for group in payload.get("results", []):
        for entry in group.get("entries", []):
            entry_species = entry.get("species")
            if isinstance(entry_species, list):
                entry_species = entry_species[0] if entry_species else None
            rows.append(
                {
                    "stable_id": entry.get("stId"),
                    "name": _strip_html(entry.get("name")),
                    "type": entry.get("exactType") or entry.get("type"),
                    "species": entry_species,
                    "reactome_id": entry.get("id"),
                }
            )
    return pd.DataFrame(rows, columns=["stable_id", "name", "type", "species", "reactome_id"])


def _reactome_entity(query: str, verbose: bool = True) -> pd.DataFrame:
    """Fetch details for a Reactome entry (pathway, reaction, physical entity, ...) by stable ID.

    Uses the ContentService '/data/query/{id}' endpoint.
    """
    if verbose:
        logger.info(f"Fetching Reactome entry '{query}'.")

    try:
        payload = http_json(
            "GET",
            f"{REACTOME_CONTENT_API}/data/query/{query}",
            context="Reactome ContentService (entity)",
            headers=_REACTOME_HEADERS,
        )
    except RuntimeError as e:
        if _is_http_status(e, 404):
            raise ValueError(
                f"No Reactome entry found for identifier '{query}'. "
                "Provide a valid Reactome stable ID (e.g. 'R-HSA-6804754') or database ID."
            ) from e
        raise

    name = payload.get("displayName")
    if name is None:
        names = payload.get("name")
        if isinstance(names, list) and names:
            name = names[0]

    row = {
        "stable_id": payload.get("stId"),
        "name": name,
        "schema_class": payload.get("schemaClass"),
        "species": payload.get("speciesName"),
        "in_disease": payload.get("isInDisease"),
        "summation": None,
    }
    summation = payload.get("summation")
    if isinstance(summation, list) and summation:
        row["summation"] = _strip_html(summation[0].get("text"))

    return pd.DataFrame([row], columns=["stable_id", "name", "schema_class", "species", "in_disease", "summation"])


def reactome(
    query: str,
    resource: str = "pathways",
    source: str = "UniProt",
    species: str | None = None,
    types: str | None = None,
    json: bool = False,
    verbose: bool = True,
) -> pd.DataFrame | list[dict[str, Any]]:
    """Query the Reactome pathway knowledgebase (https://reactome.org/).

    Args:
      - query       Identifier or search term to query (str). Its meaning depends on 'resource':
                      - resource="pathways": an identifier (e.g. UniProt accession 'P04637') whose
                        Reactome pathways should be returned.
                      - resource="search":   a free-text search term (e.g. 'TP53').
                      - resource="entity":   a Reactome stable ID (e.g. 'R-HSA-6804754').
      - resource    Type of query to perform (str). One of:
                      - "pathways" (default): pathways the identifier participates in.
                      - "search":             full-text search of the Reactome knowledgebase.
                      - "entity":             details for a Reactome stable ID.
      - source      Identifier resource/database for resource="pathways" (str), e.g. 'UniProt',
                    'Ensembl', 'ChEBI', 'NCBI'. Default: "UniProt".
      - species     Restrict results to a species (str), as a name (e.g. 'Homo sapiens') or NCBI
                    taxonomy ID (e.g. '9606'). Applies to resource="pathways" and resource="search".
                    Default: None (no species filter).
      - types       Restrict resource="search" results to one or more entry types (str), e.g.
                    'Pathway', 'Reaction', 'Protein'. Default: None (all types).
      - json        If True, return the result as a JSON-serializable list of dicts instead of a
                    DataFrame (default: False).
      - verbose     True/False whether to print progress information. Default: True.

    Returns the requested information as a DataFrame (or list of dicts if json=True).
    """
    if resource not in REACTOME_RESOURCES:
        raise ValueError(
            f"Argument 'resource' must be one of {REACTOME_RESOURCES}, not '{resource}'."
        )

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Argument 'query' must be a non-empty string.")

    if resource == "pathways":
        df = _reactome_pathways(query, source=source, species=species, verbose=verbose)
    elif resource == "search":
        df = _reactome_search(query, species=species, types=types, verbose=verbose)
    else:  # resource == "entity"
        df = _reactome_entity(query, verbose=verbose)

    if json:
        return json_.loads(df.to_json(orient="records", force_ascii=False))
    return df
