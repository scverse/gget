import base64
import getpass
import gzip
import json as json_package
import os
import re
import shutil
import subprocess
import tarfile

import pandas as pd

# Constants
from .utils import get_latest_cosmic, set_up_logger

logger = set_up_logger()


def is_valid_email(email):
    """Check if an e-mail address is valid."""
    email_pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

    return re.match(email_pattern, email) is not None


def download_reference(download_link, tar_folder_path, file_path, verbose, email=None, password=None, unzip=False):
    """Download a COSMIC reference file using email/password authentication, extract the tar, and optionally unzip it."""
    if not email:
        email = input("Please enter your COSMIC email: ")
    if not is_valid_email(email):
        raise ValueError("The email address is not valid.")
    if not password:
        password = getpass.getpass("Please enter your COSMIC password: ")

    # Concatenate the email and password with a colon
    input_string = f"{email}:{password}\n"

    encoded_bytes = base64.b64encode(input_string.encode("utf-8"))
    encoded_string = encoded_bytes.decode("utf-8")
    curl_command = [
        "curl",
        "-H",
        f"Authorization: Basic {encoded_string}",
        download_link,
    ]

    if verbose:
        logger.info("Downloading data...")

    result = subprocess.run(curl_command, capture_output=True, text=True)

    try:
        response_data = json_package.loads(result.stdout)
    except json_package.JSONDecodeError:
        raise RuntimeError(
            "Failed to download file. Please double-check arguments (especially cosmic_version) and try again."
        ) from None
    try:
        true_download_url = response_data.get("url")
    except AttributeError:
        raise AttributeError("Invalid username or password.") from None

    curl_command2 = ["curl", true_download_url, "--output", f"{tar_folder_path}.tar"]
    result2 = subprocess.run(curl_command2, capture_output=True, text=True)

    if result2.returncode != 0:
        raise RuntimeError(f"Failed to download file. Return code: {result2.returncode}\n{result2.stderr}")

    with tarfile.open(f"{tar_folder_path}.tar", "r") as tar:
        tar.extractall(path=tar_folder_path)
        if verbose:
            logger.info(f"Extracted tar file to {tar_folder_path}")

    if unzip:
        with gzip.open(f"{file_path}.gz", "rb") as f_in:
            with open(file_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            if verbose:
                logger.info(f"Unzipped file to {file_path}")


def select_reference(
    cosmic_project,
    reference_dir,
    grch_version,
    cosmic_version,
    verbose,
    email=None,
    password=None,
    unzip=True,
    overwrite=None,
):
    """Resolve the download link and paths for the requested COSMIC project, then download and extract the database, returning the file path and overwrite flag."""
    # if cosmic_project == "transcriptome":
    #     download_link = f"https://cancer.sanger.ac.uk/api/mono/products/v1/downloads/scripted?path=grch{grch_version}/cosmic/v{cosmic_version}/Cosmic_Genes_Fasta_v{cosmic_version}_GRCh{grch_version}.tar&bucket=downloads"
    #     tarred_folder = f"Cosmic_Genes_Fasta_v{cosmic_version}_GRCh{grch_version}"
    #     contained_file = f"Cosmic_Genes_v{cosmic_version}_GRCh{grch_version}.fasta"

    if cosmic_project == "cancer":
        if grch_version == 38:
            logger.error("CancerMutationCensus data is only available for GRCh37. Define grch_version=37.")
        download_link = f"https://cancer.sanger.ac.uk/api/mono/products/v1/downloads/scripted?path=grch{grch_version}/cmc/v{cosmic_version}/CancerMutationCensus_AllData_Tsv_v{cosmic_version}_GRCh{grch_version}.tar&bucket=downloads"
        tarred_folder = f"CancerMutationCensus_AllData_Tsv_v{cosmic_version}_GRCh{grch_version}"
        contained_file = f"CancerMutationCensus_AllData_v{cosmic_version}_GRCh{grch_version}.tsv"
        if str(cosmic_version) == "100":  # special treatment due to v2
            download_link = download_link.replace(".tar&bucket=downloads", "_v2.tar&bucket=downloads")
            tarred_folder += "_v2"
        if (
            str(cosmic_version) == "99" or str(cosmic_version) == "100"
        ):  # special treatment due to link difference - path=GRCh37 instead of path=grch37
            download_link = download_link.replace(f"path=grch{grch_version}", f"path=GRCh{grch_version}")

    elif cosmic_project == "cell_line":
        download_link = f"https://cancer.sanger.ac.uk/api/mono/products/v1/downloads/scripted?path=grch{grch_version}/cell_lines/v{cosmic_version}/CellLinesProject_GenomeScreensMutant_Tsv_v{cosmic_version}_GRCh{grch_version}.tar&bucket=downloads"
        tarred_folder = f"CellLinesProject_GenomeScreensMutant_Tsv_v{cosmic_version}_GRCh{grch_version}"
        contained_file = f"CellLinesProject_GenomeScreensMutant_v{cosmic_version}_GRCh{grch_version}.tsv"

    elif cosmic_project == "census":
        download_link = f"https://cancer.sanger.ac.uk/api/mono/products/v1/downloads/scripted?path=grch{grch_version}/cosmic/v{cosmic_version}/Cosmic_MutantCensus_Tsv_v{cosmic_version}_GRCh{grch_version}.tar&bucket=downloads"
        tarred_folder = f"Cosmic_MutantCensus_Tsv_v{cosmic_version}_GRCh{grch_version}"
        contained_file = f"Cosmic_MutantCensus_v{cosmic_version}_GRCh{grch_version}.tsv"

    elif cosmic_project == "resistance":
        download_link = f"https://cancer.sanger.ac.uk/api/mono/products/v1/downloads/scripted?path=grch{grch_version}/cosmic/v{cosmic_version}/Cosmic_ResistanceMutations_Tsv_v{cosmic_version}_GRCh{grch_version}.tar&bucket=downloads"
        tarred_folder = f"Cosmic_ResistanceMutations_Tsv_v{cosmic_version}_GRCh{grch_version}"
        contained_file = f"Cosmic_ResistanceMutations_v{cosmic_version}_GRCh{grch_version}.tsv"

    elif cosmic_project == "genome_screen":
        download_link = f"https://cancer.sanger.ac.uk/api/mono/products/v1/downloads/scripted?path=grch{grch_version}/cosmic/v{cosmic_version}/Cosmic_GenomeScreensMutant_Tsv_v{cosmic_version}_GRCh{grch_version}.tar&bucket=downloads"
        tarred_folder = f"Cosmic_GenomeScreensMutant_Tsv_v{cosmic_version}_GRCh{grch_version}"
        contained_file = f"Cosmic_GenomeScreensMutant_v{cosmic_version}_GRCh{grch_version}.tsv"

    elif cosmic_project == "targeted_screen":
        download_link = f"https://cancer.sanger.ac.uk/api/mono/products/v1/downloads/scripted?path=grch{grch_version}/cosmic/v{cosmic_version}/Cosmic_CompleteTargetedScreensMutant_Tsv_v{cosmic_version}_GRCh{grch_version}.tar&bucket=downloads"
        tarred_folder = f"Cosmic_CompleteTargetedScreensMutant_Tsv_v{cosmic_version}_GRCh{grch_version}"
        contained_file = f"Cosmic_CompleteTargetedScreensMutant_v{cosmic_version}_GRCh{grch_version}.tsv"

    # Only available for the latest COSMIC version
    elif cosmic_project == "cancer_example":
        download_link = f"https://cog.sanger.ac.uk/cosmic-downloads-production/taster/example_grch{grch_version}.tar"
        tarred_folder = f"example_GRCh{grch_version}"
        contained_file = f"CancerMutationCensus_AllData_v{get_latest_cosmic()}_GRCh{grch_version}.tsv"

    tar_folder_path = os.path.join(reference_dir, tarred_folder)
    file_path = os.path.join(tar_folder_path, contained_file)
    if not unzip:
        file_path += ".gz"

    if os.path.exists(file_path):
        if overwrite is None:
            proceed = (
                input(
                    "The requested COSMIC database already exists at the destination. Would you like to overwrite the existing files (y/n)? "
                )
                .strip()
                .lower()
            )
            overwrite = proceed in ["yes", "y"]
        if overwrite:
            logger.info(f"Overwriting existing COSMIC database at {file_path}...")
        else:
            logger.info(f"Using existing COSMIC database at {file_path}...")
            return file_path, overwrite

    # Only the example database can be downloaded directly (without an account)
    if cosmic_project == "cancer_example":
        curl_command = [
            "curl",
            "-L",
            "--output",
            f"{tar_folder_path}.tar",
            download_link,
        ]
        subprocess.run(curl_command, capture_output=True, text=True)

        with tarfile.open(f"{tar_folder_path}.tar", "r") as tar:
            tar.extractall(path=tar_folder_path)
            if verbose:
                logger.info(f"Extracted tar file to {tar_folder_path}")

    # Download full databases
    else:
        if email and password:
            proceed = "yes"
        else:
            proceed = (
                input(
                    "Downloading complete databases from COSMIC requires an account (https://cancer.sanger.ac.uk/cosmic/register; free for academic use, license for commercial use).\nWould you like to proceed (y/n)? "
                )
                .strip()
                .lower()
            )
        if proceed in ["yes", "y"]:
            download_reference(
                download_link, tar_folder_path, file_path, verbose, email=email, password=password, unzip=unzip
            )
        else:
            raise KeyboardInterrupt(
                "Database download canceled. Learn more about COSMIC at https://cancer.sanger.ac.uk/cosmic/download/cosmic."
            )

    return file_path, overwrite


def make_exact_match_mask(df, searchterm_lower, cols_to_check):
    """Build a boolean mask for rows where any of the specified columns match the search term exactly.

    Handles special case for ACCESSION_NUMBER to match both with and without version.
    Allows for columns in cols_to_check to be missing from the DataFrame.
    """
    temp_cols = []
    conditions = []

    for col in cols_to_check:
        if col not in df.columns:
            continue

        if col in ("ACCESSION_NUMBER", "TRANSCRIPT_ACCESSION"):
            # Lowercased full Ensembl accession
            acc_col = "__accession_number"
            df[acc_col] = df[col].astype(str).str.lower()
            conditions.append(df[acc_col] == searchterm_lower)
            temp_cols.append(acc_col)

            # Lowercased Ensembl accession without version number
            acc_nov_col = "__accession_number_no_version"
            df[acc_nov_col] = df[col].astype(str).str.split(".").str[0].str.lower()
            conditions.append(df[acc_nov_col] == searchterm_lower)
            temp_cols.append(acc_nov_col)

        else:
            temp_col = f"__{col.replace(' ', '_').lower()}"
            df[temp_col] = df[col].astype(str).str.lower()
            conditions.append(df[temp_col] == searchterm_lower)
            temp_cols.append(temp_col)

    if not conditions:
        missing = ", ".join(cols_to_check)
        raise ValueError(f"None of the specified columns were found in the DataFrame: {missing}")

    mask = conditions[0]
    for cond in conditions[1:]:
        mask |= cond

    return mask


def query_local_cosmic(cosmic_tsv_path, cosmic_project, searchterm, limit):
    """Search the local COSMIC mutation census file for matching entries."""
    df = pd.read_csv(cosmic_tsv_path, sep="\t", low_memory=False)
    searchterm_lower = searchterm.lower()
    results = []

    def match_and_limit(mask, extract_fn):
        for _, row in df[mask].head(limit).iterrows():
            results.append(extract_fn(row))

    if cosmic_project in ["cancer", "cancer_example"]:
        # Columns to check for search term
        cols_to_check = [
            "GENE_NAME",
            "ACCESSION_NUMBER",
            "LEGACY_MUTATION_ID",
            "Mutation CDS",
            "Mutation AA",
            "GENOMIC_MUTATION_ID",
        ]
        mask = make_exact_match_mask(df, searchterm_lower, cols_to_check)

        match_and_limit(
            mask, lambda row: {col.replace(" ", "_"): row[col] for col in row.index if not col.startswith("__")}
        )

    elif cosmic_project in ["census", "resistance", "cell_line", "genome_screen", "targeted_screen", "other"]:
        # Columns to check for search term
        cols_to_check = [
            "GENE_SYMBOL",
            "TRANSCRIPT_ACCESSION",
            "COSMIC_GENE_ID",
            "COSMIC_SAMPLE_ID",
            "COSMIC_PHENOTYPE_ID",
            "GENOMIC_MUTATION_ID",
            "LEGACY_MUTATION_ID",
            "SAMPLE_NAME",
            "MUTATION_CDS",
            "MUTATION_AA",
            "MUTATION_ID",
            "COSMIC_STUDY_ID",
        ]
        mask = make_exact_match_mask(df, searchterm_lower, cols_to_check)

        match_and_limit(
            mask, lambda row: {col.replace(" ", "_"): row[col] for col in row.index if not col.startswith("__")}
        )

    else:
        raise ValueError(f"Unsupported cosmic_project: {cosmic_project}")

    if len(results) == 0:
        raise ValueError(
            f"No results were found for searchterm '{searchterm}' and cosmic_project '{cosmic_project}' in COSMIC database file (cosmic_tsv_path) '{cosmic_tsv_path}'."
        )

    return results


def cosmic(
    searchterm,
    cosmic_tsv_path=None,
    limit=100,
    json=False,
    download_cosmic=False,
    cosmic_project=None,
    cosmic_version=None,
    grch_version=37,
    email=None,
    password=None,
    gget_mutate=False,
    keep_genome_info=False,
    remove_duplicates=False,
    seq_id_column="seq_ID",
    mutation_column="mutation",
    mut_id_column="mutation_id",
    out=None,
    verbose=True,
):
    """Search for genes, mutations, etc associated with cancers using the COSMIC database.

    (Catalogue Of Somatic Mutations In Cancer) database
    (https://cancer.sanger.ac.uk/cosmic).
    NOTE: Licence fees apply for the commercial use of COSMIC (https://www.cosmickb.org/licensing).

    Args for downloading COSMIC databases:
    NOTE: Downloading COSMIC databases requires an account (https://cancer.sanger.ac.uk/cosmic/register).
    - download_cosmic   (True/False) whether to switch into database download mode. Default: False
    - cosmic_project    (str) Type of COSMIC database. Default: 'cancer'. One of the following:

                        | cosmic_project  | Description                                                           | Notes                                                                              | Size   |
                        |-----------------|-----------------------------------------------------------------------|------------------------------------------------------------------------------------|--------|
                        | cancer          | Cancer Mutation Census (CMC) (most commonly used COSMIC mutation set) | Only available for GRCh37. Most feature-rich schema (takes the longest to search). | 2 GB   |
                        | cancer_example  | Example CMC subset provided for testing and demonstration             | Downloadable without a COSMIC account. Minimal dataset.                            | 2.5 MB |
                        | census          | COSMIC census of curated somatic mutations in known cancer genes      | Smaller curated set of known cancer drivers.                                       | 630 MB |
                        | resistance      | Mutations associated with drug resistance                             | Helpful for pharmacogenomics research.                                             | 1.6 MB |
                        | cell_line       | Cell Lines Project mutation data                                      | Sample metadata often available.                                                   | 2.7 GB |
                        | genome_screen   | Mutations from genome screening efforts                               | Includes less curated data, good for large-scale screens.                          |  |
                        | targeted_screen | Mutations from targeted screening panels                              | Focused panel datasets, good for clinical settings.                                |  |

    - cosmic_version    (int) Version of the COSMIC database. Default: None -> Defaults to latest version.
    - grch_version      (int) Version of the human GRCh reference genome the COSMIC database was based on (37 or 38). Default: 37
    - email             (str) Email for COSMIC login. Helpful for avoiding required input upon running gget cosmic. Default: None
    - password          (str) Password for COSMIC login. Helpful for avoiding required input upon running gget cosmic, but password will be stored in plain text in the script. Default: None
    - gget_mutate       (True/False) Whether to create a modified version of the database adjusted for use as input to 'gget mutate'. Default: False
        - keep_genome_info  (True/False) Whether to keep genome information (e.g. location of mutation in the genome) in the modified database for use with 'gget mutate'. Default: False
        - remove_duplicates (True/False) Whether to remove duplicate rows from the modified database for use with 'gget mutate'. Default: False
        - seq_id_column     (str) Name of the seq_id column in the csv file created by 'gget_mutate'. Default: "seq_ID"
        - mutation_column   (str) Name of the mutation column in the csv file created by 'gget_mutate'. Default: "mutation"
        - mut_id_column     (str) Name of the mutation_id column in the csv file created by gget_mutate. Default: "mutation_id"

    -> Saves the requested database into the specified folder (or current working directory if out=None).

    Args for querying information about specific cancers/genes/etc:
    - searchterm        (str) Search term, which can be a mutation, gene name (or Ensembl ID), sample, etc.
                        Examples: EGFR, ENST00000275493, c.650A>T, p.Q217L, COSV51765119, BT2012100223LNCTB (sample ID)
                        NOTE: Set to None when downloading COSMIC databases with download_cosmic=True.
    - cosmic_tsv_path   (str) Path to the COSMIC mutation tsv file, e.g. 'path/to/CancerMutationCensus_AllData_v101_GRCh37.tsv'.
                        This file is downloaded when downloading COSMIC databases using the arguments described above.
                        NOTE: This is a required argument when download_cosmic=False.
    - limit             (int) Number of hits to return. Default: 100
    - json              (True/False) If True, returns results in json format instead of data frame. Default: False

    -> Returns a data frame (or json dictionary) with the requested results.

    General args:
    - out             (str) Path to the file (or folder when downloading databases with the download_cosmic flag) the results will be saved in, e.g. 'path/to/results.json'.
                      Defaults:
                      - When download_cosmic=False: Results will be returned to standard out
                      - When download_cosmic=True: Database will be downloaded into current working directory
    - verbose         (True/False) whether to print progress information. Default: True
    """
    if verbose:
        logger.info("NOTE: Licence fees apply for the commercial use of COSMIC (https://www.cosmickb.org/licensing).")

    ## Database download
    if download_cosmic:
        if not cosmic_project:
            cosmic_project = "cancer"
            if verbose:
                logger.info(
                    f"No cosmic_project provided. Defaulting to cosmic_project '{cosmic_project}' (also works for 'cancer_example')."
                )

        mut_class_allowed = [
            "cancer",
            "cell_line",
            "census",
            "resistance",
            "genome_screen",
            "targeted_screen",
            "cancer_example",
        ]
        if cosmic_project not in mut_class_allowed:
            raise ValueError(
                f"Parameter 'cosmic_project' must be one of the following: {', '.join(mut_class_allowed)}.\n"
            )

        grch_allowed = ["37", "38"]
        if str(grch_version) not in grch_allowed:
            raise ValueError(f"Parameter 'grch_version' must be one of the following: {', '.join(grch_allowed)}.\n")

        if not out:
            out = os.getcwd()

        if not os.path.exists(out):
            os.makedirs(out)

        if not cosmic_version:
            cosmic_version = get_latest_cosmic()
            if verbose:
                logger.info(f"Downloading data from latest COSMIC version (v{cosmic_version}).")

        ## Download requested database
        mutation_tsv_file, overwrite = select_reference(
            cosmic_project, out, grch_version, cosmic_version, verbose, email=email, password=password
        )

        if gget_mutate and overwrite is not False:
            ## Create copy of results formatted for further use by gget mutate
            if verbose:
                logger.info("Creating modified mutations file for use with gget mutate...")

            if cosmic_project == "cancer" or cosmic_project == "cancer_example":
                relevant_cols = [
                    "GENE_NAME",
                    "ACCESSION_NUMBER",
                    "MUTATION_URL",
                    "Mutation CDS",
                    "Mutation AA",
                ]
                if keep_genome_info:
                    relevant_cols.extend(
                        [
                            "Mutation genome position GRCh37",
                            "GENOMIC_WT_ALLELE_SEQ",
                            "GENOMIC_MUT_ALLELE_SEQ",
                            "GENOMIC_MUTATION_ID",
                        ]
                    )  # * uncomment to include strand information (tested not to be accurate for CMC)
                    # relevant_cols.extend(['Mutation genome position GRCh37', 'GENOMIC_MUTATION_ID'])    #* erase to include strand information (tested not to be accurate for CMC)
            else:
                relevant_cols = [
                    "GENE_SYMBOL",
                    "TRANSCRIPT_ACCESSION",
                    "MUTATION_ID",
                    "MUTATION_CDS",
                    "MUTATION_AA",
                ]
                if keep_genome_info:
                    relevant_cols.extend(["HGVSG", "STRAND", "GENOMIC_MUTATION_ID"])

            df = pd.read_csv(mutation_tsv_file, usecols=relevant_cols, sep="\t")

            # Get seq_ID and mutation columns
            if cosmic_project == "cancer" or cosmic_project == "cancer_example":
                df["MUTATION_URL"] = df["MUTATION_URL"].str.extract(r"id=(\d+)")
                df = df.rename(
                    columns={
                        "ACCESSION_NUMBER": "seq_ID",
                        "Mutation CDS": "mutation",
                        "MUTATION_URL": "MUTATION_ID",
                        "Mutation AA": "mutation_aa",
                    }
                )

                if keep_genome_info:
                    # * erase to include strand information (tested not to be accurate for CMC)
                    # df = df.rename(
                    #     columns={
                    #         "Mutation genome position GRCh37": "position_genome",
                    #     }
                    # )

                    import numpy as np

                    from gget.gget_mutate import convert_chromosome_value_to_int_when_possible, mutation_pattern

                    # * uncomment to include strand information (tested not to be accurate for CMC)
                    df[["chromosome", "GENOME_POS"]] = df["Mutation genome position GRCh37"].str.split(":", expand=True)
                    df["chromosome"] = df["chromosome"].apply(convert_chromosome_value_to_int_when_possible)
                    df[["GENOME_START", "GENOME_STOP"]] = df["GENOME_POS"].str.split("-", expand=True)

                    df[["nucleotide_positions", "actual_mutation"]] = df["mutation"].str.extract(mutation_pattern)

                    sub_mask = df["actual_mutation"].str.contains(">")
                    ins_mask = (df["actual_mutation"].str.contains("ins")) & (
                        ~df["actual_mutation"].str.contains("delins")
                    )
                    delins_mask = df["actual_mutation"].str.contains("delins")
                    ins_delins_mask = ins_mask | delins_mask
                    sub_ins_delins_mask = sub_mask | ins_delins_mask

                    df.loc[sub_mask, "wt_allele_cds"] = df.loc[sub_mask, "actual_mutation"].str.split(">").str[0]
                    df.loc[sub_mask, "mut_allele_cds"] = df.loc[sub_mask, "actual_mutation"].str.split(">").str[1]

                    df.loc[ins_delins_mask, "mut_allele_cds"] = df.loc[ins_delins_mask, "actual_mutation"].str.extract(
                        r"ins(.+)"
                    )[0]

                    df["strand"] = np.nan

                    df.loc[sub_ins_delins_mask, "strand"] = np.where(
                        pd.isna(df.loc[sub_ins_delins_mask, "GENOMIC_MUT_ALLELE_SEQ"]),
                        np.nan,
                        np.where(
                            df.loc[sub_ins_delins_mask, "mut_allele_cds"]
                            != df.loc[sub_ins_delins_mask, "GENOMIC_MUT_ALLELE_SEQ"],
                            "-",
                            "+",
                        ),
                    )

                    df.loc[sub_mask, "actual_mutation_updated"] = (
                        df.loc[sub_mask, "GENOMIC_WT_ALLELE_SEQ"] + ">" + df.loc[sub_mask, "GENOMIC_MUT_ALLELE_SEQ"]
                    )
                    df.loc[ins_mask, "actual_mutation_updated"] = "ins" + df.loc[ins_mask, "GENOMIC_MUT_ALLELE_SEQ"]
                    df.loc[delins_mask, "actual_mutation_updated"] = (
                        "delins" + df.loc[delins_mask, "GENOMIC_MUT_ALLELE_SEQ"]
                    )

                    df.loc[~sub_ins_delins_mask, "actual_mutation_final"] = df.loc[
                        ~sub_ins_delins_mask, "actual_mutation"
                    ]

                    df.loc[sub_ins_delins_mask, "actual_mutation_final"] = np.where(
                        pd.isna(df.loc[sub_ins_delins_mask, "strand"]),
                        np.nan,
                        np.where(
                            df.loc[sub_ins_delins_mask, "strand"] == "+",
                            df.loc[sub_ins_delins_mask, "actual_mutation"],
                            df.loc[sub_ins_delins_mask, "actual_mutation_updated"],
                        ),
                    )

                    df["mutation_genome"] = np.where(
                        df["GENOME_START"] != df["GENOME_STOP"],
                        "g."
                        + df["GENOME_START"].astype(str)
                        + "_"
                        + df["GENOME_STOP"].astype(str)
                        + df["actual_mutation_final"],
                        "g." + df["GENOME_START"].astype(str) + df["actual_mutation_final"],
                    )

                    df.loc[df["Mutation genome position GRCh37"].isna(), "mutation_genome"] = np.nan

                    df.drop(
                        columns=[
                            "GENOME_POS",
                            "GENOME_START",
                            "GENOME_STOP",
                            "nucleotide_positions",
                            "actual_mutation",
                            "actual_mutation_updated",
                            "actual_mutation_final",
                            "Mutation genome position GRCh37",
                            "wt_allele_cds",
                            "mut_allele_cds",
                            "GENOMIC_WT_ALLELE_SEQ",
                            "GENOMIC_MUT_ALLELE_SEQ",
                        ],
                        inplace=True,
                    )

            else:
                df = df.rename(
                    columns={
                        "GENE_SYMBOL": "GENE_NAME",
                        "TRANSCRIPT_ACCESSION": "seq_ID",
                        "MUTATION_CDS": "mutation",
                        "MUTATION_AA": "mutation_aa",
                    }
                )

                if keep_genome_info:
                    df["mutation_genome"] = df["HGVSG"].str.split(":").str[1]

                    df.drop(columns=["HGVSG"], inplace=True)

                    df = df.rename(
                        columns={
                            "CHROMOSOME": "chromosome",
                            "STRAND": "strand",
                        }
                    )

            # Remove version numbers from Ensembl IDs
            df["seq_ID"] = df["seq_ID"].str.split(".").str[0]

            df["gene_name"] = df["GENE_NAME"].astype(str)
            df["mutation_id"] = df["MUTATION_ID"].astype(str)

            df = df.drop(columns=["GENE_NAME", "MUTATION_ID"])

            if remove_duplicates:
                duplicate_count = df.duplicated(subset=["seq_ID", "mutation"], keep=False).sum() // 2
                print(
                    f"Removing {duplicate_count} duplicate entries from the COSMIC csv for gget mutate: {duplicate_count}"
                )
                df["non_na_count"] = df.notna().sum(axis=1)
                df = df.sort_values(by="non_na_count", ascending=False)
                df = df.drop_duplicates(subset=["seq_ID", "mutation"], keep="first")
                df = df.drop(columns=["non_na_count"])

            if isinstance(seq_id_column, str) and seq_id_column != "seq_ID":
                df.rename(columns={"seq_ID": seq_id_column}, inplace=True)
            if isinstance(mutation_column, str) and mutation_column and mutation_column != "mutation":
                df.rename(columns={"mutation": mutation_column}, inplace=True)
            if isinstance(mut_id_column, str) and mut_id_column != "mutation_id":
                df.rename(columns={"mutation_id": mut_id_column}, inplace=True)

            mutate_csv_out = mutation_tsv_file.replace(".tsv", "_mutation_workflow.csv")
            df.to_csv(mutate_csv_out, index=False)

            if verbose:
                logger.info(f"Modified mutations file for use with gget mutate created at {mutate_csv_out}")

    else:
        # Old code from when COSMIC was acccessible without an account:
        # # Check if 'entity' argument is valid
        # sps = [
        #     "mutations",
        #     "genes",
        #     "pubmed",
        #     "studies",
        #     "samples",
        #     "cancer",
        #     "tumour_site",
        # ]
        # if entity not in sps:
        #     raise ValueError(
        #         f"'entity' argument specified as {entity}. Expected one of: {', '.join(sps)}"
        #     )

        # # Translate categories to match COSMIC data table IDs
        # if entity == "cancer":
        #     entity = "disease"

        # if entity == "tumour_site":
        #     entity = "tumour"

        # r = requests.get(
        #     url=COSMIC_GET_URL + entity + "?q=" + searchterm + "&export=json"
        # )

        # # Check if the request returned an error (e.g. gene not found)
        # if not r.ok:
        #     raise RuntimeError(
        #         f"COSMIC API request returned error {r.status_code}. "
        #         "Please double-check the arguments and try again.\n"
        #     )

        # if r.text == "\n":
        #     logger.warning(
        #         f"searchterm = '{searchterm}' did not return any results with entity = '{entity}'. "
        #         "Please double-check the arguments and try again.\n"
        #     )
        #     return None

        # data = r.text.split("\n")
        # dicts = {}
        # counter = 1
        # if entity == "mutations":
        #     dicts = {"Gene": [], "Syntax": [], "Alternate IDs": [], "Canonical": []}
        #     for i in data:
        #         if len(i) > 2:
        #             parsing_mutations = i.split("\t")
        #             dicts["Gene"].append(parsing_mutations[0])
        #             dicts["Syntax"].append(parsing_mutations[1])
        #             dicts["Alternate IDs"].append(
        #                 parsing_mutations[2].replace('" ', "").replace('"', "")
        #             )
        #             dicts["Canonical"].append(parsing_mutations[3])
        #             counter = counter + 1
        #             if limit < counter:
        #                 break

        # elif entity == "pubmed":
        #     dicts = {"Pubmed": [], "Paper title": [], "Author": []}
        #     for i in data:
        #         if len(i) > 2:
        #             parsing_mutations = i.split("\t")
        #             dicts["Pubmed"].append(parsing_mutations[0])
        #             dicts["Paper title"].append(
        #                 parsing_mutations[1]
        #                 .replace('" ', "")
        #                 .replace('"', "")
        #                 .capitalize()
        #             )
        #             dicts["Author"].append(
        #                 parsing_mutations[2].replace('" ', "").replace('"', "")
        #             )
        #             counter = counter + 1
        #             if limit < counter:
        #                 break

        # elif entity == "genes":
        #     dicts = {
        #         "Gene": [],
        #         "Alternate IDs": [],
        #         "Tested samples": [],
        #         "Simple Mutations": [],
        #         "Fusions": [],
        #         "Coding Mutations": [],
        #     }
        #     for i in data:
        #         if len(i) > 2:
        #             parsing_mutations = i.split("\t")
        #             dicts["Gene"].append(parsing_mutations[0])
        #             dicts["Alternate IDs"].append(
        #                 parsing_mutations[1].replace('" ', "").replace('"', "")
        #             )
        #             dicts["Tested samples"].append(parsing_mutations[2])
        #             dicts["Simple Mutations"].append(parsing_mutations[3])
        #             dicts["Fusions"].append(parsing_mutations[4])
        #             dicts["Coding Mutations"].append(parsing_mutations[5])
        #             counter = counter + 1
        #             if limit < counter:
        #                 break

        # elif entity == "samples":
        #     dicts = {
        #         "Sample Name": [],
        #         "Sites & Histologies": [],
        #         "Analysed Genes": [],
        #         "Mutations": [],
        #         "Fusions": [],
        #         "Structual variants": [],
        #     }
        #     for i in data:
        #         if len(i) > 2:
        #             parsing_mutations = i.split("\t")
        #             dicts["Sample Name"].append(parsing_mutations[0])
        #             dicts["Sites & Histologies"].append(
        #                 parsing_mutations[1].replace(":", ", ")
        #             )
        #             dicts["Analysed Genes"].append(parsing_mutations[2])
        #             dicts["Mutations"].append(parsing_mutations[3])
        #             dicts["Fusions"].append(parsing_mutations[4])
        #             dicts["Structual variants"].append(parsing_mutations[5])
        #             counter = counter + 1
        #             if limit < counter:
        #                 break

        # elif entity == "studies":
        #     dicts = {
        #         "Study Id": [],
        #         "Project Code": [],
        #         "Description": [],
        #     }
        #     for i in data:
        #         if len(i) > 2:
        #             parsing_mutations = i.split("\t")
        #             dicts["Study Id"].append(parsing_mutations[0])
        #             dicts["Project Code"].append(parsing_mutations[1])
        #             dicts["Description"].append(parsing_mutations[2])
        #             counter = counter + 1
        #             if limit < counter:
        #                 break

        # elif entity == "disease":
        #     dicts = {
        #         "COSMIC classification": [],
        #         "Paper description": [],
        #         "Tested samples": [],
        #         "Mutations": [],
        #     }
        #     for i in data:
        #         if len(i) > 2:
        #             parsing_mutations = i.split("\t")
        #             dicts["COSMIC classification"].append(
        #                 parsing_mutations[0].replace('" ', "").replace('"', "")
        #             )
        #             dicts["Paper description"].append(
        #                 parsing_mutations[1].replace('" ', "").replace('"', "")
        #             )
        #             dicts["Tested samples"].append(parsing_mutations[2])
        #             dicts["Mutations"].append(parsing_mutations[3])
        #             counter = counter + 1
        #             if limit < counter:
        #                 break

        # elif entity == "tumour":
        #     dicts = {
        #         "Primary Site": [],
        #         "Tested sample": [],
        #         "Analyzed genes": [],
        #         "Mutations": [],
        #         "Fusions": [],
        #         "Structural variants": [],
        #     }
        #     for i in data:
        #         if len(i) > 2:
        #             parsing_mutations = i.split("\t")
        #             dicts["Primary Site"].append(parsing_mutations[0])
        #             dicts["Tested sample"].append(parsing_mutations[1])
        #             dicts["Analyzed genes"].append(parsing_mutations[2])
        #             dicts["Mutations"].append(parsing_mutations[3])
        #             dicts["Fusions"].append(parsing_mutations[4])
        #             dicts["Structural variants"].append(parsing_mutations[5])
        #             counter = counter + 1
        #             if limit < counter:
        #                 break

        # Check if cosmic_tsv_path exists
        if not cosmic_tsv_path or not os.path.exists(cosmic_tsv_path):
            example_call_python = f"gget.cosmic(download_cosmic=True, searchterm=None, cosmic_project='{cosmic_project}', grch_version={grch_version}, cosmic_version={cosmic_version or get_latest_cosmic()})"
            example_call_bash = f"gget cosmic --download_cosmic --cosmic_project {cosmic_project} --grch_version {grch_version} --cosmic_version {cosmic_version or get_latest_cosmic()}"

            raise FileNotFoundError(
                f"The provided cosmic_tsv_path does not exist: '{cosmic_tsv_path}'.\n"
                f"Please run the following command first to download the appropriate COSMIC database:\n"
                f"Python: {example_call_python}\n"
                f"Command line: {example_call_bash}\n"
            )

        if not cosmic_project:
            if "CancerMutationCensus_AllData" in cosmic_tsv_path:
                cosmic_project = "cancer"
                if verbose:
                    logger.info(f"No cosmic_project provided. Defaulting to cosmic_project '{cosmic_project}'.")
            else:
                cosmic_project = "other"
                if verbose:
                    logger.info(
                        f"No cosmic_project provided. Defaulting to cosmic_project '{cosmic_project}' (incapsulates all mutation classes except 'cancer' and 'cancer_example')."
                    )

        # Query local COSMIC database
        dicts = query_local_cosmic(cosmic_tsv_path, cosmic_project, searchterm, limit)

        # Return results
        corr_df = pd.DataFrame(dicts)

        if json:
            results_dict = json_package.loads(corr_df.to_json(orient="records"))
            if out:
                # Create saving directory
                directory = "/".join(out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)

                json_out = os.path.join(out, f"gget_cosmic_{cosmic_project}_{searchterm}.json")
                with open(json_out, "w", encoding="utf-8") as f:
                    json_package.dump(results_dict, f, ensure_ascii=False, indent=4)

            else:
                return results_dict

        else:
            if out:
                # Create saving directory
                directory = "/".join(out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)

                df_out = os.path.join(out, f"gget_cosmic_{cosmic_project}_{searchterm}.csv")
                corr_df.to_csv(df_out, index=False)

            else:
                return corr_df
