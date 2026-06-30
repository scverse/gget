from __future__ import annotations

import json as json_package
import os
from typing import Any, Literal, overload

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .constants import DEFAULT_REQUESTS_TIMEOUT, PINEAPPLE_GDRIVE_URL
from .utils import set_up_logger

logger = set_up_logger()

# ---------------------------------------------------------------------------
# Pineapple data catalog.
#
# Pineapple (https://github.com/tomouellette/pineapple) is a command-line tool
# for processing/profiling morphological data in bio-imaging datasets. Its
# `pineapple download` command distributes a curated set of standardized
# bio-imaging datasets and pre-trained model weights, each hosted on Google
# Drive. The file IDs, licenses, authors, and sizes below are mirrored verbatim
# from the pineapple `pineapple-data` crate so that gget can list and download
# the same resources without requiring the Rust binary.
# ---------------------------------------------------------------------------

_SEGMENTATION: dict[str, dict[str, str]] = {
    "almeida_2023": {
        "file_id": "1BlHvG0MkWwuqGA3ImUJ09D9E7rsVt5ER",
        "data_authors": "Almeida et al. 2023",
        "size_gb": "0.927",
        "license": "CC BY 4.0",
    },
    "arvidsson_2022": {
        "file_id": "12Cwk5MX3V9z_2KmBJyn5jXc-JuW7-e2k",
        "data_authors": "Arvidsson et al. 2022",
        "size_gb": "0.028",
        "license": "CC BY 4.0",
    },
    "cellpose_2021": {
        "file_id": "12Z9PpJEdSE0bHALNxpAAeD6WA9aBhMEO",
        "data_authors": "Stringer et al. 2021",
        "size_gb": "0.356",
        "license": "Custom NC",
    },
    "conic_2022": {
        "file_id": "1nXOnDkWpRfU5iGXFZe06-CQaAMFq13f_",
        "data_authors": "Graham et al. 2022",
        "size_gb": "1.920",
        "license": "CC BY-NC 4.0",
    },
    "cryonuseg_2021": {
        "file_id": "1cfIY9BSlTe0RNaq1V8fZmKJwWyBs4WEj",
        "data_authors": "Mahbod et al. 2021",
        "size_gb": "0.031",
        "license": "MIT",
    },
    "dsb_2019": {
        "file_id": "1qgAyMcrZwLudlA4vjy7jwuKTjAxT7Ky2",
        "data_authors": "Caicedo et al. 2019",
        "size_gb": "0.112",
        "license": "CC0 1.0 Universal",
    },
    "hpa_2022": {
        "file_id": "1NyV6xuIAIuaSiXp0H-4VCV8tjaNSpXtX",
        "data_authors": "HPA 2022",
        "size_gb": "1.630",
        "license": "CC BY 4.0",
    },
    "livecell_2021": {
        "file_id": "1JNXkZS0QSQW25b-opoyKomPKCfO_3pkx",
        "data_authors": "Edlund et al. 2021",
        "size_gb": "3.260",
        "license": "CC BY-NC 4.0",
    },
    "nuinseg_2024": {
        "file_id": "1gSmbsfhO7aP1yBB5R9XMMrAH4hy-Thmm",
        "data_authors": "Mahbod et al. 2024",
        "size_gb": "0.347",
        "license": "MIT",
    },
    "pannuke_2020": {
        "file_id": "1J9CeH9t23EpottNyUKeBBkYpTfMR3EgT",
        "data_authors": "Gamper et al. 2020",
        "size_gb": "1.250",
        "license": "CC BY-NC-SA 4.0",
    },
    "tissuenet_2022": {
        "file_id": "1ilHrzUuGfobSdFmTezyynCWCLIoJwaHQ",
        "data_authors": "Greenwald et al. 2022",
        "size_gb": "4.270",
        "license": "Modified NC Apache",
    },
    "vicar_2021": {
        "file_id": "12tJOlIHZPFqp8GLek_jV__Uhhgsa530_",
        "data_authors": "Vicar et al. 2021",
        "size_gb": "0.113",
        "license": "CC BY 4.0",
    },
}

