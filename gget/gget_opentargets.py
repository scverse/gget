from __future__ import annotations

import json as json_
import textwrap
from typing import Any, Literal, overload

import pandas as pd

from .constants import DEFAULT_REQUESTS_TIMEOUT, OPENTARGETS_GRAPHQL_API
from .utils import dig, http_json, set_up_logger

logger = set_up_logger()  # export GGET_LOGLEVEL=DEBUG

QUERY_STRING_DISEASES = """
query target($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    associatedDiseases {
      rows {
        score
        disease {
          id
          name
          description
        }
      }
    }
  }
}
"""

QUERY_STRING_DRUGS = """
query target($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    drugAndClinicalCandidates {
      rows {
        drug {
          id
          name
          drugType
          mechanismsOfAction {
            rows {
              mechanismOfAction
            }
          }
          description
          # synonyms and tradeNames are now [DrugLabelAndSource!]! (were scalar
          # lists); query the `label` sub-field so _collapse_singletons flattens
          # each {label: "X"} back to "X", preserving the list[str] shape users
          # see in the resulting DataFrame.
          synonyms {
            label
          }
          tradeNames {
            label
          }
          maximumClinicalStage
          indications {
            rows {
              disease {
                id
                name
              }
            }
          }
        }
      }
    }
  }
}
"""

QUERY_STRING_TRACTABILITY = """
query target($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    tractability {
      modality
      label
      value
    }
  }
}
"""

QUERY_STRING_PHARMACOGENETICS = """
query target($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    pharmacogenomics {
      variantId
      genotypeId
      genotype
      variantFunctionalConsequence {
        id
        label
      }
      drugs {
        drug {
          id
          name
        }
      }
      phenotypeText
      genotypeAnnotationText
      pgxCategory
      isDirectTarget
      evidenceLevel
      datasourceId
      literature
    }
  }
}
"""

# OpenTargets retired the per-tissue `target.expressions` field (it now returns an
# empty list for every gene). Baseline expression data moved to the paginated
# `target.baselineExpression { count rows { ... } }` field, which provides per-biosample
# (tissue and/or cell type) expression summary statistics. The page `size` is supplied
# as a GraphQL variable so it can be driven by the caller's `limit` (and capped at the
# API's documented max page size). `count` is the true total number of biosamples
# upstream, used to warn the user when the result is truncated.
QUERY_STRING_EXPRESSION = """
query target($ensemblId: String!, $size: Int!) {
  target(ensemblId: $ensemblId) {
    baselineExpression(page: { index: 0, size: $size }) {
      count
      rows {
        tissueBiosample {
          biosampleId
          biosampleName
        }
        celltypeBiosample {
          biosampleId
          biosampleName
        }
        median
        min
        q1
        q3
        max
        unit
        datasourceId
        datatypeId
      }
    }
  }
}
"""

# OpenTargets caps a single GraphQL page at 3000 rows.
MAX_EXPRESSION_PAGE_SIZE = 3000

QUERY_STRING_DEPMAP = """
query target($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    depMapEssentiality {
      tissueId
      tissueName
      screens {
        cellLineName
        mutation
        expression
        diseaseFromSource
        depmapId
        geneEffect
      }
    }
  }
}
"""

QUERY_STRING_INTERACTIONS = """
query target($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    interactions {
      rows {
        score
        count
        sourceDatabase
        intA
        targetA {
          id
          approvedSymbol
        }
        intABiologicalRole
        speciesA {
          taxonId
        }
        intB
        targetB {
          id
          approvedSymbol
        }
        intBBiologicalRole
        speciesB {
          taxonId
        }
      }
    }
  }
}
"""

OPENTARGETS_RESOURCES = {
    "diseases",
    "drugs",
    "tractability",
    "pharmacogenetics",
    "expression",
    "depmap",
    "interactions",
}


