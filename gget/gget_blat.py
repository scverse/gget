import json as json_package
import time
from json.decoder import JSONDecodeError
import pandas as pd
from urllib import request
from urllib.error import HTTPError, URLError

from .utils import set_up_logger, read_fasta

logger = set_up_logger()

# Retry settings for transient UCSC failures (rate limits, HTML error pages, 5xx)
_BLAT_MAX_ATTEMPTS = 4
_BLAT_BACKOFF_BASE_SECONDS = 1.5


def blat(
    sequence,
    seqtype="default",
    assembly="human",
    json=False,
    save=False,
    verbose=True,
):
    """
    BLAT a nucleotide or amino acid sequence against any BLAT UCSC assembly.

    Args:
     - sequence       Sequence (str) or path to fasta file containing one sequence.
     - seqtype        'DNA', 'protein', 'translated%20RNA', or 'translated%20DNA'.
                      Default: 'DNA' for nucleotide sequences; 'protein' for amino acid sequences.
     - assembly       'human' (hg38) (default), 'mouse' (mm39), 'zebrafinch' (taeGut2),
                      or any of the species assemblies available at https://genome.ucsc.edu/cgi-bin/hgBlat
                      (use short assembly name as listed after the "/").
     - json           If True, returns results in json format instead of data frame. Default: False.
     - save           If True, the data frame is saved as a csv in the current directory (default: False).
     - verbose        True/False whether to print progress information. Default True.

    Returns a data frame with the BLAT results.
    """

    ## Clean up sequence
    # If the path to a fasta file was provided instead of a nucleotide sequence,
    # read the file and extract the first sequence
    if "." in sequence:
        if ".txt" in sequence or ".fa" in sequence:
            _, seqs = read_fasta(sequence)

        else:
            raise ValueError(
                "File format not recognized. gget BLAT currently only supports '.txt' or '.fa' files. "
            )

        # Set the first sequence from the fasta file as 'sequence'
        sequence = seqs[0]
        if len(seqs) > 1:
            if verbose:
                logger.info(
                    "File contains more than one sequence. Only the first sequence will be submitted to BLAT."
                )

    # Shorten sequence to length limit if necessary
    if len(sequence) > 8000:
        if verbose:
            logger.info(
                "Length of sequence is > 8000. Only the fist 8000 characters will be submitted to BLAT."
            )
        sequence = sequence[:8000]

    # Convert sequence to upper case
    sequence = sequence.upper()

    ## Set seqtype
    # Valid seqtype options
    seqtypes = ["DNA", "protein", "translated%20RNA", "translated%20DNA"]

    # If user does not specify the seqtype,
    # check if a nucleotide or amino acid sequence was passed
    if seqtype == "default":
        # Set of all possible nucleotides and amino acids
        nucleotides = set("ATGCN")
        amino_acids = set("ARNDCQEGHILKMFPSTWYVBZXBJZ")

        # If sequence is a nucleotide sequence, set seqtype to DNA
        if set(sequence) <= nucleotides:
            seqtype = "DNA"
            if verbose:
                logger.info(
                    f"Sequence recognized as nucleotide sequence. 'seqtype' will be set as {seqtype}."
                )

        # If sequence is an amino acid sequence, set seqtype to protein
        elif set(sequence) <= amino_acids:
            seqtype = "protein"
            if verbose:
                logger.info(
                    f"Sequence recognized as amino acid sequence. 'seqtype' will be set as {seqtype}."
                )

        else:
            raise ValueError(
                f"""
                Sequence not automatically recognized as a nucleotide or amino acid sequence.
                Please specify 'seqtype'.
                Seqtype options: {', '.join(seqtypes)} 
                """
            )

    else:
        # Check if the user specified seqtype is valid
        if seqtype not in seqtypes:
            raise ValueError(
                f"Seqtype specified is {seqtype}. Expected one of {', '.join(seqtypes)}"
            )

    ## Set assembly
    # Note: If assembly not found, defaults to hg38
    if assembly == "human" or assembly == "homo_sapiens":
        database = "hg38"
    elif assembly == "mouse" or assembly == "mus_musculus":
        database = "mm39"
    elif assembly == "zebrafinch" or assembly == "taeniopygia_guttata":
        database = "taeGut2"
    else:
        database = assembly

    # Define server URL
    url = f"https://genome.ucsc.edu/cgi-bin/hgBlat?userSeq={sequence}&type={seqtype}&db={database}&output=json"

    results = _fetch_blat_results(url, seqtype, database)
    if results is None:
        return

    if len(results["blat"]) == 0:
        if verbose:
            logger.info(
                f"No {seqtype} BLAT matches were found for this sequence in genome {results['genome']}."
            )
        return

    # Let user know if assembly was not found
    # If this is the case, BLAT automatically defaults to human (hg38)
    if results["genome"] != database:
        logger.warning(
            f"Assembly {database} not recognized. Defaulted to {results['genome']} instead."
        )

    ## Build data frame to resemble BLAT web search results
    # Define dataframe from dictionary
    df_dict = {}

    for field in results["fields"]:
        df_dict.update({field: []})

    for blat_result_list in results["blat"]:
        for field, (i, result) in zip(results["fields"], enumerate(blat_result_list)):
            df_dict[field].append(result)

    df = pd.DataFrame(df_dict)

    # Calculate % aligned sequence of submitted sequence
    aligned_size = df["qEnd"] - df["qStart"]
    df["%_aligned"] = round((100 / df["qSize"]) * aligned_size, 2)
    # Calculate % matched sequence of aligned sequence
    df["%_matched"] = round((100 / aligned_size) * df["matches"], 2)
    # Add genome column
    df["genome"] = results["genome"]

    # Adjust sequence start to match website
    df["qStart"] = df["qStart"] + 1
    df["tStart"] = df["tStart"] + 1

    # Rename columns
    columns_dict = {
        "misMatches": "mismatches",
        "qName": "query",
        "qSize": "query_size",
        "qStart": "aligned_start",
        "qEnd": "aligned_end",
        "tName": "chromosome",
        "tStart": "start",
        "tEnd": "end",
    }

    df = df.rename(columns=columns_dict)

    # Change columns order (this also drops all unmentioned columns)
    df = df.reindex(
        columns=[
            "genome",
            "query_size",
            "aligned_start",
            "aligned_end",
            "matches",
            "mismatches",
            "%_aligned",
            "%_matched",
            "chromosome",
            "strand",
            "start",
            "end",
        ]
    )

    if json:
        results_dict = json_package.loads(df.to_json(orient="records"))
        if save:
            with open("gget_blat_results.json", "w", encoding="utf-8") as f:
                json_package.dump(results_dict, f, ensure_ascii=False, indent=4)

        return results_dict

    else:
        if save:
            df.to_csv("gget_blat_results.csv", index=False)

        return df


