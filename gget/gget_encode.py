from __future__ import annotations

import json as json_package
import os
import re
from typing import Any, Literal, overload

import pandas as pd
import requests

from .constants import DEFAULT_REQUESTS_TIMEOUT, ENCODE_URL
from .utils import set_up_logger

logger = set_up_logger()

# Columns returned for ENCODE file listings (experiment/file accessions)
_FILE_COLUMNS = [
    "file_accession",
    "file_format",
    "output_type",
    "assembly",
    "file_size",
    "status",
    "url",
]
# Columns returned for free-text searches
_SEARCH_COLUMNS = [
    "accession",
    "assay_title",
    "biosample_summary",
    "target",
    "description",
    "status",
    "lab",
]

# ENCODE accessions look like ENCSR000AKS (experiment), ENCFF000BXK (file), etc.
_ACCESSION_RE = re.compile(r"^ENC[A-Z]{2}[0-9A-Za-z]+$")


def _is_encode_accession(term: str) -> bool:
    """Return True if 'term' looks like an ENCODE accession (e.g. ENCSR000AKS)."""
    return bool(_ACCESSION_RE.match(term.strip()))


def _encode_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """GET a JSON object from the ENCODE REST API."""
    url = f"{ENCODE_URL}{path}"
    try:
        response = requests.get(
            url,
            params=params,
            headers={"Accept": "application/json"},
            timeout=DEFAULT_REQUESTS_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"The ENCODE server request failed: {exc}") from exc

    if response.status_code == 404:
        raise ValueError(f"ENCODE returned 404 (not found) for '{path}'. Please double-check the accession/term.")
    if not response.ok:
        raise RuntimeError(
            f"The ENCODE server returned error status code {response.status_code}. Please try again later."
        )

    return response.json()


def _files_to_df(
    files: list[dict[str, Any]],
    assembly: str | None = None,
    file_format: str | None = None,
    output_type: str | None = None,
) -> pd.DataFrame:
    """Build a data frame of ENCODE files, applying optional filters."""
    rows = []
    for f in files:
        if assembly is not None and f.get("assembly") != assembly:
            continue
        if file_format is not None and f.get("file_format") != file_format:
            continue
        if output_type is not None and f.get("output_type") != output_type:
            continue
        href = f.get("href")
        rows.append(
            {
                "file_accession": f.get("accession"),
                "file_format": f.get("file_format"),
                "output_type": f.get("output_type"),
                "assembly": f.get("assembly"),
                "file_size": f.get("file_size"),
                "status": f.get("status"),
                "url": f"{ENCODE_URL}{href}" if href else None,
            }
        )
    return pd.DataFrame(rows, columns=_FILE_COLUMNS)


def _search_row(g: dict[str, Any]) -> dict[str, Any]:
    """Flatten one ENCODE search result into a row of scalar values."""
    target = g.get("target")
    target_label = target.get("label") if isinstance(target, dict) else target
    lab = g.get("lab")
    lab_title = lab.get("title") if isinstance(lab, dict) else lab
    return {
        "accession": g.get("accession"),
        "assay_title": g.get("assay_title"),
        "biosample_summary": g.get("biosample_summary"),
        "target": target_label,
        "description": g.get("description"),
        "status": g.get("status"),
        "lab": lab_title,
    }


def _download_files(df: pd.DataFrame, out_dir: str, verbose: bool = True) -> None:
    """Download every file in the 'url' column of 'df' into out_dir."""
    urls = [u for u in df.get("url", []) if u]
    if len(urls) == 0:
        logger.warning("No downloadable files found for the given query.")
        return

    os.makedirs(out_dir, exist_ok=True)
    for url in urls:
        filename = url.split("/")[-1]
        dest = os.path.join(out_dir, filename)
        if verbose:
            logger.info(f"Downloading {filename}...")
        try:
            with requests.get(url, stream=True, timeout=DEFAULT_REQUESTS_TIMEOUT) as r:
                r.raise_for_status()
                with open(dest, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=8192):
                        fh.write(chunk)
        except requests.exceptions.RequestException as exc:
            logger.error(f"Failed to download {filename}: {exc}")