def _collapse_singletons(obj: Any) -> Any:
    """Recursively collapse nested single-element lists and single dicts with one key.

    - nested single-element lists
    - single dicts with one key → value.
    """
    # -------------------------
    # Case 1: list
    # -------------------------
    if isinstance(obj, list):
        # flatten nested lists
        def flatten(x):
            for el in x:
                if isinstance(el, list):
                    yield from flatten(el)
                else:
                    yield el

        flat = list(flatten(obj))
        flat = [el for el in flat if el is not None]

        # if exactly one element → recurse
        if len(flat) == 1:
            return _collapse_singletons(flat[0])

        # otherwise recurse inside but keep structure
        return [_collapse_singletons(el) for el in flat]

    # -------------------------
    # Case 2: dict
    # -------------------------
    if isinstance(obj, dict):
        # recurse into values
        obj = {k: _collapse_singletons(v) for k, v in obj.items()}

        if len(obj) == 0:
            return None

        # if single key → collapse
        if len(obj) == 1:
            return next(iter(obj.values()))

        return obj

    # -------------------------
    # Base case
    # -------------------------
    return obj


def _make_hashable(x: Any) -> Any:
    if isinstance(x, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in x.items()))
    elif isinstance(x, list):
        return tuple(_make_hashable(v) for v in x)
    elif isinstance(x, set):
        return tuple(sorted(_make_hashable(v) for v in x))
    else:
        return x


def _unhash(x: Any) -> Any:
    if isinstance(x, tuple):
        # detect dict-like tuples
        if all(isinstance(i, tuple) and len(i) == 2 for i in x):
            return {k: _unhash(v) for k, v in x}
        return [_unhash(v) for v in x]
    return x


@overload
def opentargets(
    ensembl_id: str,
    resource: str = "diseases",
    limit: int | None = None,
    verbose: bool = True,
    wrap_text: bool = False,
    filters: dict[str, Any] | None = None,
    json: Literal[False] = False,
) -> pd.DataFrame: ...


@overload
def opentargets(
    ensembl_id: str,
    resource: str = "diseases",
    limit: int | None = None,
    verbose: bool = True,
    wrap_text: bool = False,
    filters: dict[str, Any] | None = None,
    json: Literal[True] = ...,
) -> list[dict[str, Any]]: ...