class _RetryableBlatError(Exception):
    """Raised when a BLAT attempt failed in a way that may succeed on retry."""


def _fetch_blat_results(url, seqtype, database):
    """
    Submit a BLAT request to UCSC and return the parsed JSON dict, or None
    on a non-recoverable failure. Retries transient failures (5xx, network
    errors, non-JSON responses from rate-limiting / HTML error pages) with
    exponential backoff. The legacy "sequence too short or assembly invalid"
    message is replaced with the actual server response so failures are
    diagnosable.
    """
    last_error = None
    for attempt in range(1, _BLAT_MAX_ATTEMPTS + 1):
        try:
            return _fetch_blat_attempt(url, seqtype, database)
        except _RetryableBlatError as e:
            last_error = str(e)
            if attempt < _BLAT_MAX_ATTEMPTS:
                delay = _BLAT_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    f"BLAT attempt {attempt}/{_BLAT_MAX_ATTEMPTS} failed ({last_error}). "
                    f"Retrying in {delay:.1f}s."
                )
                time.sleep(delay)

    logger.error(
        f"BLAT of seqtype '{seqtype}' using assembly '{database}' failed after "
        f"{_BLAT_MAX_ATTEMPTS} attempts. Last error: {last_error}. "
        f"If the sequence is shorter than 20 characters or the assembly is invalid, "
        f"see https://genome.ucsc.edu/cgi-bin/hgBlat."
    )
    return None


def _fetch_blat_attempt(url, seqtype, database):
    """One BLAT attempt. Raises _RetryableBlatError on transient failures."""
    req = request.Request(url, headers={"User-Agent": "gget"})

    try:
        r = request.urlopen(req)
    except HTTPError as e:
        body = _safe_read_preview(e)
        # 5xx and 429 are transient; 4xx (other) are not.
        if e.code >= 500 or e.code == 429:
            raise _RetryableBlatError(f"HTTP {e.code} {e.reason}: {body!r}") from e
        logger.error(
            f"BLAT request failed: HTTP {e.code} {e.reason}. "
            f"seqtype='{seqtype}', assembly='{database}'. "
            f"Response preview: {body!r}"
        )
        return None
    except URLError as e:
        raise _RetryableBlatError(f"network error ({e.reason})") from e

    code = getattr(r, "status", None)
    if code is None:
        code = r.getcode()

    if code != 200:
        raise RuntimeError(
            f"HTTP response status code {code}. "
            "Please double-check arguments and try again.\n"
        )

    raw = r.read()
    try:
        return json_package.loads(raw)
    except JSONDecodeError:
        preview = _preview_bytes(raw)
        # Non-JSON from a 200 response is almost always an HTML error / throttle
        # page from UCSC, which is worth retrying.
        raise _RetryableBlatError(f"non-JSON response: {preview!r}")


def _safe_read_preview(response, limit=300):
    try:
        return _preview_bytes(response.read(), limit=limit)
    except Exception:
        return ""


def _preview_bytes(raw, limit=300):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    raw = raw.strip()
    if len(raw) > limit:
        return raw[:limit] + "..."
    return raw
