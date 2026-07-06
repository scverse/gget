from __future__ import annotations

import json as json_
import re
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import pandas as pd

from .utils import HTTPStatusError, http_json, set_up_logger

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
REACTOME_RESOURCES = ("pathways", "search", "entity", "interactors", "orthology", "event-hierarchy")

# Regex to strip the <span class="highlighting">...</span> tags Reactome wraps around
# matched search terms.
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: Any) -> Any:
    """Remove HTML highlight tags returned by the Reactome search endpoint."""
    if isinstance(text, str):
        return _HTML_TAG_RE.sub("", text)
    return text


def _is_http_status(error: Exception, status: int) -> bool:
    """True if the error raised by http_json corresponds to the given HTTP status."""
    return isinstance(error, HTTPStatusError) and error.status_code == status


def _reactome_release() -> str | None:
    """Return the current Reactome release version (e.g. '97'), or None if unavailable."""
    # This endpoint returns a plain-text integer; requesting application/json yields HTTP 406.
    headers = {**_REACTOME_HEADERS, "Accept": "text/plain"}
    try:
        return str(http_json("GET", f"{REACTOME_CONTENT_API}/data/database/version", headers=headers)).strip()
    except (RuntimeError, ValueError):
        return None


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


def _reactome_species_dbid(species: str) -> int:
    """Resolve a species name or NCBI taxonomy ID to its Reactome species dbId."""
    payload = http_json("GET", f"{REACTOME_CONTENT_API}/data/species/main", headers=_REACTOME_HEADERS)
    wanted = str(species).strip().lower()
    for entry in payload:
        if wanted in (str(entry.get("displayName", "")).lower(), str(entry.get("taxId", "")).lower()):
            return int(entry["dbId"])
    raise ValueError(
        f"Species '{species}' was not found among Reactome's species. Provide a Reactome species "
        "name (e.g. 'Mus musculus') or NCBI taxonomy ID (e.g. '10090')."
    )


def _reactome_interactors(query: str, verbose: bool = True) -> pd.DataFrame:
    """Return the molecular interactors of an identifier (IntAct static interactors).

    Uses the ContentService '/interactors/static/molecule/{acc}/details' endpoint.
    """
    if verbose:
        logger.info(f"Querying Reactome interactors for '{query}'.")

    columns = ["interactor_acc", "interactor_name", "score", "evidences"]
    try:
        payload = http_json(
            "GET",
            f"{REACTOME_CONTENT_API}/interactors/static/molecule/{query}/details",
            context="Reactome ContentService (interactors)",
            headers=_REACTOME_HEADERS,
        )
    except RuntimeError as e:
        if _is_http_status(e, 404):
            logger.warning(f"No Reactome interactors found for '{query}'.")
            return pd.DataFrame(columns=columns)
        raise

    entities = payload.get("entities", [])
    interactors = entities[0].get("interactors", []) if entities else []
    rows = [
        {
            "interactor_acc": it.get("acc"),
            "interactor_name": it.get("alias"),
            "score": it.get("score"),
            "evidences": it.get("evidences"),
        }
        for it in interactors
    ]
    return pd.DataFrame(rows, columns=columns)


def _reactome_orthology(query: str, species: str | None, verbose: bool = True) -> pd.DataFrame:
    """Project a Reactome event/entity to its ortholog in another species.

    Uses the ContentService '/data/orthology/{id}/species/{speciesDbId}' endpoint.
    """
    if species is None:
        raise ValueError("resource='orthology' requires a target 'species' (e.g. species='Mus musculus' or '10090').")

    species_dbid = _reactome_species_dbid(species)
    if verbose:
        logger.info(f"Projecting Reactome entry '{query}' to species '{species}'.")

    try:
        payload = http_json(
            "GET",
            f"{REACTOME_CONTENT_API}/data/orthology/{query}/species/{species_dbid}",
            context="Reactome ContentService (orthology)",
            headers=_REACTOME_HEADERS,
        )
    except RuntimeError as e:
        if _is_http_status(e, 404):
            raise ValueError(
                f"No Reactome ortholog found for '{query}' in species '{species}'. Provide a valid "
                "Reactome stable ID (e.g. 'R-HSA-6804754') and a species Reactome covers."
            ) from e
        raise

    row = {
        "stable_id": payload.get("stId"),
        "name": payload.get("displayName"),
        "species": payload.get("speciesName"),
        "schema_class": payload.get("schemaClass"),
    }
    return pd.DataFrame([row], columns=["stable_id", "name", "species", "schema_class"])


