import pandas as pd
import json as json_

from .utils import set_up_logger, json_list_to_df, http_json, dig

logger = set_up_logger()


def _bgee_species(gene_id: str, verbose=True):
    """
    Get species ID from Bgee
    :param gene_id: Ensembl gene ID
    :param verbose: log progress
    :return: species ID
    """

    if verbose:
        logger.info(f"Getting species ID for gene {gene_id} from Bgee")

    payload = http_json(
        "GET",
        "https://bgee.org/api/",
        context="Bgee API (species lookup)",
        params={
            "display_type": "json",
            "page": "gene",
            "action": "general_info",
            "gene_id": gene_id,
        },
    )

    genes_data = dig(payload, "data", "genes", context="Bgee API (species lookup)")
    assert len(genes_data) == 1
    gene_data = genes_data[0]

    species: int = gene_data["species"]["genomeSpeciesId"]
    return species


def _bgee_orthologs(gene_id, json=False, verbose=True):
    """
    Get orthologs for a gene from Bgee

    Args:

    :param gene_id: Ensembl gene ID
    :param json:    return JSON instead of DataFrame
    :param verbose: log progress

    Returns requested information as a DataFrame or JSON
    """
    # if single Ensembl ID passed as string, convert to list
    if isinstance(gene_id, list):
        raise ValueError(
            "One a single gene ID can be passed at a time for ortholog searches."
        )

    # must first obtain species
    species = _bgee_species(gene_id, verbose=verbose)

    if verbose:
        logger.info(f"Getting orthologs for gene {gene_id} from Bgee")

    # then obtain homologs
    payload = http_json(
        "GET",
        "https://bgee.org/api/",
        context="Bgee API (orthologs)",
        params={
            "display_type": "json",
            "page": "gene",
            "action": "homologs",
            "gene_id": gene_id,
            "species_id": species,
        },
    )

    homologs_data = dig(payload, "data", "orthologsByTaxon", context="Bgee API (orthologs)")
    homologs_data = sum([v["genes"] for v in homologs_data], [])

    df = json_list_to_df(
        homologs_data,
        [
            ("gene_id", "geneId"),
            ("gene_name", "name"),
            ("species_id", "species.id"),
            ("genus", "species.genus"),
            ("species", "species.speciesName"),
        ],
    )

    if json:
        return json_.loads(df.to_json(orient="records", force_ascii=False))
    else:
        return df


def _bgee_expression(gene_id, json=False, verbose=True):
    """
    Get expression data from Bgee

    Args:

    :param gene_id: Ensembl gene ID(s)
    :param json:    return JSON instead of DataFrame
    :param verbose: log progress

    Returns requested information as a DataFrame or JSON
    """
    # if single Ensembl ID passed as string, convert to list
    if isinstance(gene_id, str):
        gene_ids = [gene_id]
    else:
        gene_ids = gene_id

    # make sure all gene IDs correspond to the same species
    species_set = {_bgee_species(gene_id, verbose=verbose) for gene_id in gene_ids}

    if len(species_set) != 1:
        raise RuntimeError("All Ensembl gene IDs must be from a single species.")

    # get the single species from the set
    species = species_set.pop()

    if verbose:
        logger.info(f"Getting expression data for gene {', '.join(gene_ids)} from Bgee")

    # then obtain expression data
    payload = http_json(
        "GET",
        "https://bgee.org/api/",
        context="Bgee API (expression)",
        params={
            "display_type": "json",
            "page": "data",
            "action": "expr_calls",
            "gene_id": gene_ids,
            "species_id": species,
            "cond_param": ["anat_entity", "cell_type"],
            "data_type": "all",
            "get_results": "true",
        },
    )

    expression_data = dig(
        payload, "data", "expressionData", "expressionCalls",
        context="Bgee API (expression)",
    )

    df = json_list_to_df(
        expression_data,
        [
            ("anat_entity_id", "condition.anatEntity.id"),
            ("anat_entity_name", "condition.anatEntity.name"),
            ("score", "expressionScore.expressionScore"),
            ("score_confidence", "expressionScore.expressionScoreConfidence"),
            ("expression_state", "expressionState"),
        ],
    )

    df["score"] = df["score"].astype(float)

    if json:
        return json_.loads(df.to_json(orient="records", force_ascii=False))
    else:
        return df


# noinspection PyShadowingBuiltins
def bgee(
    gene_id,
    type="orthologs",
    json=False,
    verbose=True,
):
    """
    Get orthologs/expression data for a gene from Bgee (https://www.bgee.org/).

    Args:
    type        type of data to retrieve ('expression' or 'orthologs')
    gene_id     Ensembl gene ID
    json        return JSON instead of DataFrame
    verbose     log progress

    Returns requested information as a DataFrame or JSON.
    """
    if type == "expression":
        return _bgee_expression(gene_id, json=json, verbose=verbose)
    elif type == "orthologs":
        return _bgee_orthologs(gene_id, json=json, verbose=verbose)
    else:
        raise ValueError(
            f"Argument type should be 'expression' or 'orthologs', not '{type}'"
        )
