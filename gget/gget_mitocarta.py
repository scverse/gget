from __future__ import annotations

import io
import json as json_package
from typing import Any

import pandas as pd
import requests

from .constants import DEFAULT_REQUESTS_TIMEOUT, MITOCARTA_URLS
from .utils import set_up_logger

logger = set_up_logger()

# Map the `which` argument to the leading character of the corresponding Excel sheet name.
# The MitoCarta3.0 workbook contains the sheets:
#   "A <Species> MitoCarta3.0"  -> the mitochondrial gene inventory
#   "B <Species> All Genes"     -> all genes with Maestro mitochondrial-localization scores
#   "C MitoPathways"            -> the MitoPathways hierarchy and their genes
_WHICH_TO_SHEET_PREFIX = {
    "mitocarta": "A ",
    "all_genes": "B ",
    "pathways": "C ",
}

# Accepted species spellings -> canonical key
_SPECIES_ALIASES = {
    "human": "human",
    "homo_sapiens": "human",
    "homo sapiens": "human",
    "mouse": "mouse",
    "mus_musculus": "mouse",
    "mus musculus": "mouse",
}


def mitocarta(
    species: str = "human",
    which: str = "mitocarta",
    json: bool = False,
    save: bool = False,
    verbose: bool = True,
) -> pd.DataFrame | list[dict[str, Any]]:
    """Fetch the MitoCarta3.0 inventory of mammalian mitochondrial proteins and pathways.

    MitoCarta3.0 (Broad Institute) is an inventory of genes encoding proteins with strong support
    of mitochondrial localization, with sub-mitochondrial localization and pathway annotations.
    See https://www.broadinstitute.org/mitocarta/.

    Args:
    - species   Species to fetch: 'human' (default) or 'mouse'
                ('homo_sapiens'/'mus_musculus' are also accepted).
    - which     Which table to return:
                'mitocarta' (default) -> the MitoCarta3.0 inventory of mitochondrial genes.
                'all_genes'           -> all genes scored for mitochondrial localization (Maestro scores).
                'pathways'            -> the MitoPathways hierarchy and the genes in each pathway.
    - json      If True, returns a list of dictionaries instead of a pandas DataFrame (default: False).
    - save      If True, saves the result to 'gget_mitocarta_{species}_{which}.csv'
                (or .json if json=True) in the current working directory (default: False).
    - verbose   True/False whether to print progress information (default: True).

    Returns the requested MitoCarta3.0 table as a pandas DataFrame (or a list of dictionaries if json=True).
    """
    species_key = _SPECIES_ALIASES.get(species.lower())
    if species_key is None:
        raise ValueError(
            f"Species '{species}' not supported. MitoCarta3.0 is available for 'human' and 'mouse' only.\n"
        )

    if which not in _WHICH_TO_SHEET_PREFIX:
        raise ValueError(
            f"Argument 'which' must be one of {sorted(_WHICH_TO_SHEET_PREFIX)}, but '{which}' was passed.\n"
        )

    url = MITOCARTA_URLS[species_key]

    if verbose:
        logger.info(f"Downloading MitoCarta3.0 ({species_key}) from {url} ...")

    response = requests.get(url, timeout=DEFAULT_REQUESTS_TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError(
            f"MitoCarta3.0 download returned status code {response.status_code} ({url}). Please try again.\n"
        )

    try:
        excel_file = pd.ExcelFile(io.BytesIO(response.content), engine="xlrd")
    except ImportError as e:
        raise RuntimeError(
            "Reading the MitoCarta3.0 Excel file requires the 'xlrd' package. Install it with `pip install xlrd`.\n"
        ) from e

    # Resolve the sheet name by its leading character (species word differs between human/mouse)
    prefix = _WHICH_TO_SHEET_PREFIX[which]
    matching = [name for name in excel_file.sheet_names if name.startswith(prefix)]
    if not matching:
        raise RuntimeError(
            f"Could not find the '{which}' sheet in the MitoCarta3.0 workbook. "
            f"Available sheets: {excel_file.sheet_names}\n"
        )
    sheet_name = matching[0]

    if verbose:
        logger.info(f"Parsing MitoCarta3.0 sheet '{sheet_name}'.")

    df = pd.read_excel(excel_file, sheet_name=sheet_name)

    if save:
        if json:
            records = json_package.loads(df.to_json(orient="records", force_ascii=False))
            with open(f"gget_mitocarta_{species_key}_{which}.json", "w", encoding="utf-8") as f:
                json_package.dump(records, f, ensure_ascii=False, indent=4)
        else:
            df.to_csv(f"gget_mitocarta_{species_key}_{which}.csv", index=False)

    if json:
        result: list[dict[str, Any]] = json_package.loads(df.to_json(orient="records", force_ascii=False))
        return result

    return df
