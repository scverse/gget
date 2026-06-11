import json as json_package
import os
import re

import numpy as np
import pandas as pd

from .utils import get_uniprot_seqs, set_up_logger, tsv_to_df

logger = set_up_logger()

from .constants import UNIPROT_REST_API  # noqa: E402
from .gget_diamond import diamond  # noqa: E402
from .gget_setup import (  # noqa: E402
    ELM_CLASSES_TSV,
    ELM_INSTANCES_FASTA,
    ELM_INSTANCES_TSV,
    ELM_INTDOMAINS_TSV,
)


def motif_in_query(row):
    """Checks if motif is in the overlapping region with the query sequence.

    Args:
    row     - row in dataframe

    Returns: True if the motif is in between the subject start and end of sequence. False otherwise
    """
    return (
        True
        if (row["motif_start_in_subject"] >= row["subject_start"]) & (row["motif_end_in_subject"] <= row["subject_end"])
        else False
    )


def get_elm_instances(UniProtID):
    """Get ELM instances and their information from local ELM tsv files.

    Args:
    - UniProtID   UniProt Acc to search for in the accession column of ELM tsv files.

    Returns: dataframe combining ELM instances and information (description, functional site...)
    """
    # Get matching rows from elm_instances.tsv
    # ELM Instances.tsv file contains 5 lines before headers and data
    df_full_instances = tsv_to_df(ELM_INSTANCES_TSV, skiprows=5)
    df_instances_matching = df_full_instances[df_full_instances["Primary_Acc"] == UniProtID]
    # Rename columns
    df_instances_matching = df_instances_matching.rename(
        columns={
            "Primary_Acc": "Ortholog_UniProt_Acc",
            "Start": "motif_start_in_subject",
            "End": "motif_end_in_subject",
        }
    )

    # Get class descriptions
    df_classes = tsv_to_df(ELM_CLASSES_TSV, skiprows=5)
    df_classes = df_classes.rename(columns={"Accession": "class_accession"})

    # Get interaction domains
    df_intdomains = tsv_to_df(ELM_INTDOMAINS_TSV)
    df_intdomains = df_intdomains.rename(
        columns={
            "ELM identifier": "ELMIdentifier",
            "Interaction Domain Id": "InteractionDomainId",
            "Interaction Domain Description": "InteractionDomainDescription",
            "Interaction Domain Name": "InteractionDomainName",
        }
    )

    # Merge data frames using ELM Identifier
    df_final = df_instances_matching.merge(df_classes, how="left", on="ELMIdentifier")
    df_final = df_final.merge(df_intdomains, how="left", on="ELMIdentifier")

    return df_final


def seq_workflow(
    sequences,
    # sequence_lengths,
    reference,
    sensitivity,
    threads,
    verbose,
    diamond_binary,
):
    """Alignment of sequence using DIAMOND to get UniProt Acc. Use the UniProt Acc to construct an ortholog dataframe similar to the UniProt workflow

    except for additional columns for start, end and whether the motif overlaps the subject sequence.

    Args:
    sequences        - list of user input amino acid sequence
    sequence_lengths - list of lengths respective to each sequence DEPRECATED
    reference        - Path to reference FASTA file
    sensitivity      - Sensitivity of DIAMOND alignment.
                       One of the following: fast, mid-sensitive, sensitive, more-sensitive, very-sensitive or ultra-sensitive.
    threads          - Number of threads used for DIAMOND alignment
    verbose          - If True, turns on logging for INFO_level messages
    diamond_binary   - Path to DIAMOND binary

    Returns: data frame consisting of ELM instances, class information, start, end in query, and if motif overlaps with subject sequence
    """
    if verbose:
        logger.info(
            f"ORTHO Performing pairwise sequence alignment against ELM database using DIAMOND for {len(sequences)} sequence(s)..."
        )

    df = pd.DataFrame()
    seq_number = 1
    # for sequence, seq_len in zip(sequences, sequence_lengths):
    for sequence in sequences:
        df_diamond = diamond(
            query=sequence,
            reference=reference,
            sensitivity=sensitivity,
            threads=threads,
            verbose=verbose,
            diamond_binary=diamond_binary,
        )

        if len(df_diamond) == 0:
            logger.warning(
                f"ORTHO Sequence {seq_number}/{len(sequences)}: No orthologous proteins found in ELM database."
            )

        else:
            # Construct df with elm instances from UniProt Acc returned from diamond
            # TODO double check that this gets info if more than one UniProt Acc matched
            if verbose:
                uniprot_ids = [str(id).split("|")[1] for id in df_diamond["subject_accession"].values]
                logger.info(
                    f"ORTHO Sequence {seq_number}/{len(sequences)}: DIAMOND found the following orthologous proteins: {', '.join(uniprot_ids)}. Retrieving ELMs for each UniProt Acc..."
                )

            for i, uniprot_id in enumerate(df_diamond["subject_accession"].values):
                # print(f"UniProt Acc {uniprot_id}")
                df_elm = get_elm_instances(str(uniprot_id).split("|")[1])
                # missing motifs other than the first one
                # df_elm["query_cover"] = df_diamond["length"].values[i] / seq_len * 100
                df_elm["query_seq_length"] = df_diamond["query_seq_length"].values[i]
                df_elm["subject_seq_length"] = df_diamond["subject_seq_length"].values[i]
                df_elm["alignment_length"] = df_diamond["length"].values[i]
                df_elm["identity_percentage"] = df_diamond["identity_percentage"].values[i]
                df_elm["query_start"] = int(df_diamond["query_start"].values[i])
                df_elm["query_end"] = int(df_diamond["query_end"].values[i])
                df_elm["subject_start"] = int(df_diamond["subject_start"].values[i])
                df_elm["subject_end"] = int(df_diamond["subject_end"].values[i])
                df_elm["motif_inside_subject_query_overlap"] = df_elm.apply(motif_in_query, axis=1)

                df = pd.concat([df, df_elm])

        seq_number += 1

    return df


