import numpy as np
import pandas as pd
import json as json_package
import requests
from bs4 import BeautifulSoup

# Custom functions
from .utils import (
    rest_query,
    get_uniprot_info,
    wrap_cols_func,
    get_pdb_ids,
    set_up_logger,
    post_query,
)

logger = set_up_logger()

# Constants
from .constants import (
    ENSEMBL_REST_API,
    UNIPROT_REST_API,
    NCBI_URL,
    DEFAULT_REQUESTS_TIMEOUT,
)


## gget info
def info(
    ens_ids,
    wrap_text=False,
    ncbi=True,
    uniprot=True,
    pdb=False,
    json=False,
    verbose=True,
    save=False,
    expand=False,
    ensembl_only=False,
):
    """
    Fetch gene and transcript metadata using Ensembl IDs.

    Args:
    - ens_ids       One or more Ensembl IDs to look up (string or list of strings).
                    Also supports WormBase and Flybase IDs.
    - wrap_text     If True, displays data frame with wrapped text for easy reading. Default: False.
    - ncbi          If False, does not return data from NCBI. Default: True.
    - uniprot       If False, does not return data from UniProt. Default: True.
    - pdb           If True, also returns PDB IDs (might increase run time). Default: False.
    - json          If True, returns results in json/dictionary format instead of data frame. Default: False.
    - verbose       True/False whether to print progress information. Default True.
    - save          True/False wether to save csv with query results in current working directory. Default: False.

    Returns a data frame containing the requested information.

    Deprecated arguments:
    - expand        (gget info now always returns all of the available information)
    - ensembl_only  If True, only returns results from Ensembl (excludes PDB, UniProt, and NCBI results). Default: False.
    """
    # Handle deprecated arguments
    if expand:
        if verbose:
            logger.warning(
                "'expand' argument deprecated! gget info now always returns all of the available information."
            )
    if ensembl_only:
        if verbose:
            logger.warning(
                "'ensembl_only' argument deprecated! Please use arguments 'ncbi=False' and 'uniprot=False'."
            )

    # Set synonyms found by each database initially to none
    ncbi_synonyms = None
    df_uniprot = None
    df_pdb = pd.DataFrame()
    df_ncbi = pd.DataFrame()

    # Rename pdb, uniprot, ncbi arguments
    fetch_ncbi = ncbi
    fetch_uniprot = uniprot
    fetch_pdb = pdb

    # Define Ensembl REST API server
    server = ENSEMBL_REST_API
    # Define type of returned content from REST
    content_type = "application/json"

    ## Clean up Ensembl IDs
    # If single Ensembl ID passed as string, convert to list
    if type(ens_ids) == str:
        ens_ids = [ens_ids]
    # Remove Ensembl ID version if passed
    ens_ids_clean = []
    temp = 0
    for ensembl_ID in ens_ids:
        # But only for Ensembl ID (and not for flybase/wormbase IDs)
        if ensembl_ID.startswith("ENS"):
            ens_ids_clean.append(ensembl_ID.split(".")[0])

            if "." in ensembl_ID and temp == 0:
                if verbose is True:
                    logger.info(
                        "We noticed that you passed a version number with your Ensembl ID.\n"
                        "Please note that gget info will always return information linked to the latest Ensembl ID version (see 'ensembl_id')."
                    )
                temp = +1

        else:
            ens_ids_clean.append(ensembl_ID)

    # Remove duplicates in the Ensembl ID list without changing their order
    ens_ids_clean = sorted(set(ens_ids_clean), key=ens_ids_clean.index)
    # Create second clean list of Ensembl IDs which will not include IDs that were not found
    ens_ids_clean_2 = ens_ids_clean.copy()

    # Initiate dictionary to save results for all IDs in
    master_dict = {}

    # Query REST APIs from https://rest.ensembl.org/
    endpoint = "lookup/id/"
    query = {"ids": ens_ids_clean, "expand": True}

    results_dict = post_query(server, endpoint, query)
    results_dict = {k: v for k, v in results_dict.items() if v is not None}

    for ensembl_ID, df_temp in results_dict.items():
        try:
            # Add Ensembl ID with latest version number to df_temp
            df_temp["ensembl_id"] = str(df_temp["id"]) + "." + str(df_temp["version"])
        except KeyError:
            # Just add Ensembl ID if no version found
            df_temp["ensembl_id"] = str(df_temp["id"])

    # second pass for ids that were not found in the initial query
    ens_ids_clean_tmp = [
        ensembl_ID
        for ensembl_ID in ens_ids_clean
        if ensembl_ID not in results_dict.keys()
    ]

    if len(ens_ids_clean_tmp) > 0:
        # print(f"Second pass for ids: {ens_ids_clean_tmp}")
        # Try submitting query without expand (expand does not work for exons and translation IDs)
        query = {"ids": ens_ids_clean_tmp}
        results_dict_new = post_query(server, endpoint, query)
        results_dict_new = {k: v for k, v in results_dict_new.items() if v is not None}

        for ensembl_ID, df_temp in results_dict_new.items():
            try:
                # Add Ensembl ID with latest version number to df_temp
                df_temp["ensembl_id"] = (
                    str(df_temp["id"]) + "." + str(df_temp["version"])
                )
            except KeyError:
                # Just add Ensembl ID if no version found
                df_temp["ensembl_id"] = str(df_temp["id"])

        results_dict.update(results_dict_new)

    ens_ids_clean_2 = []
    for ensembl_ID in ens_ids_clean:
        if ensembl_ID in results_dict.keys():
            ens_ids_clean_2.append(ensembl_ID)
        else:
            if verbose:
                logger.warning(
                    f"ID '{ensembl_ID}' not found. Please double-check spelling/arguments and try again."
                )

    # rewrite results to be in the input order
    results_dict = {
        ensembl_ID: results_dict[ensembl_ID] for ensembl_ID in ens_ids_clean_2
    }

    master_dict.update(results_dict)

    # Return None if none of the Ensembl IDs were found
    if len(master_dict) == 0:
        return None

    ## Build data frame from dictionary
    df = pd.DataFrame.from_dict(master_dict)

    # Rename indeces
    df = df.rename(
        index={
            "description": "ensembl_description",
            "Parent": "parent_gene",
            "display_name": "ensembl_gene_name",
        }
    )

    if ensembl_only is False:
        # df_temp will hold information from NCBI, UniProt and PDB for each of the Ensembl IDs
        df_temp = pd.DataFrame()

        for ens_id in ens_ids_clean_2:
            if fetch_uniprot is True:
                try:
                    # Get gene names and descriptions from UniProt
                    df_uniprot = get_uniprot_info(
                        UNIPROT_REST_API, ens_id, verbose=verbose
                    )

                except Exception as e:
                    if verbose:
                        logger.warning(
                            f"UniProt server request for ID '{ens_id}' returned the following error:\n{e}"
                        )
                    continue

                if not isinstance(df_uniprot, type(None)):
                    # If two different UniProt IDs for a single query ID are returned, they should be merged into one column
                    # So len(df_uniprot) should always be 1
                    if len(df_uniprot) > 1:
                        # If the above somehow failed, we will only return the first result.
                        df_uniprot = df_uniprot.iloc[[0]]

                        if verbose:
                            logger.warning(
                                f"More than one UniProt match was found for ID {ens_id}. Only the first match and its associated information will be returned."
                            )

                    # Get uniprot synonyms and remove NaN values
                    uni_synonyms = df_uniprot["uni_synonyms"].values[0]
                    uni_synonyms = [
                        item for item in uni_synonyms if not (pd.isnull(item)) == True
                    ]

                    # Transpose UniProt data frame and add Ensembl ID as column name
                    df_uniprot = df_uniprot.T
                    df_uniprot.columns = [ens_id]

                else:
                    if verbose:
                        logger.warning(f"No UniProt entry was found for ID {ens_id}.")

            if fetch_ncbi is True:
                ## Get NCBI gene ID and description (for genes only)
                url = NCBI_URL + f"/gene/?term={ens_id}"

                try:
                    html = requests.get(url, timeout=DEFAULT_REQUESTS_TIMEOUT)
                    # Raise error if status code not "OK" Response
                    if html.status_code != 200:
                        logger.error(
                            f"NCBI server request for {ens_id} returned error status code:\n{html.status_code}.\nPlease double-check arguments or try again later."
                        )

                    ## Web scrape NCBI website for gene ID, synonyms and description
                    soup = BeautifulSoup(html.text, "html.parser")

                    # Check for error message in NCBI return
                    if (
                        soup.find("li", class_="error icon") is not None
                        and "An error has occured"
                        in soup.find("li", class_="error icon").text.strip()
                    ):
                        error_message = soup.find(
                            "li", class_="error icon"
                        ).text.strip()

                        logger.error(
                            f"The NCBI server request for Ensembl ID '{ens_id}' returned the following error:\n{error_message}"
                        )

                        ncbi_gene_id = np.nan
                        ncbi_description = np.nan
                        ncbi_synonyms = None
                        continue

                    # Check if NCBI gene ID is available
                    try:
                        ncbi_gene_id = soup.find("input", {"id": "gene-id-value"}).get(
                            "value"
                        )
                    except AttributeError:
                        ncbi_gene_id = np.nan

                    # Check if NCBI description is available
                    try:
                        ncbi_description = (
                            soup.find("div", class_="section", id="summaryDiv")
                            .find("dt", string="Summary")
                            .find_next_sibling("dd")
                            .text
                        )
                    except AttributeError:
                        ncbi_description = np.nan

                    # Check if NCBI synonyms are available
                    try:
                        ncbi_synonyms = (
                            soup.find("div", class_="section", id="summaryDiv")
                            .find("dt", string="Also known as")
                            .find_next_sibling("dd")
                            .text
                        )
                        # Split NCBI synonyms
                        ncbi_synonyms = ncbi_synonyms.split("; ")
                    except AttributeError:
                        ncbi_synonyms = None

                except Exception as e:
                    logger.error(
                        f"The NCBI server request for Ensembl ID '{ens_id}' returned the following error:\n{e}"
                    )

                    ncbi_gene_id = np.nan
                    ncbi_description = np.nan
                    ncbi_synonyms = None
                    continue

                # Save NCBI info to data frame
                df_ncbi = pd.DataFrame(
                    {
                        "ncbi_gene_id": [ncbi_gene_id],
                        "ncbi_description": [ncbi_description],
                    },
                )

                # Transpose NCBI df and add Ensembl ID as column name
                df_ncbi = df_ncbi.T
                df_ncbi.columns = [ens_id]

            if fetch_pdb:
                ## Get PDB IDs from Ensembl ID
                try:
                    pdb_ids = get_pdb_ids(ens_id)

                except Exception as e:
                    if verbose:
                        logger.warning(
                            f"The PDBe server request for Ensembl ID '{ens_id}' returned the following error:\n{e}"
                        )
                    continue

                # Add pdb_ids to data frame
                if pdb_ids:
                    df_pdb["pdb_id"] = [pdb_ids]
                else:
                    df_pdb["pdb_id"] = [np.nan]

                # Transpose pdb df and add Ensembl ID as column name
                df_pdb = df_pdb.T
                df_pdb.columns = [ens_id]

            ## Handle synonyms
            # If both NCBI and UniProt synonyms available,
            # final synonyms list will be combined set of both lists
            if ncbi_synonyms is not None and not isinstance(df_uniprot, type(None)):
                synonyms = list(set().union(uni_synonyms, ncbi_synonyms))
                # Remove nan values
                synonyms = [item for item in synonyms if not (pd.isnull(item)) == True]

            # Add only UniProt synonyms if NCBI syns not available
            elif ncbi_synonyms is None and not isinstance(df_uniprot, type(None)):
                # Remove nan values
                synonyms = uni_synonyms

            # Add only NCBI synonyms if UniProt syns not available
            elif ncbi_synonyms is not None and isinstance(df_uniprot, type(None)):
                # Remove nan values
                synonyms = ncbi_synonyms

            else:
                synonyms = []

            # Sort synonyms alphabetically (if sortable)
            try:
                synonyms = sorted(synonyms)
            except:
                pass

            # Append dataframes with data from NCBI, UniProt and PDB from ens_id to df_temp
            frames = [df_uniprot, df_ncbi, df_pdb]
            df_uni_ncbi = pd.concat(frames)

            if not df_uni_ncbi.empty:
                df_uni_ncbi.loc["synonyms"] = [synonyms]

            df_temp = pd.concat([df_temp, df_uni_ncbi], axis=1)

        # Append info from NCBI, UniProt and PDB to master df which contains info from Ensembl
        df = pd.concat([df, df_temp])

    # Reindex df (this also drops all unmentioned indices)
    df_final = df.reindex(
        [
            "ensembl_id",
            "uniprot_id",
            "pdb_id",
            "ncbi_gene_id",
            "species",
            "assembly_name",
            "primary_gene_name",
            "ensembl_gene_name",
            "synonyms",
            "parent_gene",
            "protein_names",
            "ensembl_description",
            "uniprot_description",
            "ncbi_description",
            "subcellular_localisation",
            "object_type",
            "biotype",
            "canonical_transcript",
            "seq_region_name",
            "strand",
            "start",
            "end",
        ]
    )

    ens_ids = []
    # Dictionary to save clean info
    data = {
        "all_transcripts": [],
        "transcript_biotypes": [],
        "transcript_names": [],
        "transcript_strands": [],
        "transcript_starts": [],
        "transcript_ends": [],
        "all_exons": [],
        "exon_starts": [],
        "exon_ends": [],
        "all_translations": [],
        "translation_starts": [],
        "translation_ends": [],
    }

    # Collect the transcripts info for each ID in separate lists
    for ens_id in df.columns:
        # Record Ensembl ID
        ens_ids.append(ens_id)

        # Clean up transcript info, if available
        all_transcripts = []
        transcript_biotypes = []
        transcript_names = []
        transcript_strands = []
        transcript_starts = []
        transcript_ends = []

        try:
            for trans_dict in df[ens_id]["Transcript"]:
                try:
                    try:
                        # Add Transcript ID with latest version if available
                        versioned_trans_id = (
                            str(trans_dict["id"]) + "." + str(trans_dict["version"])
                        )
                        all_transcripts.append(versioned_trans_id)
                    except KeyError:
                        # Just add ID if no version found
                        all_transcripts.append(trans_dict["id"])
                except:
                    all_transcripts.append(np.nan)
                try:
                    transcript_names.append(trans_dict["display_name"])
                except:
                    transcript_names.append(np.nan)
                try:
                    transcript_biotypes.append(trans_dict["biotype"])
                except:
                    transcript_biotypes.append(np.nan)
                try:
                    transcript_starts.append(trans_dict["start"])
                except:
                    transcript_starts.append(np.nan)
                try:
                    transcript_ends.append(trans_dict["end"])
                except:
                    transcript_ends.append(np.nan)
                try:
                    transcript_strands.append(trans_dict["strand"])
                except:
                    transcript_strands.append(np.nan)

            data["all_transcripts"].append(all_transcripts)
            data["transcript_biotypes"].append(transcript_biotypes)
            data["transcript_names"].append(transcript_names)
            data["transcript_strands"].append(transcript_strands)
            data["transcript_starts"].append(transcript_starts)
            data["transcript_ends"].append(transcript_ends)

        except:
            data["all_transcripts"].append(np.nan)
            data["transcript_biotypes"].append(np.nan)
            data["transcript_names"].append(np.nan)
            data["transcript_strands"].append(np.nan)
            data["transcript_starts"].append(np.nan)
            data["transcript_ends"].append(np.nan)

        # Clean up exon info, if available
        all_exons = []
        exon_starts = []
        exon_ends = []
        try:
            for exon_dict in df[ens_id]["Exon"]:
                try:
                    try:
                        # Add ID with latest version if available
                        versioned_id = (
                            str(exon_dict["id"]) + "." + str(exon_dict["version"])
                        )
                        all_exons.append(versioned_id)
                    except KeyError:
                        # Just add ID if no version found
                        all_exons.append(exon_dict["id"])
                except:
                    all_exons.append(np.nan)
                try:
                    exon_starts.append(exon_dict["start"])
                except:
                    exon_starts.append(np.nan)
                try:
                    exon_ends.append(exon_dict["end"])
                except:
                    exon_ends.append(np.nan)

            data["all_exons"].append(all_exons)
            data["exon_starts"].append(exon_starts)
            data["exon_ends"].append(exon_ends)

        except:
            data["all_exons"].append(np.nan)
            data["exon_starts"].append(np.nan)
            data["exon_ends"].append(np.nan)

        # Clean up translation info, if available
        all_translations = []
        translation_starts = []
        translation_ends = []
        try:
            for transl_dict in df[ens_id]["Exon"]:
                try:
                    try:
                        # Add ID with latest version if available
                        versioned_id = (
                            str(transl_dict["id"]) + "." + str(transl_dict["version"])
                        )
                        all_translations.append(versioned_id)
                    except KeyError:
                        # Just add ID if no version found
                        all_translations.append(transl_dict["id"])
                except:
                    all_translations.append(np.nan)
                try:
                    translation_starts.append(transl_dict["start"])
                except:
                    translation_starts.append(np.nan)
                try:
                    translation_ends.append(transl_dict["end"])
                except:
                    translation_ends.append(np.nan)

            data["all_translations"].append(all_translations)
            data["translation_starts"].append(translation_starts)
            data["translation_ends"].append(translation_ends)

        except:
            data["all_translations"].append(np.nan)
            data["translation_starts"].append(np.nan)
            data["translation_ends"].append(np.nan)

    # Append cleaned up info to df_final
    df_final = pd.concat(
        [df_final, pd.DataFrame.from_dict(data, orient="index", columns=ens_ids)]
    )

    ## Transpose data frame so each row corresponds to one Ensembl ID
    df_final = df_final.T

    # # Add Ensembl ID column from index
    # df_final.insert(0, "ensembl_id", df_final.index)

    if wrap_text:
        df_wrapped = df_final.copy()
        wrap_cols_func(df_wrapped, ["uniprot_description", "ensembl_description"])

    if json:
        results_dict = json_package.loads(df_final.to_json(orient="index"))

        # Restructure transcripts, translations and exons lists into lists of dictionaries
        for ens_id in df_final.index.values:
            ## Get info for all transcripts
            transcript_ids = results_dict[ens_id]["all_transcripts"]
            transcript_biotypes = results_dict[ens_id]["transcript_biotypes"]
            transcript_names = results_dict[ens_id]["transcript_names"]
            transcript_strands = results_dict[ens_id]["transcript_strands"]
            transcript_starts = results_dict[ens_id]["transcript_starts"]
            transcript_ends = results_dict[ens_id]["transcript_ends"]

            # Delete old keys
            results_dict[ens_id].pop("all_transcripts", None)
            results_dict[ens_id].pop("transcript_biotypes", None)
            results_dict[ens_id].pop("transcript_names", None)
            results_dict[ens_id].pop("transcript_strands", None)
            results_dict[ens_id].pop("transcript_starts", None)
            results_dict[ens_id].pop("transcript_ends", None)

            # Build new dictionary entries
            results_dict[ens_id].update({"all_transcripts": []})
            for (
                transcript_id,
                transcript_biotype,
                transcript_name,
                transcript_strand,
                transcript_start,
                transcript_end,
            ) in zip(
                transcript_ids or [],
                transcript_biotypes or [],
                transcript_names or [],
                transcript_strands or [],
                transcript_starts or [],
                transcript_ends or [],
            ):
                results_dict[ens_id]["all_transcripts"].append(
                    {
                        "transcript_id": transcript_id,
                        "transcript_biotype": transcript_biotype,
                        "transcript_name": transcript_name,
                        "transcript_strand": transcript_strand,
                        "transcript_start": transcript_start,
                        "transcript_end": transcript_end,
                    }
                )

            ## Get info for all exons
            exon_ids = results_dict[ens_id]["all_exons"]
            exon_starts = results_dict[ens_id]["exon_starts"]
            exon_ends = results_dict[ens_id]["exon_ends"]

            # Delete old keys
            results_dict[ens_id].pop("all_exons", None)
            results_dict[ens_id].pop("exon_starts", None)
            results_dict[ens_id].pop("exon_ends", None)

            # Build new dictionary entries
            results_dict[ens_id].update({"all_exons": []})
            for exon_id, exon_start, exon_end in zip(
                exon_ids or [], exon_starts or [], exon_ends or []
            ):
                results_dict[ens_id]["all_exons"].append(
                    {"exon_id": exon_id, "exon_start": exon_start, "exon_end": exon_end}
                )

            ## Get info for all translations
            translation_ids = results_dict[ens_id]["all_translations"]
            translation_starts = results_dict[ens_id]["translation_starts"]
            translation_ends = results_dict[ens_id]["translation_ends"]

            # Delete old keys
            results_dict[ens_id].pop("all_translations", None)
            results_dict[ens_id].pop("translation_starts", None)
            results_dict[ens_id].pop("translation_ends", None)

            # Build new dictionary entries
            results_dict[ens_id].update({"all_translations": []})
            for translation_id, translation_start, translation_end in zip(
                translation_ids or [], translation_starts or [], translation_ends or []
            ):
                results_dict[ens_id]["all_translations"].append(
                    {
                        "translation_id": translation_id,
                        "translation_start": translation_start,
                        "translation_end": translation_end,
                    }
                )

        if save:
            with open("gget_info_results.json", "w", encoding="utf-8") as f:
                json_package.dump(results_dict, f, ensure_ascii=False, indent=4)

        return results_dict

    else:
        if save:
            df_final.to_csv("gget_info_results.csv", index=False)

        return df_final
