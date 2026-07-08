from __future__ import annotations

import html
import json as json_package
from typing import Any, Literal, overload
from urllib.parse import unquote

import pandas as pd
import requests

from .constants import DEFAULT_REQUESTS_TIMEOUT, UCSC_API_URL
from .utils import set_up_logger

logger = set_up_logger()

_COLUMNS = [
    "track",
    "ucsc_id",
    "chrom",
    "start",
    "end",
    "name",
    "description",
]


def _parse_position(position: str | None) -> tuple[str | None, int | None, int | None]:
    """Parse a UCSC position string 'chr13:32315508-32400268' into (chrom, start, end)."""
    if not position or ":" not in position:
        return position, None, None
    chrom, _, span = position.partition(":")
    if "-" not in span:
        return chrom, None, None
    start_str, _, end_str = span.partition("-")
    start_str = start_str.replace(",", "").strip()
    end_str = end_str.replace(",", "").strip()
    start = int(start_str) if start_str.isdigit() else None
    end = int(end_str) if end_str.isdigit() else None
    return chrom, start, end


def _match_rows(group: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten one UCSC positionMatches track group into rows."""
    track = group.get("trackName") or group.get("name")
    group_desc = group.get("description")
    rows = []
    for m in group.get("matches", []):
        chrom, start, end = _parse_position(m.get("position"))
        ucsc_id = m.get("hgFindMatches")
        if ucsc_id is not None:
            ucsc_id = unquote(str(ucsc_id))
        pos_name = m.get("posName")
        match_desc = m.get("description") or group_desc
        rows.append(
            {
                "track": track,
                "ucsc_id": ucsc_id,
                "chrom": chrom,
                "start": start,
                "end": end,
                "name": html.unescape(pos_name) if isinstance(pos_name, str) else pos_name,
                "description": html.unescape(match_desc) if isinstance(match_desc, str) else match_desc,
            }
        )
    return rows


@overload
def ucsc(
    search_term: str,
    genome: str = "hg38",
    track: str | None = None,
    limit: int | None = None,
    save: bool = False,
    verbose: bool = True,
    *,
    json: Literal[True],
) -> list[dict[str, Any]] | None: ...


@overload
def ucsc(
    search_term: str,
    genome: str = "hg38",
    track: str | None = None,
    limit: int | None = None,
    save: bool = False,
    verbose: bool = True,
    json: Literal[False] = False,
) -> pd.DataFrame | None: ...


def ucsc(
    search_term: str,
    genome: str = "hg38",
    track: str | None = None,
    limit: int | None = None,
    save: bool = False,
    verbose: bool = True,
    json: bool = False,
) -> pd.DataFrame | list[dict[str, Any]] | None:
    """Fetch UCSC Genome Browser IDs for a gene/term, similar to gget search.

    Searches the UCSC Genome Browser for a gene symbol, accession, or other term
    and returns the matching identifiers (e.g. UCSC known gene / transcript IDs)
    together with their genomic positions, grouped by the track they come from.

    Args:
     - search_term  Gene symbol, accession, or free-text term to search for, e.g. "BRCA2".
     - genome       UCSC genome assembly to search, e.g. "hg38", "hg19", "mm39". Default: "hg38".
     - track        If provided, only return matches from tracks whose name contains
                    this (case-insensitive) substring, e.g. "knownGene". Default: None.
     - limit        Maximum number of matches to return. Default: None (all matches).
     - save         If True, save the results table as csv/json in the working directory. Default: False.
     - verbose      True/False whether to print progress information. Default: True.
     - json         If True, returns results in json format instead of data frame. Default: False.

    Returns a data frame (or list of dicts if json=True) with one row per match,
    including the track, UCSC ID, chromosome, start, end, name, and description.
    Returns None if no matches are found.
    """
    if search_term is None or str(search_term).strip() == "":
        raise ValueError("Please provide a gene symbol or search term in 'search_term'.")

    term = str(search_term).strip()
    url = f"{UCSC_API_URL}/search"
    params = {"search": term, "genome": genome}

    if verbose:
        logger.info(f"Searching UCSC ({genome}) for '{term}'...")

    try:
        response = requests.get(
            url,
            params=params,
            headers={"Accept": "application/json"},
            timeout=DEFAULT_REQUESTS_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"The UCSC server request failed: {exc}") from exc

    # Parse the JSON body before checking the status code: a bad genome or bad
    # parameter returns a 4xx together with an informative "error" field, which we
    # want to surface instead of a generic message.
    try:
        data = response.json()
    except ValueError:
        data = None

    if isinstance(data, dict) and data.get("error"):
        raise ValueError(f"UCSC returned an error: {data['error']}")

    if not response.ok:
        raise RuntimeError(
            f"The UCSC server returned error status code {response.status_code}. Please try again later."
        )

    if not isinstance(data, dict):
        raise RuntimeError("The UCSC server returned an unexpected (non-JSON) response.")

    rows = []
    for group in data.get("positionMatches", []):
        rows.extend(_match_rows(group))

    # Optional track filter
    if track is not None:
        track_lower = str(track).lower()
        rows = [r for r in rows if r["track"] and track_lower in str(r["track"]).lower()]

    # Optional limit
    if limit is not None:
        rows = rows[: int(limit)]

    results_df = pd.DataFrame(rows, columns=_COLUMNS)

    if len(results_df) == 0:
        logger.warning(f"No UCSC matches found for '{term}' in genome '{genome}'.")
        return None

    if json:
        results_dict = json_package.loads(results_df.to_json(orient="records"))
        if save:
            with open("gget_ucsc_results.json", "w", encoding="utf-8") as f:
                json_package.dump(results_dict, f, ensure_ascii=False, indent=4)
        return results_dict

    if save:
        results_df.to_csv("gget_ucsc_results.csv", index=False)

    return results_df