def regex_match(sequence):
    """Compare ELM regex with input sequence and return all matching elms.

    Args:
    sequence - user input sequence (can be either amino acid seq or UniProt Acc)

    Returns
    -------
    df_final - dataframe containing regex matches
    TODO: Make sure this returns empty dataframe if no matches were found

    """
    # Get all motif regex patterns from elm db local file
    df_elm_classes = tsv_to_df(ELM_CLASSES_TSV, skiprows=5)
    df_full_instances = tsv_to_df(ELM_INSTANCES_TSV, skiprows=5)
    df_full_intdomains = tsv_to_df(ELM_INTDOMAINS_TSV)
    df_full_intdomains = df_full_intdomains.rename(
        columns={
            "ELM identifier": "ELMIdentifier",
            "Interaction Domain Id": "InteractionDomainId",
            "Interaction Domain Description": "InteractionDomainDescription",
            "Interaction Domain Name": "InteractionDomainName",
        }
    )

    elm_ids = df_elm_classes["Accession"]
    regex_patterns = df_elm_classes["Regex"]

    df_final = pd.DataFrame()

    # Compare ELM regex with input sequence and return all matching elms
    for elm_id, pattern in zip(elm_ids, regex_patterns, strict=False):
        regex_matches = re.finditer(f"(?=({pattern}))", sequence)

        for match_string in regex_matches:
            elm_row = df_elm_classes[df_elm_classes["Accession"] == elm_id]
            elm_row.insert(
                loc=1,
                column="Instances (Matched Sequence)",
                value=match_string.group(1),
            )

            (start, end) = match_string.span(1)
            elm_row.insert(loc=2, column="motif_start_in_query", value=int(start + 1))
            elm_row.insert(loc=3, column="motif_end_in_query", value=int(end))

            [str(x) for x in elm_row["ELMIdentifier"]][0]

            # df_instances_matching = df_full_instances.loc[
            #     df_full_instances["ELMIdentifier"] == elm_identifier
            # ]

            # merge two dataframes using ELM Identifier, since some Accessions are missing from elm_instances.tsv
            elm_row = elm_row.merge(df_full_instances, how="left", on="ELMIdentifier")
            elm_row = elm_row.merge(df_full_intdomains, how="left", on="ELMIdentifier")

            df_final = pd.concat([df_final, elm_row])

    if len(df_final) > 0:
        df_final.rename(columns={"Accession_x": "Instance_accession"}, inplace=True)

    return df_final


