import io
import json as json_package

import pandas as pd
import requests

from .utils import set_up_logger

logger = set_up_logger()

# Custom functions
# Constants
from .constants import EXPRESSION_URL, GENECORR_URL  # noqa: E402
from .gget_info import info  # noqa: E402


def archs4(
    gene,
    ensembl=False,
    which="correlation",
    gene_count=100,
    species="human",
    json=False,
    save=False,
    verbose=True,
):
    """Find the most correlated genes or the tissue expression atlas of a gene of interest.

    Uses data from the human and mouse RNA-seq
    database ARCHS4 (https://maayanlab.cloud/archs4/).

    Args:
    - gene          Short name (Entrez gene symbol) of gene of interest (str), e.g. 'STAT4'.
                    Set 'ensembl=True' to input an Ensembl gene ID, e.g. ENSG00000138378.
    - ensembl       Define as 'True' if 'gene' is an Ensembl gene ID. (Default: False)
    - which         'correlation' (default) or 'tissue'.
                    - 'correlation' returns a gene correlation table that contains the
                    100 most correlated genes to the gene of interest. The Pearson
                    correlation is calculated over all samples and tissues in ARCHS4.
                    - 'tissue' returns a tissue expression atlas calculated from
                    human or mouse samples (as defined by 'species') in ARCHS4.
    - gene_count    Number of correlated genes to return (default: 100).
                    (Only for gene correlation.)
    - species       'human' (default) or 'mouse'.
                    (Only for tissue expression atlas.)
    - json          If True, returns results in json format instead of data frame. Default: False.
    - save          True/False whether to save the results in the local directory.
    - verbose        True/False whether to print progress information. Default True.

    Returns a data frame with the requested results.
    """
    # Check if 'which' argument is valid
    whichs = ["correlation", "tissue"]
    if which not in whichs:
        raise ValueError(f"'which' argument specified as {which}. Expected one of: {', '.join(whichs)}")

    # Check if 'species' argument is valid
    sps = ["human", "mouse"]
    if species not in sps:
        raise ValueError(f"'species' argument specified as {species}. Expected one of: {', '.join(sps)}")

    ## Transform Ensembl IDs to gene symbols
    if ensembl:
        # Remove version number if passed
        gene = gene.split(".")[0]

        info_df = info(gene, verbose=False, pdb=False, ncbi=False, uniprot=False)

        # Check if Ensembl ID was found
        if isinstance(info_df, type(None)):
            logger.error(f"ID '{gene}' not found. Please double-check spelling/arguments and try again.")
            return

        gene_symbol = info_df.loc[gene]["ensembl_gene_name"]

        # If more than one gene symbol was returned, use first entry
        if isinstance(gene_symbol, list):
            gene = gene_symbol[0]
        else:
            gene = gene_symbol

    # Make all gene letters uppercase
    gene = gene.upper()

    if which == "correlation":
        if verbose:
            logger.info(f"Fetching the {gene_count} most correlated genes to {gene} from ARCHS4.")

        ## Find most similar genes based on co-expression
        # Define number of correlated genes to return (+1 to account for Python indexing)
        gene_count = gene_count + 1

        # Dictionary with arguments
        json_dict = {"id": gene, "count": gene_count}

        r = requests.post(url=GENECORR_URL, json=json_dict)

        if not r.ok:
            raise RuntimeError(
                f"Gene correlation API request returned with error code: {r.status_code}. "
                "Please double-check the arguments and try again.\n"
            )

        corr_data = r.json()

        # Check if the request returned an error (e.g. gene not found)
        if "error" in corr_data.keys():
            if corr_data["error"] == f"{gene} not in colids":
                logger.error(
                    f"Gene '{gene}' did not return any gene correlation results. \n"
                    "If the gene is an Ensembl ID, please set argument 'ensembl=True' (for terminal, add flag: [--ensembl])."
                )
                return
            else:
                logger.error(f"Gene correlation request for search term '{gene}' returned error: {corr_data['error']}")
                return

        else:
            # Build data frame from returned results
            corr_df = pd.DataFrame()
            corr_df["gene_symbol"] = corr_data["rowids"]
            corr_df["pearson_correlation"] = corr_data["values"]
            # Drop the first row (since that is the searched gene against itself)
            corr_df = corr_df.iloc[1:, :]

        if json:
            results_dict = json_package.loads(corr_df.to_json(orient="records"))
            if save:
                with open(f"gget_archs4_gene-correlation_{gene}.json", "w", encoding="utf-8") as f:
                    json_package.dump(results_dict, f, ensure_ascii=False, indent=4)

            return results_dict

        else:
            if save:
                corr_df.to_csv(f"gget_archs4_gene-correlation_{gene}.csv", index=False)

            return corr_df

    if which == "tissue":
        if verbose:
            logger.info(f"Fetching the tissue expression atlas of {gene} from {species} ARCHS4 data.")

        ## Find tissue expression data
        ## Define API query
        # # Query for cell line data
        # query = f"search={gene}&species={species}&type=cellline"
        # Query for tissue data
        query = f"search={gene}&species={species}&type=tissue"
        url = EXPRESSION_URL + query

        # Submit API query
        r = requests.post(url=url, headers={"Content-Type": "application/json"})

        if not r.ok:
            raise RuntimeError(
                f"Tissue expression API request returned with error code: {r.status_code}. "
                "Please double-check the arguments and try again.\n"
            )

        # Read query results into data frame
        tissue_exp_df = pd.read_csv(io.StringIO(r.content.decode("utf-8")))
        # Check if any results were returned
        if len(tissue_exp_df) < 2:
            logger.error(
                f"Gene '{gene}' did not return any tissue expression results. \n"
                "If the gene is an Ensembl ID, please set argument 'ensembl=True' (for terminal, add flag: [--ensembl])."
            )
            return

        # Drop NaN rows
        tissue_exp_df = tissue_exp_df.dropna()

        # Drop color columns
        tissue_exp_df = tissue_exp_df.drop(["color"], axis=1)

        # Sort data frame by median expression
        tissue_exp_df = tissue_exp_df.sort_values("median", ascending=False)
        tissue_exp_df = tissue_exp_df.reset_index(drop=True)

        if json:
            results_dict = json_package.loads(tissue_exp_df.to_json(orient="records"))
            if save:
                with open(f"gget_archs4_tissue-expression_{gene}.json", "w", encoding="utf-8") as f:
                    json_package.dump(results_dict, f, ensure_ascii=False, indent=4)

            return results_dict

        else:
            if save:
                tissue_exp_df.to_csv(f"gget_archs4_tissue-expression_{gene}.csv", index=False)

            return tissue_exp_df