@overload
def encode(
    search_term: str,
    type: str = "Experiment",
    limit: int = 10,
    assembly: str | None = None,
    file_format: str | None = None,
    output_type: str | None = None,
    download: bool = False,
    out_dir: str = ".",
    save: bool = False,
    verbose: bool = True,
    *,
    json: Literal[True],
) -> list[dict[str, Any]] | None: ...


@overload
def encode(
    search_term: str,
    type: str = "Experiment",
    limit: int = 10,
    assembly: str | None = None,
    file_format: str | None = None,
    output_type: str | None = None,
    download: bool = False,
    out_dir: str = ".",
    save: bool = False,
    verbose: bool = True,
    json: Literal[False] = False,
) -> pd.DataFrame | None: ...


def encode(
    search_term: str,
    type: str = "Experiment",
    limit: int = 10,
    assembly: str | None = None,
    file_format: str | None = None,
    output_type: str | None = None,
    download: bool = False,
    out_dir: str = ".",
    save: bool = False,
    verbose: bool = True,
    json: bool = False,
) -> pd.DataFrame | list[dict[str, Any]] | None:
    """Query and download data from the ENCODE project (https://www.encodeproject.org/).

    Two modes, chosen automatically from 'search_term':
      - If 'search_term' is an ENCODE accession (e.g. "ENCSR000AKS" for an
        experiment or "ENCFF000BXK" for a file), the matching object is fetched
        and its file(s) are returned (with download URLs).
      - Otherwise, 'search_term' is used as a free-text query against the ENCODE
        search endpoint and the matching objects of the given 'type' are returned.

    Args:
     - search_term  ENCODE accession (experiment/file/...) or free-text search term.
     - type         ENCODE object type for free-text searches, e.g. "Experiment",
                    "File", "Biosample". Default: "Experiment".
     - limit        Maximum number of results for free-text searches. Default: 10.
     - assembly     Only return files for this genome assembly, e.g. "GRCh38". Default: None.
     - file_format  Only return files of this format, e.g. "bam", "fastq", "bigWig". Default: None.
     - output_type  Only return files of this output type, e.g. "alignments". Default: None.
     - download     If True, download the returned files into 'out_dir'. Default: False.
     - out_dir      Directory to download files into. Default: "." (current directory).
     - save         If True, save the results table as csv/json in the working directory. Default: False.
     - verbose      True/False whether to print progress information. Default: True.
     - json         If True, returns results in json format instead of data frame. Default: False.

    Returns a data frame (or list of dicts if json=True) of files or search results.
    Returns None if no results are found.
    """
    if search_term is None or str(search_term).strip() == "":
        raise ValueError("Please provide a search term or ENCODE accession in 'search_term'.")

    term = str(search_term).strip()
    source = "encode_search"

    if _is_encode_accession(term):
        if verbose:
            logger.info(f"Fetching ENCODE object {term}...")
        obj = _encode_get(f"/{term}/", params={"format": "json"})
        obj_types = obj.get("@type", [])

        if "File" in obj_types:
            source = "encode_files"
            results_df = _files_to_df([obj], assembly, file_format, output_type)
        elif "files" in obj:
            source = "encode_files"
            results_df = _files_to_df(obj.get("files", []), assembly, file_format, output_type)
        else:
            # Generic object: return its top-level scalar metadata as a single row
            source = "encode_metadata"
            scalar = {k: v for k, v in obj.items() if isinstance(v, (str, int, float, bool)) or v is None}
            results_df = pd.DataFrame([scalar])

        if download:
            _download_files(results_df, out_dir, verbose)
    else:
        if verbose:
            logger.info(f"Searching ENCODE for '{term}' (type={type})...")
        data = _encode_get(
            "/search/",
            params={"type": type, "searchTerm": term, "limit": limit, "format": "json"},
        )
        rows = [_search_row(g) for g in data.get("@graph", [])]
        results_df = pd.DataFrame(rows, columns=_SEARCH_COLUMNS)
        if download:
            logger.warning("'download' is only supported for ENCODE accessions (experiments/files), not free-text searches.")

    if len(results_df) == 0:
        logger.warning(f"No ENCODE results found for '{term}'.")
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
