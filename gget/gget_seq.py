# Custom functions
from .utils import get_uniprot_seqs, post_query, rest_query, set_up_logger

logger = set_up_logger()
# Constants
from .constants import ENSEMBL_REST_API, UNIPROT_REST_API  # noqa: E402
from .gget_info import info  # noqa: E402


def seq(
    ens_ids,
    translate=False,
    isoforms=False,
    save=False,
    transcribe=None,
    seqtype=None,
    verbose=True,
):
    """Fetch nucleotide or amino acid sequence (FASTA) of a gene or transcript.

    Fetches the gene (and all its isoforms) or transcript by Ensembl, WormBase or FlyBase ID.

    Args:
    - ens_ids       One or more Ensembl IDs (passed as string or list of strings).
                    Also supports WormBase and FlyBase IDs.
    - translate     True/False (default: False -> returns nucleotide sequences).
                    Defines whether nucleotide or amino acid sequences are returned.
                    Nucleotide sequences are fetched from the Ensembl REST API server.
                    Amino acid sequences are fetched from the UniProt REST API server.
    - isoforms      If True, returns the sequences of all known transcripts (default: False).
                    (Only for gene IDs.)
    - save          If True, saves output FASTA to current directory (default: False).
    - verbose       True/False whether to print progress information. Default True.

    Returns a list (or FASTA file if 'save=True') containing the requested sequences.

    Deprecated arguments: 'seqtype', 'transcribe' (use True/False flag 'translate' instead.)
    """
    # Handle deprecated arguments
    if seqtype:
        logger.error("'seqtype' argument deprecated! Please use True/False argument 'translate' instead.")
        return
    if transcribe:
        translate = transcribe

    ## Clean up arguments
    # Clean up Ensembl IDs
    # If single Ensembl ID passed as string, convert to list
    if isinstance(ens_ids, str):
        ens_ids = [ens_ids]
    # Remove Ensembl ID version if passed
    ens_ids_clean = []
    temp = 0
    for ensembl_ID in ens_ids:
        # But only for Ensembl ID (and not for flybase/wormbase IDs)
        if ensembl_ID.startswith("ENS"):
            ens_ids_clean.append(ensembl_ID.split(".")[0])

            if "." in ensembl_ID and temp == 0:
                if verbose:
                    logger.info(
                        "We noticed that you may have passed a version number with your Ensembl ID.\n"
                        "Please note that gget seq will return information linked to the latest Ensembl ID version."
                    )
                temp = +1

        else:
            ens_ids_clean.append(ensembl_ID)

    # Initiate empty 'fasta'
    fasta = []

    ## Fetch nucleotide sequece
    if translate is False:
        # Define Ensembl REST API server
        server = ENSEMBL_REST_API
        # Define type of returned content from REST
        content_type = "application/json"

        # Initiate dictionary to save results for all IDs in
        master_dict = {}

        # Query REST APIs from https://rest.ensembl.org/

        # If isoforms False, just fetch sequences of passed Ensembl ID
        if not isoforms:
            actual_results_dict = {}

            endpoint = "sequence/id/"
            query = {"ids": ens_ids_clean}

            # noinspection PyTypeChecker
            results_list = post_query(server, endpoint, query)
            results_dict = {v["query"]: v for v in results_list if v is not None}

            for ensembl_ID, df_temp in results_dict.items():
                # Delete superfluous entries
                keys_to_delete = ["query", "id", "version", "molecule"]
                for key in keys_to_delete:
                    # Pop keys, None -> do not raise an error if key to delete not found
                    df_temp.pop(key, None)

                # Add results to main dict
                actual_results_dict[ensembl_ID] = {"seq": df_temp}

                if verbose:
                    logger.info(f"Requesting nucleotide sequence of {ensembl_ID} from Ensembl.")

            missing_ids = set(ens_ids_clean) - set(actual_results_dict.keys())

            for missing in missing_ids:
                logger.error(f"ID {missing} not found. Please double-check spelling/arguments and try again.")

            # Add results to master dict
            master_dict.update(actual_results_dict)

        # If isoforms true, fetch sequences of isoforms instead
        # todo this could possibly be refactored to use bulk queries
        else:
            for ensembl_ID in ens_ids_clean:
                # Create dict to save query results
                results_dict = {ensembl_ID: {}}

                # Get ID type (gene, transcript, ...) using gget info
                info_df = info(ensembl_ID, verbose=False, pdb=False, ncbi=False, uniprot=False)

                # Check if Ensembl ID was found
                if isinstance(info_df, type(None)):
                    logger.warning(
                        f"ID '{ensembl_ID}' not found. Please double-check spelling/arguments and try again."
                    )
                    continue

                ens_ID_type = info_df.loc[ensembl_ID]["object_type"]

                # If the ID is a gene, get the IDs of all its transcripts
                if ens_ID_type == "Gene":
                    if verbose:
                        logger.info(f"Requesting nucleotide sequences of all transcripts of {ensembl_ID} from Ensembl.")

                    for transcipt_id in info_df.loc[ensembl_ID]["all_transcripts"]:
                        # Remove version number for Ensembl IDs (not for flybase/wormbase IDs)
                        if transcipt_id.startswith("ENS"):
                            transcipt_id = transcipt_id.split(".")[0]

                        # Try if query is valid
                        try:
                            # Define the REST query
                            query = "sequence/id/" + transcipt_id + "?"
                            # Submit query
                            df_temp = rest_query(server, query, content_type)

                            # Delete superfluous entries
                            keys_to_delete = ["query", "version", "molecule"]
                            for key in keys_to_delete:
                                # Pop keys, None -> do not raise an error if key to delete not found
                                df_temp.pop(key, None)

                            # Add results to main dict
                            results_dict[ensembl_ID].update({f"{transcipt_id}": df_temp})

                        except RuntimeError:
                            logger.error(
                                f"ID {transcipt_id} not found. Please double-check spelling/arguments and try again."
                            )

                # If isoform true, but ID is not a gene; ignore the isoform parameter
                else:
                    # Try if query is valid
                    try:
                        # Define the REST query
                        query = "sequence/id/" + ensembl_ID + "?"

                        # Submit query
                        df_temp = rest_query(server, query, content_type)

                        # Delete superfluous entries
                        keys_to_delete = ["query", "id", "version", "molecule"]
                        for key in keys_to_delete:
                            # Pop keys, None -> do not raise an error if key to delete not found
                            df_temp.pop(key, None)

                        # Add results to main dict
                        results_dict[ensembl_ID].update({"seq": df_temp})

                        logger.info(f"Requesting nucleotide sequence of {ensembl_ID} from Ensembl.")
                        logger.warning("The isoform option only applies to gene IDs.")

                    except RuntimeError:
                        logger.error(
                            f"ID {ensembl_ID} not found. Please double-check spelling/arguments and try again."
                        )

                # Add results to master dict
                master_dict.update(results_dict)

        # Build FASTA file
        for ens_ID in master_dict:
            for key in master_dict[ens_ID].keys():
                if key == "seq":
                    fasta.append(">" + ens_ID + " " + master_dict[ens_ID][key]["desc"])
                    fasta.append(master_dict[ens_ID][key]["seq"])
                else:
                    fasta.append(">" + master_dict[ens_ID][key]["id"] + " " + master_dict[ens_ID][key]["desc"])
                    fasta.append(master_dict[ens_ID][key]["seq"])

    ## Fetch amino acid sequences from UniProt
    if translate is True:
        if isoforms is False:
            # List to collect transcript IDs
            trans_ids = []

            for ensembl_ID in ens_ids_clean:
                # Get ID type (gene, transcript, ...) using gget info
                info_df = info(ensembl_ID, verbose=False, pdb=False, ncbi=False, uniprot=False)

                # Check that Ensembl ID was found
                if isinstance(info_df, type(None)):
                    logger.warning(f"ID '{ensembl_ID}' not found. Please double-check spelling/arguments.")
                    continue

                ens_ID_type = info_df.loc[ensembl_ID]["object_type"]

                # If the ID is a gene, use the ID of its canonical transcript
                if ens_ID_type == "Gene":
                    # Get ID of canonical transcript
                    can_trans = info_df.loc[ensembl_ID]["canonical_transcript"]

                    if ensembl_ID.startswith("ENS"):
                        # Remove Ensembl ID version from transcript IDs and append to transcript IDs list
                        temp_trans_id = can_trans.split(".")[0]
                        trans_ids.append(temp_trans_id)

                    elif ensembl_ID.startswith("WB"):
                        # Remove added "." at the end of transcript IDs
                        temp_trans_id = ".".join(can_trans.split(".")[:-1])
                        # # For WormBase transcript IDs, also remove the version number for submission to UniProt API
                        # temp_trans_id = ".".join(temp_trans_id1.split(".")[:-1])
                        trans_ids.append(temp_trans_id)

                    else:
                        # Remove added "." at the end of other transcript IDs
                        temp_trans_id = ".".join(can_trans.split(".")[:-1])
                        trans_ids.append(temp_trans_id)

                    if verbose:
                        logger.info(
                            f"Requesting amino acid sequence of the canonical transcript {temp_trans_id} of gene {ensembl_ID} from UniProt."
                        )

                # If the ID is a transcript, append the ID directly
                elif ens_ID_type == "Transcript":
                    # # For WormBase transcript IDs, remove the version number for submission to UniProt API
                    # if ensembl_ID.startswith("T"):
                    #     trans_ids.append(".".join(ensembl_ID.split(".")[:-1]))
                    # else:
                    trans_ids.append(ensembl_ID)

                    if verbose:
                        logger.info(f"Requesting amino acid sequence of {ensembl_ID} from UniProt.")

                else:
                    logger.warning(
                        f"{ensembl_ID} not recognized as either a gene or transcript ID. It will not be included in the UniProt query."
                    )

            # Fetch the amino acid sequences of the transcript Ensembl IDs
            df_uniprot = get_uniprot_seqs(UNIPROT_REST_API, trans_ids)

        if isoforms is True:
            # List to collect transcript IDs
            trans_ids = []

            for ensembl_ID in ens_ids_clean:
                # Get ID type (gene, transcript, ...) using gget info
                info_df = info(ensembl_ID, verbose=False, pdb=False, ncbi=False, uniprot=False)

                # Check that Ensembl ID was found
                if isinstance(info_df, type(None)):
                    logger.warning(f"ID '{ensembl_ID}' not found. Please double-check spelling/arguments.")
                    continue

                ens_ID_type = info_df.loc[ensembl_ID]["object_type"]

                # If the ID is a gene, get the IDs of all isoforms
                if ens_ID_type == "Gene":
                    # Get the IDs of all transcripts from the gget info results
                    for transcipt_id in info_df.loc[ensembl_ID]["all_transcripts"]:
                        if ensembl_ID.startswith("ENS"):
                            # Append transcript ID (without Ensembl version number) to list of transcripts to fetch
                            trans_ids.append(transcipt_id.split(".")[0])

                        # elif ensembl_ID.startswith("WB"):
                        #     # For WormBase transcript IDs, remove the version number for submission to UniProt API
                        #     temp_trans_id = ".".join(transcipt_id.split(".")[:-1])
                        #     trans_ids.append(temp_trans_id)

                        else:
                            # Note: No need to remove the added "." at the end of unversioned transcripts here, because "all_transcripts" are returned without it
                            trans_ids.append(transcipt_id)

                    if verbose:
                        logger.info(
                            f"Requesting amino acid sequences of all transcripts of gene {ensembl_ID} from UniProt."
                        )

                elif ens_ID_type == "Transcript":
                    # # For WormBase transcript IDs, remove the version number for submission to UniProt API
                    # if ensembl_ID.startswith("T"):
                    #     trans_ids.append(".".join(ensembl_ID.split(".")[:-1]))

                    # else:
                    trans_ids.append(ensembl_ID)

                    if verbose:
                        logger.info(f"Requesting amino acid sequence of {ensembl_ID} from UniProt.")
                    logger.warning("The isoform option only applies to gene IDs.")

                else:
                    logger.warning(
                        f"{ensembl_ID} not recognized as either a gene or transcript ID. It will not be included in the UniProt query."
                    )

            # Fetch amino acid sequences of all isoforms from the UniProt REST API
            df_uniprot = get_uniprot_seqs(UNIPROT_REST_API, trans_ids)

        # Check if any results were found
        if len(df_uniprot) < 1:
            logger.error("No UniProt amino acid sequences were found for these ID(s).")

        else:
            # Build FASTA file from UniProt results
            for (
                uniprot_id,
                query_ensembl_id,
                gene_name,
                organism,
                sequence_length,
                uniprot_seq,
            ) in zip(
                df_uniprot["uniprot_id"].values,
                df_uniprot["query"].values,
                df_uniprot["gene_name"].values,
                df_uniprot["organism"].values,
                df_uniprot["sequence_length"].values,
                df_uniprot["sequence"].values,
                strict=False,
            ):
                fasta.append(
                    ">"
                    + str(query_ensembl_id)
                    + " uniprot_id: "
                    + str(uniprot_id)
                    + " ensembl_id: "
                    + str(query_ensembl_id)
                    + " gene_name: "
                    + str(gene_name)
                    + " organism: "
                    + str(organism)
                    + " sequence_length: "
                    + str(sequence_length)
                )
                fasta.append(str(uniprot_seq))

    # Save
    if save:
        file = open("gget_seq_results.fa", "w")
        for element in fasta:
            file.write(element + "\n")
        file.close()

    return fasta