def opentargets(
    ensembl_id: str,
    resource: str = "diseases",
    limit: int | None = None,
    verbose: bool = True,
    wrap_text: bool = False,
    filters: dict[str, Any] | None = None,
    json: bool = False,
) -> pd.DataFrame | list[dict[str, Any]]:
    """Query OpenTargets for data associated with a given Ensembl gene ID.

    Args:

    - ensembl_id    Ensembl gene ID to be queried (str), e.g. "ENSG00000169194".
    - resource      Defines type of information to be returned.
                    "diseases":         Returns diseases associated with the gene (default).
                    "drugs":            Returns drugs associated with the gene.
                    "tractability":     Returns tractability data for the gene.
                    "pharmacogenetics": Returns pharmacogenetics data for the gene.
                    "expression":       Returns baseline expression per biosample (tissue and/or cell type) as
                                        summary statistics (median, min, q1, q3, max, unit) with tissueBiosample/
                                        celltypeBiosample identifiers and datasourceId/datatypeId.
                    "depmap":           Returns DepMap gene-disease effect data for the gene.
                    "interactions":     Returns protein-protein interactions for the gene.
    - limit         Limit the number of results returned (default: No limit).
                    Note: Not compatible with the 'tractability' and 'depmap' resources.
    - verbose       Print progress messages (default: True).
    - wrap_text     If True, displays data frame with wrapped text for easy reading. Default: False.
    - filters       Filters to apply to the data. Supported filters by equality for any column in the returned data frame. Dictionary of {column: value} pairs. Default: None (no filters applied).
    - json          If True, returns results in JSON format instead of as a Data Frame. Default: False.


    Returns requested information in DataFrame format.
    """
    if resource == "diseases":
        query_string = QUERY_STRING_DISEASES
        rows_path = ["associatedDiseases", "rows"]
    elif resource == "drugs":
        query_string = QUERY_STRING_DRUGS
        rows_path = ["drugAndClinicalCandidates", "rows"]
    elif resource == "tractability":
        query_string = QUERY_STRING_TRACTABILITY
        rows_path = ["tractability"]
    elif resource == "pharmacogenetics":
        query_string = QUERY_STRING_PHARMACOGENETICS
        rows_path = ["pharmacogenomics"]
    elif resource == "expression":
        query_string = QUERY_STRING_EXPRESSION
        rows_path = ["baselineExpression", "rows"]
        # Drive the page size from `limit` so a small limit fetches only what's needed
        # and (crucially) a large/absent limit fetches everything up to the API max,
        # rather than silently capping at a fixed page size.
        expression_page_size = min(limit, MAX_EXPRESSION_PAGE_SIZE) if limit is not None else MAX_EXPRESSION_PAGE_SIZE
    elif resource == "depmap":
        query_string = QUERY_STRING_DEPMAP
        rows_path = [
            "depMapEssentiality",
            "_FLATTEN_screens",
        ]  # * _FLATTEN_ indicates that we want to flatten the nested 'screens' field into the main table
    elif resource == "interactions":
        query_string = QUERY_STRING_INTERACTIONS
        rows_path = ["interactions", "rows"]
    else:
        raise ValueError(
            f"'resource' argument specified as {resource}. Expected one of: {', '.join(OPENTARGETS_RESOURCES)}"
        )

    variables = {"ensemblId": ensembl_id}
    if resource == "expression":
        variables["size"] = expression_page_size

    if verbose:
        logger.info(f"Querying OpenTargets for {resource} associated with {ensembl_id}...")
        logger.debug(f"GraphQL query string:\n{query_string}\n\nWith variables:\n{variables}")

    api_response = http_json(
        "POST",
        OPENTARGETS_GRAPHQL_API,
        context="OpenTargets GraphQL",
        json={"query": query_string, "variables": variables},
        timeout=DEFAULT_REQUESTS_TIMEOUT,
    )

    if "errors" in api_response:
        raise ValueError(api_response["errors"])

    if verbose:
        logger.debug(f"Raw API response:\n{json_.dumps(api_response, indent=2)}")

    # if json:
    #     return api_response

    api_target = dig(api_response, "data", "target", context="OpenTargets GraphQL")

    # Warn when the gene has more baseline-expression biosamples upstream than a single
    # API page can return (only possible when the user did not set an explicit limit;
    # an explicit limit is treated as intentional). Without this, the result would be a
    # silent partial slice of the data.
    if resource == "expression" and limit is None:
        total = (api_target.get("baselineExpression") or {}).get("count")
        if isinstance(total, int) and total > MAX_EXPRESSION_PAGE_SIZE:
            logger.warning(
                f"{ensembl_id} has {total} baseline-expression biosamples, but the OpenTargets API "
                f"returns at most {MAX_EXPRESSION_PAGE_SIZE} per request; the result is truncated to "
                f"{MAX_EXPRESSION_PAGE_SIZE}. Use the 'filters' argument (e.g. datasourceId or datatypeId) "
                "to narrow the query to the biosamples you need."
            )

    rows = api_target
    for row_key in rows_path:
        if not row_key.startswith("_FLATTEN_"):
            rows = rows[row_key]
        else:
            row_key = row_key.replace("_FLATTEN_", "")
            rows = [
                {
                    **{k: v for k, v in row.items() if k != row_key},  # keep everything except the nested field
                    **subdict,  # unpack the nested dict
                }
                for row in rows
                for subdict in row[row_key]
            ]

    if len(rows) == 0:
        if verbose:
            logger.info(f"No {resource} data found for {ensembl_id}.")
        return pd.DataFrame() if not json else []

    # ---------------------------
    # If JSON → return normalized JSON
    # ---------------------------
    df = pd.json_normalize(rows, sep=".")
    df = df.dropna(axis=1, how="all")  # drop any all-NaN columns
    df = df.dropna(axis=0, how="all")  # drop any all-NaN rows
    df = df.map(_make_hashable).drop_duplicates()

    if limit is not None:
        df = df.head(limit)

    df = df.map(_unhash)
    df = df.map(_collapse_singletons)

    if filters is not None:
        for filter_key, filter_value in filters.items():
            if filter_key not in df.columns:
                raise ValueError(
                    f"Filter key '{filter_key}' not found in data columns. Available columns: {', '.join(df.columns)}"
                )
            df = df[df[filter_key] == filter_value]

    if wrap_text:
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].apply(lambda x: textwrap.fill(str(x), width=40) if isinstance(x, str) else x)

    if json:
        return json_.loads(df.to_json(orient="records", force_ascii=False))

    return df
