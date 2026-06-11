import json as json_package
import time
import warnings

import mysql.connector as sql
import numpy as np
import pandas as pd

warnings.simplefilter(action="ignore", category=UserWarning)

# Custom functions
from .utils import (  # noqa: E402
    find_latest_ens_rel,
    find_nv_kingdom,
    search_species_options,
    set_up_logger,
    wrap_cols_func,
)

logger = set_up_logger()

from gget.constants import ENSEMBL_FTP_URL, ENSEMBL_FTP_URL_NV  # noqa: E402


def clean_cols(x):
    """Collapse a list to its single unique value, or return x unchanged if not a list."""
    if isinstance(x, list):
        unique_list = list(set(x))
        if len(unique_list) == 1:
            return unique_list[0]
        else:
            return unique_list
    else:
        return x


def search(
    searchwords,
    species,
    release=None,
    id_type="gene",
    seqtype=None,
    andor="or",
    limit=None,
    wrap_text=False,
    json=False,
    save=False,
    verbose=True,
):
    """Function to query Ensembl for genes based on species and free form search terms.

    Automatically fetches results from latest Ensembl release, unless user specifies database (see 'species' argument)
    or release database (see 'release' argument).

    Args:
    - searchwords     Free form search words (not case-sensitive) as a string or list of strings
                      (e.g.searchwords = ["GABA", "gamma-aminobutyric"]).
    - species         Species can be passed in the format "genus_species", e.g. "homo_sapiens" or "arabidopsis_thaliana".
                      To pass a specific database, enter the name of the core database, e.g. "mus_musculus_dba2j_core_105_1".
                      All available core databases can be found here:
                      Vertebrates: http://ftp.ensembl.org/pub/current/mysql/
                      Invertebrates: http://ftp.ensemblgenomes.org/pub/current/ + kingdom + mysql/
    - release         Defines the Ensembl release number from which the files are fetched, e.g. 104.
                      Note: This argument does not apply to invertebrate species (you can pass a specific core database (which includes release number) to the species argument instead).
                      This argument is overwritten if a specific database (which includes a release number) is passed to the species argument.
                      Default: None -> latest Ensembl release is used
    - id_type         "gene" (default) or "transcript"
                      Defines whether genes or transcripts matching the searchwords are returned.
    - andor           "or" (default) or "and"
                      "or": Returns all genes that INCLUDE AT LEAST ONE of the searchwords in their name/description.
                      "and": Returns only genes that INCLUDE ALL of the searchwords in their name/description.
    - limit           (int) Limit the number of search results returned (default: None).
    - wrap_text       If True, displays data frame with wrapped text for easy reading. Default: False.
    - json            If True, returns results in json format instead of data frame. Default: False.
    - save            If True, the data frame is saved as a csv in the current directory (default: False).
    - verbose         True/False whether to print progress information. Default True.

    Returns a data frame with the query results.

    Note: Only returns results based on matches in the "gene name" or "description" sections in the Ensembl database.

    Deprecated arguments: 'seqtype' (renamed to id_type)
    """
    # Handle deprecated arguments
    if seqtype:
        logger.error("'seqtype' argument deprecated! Please use argument 'id_type' instead.")
        return

    start_time = time.time()

    ## Check validity or arguments
    # Check if id_type is valid
    id_types = ["gene", "transcript"]
    id_type = id_type.lower()
    if id_type not in id_types:
        raise ValueError(f"ID type (id_type) specified is '{id_type}'. Expected one of: {', '.join(id_types)}")

    # Check if 'andor' arg is valid
    andors = ["and", "or"]
    andor = andor.lower()
    if andor not in andors:
        raise ValueError(f"'andor' argument specified as {andor}. Expected one of {', '.join(andors)}")

    ## Get database for specified species
    # Species shortcuts
    if species == "human":
        species = "homo_sapiens"
    if species == "mouse":
        species = "mus_musculus"

    # If a specific database is passed with the "/" at the end, remove it
    if "/" in species:
        species = species.split("/")[0]

    # In case species was passed with upper case letters
    species = species.lower()

    if "core" in species:
        db = species
        if release:
            logger.warning("Specified release overwritten because database name was provided.")
    else:
        if release:
            ens_rel = release
        else:
            # Find latest Ensembl release
            ens_rel = find_latest_ens_rel()

        # Fetch ensembl databases
        databases = search_species_options(database=ENSEMBL_FTP_URL, release=ens_rel)

        # Add ensembl invertebrate databases
        databases += search_species_options(database=ENSEMBL_FTP_URL_NV, release=None)

        db = []
        for datab in databases:
            if species in datab:
                db.append(datab)

        # Unless an unambigious mouse database is specified,
        # the standard core database will be used
        if len(db) > 1 and "mus_musculus" in species:
            db = f"mus_musculus_core_{ens_rel}_39"
            logger.warning(
                f"Defaulting to mus musculus core database: {db}.\n"
                "All available vertebrate databases can be found here:\n"
                f"http://ftp.ensembl.org/pub/release-{ens_rel}/mysql/ \n"
            )

        elif len(db) > 1 and "homo_sapiens" in species:
            db = f"homo_sapiens_core_{ens_rel}_38"

        # Check for ambiguous species matches in species other than mouse and human
        elif len(db) > 1 and "mus_musculus" not in species and "homo_sapiens" not in species:
            logger.warning(
                f"Species matches more than one database. Defaulting to first database: {db[0]}.\n"
                "All available databases can be found here:\n"
                f"Vertebrates: http://ftp.ensembl.org/pub/release-{ens_rel}/mysql/ \n"
                f"Invertebrates: http://ftp.ensemblgenomes.org/pub/release-{find_latest_ens_rel(database=ENSEMBL_FTP_URL_NV)} + kingdom + mysql/"
            )
            db = db[0]

        # Raise error if no matching database was found
        elif len(db) == 0:
            raise ValueError(
                "Species not found. Please double-check spelling or pass a specific CORE database.\n"
                "All available CORE databases can be found here:\n"
                f"Vertebrates: http://ftp.ensembl.org/pub/release-{ens_rel}/mysql/ \n"
                f"Invertebrates: http://ftp.ensemblgenomes.org/pub/release-{find_latest_ens_rel(database=ENSEMBL_FTP_URL_NV)} + kingdom + mysql/"
            )

        else:
            db = db[0]

    if verbose:
        logger.info(f"Fetching results from database: {db}")

    ## Connect to Ensembl SQL server data for specified species
    # Ports to try (some databases are stored in different ports)
    # 3306 (and 5306) for the Ensembl instances, 3337 for GRCh37, 4157 for Ensembl Genomes, and 5316 for mart
    ports = [3306, 5306, 4157, 3337, 5316]

    connection_successful = False
    last_exception = None
    for port in ports:
        try:
            db_connection = sql.connect(
                host="mysql-eg-publicsql.ebi.ac.uk",
                database=db,
                user="anonymous",
                password="",
                port=port,
            )
            connection_successful = True
            break
        except Exception as e:  # noqa: BLE001
            last_exception = e
            # Continue to the next port if the connection is unsuccessful
            continue

    # If none of the ports work, raise an error with the last exception encountered
    if not connection_successful:
        if "Access denied" in str(last_exception):
            raise RuntimeError(
                f"""
                The Ensembl server returned the following error: {str(last_exception)}.
                This might be caused by the Ensembl release number being too low.
                Please try again with a more recent release.
                """
            )
        else:
            raise RuntimeError(f"The Ensembl server returned the following error: {str(last_exception)}")

    ## Clean up list of searchwords
    # If single searchword passed as string, convert to list
    if isinstance(searchwords, str):
        searchwords = [searchwords]

    ## Find genes
    for i, searchword in enumerate(searchwords):
        if id_type == "gene":
            query = f"""
            SELECT gene.stable_id AS 'ensembl_id', xref.display_label AS 'gene_name', gene.description AS 'ensembl_description', xref.description AS 'ext_ref_description', gene.biotype AS 'biotype', external_synonym.synonym AS 'synonym'
            FROM gene
            LEFT JOIN xref ON gene.display_xref_id = xref.xref_id
            LEFT JOIN external_synonym ON gene.display_xref_id = external_synonym.xref_id
            LEFT JOIN gene_attrib ON gene.gene_id = gene_attrib.gene_id
            WHERE (gene.description LIKE '%{searchword}%' OR xref.description LIKE '%{searchword}%' OR xref.display_label LIKE '%{searchword}%' OR external_synonym.synonym LIKE '%{searchword}%' OR gene_attrib.value LIKE '%{searchword}%')
            """

            # Fetch the search results from the host using the specified query
            df_temp = pd.read_sql(query, con=db_connection)

            # Order by ENSEMBL ID (I am using pandas for this instead of SQL to increase speed)
            df_temp = df_temp.sort_values("ensembl_id").reset_index(drop=True)

            # If andor="or", keep all results
            if andor == "or":
                # In the first iteration, make the search results equal to the master data frame
                if i == 0:
                    df = df_temp.copy()
                # Add new search results to master data frame
                else:
                    df = pd.concat([df, df_temp])

            # If andor="and", only keep overlap between results
            if andor == "and":
                # In the first iteration, make the search results equal to the master data frame
                if i == 0:
                    df = df_temp.copy()
                # Only keep overlapping results in master data frame
                else:
                    val = np.intersect1d(df["ensembl_id"], df_temp["ensembl_id"])
                    df = df[df.ensembl_id.isin(val)]

        if id_type == "transcript":
            query = f"""
            SELECT transcript.stable_id AS 'ensembl_id', xref.display_label AS 'gene_name', transcript.description AS 'ensembl_description', xref.description AS 'ext_ref_description', transcript.biotype AS 'biotype', external_synonym.synonym AS 'synonym'
            FROM transcript
            LEFT JOIN xref ON transcript.display_xref_id = xref.xref_id
            LEFT JOIN external_synonym ON transcript.display_xref_id = external_synonym.xref_id
            LEFT JOIN transcript_attrib ON transcript.transcript_id = transcript_attrib.transcript_id
            WHERE (transcript.description LIKE '%{searchword}%' OR xref.description LIKE '%{searchword}%' OR xref.display_label LIKE '%{searchword}%' OR external_synonym.synonym LIKE '%{searchword}%' OR transcript_attrib.value LIKE '%{searchword}%')
            """

            # Fetch the search results from the host using the specified query
            df_temp = pd.read_sql(query, con=db_connection)
            # Order by ENSEMBL ID (I am using pandas for this instead of SQL to increase speed)
            df_temp = df_temp.sort_values("ensembl_id").reset_index(drop=True)

            # If andor="or", keep all results
            if andor == "or":
                # In the first iteration, make the search results equal to the master data frame
                if i == 0:
                    df = df_temp.copy()
                # Add new search results to master data frame
                else:
                    df = pd.concat([df, df_temp])
            # If andor="and", only keep overlap between results
            if andor == "and":
                # In the first iteration, make the search results equal to the master data frame
                if i == 0:
                    df = df_temp.copy()
                # Only keep overlapping results in master data frame
                else:
                    val = np.intersect1d(df["ensembl_id"], df_temp["ensembl_id"])
                    df = df[df.ensembl_id.isin(val)]

    # Remove any duplicate search results from the master data frame and reset the index
    df = df.drop_duplicates().reset_index(drop=True)

    # Collapse entries for the same Ensembl ID
    # .applymap was renamed to .map in pandas 2.1.0
    try:
        df = df.groupby("ensembl_id").agg(tuple).map(list).reset_index()
    except AttributeError:
        df = df.groupby("ensembl_id").agg(tuple).applymap(list).reset_index()

    # Convert list of values to type string if there is only one value
    # .applymap was renamed to .map in pandas 2.1.0
    try:
        df = df.map(clean_cols)
    except AttributeError:
        df = df.applymap(clean_cols)

    # Keep synonyms always of type list for consistency
    df["synonym"] = [
        np.sort(syn).tolist() if isinstance(syn, list) else np.sort([syn]).tolist() for syn in df["synonym"].values
    ]

    # If limit is not None, keep only the first {limit} rows
    if limit is not None:
        # Print number of genes/transcripts found versus fetched
        if verbose:
            logger.info(f"Returning {limit} matches of {len(df)} total matches found.")
        # Remove all but limit rows
        df = df.head(limit)

    else:
        # Print number of genes/transcripts fetched
        if verbose:
            logger.info(f"Total matches found: {len(df)}.")

    # Print query time
    if verbose:
        logger.info(f"Query time: {round(time.time() - start_time, 2)} seconds.")

    # Remove database numbers to retain only species name
    clean_db = "_".join(db.split("_")[:3]).replace("_core", "")

    ## Find kingdom for non-vertebrate species
    kingdom = find_nv_kingdom(clean_db, release=find_latest_ens_rel(database=ENSEMBL_FTP_URL_NV))

    if kingdom:
        # Add URL to gene summary on Ensembl for invertebrates
        df["url"] = f"https://{kingdom}.ensembl.org/" + clean_db + "/Gene/Summary?g=" + df["ensembl_id"]

    else:
        # Add URL to gene summary on Ensembl for vertebrates
        df["url"] = "https://useast.ensembl.org/" + clean_db + "/Gene/Summary?g=" + df["ensembl_id"]

    if wrap_text:
        df_wrapped = df.copy()
        wrap_cols_func(df_wrapped, ["ensembl_description", "ext_ref_description", "url"])

    if json:
        results_dict = json_package.loads(df.to_json(orient="records"))
        if save:
            with open("gget_search_results.json", "w", encoding="utf-8") as f:
                json_package.dump(results_dict, f, ensure_ascii=False, indent=4)

        # Return results in json format
        return results_dict

    else:
        # Save
        if save:
            df.to_csv("gget_search_results.csv", index=False)

        # Return data frame
        return df