_BENCHMARK: dict[str, dict[str, str]] = {
    "amgad_2022": {
        "file_id": "1JHlGon82bYPhpeOwbRYxz4uRxhcxasr3",
        "data_authors": "Amgad et al. 2022",
        "size_gb": "0.062",
        "license": "CC0 1.0",
    },
    "cnmc_2019": {
        "file_id": "1a7Wt0kwt3Uq1NKMtBsWmesMH4tCwqkgi",
        "data_authors": "C-NMC Challenge",
        "size_gb": "0.182",
        "license": "CC BY 3.0",
    },
    "fracatlas_2023": {
        "file_id": "1vyXNA4bxMFk-7Hw59TPiWIfX-BzTSmCd",
        "data_authors": "Abedeen et al. 2023",
        "size_gb": "0.247",
        "license": "CC BY 4.0",
    },
    "isic_2019": {
        "file_id": "1CDGbcBxs7SUemGwpBtoVYJblqCNgw469",
        "data_authors": "ISIC",
        "size_gb": "1.140",
        "license": "CC BY-NC 4.0",
    },
    "kermany_2018": {
        "file_id": "1Xk7LWa7HWzTN7Nxsa8MuefBmzNsz4VuM",
        "data_authors": "Kermany et al. 2018",
        "size_gb": "0.638",
        "license": "CC BY 4.0",
    },
    "kromp_2023": {
        "file_id": "16RXNWQXlw_scJ75DwowngxJHYB2rZsW7",
        "data_authors": "Kromp et al. 2023",
        "size_gb": "0.025",
        "license": "CC BY 4.0",
    },
    "matek_2021": {
        "file_id": "1BDYtZoqSUUZQmWgcEBtopaJTWgwrAXGz",
        "data_authors": "Matek et al. 2021",
        "size_gb": "0.508",
        "license": "CC BY 4.0",
    },
    "murphy_2001": {
        "file_id": "1fl4dwbjX11SpDRhwbIi2-lbcswvyr1F_",
        "data_authors": "Murphy et al. 2001",
        "size_gb": "0.033",
        "license": "MIT",
    },
    "opencell_2024": {
        "file_id": "1nlqt7ujUPciEoAKriIu_bqE5fUJZX4nx",
        "data_authors": "OpenCell",
        "size_gb": "1.030",
        "license": "MIT",
    },
    "phillip_2021": {
        "file_id": "1yE4BblXBAPJDT1AnK3gghHAS3cZUFCd6",
        "data_authors": "Phillip et al. 2021",
        "size_gb": "0.032",
        "license": "MIT",
    },
    "recursion_2019": {
        "file_id": "1209hlaKcOqKdEGOwvlRhJakX8ciN-SX8",
        "data_authors": "Recursion",
        "size_gb": "0.037",
        "license": "CC BY-NC-SA 4.0",
    },
    "verma_2021": {
        "file_id": "1AyU-4-doJY2GX3dmf7ryPDCvDA_x4PPD",
        "data_authors": "Verma et al. 2021",
        "size_gb": "0.021",
        "license": "CC BY-NC-SA 4.0",
    },
    "runtime": {
        "file_id": "1BlXIv49oxj2dsiiEASbTEiyh7QpIjYb_",
        "data_authors": "MIT",
        "size_gb": "0.017",
        "license": "MIT",
    },
}