def elm(
    sequence,
    uniprot=False,
    sensitivity="very-sensitive",
    threads=1,
    diamond_binary=None,
    expand=False,
    verbose=True,
    json=False,
    out=None,
):
    """Locally predicts Eukaryotic Linear Motifs from an amino acid sequence or UniProt Acc using

    data from the ELM database (http://elm.eu.org/).

    Args:
    - sequence         Amino acid sequence or Uniprot Acc (str).
                       If Uniprot Acc, set 'uniprot==True'.
    - uniprot          Set to True if the input is a Uniprot Acc instead of an amino acid sequence. Default: False.
    - sensitivity      Sensitivity of DIAMOND alignment.
                       One of the following: fast, mid-sensitive, sensitive, more-sensitive, very-sensitive, or ultra-sensitive.
                       Default: "very-sensitive"
    - threads          Number of threads used in DIAMOND alignment. Default: 1.
    - diamond_binary   Path to DIAMOND binary. Default: None -> Uses DIAMOND binary installed with gget.
    - expand           Expand the information returned in the regex data frame to include the protein names, organisms
                       and references that the motif was orignally validated on. Default: False.
    - verbose          True/False whether to print progress information. Default: True.
    - json             If True, returns results in json format instead of data frame. Default: False.
    - out              Path to folder to save results in. Default: Standard out, temporary files are deleted.

    Returns two data frames (or JSON formatted dictionaries if json=True):
    The first contains information on motifs experimentally validated in orthologous proteins and
    the second contains motifs found directly based on regex matches in the provided sequence.

    ELM data can be downloaded & distributed for non-commercial use according to the ELM Software License Agreement (http://elm.eu.org/media/Elm_academic_license.pdf).
    """
    # Check if ELM files were downloaded
    if (
        not os.path.exists(ELM_INSTANCES_FASTA)
        or not os.path.exists(ELM_CLASSES_TSV)
        or not os.path.exists(ELM_INSTANCES_TSV)
        or not os.path.exists(ELM_INTDOMAINS_TSV)
    ):
        raise FileNotFoundError(
            "Some or all ELM database files are missing. Please run 'gget setup elm' (Python: gget.setup('elm')) once to download the necessary files."
        )

    # Let users know when local ELM was last updated
    lines_number = 2
    with open(ELM_CLASSES_TSV) as input_file:
        head = [next(input_file) for _ in range(lines_number)]
    if verbose:
        logger.info(", ".join(head).replace("#", "").replace("\n", ""))
    with open(ELM_INSTANCES_TSV) as input_file:
        head = [next(input_file) for _ in range(lines_number)]
    if verbose:
        logger.info(", ".join(head).replace("#", "").replace("\n", ""))

    # Check validity of amino acid seq
    if not uniprot:
        amino_acids = set("ARNDCQEGHILKMFPSTWYVBZXBJZ")
        # Convert input sequence to upper case letters
        sequence = sequence.upper()

        # If sequence is not a valid amino sequence, raise error
        if not set(sequence) <= amino_acids:
            logger.warning(
                "Input amino acid sequence contains invalid characters. If the input is a UniProt Acc, please use flag --uniprot (Python: uniprot=True)."
            )

    # Build ortholog dataframe
    if verbose:
        logger.info("ORTHO Compiling ortholog information...")
    ortho_df = pd.DataFrame()
    if uniprot:
        ortho_df = get_elm_instances(sequence)

        if len(ortho_df) == 0:
            logger.warning(
                "ORTHO The provided UniProt Accession does not match UniProt Accessions in the ELM database. Fetching amino acid sequence from UniProt..."
            )
            df_uniprot = get_uniprot_seqs(server=UNIPROT_REST_API, ensembl_ids=sequence)

            if len(df_uniprot) > 0:
                # Only grab sequences where IDs match exactly
                aa_seqs = df_uniprot[df_uniprot["uniprot_id"] == sequence]["sequence"].values

                if len(aa_seqs) == 0:
                    raise ValueError(
                        f"No amino acid sequences found for UniProt Acc {sequence} from the UniProt server. Please double-check your UniProt Acc and try again."
                    )

                # seq_lens = [len(seq) for seq in aa_seqs]

            else:
                raise ValueError(
                    f"No amino acid sequences found for UniProt Acc {sequence} from the UniProt server. Please double-check your UniProt Acc and try again."
                )

    if len(ortho_df) == 0:
        # Add input aa sequence and its length to list
        if not uniprot:
            aa_seqs = [sequence]
            # seq_lens = [len(sequence)]

        ortho_df = seq_workflow(
            sequences=aa_seqs,
            # sequence_lengths=seq_lens,
            reference=ELM_INSTANCES_FASTA,
            sensitivity=sensitivity,
            threads=threads,
            verbose=verbose,
            diamond_binary=diamond_binary,
        )

        if len(ortho_df) == 0:
            logger.warning("ORTHO No ELM database orthologs found for input sequence or UniProt Acc.")

    # Reorder columns of ortholog data frame
    ortho_cols = [
        "Ortholog_UniProt_Acc",
        "ProteinName",
        "class_accession",
        "ELMIdentifier",
        "FunctionalSiteName",
        "Description",
        "InteractionDomainId",
        "InteractionDomainDescription",
        "InteractionDomainName",
        "Regex",
        "Probability",
        "Methods",
        "Organism",
        "query_seq_length",
        "subject_seq_length",
        "alignment_length",
        "identity_percentage",
        "motif_inside_subject_query_overlap",
        "query_start",
        "query_end",
        "subject_start",
        "subject_end",
        "motif_start_in_subject",
        "motif_end_in_subject",
        "References",
        "InstanceLogic",
        "PDB",
        "#Instances",
        "#Instances_in_PDB",
    ]
    for col in ortho_cols:
        if col not in ortho_df.columns:
            ortho_df[col] = np.nan

    ortho_df = ortho_df[ortho_cols]
    # Remove false positives and true negatives
    ortho_df = ortho_df[
        (ortho_df["InstanceLogic"] != "false positive") & (ortho_df["InstanceLogic"] != "true negative")
    ]
    # Drop duplicate rows and reset the index
    ortho_df = ortho_df.drop_duplicates().reset_index(drop=True)

    # Build data frame containing regex motif matches
    if verbose:
        logger.info("REGEX Finding regex motif matches...")
    fetch_aa_failed = False
    if uniprot:
        # use amino acid sequence associated with UniProt Acc to do regex match

        # do not fetch sequence again if already done above
        if "df_uniprot" not in locals():
            df_uniprot = get_uniprot_seqs(UNIPROT_REST_API, sequence)

        if len(df_uniprot) > 0:
            # Only grab sequences where IDs match exactly
            sequences = df_uniprot[df_uniprot["uniprot_id"] == sequence]["sequence"].values

            if len(sequences) == 0:
                logger.warning(
                    f"REGEX No amino acid sequences found for UniProt Acc {sequence} from the UniProt server."
                )
                fetch_aa_failed = True
            else:
                if len(sequences) > 1:
                    logger.warning(
                        f"REGEX More than one amino acid sequence found for UniProt Acc {sequence}. Using best match to find regex motifs."
                    )
                sequence = sequences[0]

    df_regex_matches = pd.DataFrame()
    if not fetch_aa_failed:
        df_regex_matches = regex_match(sequence)

    if len(df_regex_matches) == 0:
        logger.warning("REGEX No regex matches found for input sequence or UniProt Acc.")

    # Reorder regex columns
    if expand:
        regex_cols = [
            "Instance_accession",
            "ELMIdentifier",
            "FunctionalSiteName",
            "ELMType",
            "Description",
            "InteractionDomainId",
            "InteractionDomainDescription",
            "InteractionDomainName",
            "Regex",
            "Instances (Matched Sequence)",
            # "Probability",
            "motif_start_in_query",
            "motif_end_in_query",
            # "Methods",
            "ProteinName",
            "Organism",
            "References",
            "InstanceLogic",
            "#Instances",
            "#Instances_in_PDB",
        ]
    else:
        regex_cols = [
            "Instance_accession",
            "ELMIdentifier",
            "FunctionalSiteName",
            "ELMType",
            "Description",
            "InteractionDomainId",
            "InteractionDomainDescription",
            "InteractionDomainName",
            "Regex",
            "Instances (Matched Sequence)",
            # "Probability",
            "motif_start_in_query",
            "motif_end_in_query",
            # "Methods",
            # "ProteinName",
            # "Organism",
            # "References",
            "InstanceLogic",
            "#Instances",
            "#Instances_in_PDB",
        ]

    for col in regex_cols:
        if col not in df_regex_matches.columns:
            df_regex_matches[col] = np.nan

    df_regex_matches = df_regex_matches[regex_cols]
    # Remove false positives and true negatives
    df_regex_matches = df_regex_matches[
        (df_regex_matches["InstanceLogic"] != "false positive") & (df_regex_matches["InstanceLogic"] != "true negative")
    ]
    # Drop duplicates and reset index
    df_regex_matches = df_regex_matches.drop_duplicates().reset_index(drop=True)

    # Create out folder if it does not exist
    if out:
        os.makedirs(out, exist_ok=True)

    if json:
        ortholog_dict = json_package.loads(ortho_df.to_json(orient="records"))
        regex_dict = json_package.loads(df_regex_matches.to_json(orient="records"))

        if out:
            with open(f"{out}/ELM_ortho_results.json", "w", encoding="utf-8") as f:
                json_package.dump(ortholog_dict, f, ensure_ascii=False, indent=4)
            with open(f"{out}/ELM_regex_results.json", "w", encoding="utf-8") as f:
                json_package.dump(regex_dict, f, ensure_ascii=False, indent=4)

        return ortholog_dict, regex_dict

    else:
        if out:
            ortho_df.to_csv(f"{out}/ELM_ortho_results.csv", index=False)
            df_regex_matches.to_csv(f"{out}/ELM_regex_results.csv", index=False)

    return ortho_df, df_regex_matches