def _reactome_event_hierarchy(query: str, verbose: bool = True) -> pd.DataFrame:
    """Return the full event (pathway/reaction) hierarchy for a species as a flat adjacency table.

    Uses the ContentService '/data/eventsHierarchy/{species}' endpoint; the nested tree is flattened
    to one row per event with its parent_id and nesting level.
    """
    if verbose:
        logger.info(f"Fetching the Reactome event hierarchy for species '{query}'.")

    columns = ["stable_id", "name", "type", "species", "parent_id", "level"]
    try:
        payload = http_json(
            "GET",
            f"{REACTOME_CONTENT_API}/data/eventsHierarchy/{query}",
            context="Reactome ContentService (event-hierarchy)",
            headers=_REACTOME_HEADERS,
        )
    except RuntimeError as e:
        if _is_http_status(e, 404):
            raise ValueError(
                f"No Reactome event hierarchy found for species '{query}'. Provide a Reactome species "
                "name (e.g. 'Homo sapiens') or NCBI taxonomy ID (e.g. '9606')."
            ) from e
        raise

    rows: list[dict[str, Any]] = []

    def _walk(node: dict[str, Any], parent_id: str | None, level: int) -> None:
        rows.append(
            {
                "stable_id": node.get("stId"),
                "name": node.get("name"),
                "type": node.get("type"),
                "species": node.get("species"),
                "parent_id": parent_id,
                "level": level,
            }
        )
        for child in node.get("children", []) or []:
            _walk(child, node.get("stId"), level + 1)

    for top in payload:
        _walk(top, None, 0)

    return pd.DataFrame(rows, columns=columns)


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
      - query       Identifier, search term or species to query (str). Its meaning depends on 'resource':
                      - resource="pathways":        an identifier (e.g. UniProt accession 'P04637').
                      - resource="search":          a free-text search term (e.g. 'TP53').
                      - resource="entity":          a Reactome stable ID (e.g. 'R-HSA-6804754').
                      - resource="interactors":     a molecule accession (e.g. UniProt 'P04637').
                      - resource="orthology":       a Reactome stable ID to project to another species.
                      - resource="event-hierarchy": a species name or NCBI taxonomy ID.
      - resource    Type of query to perform (str). One of:
                      - "pathways" (default): pathways the identifier participates in.
                      - "search":             full-text search of the Reactome knowledgebase.
                      - "entity":             details for a Reactome stable ID.
                      - "interactors":        molecular interactors of an identifier (IntAct static).
                      - "orthology":          project a stable ID to its ortholog in another species
                                              (requires 'species').
                      - "event-hierarchy":    the full pathway/reaction hierarchy for a species.
      - source      Identifier resource/database for resource="pathways" (str), e.g. 'UniProt',
                    'Ensembl', 'ChEBI', 'NCBI'. Default: "UniProt".
      - species     Species as a name (e.g. 'Homo sapiens') or NCBI taxonomy ID (e.g. '9606').
                    Filters resource="pathways"/"search"; is the required target for resource="orthology".
                    Default: None.
      - types       Restrict resource="search" results to one or more entry types (str), e.g.
                    'Pathway', 'Reaction', 'Protein'. Default: None (all types).
      - json        If True, return the result as a JSON-serializable list of dicts instead of a
                    DataFrame (default: False).
      - verbose     True/False whether to print progress information. Default: True.

    Returns the requested information as a DataFrame (or list of dicts if json=True). The DataFrame's
    `.attrs["reactome_release"]` carries the Reactome release version, for reproducibility.
    """
    if resource not in REACTOME_RESOURCES:
        raise ValueError(f"Argument 'resource' must be one of {REACTOME_RESOURCES}, not '{resource}'.")

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Argument 'query' must be a non-empty string.")

    if resource == "pathways":
        df = _reactome_pathways(query, source=source, species=species, verbose=verbose)
    elif resource == "search":
        df = _reactome_search(query, species=species, types=types, verbose=verbose)
    elif resource == "entity":
        df = _reactome_entity(query, verbose=verbose)
    elif resource == "interactors":
        df = _reactome_interactors(query, verbose=verbose)
    elif resource == "orthology":
        df = _reactome_orthology(query, species=species, verbose=verbose)
    else:  # resource == "event-hierarchy"
        df = _reactome_event_hierarchy(query, verbose=verbose)

    # Record the Reactome release for reproducibility (best-effort; non-fatal).
    release = _reactome_release()
    if release is not None:
        df.attrs["reactome_release"] = release
        if verbose:
            logger.info(f"Reactome release: {release}.")

    if json:
        return json_.loads(df.to_json(orient="records", force_ascii=False))
    return df