_WEIGHTS: dict[str, dict[str, str]] = {
    "dino_vit_small": {
        "file_id": "1xuyTyPsuPiDtec8ojZwAyXSDq9AzyPQX",
        "filename": "dinov2_vits14_imagenet.safetensors",
        "data_authors": "Huggingface/candle",
        "size_gb": "0.097",
        "license": "Apache License 2.0",
    },
    "dino_vit_base": {
        "file_id": "19vy-A-KTaaF3vsWKxu0JpA0gaATU52Gh",
        "filename": "dinov2_vitb14_imagenet.safetensors",
        "data_authors": "Huggingface/candle",
        "size_gb": "0.330",
        "license": "Apache License 2.0",
    },
    "dinobloom_vit_base": {
        "file_id": "1XhzSiO2IDKppr2UCTAio_niLSk5QA6hG",
        "filename": "dinov2_vitb14_dinobloom.safetensors",
        "data_authors": "Marr Lab",
        "size_gb": "0.330",
        "license": "Apache License 2.0",
    },
    "scdino_vit_small": {
        "file_id": "1omwQNJVMkrbYCstSF11p5HsErHzINTz6",
        "filename": "scdino_vit_small.safetensors",
        "data_authors": "Snijder Lab",
        "size_gb": "0.097",
        "license": "Apache License 2.0",
    },
    "subcell_vit_base": {
        "file_id": "1LZn3xlgVVd2jQIpXst4CMCYN58F-VG-x",
        "filename": "subcell_vit_base.safetensors",
        "data_authors": "Lundberg Lab",
        "size_gb": "0.330",
        "license": "MIT License",
    },
}

_CATEGORIES: dict[str, dict[str, dict[str, str]]] = {
    "segmentation": _SEGMENTATION,
    "benchmark": _BENCHMARK,
    "weights": _WEIGHTS,
}

_COLUMNS = ["name", "category", "data_authors", "size_gb", "license", "filename", "google_drive_id"]


def _resource_filename(category: str, name: str, info: dict[str, str]) -> str:
    """Return the filename pineapple uses for a dataset/weights resource."""
    if category == "weights":
        return info["filename"]
    # Datasets are distributed as tarballs with dashes instead of underscores
    return f"{name.replace('_', '-')}.tar.gz"


def _catalog_row(category: str, name: str, info: dict[str, str]) -> dict[str, Any]:
    """Build a catalog row for a single resource."""
    return {
        "name": name,
        "category": category,
        "data_authors": info.get("data_authors"),
        "size_gb": float(info["size_gb"]) if info.get("size_gb") else None,
        "license": info.get("license"),
        "filename": _resource_filename(category, name, info),
        "google_drive_id": info.get("file_id"),
    }


