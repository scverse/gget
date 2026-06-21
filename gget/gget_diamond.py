import json as json_package
import os
import platform
import subprocess
import sys
import uuid

from .compile import PACKAGE_PATH
from .utils import create_tmp_fasta, remove_temp_files, set_up_logger, tsv_to_df

logger = set_up_logger()

# Path to precompiled diamond binary
if platform.system() == "Windows":
    PRECOMPILED_DIAMOND_PATH = os.path.join(PACKAGE_PATH, f"bins/{platform.system()}/diamond.exe")
else:
    PRECOMPILED_DIAMOND_PATH = os.path.join(PACKAGE_PATH, f"bins/{platform.system()}/diamond")


def diamond(
    query,
    reference,
    translated=False,
    diamond_db=None,
    sensitivity="very-sensitive",
    threads=1,
    diamond_binary=None,
    verbose=True,
    json=False,
    out=None,
):
    """Align multiple protein or translated DNA sequences using DIAMOND (https://www.nature.com/articles/nmeth.3176).

    Args:
    - query          Sequences (str or list) or path to FASTA file containing sequences to be aligned against the reference.
    - reference      Reference sequences (str or list) or path to FASTA file containing reference sequences.
                     Set translated=True if reference sequences are amino acid sequences and query sequences are nucleotide sequences.
    - translated     True/False whether to perform translated alignment of nucleotide sequences to amino acid reference sequences.
                     Default: False.
    - diamond_db     Path to save DIAMOND database created from reference.
                     Default: None -> Temporary db file will be deleted after alignment or saved in 'out' if 'out' is provided.
    - sensitivity    Sensitivity of DIAMOND alignment.
                     One of the following: fast, mid-sensitive, sensitive, more-sensitive, very-sensitive or ultra-sensitive.
                     Default: "very-sensitive"
    - threads        Number of threads to use for alignment. Default: 1.
    - diamond_binary Path to DIAMOND binary, e.g. path/bins/Linux/diamond. Default: None -> Uses DIAMOND binary installed with gget.
    - verbose        True/False whether to print progress information. Default True.
    - json           If True, returns results in json format instead of data frame. Default: False.
    - out            Path to folder to save DIAMOND results in. Default: Standard out, temporary files are deleted.

    Returns a data frame with the DIAMOND alignment results. (Or JSON formatted dictionary if json=True.)
    """
    # Check argument validity
    supported_sens = [
        "fast",
        "mid-sensitive",
        "sensitive",
        "more-sensitive",
        "very-sensitive",
        "ultra-sensitive",
    ]
    if sensitivity not in supported_sens:
        raise ValueError(
            f"'sensitivity' argument specified as {sensitivity}. Expected one of: {', '.join(supported_sens)}"
        )

    # Handle command line passing path to FASTA as a list
    if isinstance(query, list) and len(query) == 1:
        query = query[0]
    if isinstance(reference, list) and len(reference) == 1:
        reference = reference[0]

    # Define paths to query/reference/db/output files
    files_to_delete = []
    if "." in query:
        input_file = os.path.abspath(query)
    else:
        input_file = create_tmp_fasta(query)
        files_to_delete.append(input_file)

    if "." in reference:
        reference_file = os.path.abspath(reference)
    else:
        reference_file = create_tmp_fasta(reference)
        files_to_delete.append(reference_file)

    # Create out folder if it does not exist
    if out:
        os.makedirs(out, exist_ok=True)

    if out:
        out = os.path.abspath(out)
        output = f"{out}/DIAMOND_results.tsv"
    else:
        output = os.path.abspath(f"tmp_{str(uuid.uuid4())}_out.tsv")
        files_to_delete.append(output)

    if not diamond_db and out:
        diamond_db = f"{out}/DIAMOND_db"
    elif not diamond_db:
        diamond_db = os.path.abspath(f"tmp_db_{str(uuid.uuid4())}")
        files_to_delete.append(diamond_db + ".dmnd")

    if diamond_binary:
        DIAMOND = diamond_binary
    else:
        DIAMOND = PRECOMPILED_DIAMOND_PATH

    # Replace slashes in paths for Windows compatibility
    if platform.system() == "Windows":
        diamond_bin = DIAMOND.replace("/", "\\")
        ref_file = reference_file.replace("/", "\\")
        db_path = diamond_db.replace("/", "\\")
        in_file = input_file.replace("/", "\\")
        out_file = output.replace("/", "\\")
    else:
        diamond_bin = DIAMOND
        ref_file = reference_file
        db_path = diamond_db
        in_file = input_file
        out_file = output

    if translated:
        if verbose:
            logger.info("Aligning nucleotide query to amino acid reference (blastx mode).")
        diamond_program = "blastx"
    else:
        diamond_program = "blastp"

    # Run DIAMOND commands as separate subprocess calls (avoids shell=True security issues)
    if verbose:
        logger.info("Creating DIAMOND database and initiating alignment...")

    # Step 1: Check diamond version
    version_cmd = [diamond_bin, "version"]
    with subprocess.Popen(version_cmd, stderr=subprocess.PIPE) as process:
        stderr = process.stderr.read().decode("utf-8")
        if stderr:
            sys.stderr.write(stderr)
    if process.wait() != 0:
        raise RuntimeError("DIAMOND version check failed.")

    # Step 2: Create database
    makedb_cmd = [diamond_bin, "makedb", "--quiet", "--in", ref_file, "--db", db_path, "--threads", str(threads)]
    with subprocess.Popen(makedb_cmd, stderr=subprocess.PIPE) as process:
        stderr = process.stderr.read().decode("utf-8")
        if stderr:
            sys.stderr.write(stderr)
    if process.wait() != 0:
        raise RuntimeError("DIAMOND database creation failed.")

    # Step 3: Run alignment
    align_cmd = [
        diamond_bin,
        diamond_program,
        "--outfmt",
        "6",
        "qseqid",
        "sseqid",
        "pident",
        "qlen",
        "slen",
        "length",
        "mismatch",
        "gapopen",
        "qstart",
        "qend",
        "sstart",
        "send",
        "evalue",
        "bitscore",
        "--quiet",
        "--query",
        in_file,
        "--db",
        ref_file,
        "--out",
        out_file,
        f"--{sensitivity}",
        "--threads",
        str(threads),
        "--ignore-warnings",
    ]
    with subprocess.Popen(align_cmd, stderr=subprocess.PIPE) as process:
        stderr = process.stderr.read().decode("utf-8")
        if stderr:
            sys.stderr.write(stderr)

    if process.wait() != 0:
        raise RuntimeError("DIAMOND alignment failed.")
    else:
        if verbose:
            logger.info("DIAMOND alignment complete.")

    df_diamond = tsv_to_df(
        output,
        headers=[
            "query_accession",
            "subject_accession",
            "identity_percentage",
            "query_seq_length",
            "subject_seq_length",
            "length",
            "mismatches",
            "gap_openings",
            "query_start",
            "query_end",
            "subject_start",
            "subject_end",
            "e-value",
            "bit_score",
        ],
    )

    # Delete temporary files
    if files_to_delete:
        remove_temp_files(files_to_delete)

    if json:
        results_dict = json_package.loads(df_diamond.to_json(orient="records"))
        if out:
            with open(f"{out}/gget_diamond_results.json", "w", encoding="utf-8") as f:
                json_package.dump(results_dict, f, ensure_ascii=False, indent=4)

        return results_dict

    else:
        if out:
            df_diamond.to_csv(f"{out}/gget_diamond_results.csv", index=False)
        return df_diamond