def _parse_gdrive_form(html_text: str) -> tuple[str | None, dict[str, str]]:
    """Parse Google Drive's virus-scan-warning form (for large files).

    Mirrors the behavior of pineapple's Rust downloader: locate the
    `form#download-form` and collect its named inputs to build the confirmed
    download request.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    form = soup.find("form", id="download-form")
    if form is None:
        return None, {}
    action = form.get("action")
    params = {}
    for inp in form.find_all("input"):
        name = inp.get("name")
        if name:
            params[name] = inp.get("value", "")
    return action, params


def _resolve_gdrive_response(session: requests.Session, file_id: str) -> requests.Response:
    """Resolve a Google Drive file ID to a streaming response for the actual file.

    Small files download directly; large files first return an HTML
    "can't scan for viruses" warning page whose form must be submitted to
    obtain the real file. The returned response is opened with ``stream=True``,
    so the body is not fetched until the caller iterates it. Callers that only
    need the headers (e.g. accessibility checks) must ``close()`` the response.
    """
    response = session.get(
        PINEAPPLE_GDRIVE_URL,
        params={"id": file_id},
        stream=True,
        timeout=DEFAULT_REQUESTS_TIMEOUT,
    )
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type:
        action, params = _parse_gdrive_form(response.text)
        if action:
            response = session.get(action, params=params, stream=True, timeout=DEFAULT_REQUESTS_TIMEOUT)
            response.raise_for_status()
        else:
            # Fall back to the legacy cookie-based confirm token
            token = next((v for k, v in response.cookies.items() if k.startswith("download_warning")), None)
            if token:
                response = session.get(
                    PINEAPPLE_GDRIVE_URL,
                    params={"id": file_id, "confirm": token},
                    stream=True,
                    timeout=DEFAULT_REQUESTS_TIMEOUT,
                )
                response.raise_for_status()

    return response


def _download_from_gdrive(file_id: str, dest_path: str, verbose: bool = True) -> None:
    """Download a (potentially large) file from Google Drive by file ID."""
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; gget)"})

    response = _resolve_gdrive_response(session, file_id)

    with open(dest_path, "wb") as fh:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                fh.write(chunk)

    if verbose:
        logger.info(f"Saved {dest_path}")


@overload
def pineapple(
    name: str | None = None,
    category: str = "segmentation",
    download: bool = False,
    out_dir: str = ".",
    save: bool = False,
    verbose: bool = True,
    *,
    json: Literal[True],
) -> list[dict[str, Any]] | None: ...


@overload
def pineapple(
    name: str | None = None,
    category: str = "segmentation",
    download: bool = False,
    out_dir: str = ".",
    save: bool = False,
    verbose: bool = True,
    json: Literal[False] = False,
) -> pd.DataFrame | None: ...


def pineapple(
    name: str | None = None,
    category: str = "segmentation",
    download: bool = False,
    out_dir: str = ".",
    save: bool = False,
    verbose: bool = True,
    json: bool = False,
) -> pd.DataFrame | list[dict[str, Any]] | None:
    """List and download curated bio-imaging datasets and model weights from Pineapple.

    Pineapple (https://github.com/tomouellette/pineapple) curates and standardizes
    a collection of bio-imaging datasets (segmentation and benchmark) and
    pre-trained self-supervised model weights, hosted on Google Drive. `gget
    pineapple` lets you browse this catalog and download the resources directly,
    without installing the Pineapple Rust binary.

    Args:
     - name      Name of the dataset/weights to fetch, e.g. "vicar_2021" or
                 "dino_vit_small". If None (default), the full catalog for the
                 chosen 'category' is returned.
     - category  Resource category: "segmentation", "benchmark", or "weights".
                 Default: "segmentation".
     - download  If True (and 'name' is given), download the resource into 'out_dir'.
                 Default: False.
     - out_dir   Directory to download the resource into. Default: "." (current directory).
     - save      If True, save the returned catalog table as csv/json. Default: False.
     - verbose   True/False whether to print progress information. Default: True.
     - json      If True, returns results in json format instead of data frame. Default: False.

    Returns a data frame (or list of dicts if json=True) describing the catalog
    entry/entries (name, category, authors, size in GB, license, filename, and
    Google Drive ID). Please check each dataset's original reference and license
    before use.
    """
    category = str(category).lower()
    if category not in _CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Expected one of: {', '.join(_CATEGORIES)}")

    registry = _CATEGORIES[category]

    if name is None:
        rows = [_catalog_row(category, n, info) for n, info in registry.items()]
        results_df = pd.DataFrame(rows, columns=_COLUMNS)
        if download:
            logger.warning("'download' requires a specific 'name'; returning the catalog instead.")
    else:
        if name not in registry:
            raise ValueError(f"'{name}' not found in category '{category}'. Available: {', '.join(registry)}")
        info = registry[name]

        if download:
            os.makedirs(out_dir, exist_ok=True)
            filename = _resource_filename(category, name, info)
            dest = os.path.join(out_dir, filename)
            if verbose:
                logger.info(f"Downloading pineapple {category} resource '{name}' ({info['size_gb']} GB) to {dest}...")
            _download_from_gdrive(info["file_id"], dest, verbose)

        results_df = pd.DataFrame([_catalog_row(category, name, info)], columns=_COLUMNS)

    if json:
        results_dict = json_package.loads(results_df.to_json(orient="records"))
        if save:
            with open("gget_pineapple_results.json", "w", encoding="utf-8") as f:
                json_package.dump(results_dict, f, ensure_ascii=False, indent=4)
        return results_dict

    if save:
        results_df.to_csv("gget_pineapple_results.csv", index=False)

    return results_df
