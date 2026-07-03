from __future__ import annotations

import json
from typing import Any

import requests
from bs4 import BeautifulSoup

# Custom functions
from .utils import (
    find_latest_ens_rel,
    find_nv_kingdom,
    ref_species_options,
    set_up_logger,
)

logger = set_up_logger()

from .constants import (  # noqa: E402
    DEFAULT_REQUESTS_TIMEOUT,
    ENSEMBL_FTP_URL,
    ENSEMBL_FTP_URL_GRCH37,
    ENSEMBL_FTP_URL_NV,
    GENCODE_FTP_URL,
)

# Mapping of `which` keys to (GENCODE file-name substring template, output dict key) for gget ref.
# {ver} is filled with the GENCODE version string (e.g. "v46" for human, "vM35" for mouse).
_GENCODE_FILES: dict[str, tuple[str, str]] = {
    "gtf": ("gencode.{ver}.annotation.gtf.gz", "annotation_gtf"),
    "dna": ("primary_assembly.genome.fa.gz", "genome_dna"),
    "cdna": ("gencode.{ver}.transcripts.fa.gz", "transcriptome_cdna"),
    "ncrna": ("gencode.{ver}.lncRNA_transcripts.fa.gz", "non-coding_seq_ncRNA"),
    "pep": ("gencode.{ver}.pc_translations.fa.gz", "protein_translation_pep"),
}
# Order used when `which="all"` is requested for GENCODE (mirrors the Ensembl ordering, minus 'cds').
_GENCODE_ALL_ORDER = ["cdna", "dna", "gtf", "ncrna", "pep"]


def find_FTP_link(url: str, link_substring: str) -> tuple[str | None, str | None, str | None]:
    """Helper function for gget ref to find an FTP link, its release date and size.

    Args:
    url             - URL link to FTP subfolder (e.g. GTF) including species and release
    link_to_find    - Unique substring to identify link to find

    Returns the link, date, and size as strings.
    """
    html = requests.get(url, timeout=DEFAULT_REQUESTS_TIMEOUT)

    # Raise error if status code not "OK" Response
    if html.status_code != 200:
        raise RuntimeError(f"HTTP response status code {html.status_code}. Please try again.\n")

    soup = BeautifulSoup(html.text, "html.parser")

    link_str = None
    date_str = None
    size_str = None

    # Get all entries from the website
    links = [stuff.text.strip() for stuff in soup.findAll("td")]
    for i, link in enumerate(links):
        # Find the correct link
        if link_substring in link:
            link_str = link
            # Get date and size
            date_str = links[i + 1]
            size_str = links[i + 2]

    return link_str, date_str, size_str


def _find_latest_gencode_release(organism: str) -> str:
    """Return the latest GENCODE release identifier for 'human' (e.g. '46') or 'mouse' (e.g. 'M35')."""
    base_url = f"{GENCODE_FTP_URL}Gencode_{organism}/"
    html = requests.get(base_url, timeout=DEFAULT_REQUESTS_TIMEOUT)
    if html.status_code != 200:
        raise RuntimeError(f"GENCODE FTP returned status code {html.status_code} for {base_url}. Please try again.\n")

    soup = BeautifulSoup(html.text, "html.parser")
    releases = [
        href.strip("/").replace("release_", "")
        for href in (a.get("href", "") for a in soup.find_all("a"))
        if href.startswith("release_")
    ]

    if organism == "mouse":
        # Mouse releases are prefixed with "M" (e.g. "M35")
        nums = [int(r[1:]) for r in releases if r.startswith("M") and r[1:].isdigit()]
        if not nums:
            raise RuntimeError(f"Could not determine the latest GENCODE mouse release from {base_url}.\n")
        return f"M{max(nums)}"

    nums = [int(r) for r in releases if r.isdigit()]
    if not nums:
        raise RuntimeError(f"Could not determine the latest GENCODE human release from {base_url}.\n")
    return str(max(nums))


def _list_gencode_files(base_url: str) -> list[tuple[str, str, str]]:
    """List every file in a GENCODE release directory as (filename, date, size) tuples.

    Powers the `list_files` escape hatch of gget ref, exposing the full GENCODE release
    directory (beyond the curated `which` set). The parent-directory link and any
    subdirectories are skipped; only files are returned.
    """
    html = requests.get(base_url, timeout=DEFAULT_REQUESTS_TIMEOUT)
    if html.status_code != 200:
        raise RuntimeError(f"GENCODE FTP returned status code {html.status_code} for {base_url}. Please try again.\n")

    soup = BeautifulSoup(html.text, "html.parser")
    files: list[tuple[str, str, str]] = []
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        link = cells[1].find("a")
        if link is None:
            continue
        name = link.get("href", "")
        # Skip the parent-directory link ("../"), subdirectories (end in "/"),
        # absolute-path links, and column-sort links ("?C=...").
        if not name or name.endswith("/") or name.startswith(("/", "?")):
            continue
        date_str = cells[2].get_text().strip()
        size_str = cells[3].get_text().strip()
        files.append((name, date_str, size_str))
    return files


def _gencode_ref(
    species: str,
    which: str | list[str],
    release: int | None,
    ftp: bool,
    save: bool,
    verbose: bool,
    list_files: bool = False,
) -> Any:
    """Fetch reference GTF/FASTA FTP links from GENCODE (human and mouse only). See `ref` for details."""
    # Resolve organism (GENCODE only provides human and mouse references)
    species_lower = species.lower()
    if species_lower in ("human", "homo_sapiens"):
        organism = "human"
    elif species_lower in ("mouse", "mus_musculus"):
        organism = "mouse"
    else:
        raise ValueError(
            f"GENCODE only provides reference files for human and mouse, but species '{species}' was passed.\n"
            "Use species 'human'/'homo_sapiens' or 'mouse'/'mus_musculus' with source='gencode', "
            "or use source='ensembl' (default) for other species.\n"
        )

    # Resolve the GENCODE release identifier ("46" for human, "M35" for mouse)
    if release is None:
        rel = _find_latest_gencode_release(organism)
    else:
        rel = f"M{release}" if organism == "mouse" else str(release)
    ver = f"v{rel}"
    base_url = f"{GENCODE_FTP_URL}Gencode_{organism}/release_{rel}/"

    # Escape hatch: list every file in the release directory (beyond the curated `which` set)
    if list_files:
        if verbose:
            logger.info(f"Listing all files in the GENCODE {organism} release {rel} directory.")
        all_files = _list_gencode_files(base_url)
        file_urls = [base_url + fname for fname, _, _ in all_files]
        listing: dict[str, dict[str, Any]] = {species_lower: {}}
        for fname, f_date, f_size in all_files:
            listing[species_lower][fname] = {
                "ftp": base_url + fname,
                "gencode_release": rel,
                "release_date": f_date.split(" ")[0] if f_date else "",
                "release_time": f_date.split(" ")[1] if f_date and " " in f_date else "",
                "bytes": f_size or "",
            }
        if ftp:
            if save:
                with open("gget_ref_results.txt", "w") as tfile:
                    tfile.write("\n".join(file_urls))
            return file_urls
        if save:
            with open("gget_ref_results.json", "w", encoding="utf-8") as file:
                json.dump(listing, file, ensure_ascii=False, indent=4)
        return listing

    # Normalize and validate the 'which' parameter
    if isinstance(which, str):
        which = [which]
    if len(which) > 1 and "all" in which:
        raise ValueError(
            "Parameter 'which' must be 'all', or any one or a combination of the following: "
            "'gtf', 'cdna', 'dna', 'ncrna', 'pep'.\n"
        )
    which_allowed = ["all", *_GENCODE_FILES.keys()]
    bad = [x for x in which if x not in which_allowed]
    if bad:
        extra = ""
        if "cds" in bad:
            extra = " (GENCODE does not provide a CDS file; use 'cdna' for transcripts or 'pep' for translations)"
        raise ValueError(
            "For source='gencode', parameter 'which' must be 'all', or any one or a combination of the "
            f"following: 'gtf', 'cdna', 'dna', 'ncrna', 'pep'.{extra}\n"
        )

    keys = _GENCODE_ALL_ORDER if "all" in which else which

    if verbose:
        logger.info(f"Fetching GENCODE reference information for {organism} from release {rel}.")

    ref_dict: dict[str, dict[str, Any]] = {species_lower: {}}
    urls: list[str] = []
    for key in keys:
        substring_template, out_key = _GENCODE_FILES[key]
        link_substring = substring_template.format(ver=ver)
        link_str, date_str, size_str = find_FTP_link(url=base_url, link_substring=link_substring)
        if link_str is not None:
            file_url = base_url + link_str
            date_part = (date_str or " ").split(" ")[0]
            time_part = (date_str or "  ").split(" ")[1] if date_str and " " in date_str else ""
            size_part = size_str or ""
        else:
            logger.warning(
                f"No GENCODE file matching '{link_substring}' was found in {base_url} "
                f"(the '{key}' entry will be empty). The upstream file naming may have changed."
            )
            file_url = ""
            date_part = ""
            time_part = ""
            size_part = ""

        urls.append(file_url)
        ref_dict[species_lower][out_key] = {
            "ftp": file_url,
            "gencode_release": rel,
            "release_date": date_part,
            "release_time": time_part,
            "bytes": size_part,
        }

    if ftp:
        if save:
            with open("gget_ref_results.txt", "w") as tfile:
                tfile.write("\n".join(urls))
        return urls

    if save:
        with open("gget_ref_results.json", "w", encoding="utf-8") as file:
            json.dump(ref_dict, file, ensure_ascii=False, indent=4)
    return ref_dict


def ref(
    species: str | None,
    which: str | list[str] = "all",
    release: int | None = None,
    ftp: bool = False,
    save: bool = False,
    list_species: bool = False,
    list_iv_species: bool = False,
    source: str = "ensembl",
    list_files: bool = False,
    verbose: bool = True,
) -> Any:
    """Fetch FTPs for reference genomes and annotations by species from Ensembl or GENCODE.

    Args:
    - species         Defines the species for which the reference should be fetched in the format "<genus>_<species>",
                      e.g. species = "homo_sapiens".
                      Supported shortcuts: "human", "mouse", "human_grch37" (accesses the GRCh37 genome assembly)
                      For source='gencode', only human ('human'/'homo_sapiens') and mouse ('mouse'/'mus_musculus') are supported.
    - which           Defines which results to return.
                      Default: 'all' -> Returns all available results.
                      Possible entries are one or a combination (as a list of strings) of the following:
                      'gtf' - Returns the annotation (GTF).
                      'cdna' - Returns the trancriptome (cDNA).
                      'dna' - Returns the genome (DNA).
                      'cds - Returns the coding sequences corresponding to Ensembl genes. (Does not contain UTR or intronic sequence.)
                      'cdrna' - Returns transcript sequences corresponding to non-coding RNA genes (ncRNA).
                      'pep' - Returns the protein translations of Ensembl genes.
                      Note: source='gencode' does not provide 'cds'; 'cdna' returns GENCODE transcript sequences and
                      'ncrna' returns GENCODE long non-coding RNA transcript sequences.
    - release         Defines the release number from which the files are fetched, e.g. release = 104.
                      Default: None -> latest release is used
                      For source='gencode', this is the GENCODE release number (e.g. 46); the mouse 'M' prefix is added automatically.
    - ftp             Return only the requested FTP links in a list (default: False).
    - save            Save the results in the local directory (default: False).
    - list_species    If True and `species=None`, returns a list of all available VERTEBRATE species from the Ensembl database (default: False).
                      (Can be combined with the `release` argument to get the available species from a specific Ensembl release.)
    - list_iv_species If True and `species=None`, returns a list of all available INVERTEBRATE species from the Ensembl database (default: False).
                      (Can be combined with the `release` argument to get the available species from a specific Ensembl release.)
    - source          Reference database to fetch from: 'ensembl' (default) or 'gencode' (human and mouse only).
    - list_files      Only for source='gencode'. If True, returns every file in the GENCODE release directory
                      for the given species (not just the curated `which` set), keyed by filename. Handy for
                      fetching GENCODE-specific files (GFF3, basic/comprehensive annotation, pc_transcripts,
                      metadata, ...) that `which` does not expose (default: False).
    - verbose         True/False whether to print progress information (default: True).

    Returns a dictionary containing the requested URLs with their respective Ensembl/GENCODE version and release date and time.
    (If FTP=True, returns a list containing only the URLs.)
    """
    # Fetch from GENCODE instead of Ensembl
    if source != "ensembl":
        if source != "gencode":
            raise ValueError(f"Parameter 'source' must be 'ensembl' or 'gencode', but '{source}' was passed.\n")
        if species is None:
            raise ValueError(
                "A species ('human'/'homo_sapiens' or 'mouse'/'mus_musculus') must be provided for source='gencode'.\n"
            )
        return _gencode_ref(species, which, release, ftp, save, verbose, list_files=list_files)

    if list_files:
        raise ValueError(
            "list_files=True is only supported with source='gencode' (it lists the full GENCODE release "
            "directory). Ensembl organizes files in per-type subdirectories; use the 'which' argument instead.\n"
        )

    # Return list of all available species
    if list_species:
        if release is None:
            if verbose:
                logger.info(
                    f"Fetching available vertebrate genomes (GTF and FASTA available) from Ensembl release {find_latest_ens_rel()} (latest)."
                )
        else:
            if verbose:
                logger.info(
                    f"Fetching available vertebrate genomes (GTF and FASTA available) from Ensembl release {release}."
                )

        # Find all available species for GTFs for this Ensembl release
        species_list_gtf = ref_species_options("gtf", release=release)
        # Find all available species for FASTAs for this Ensembl release
        species_list_dna = ref_species_options("dna", release=release)

        # Find intersection of the two lists
        # (Only species which have GTF and FASTAs available can continue)
        species_list = list(set(species_list_gtf) & set(species_list_dna))

        if save:
            with open("ensembl_species.txt", "w") as tfile:
                tfile.write("\n".join(species_list))

        return sorted(species_list)

    # Return list of all available invertebrate species
    elif list_iv_species:
        if release is None:
            if verbose:
                logger.info(
                    f"Fetching available invertebrate genomes (GTF and FASTA present) from Ensembl release {find_latest_ens_rel(database=ENSEMBL_FTP_URL_NV)} (latest)."
                )
        else:
            if verbose:
                logger.info(
                    f"Fetching available invertebrate genomes (GTF and FASTA present) from Ensembl release {release}."
                )

        # Find all available species for GTFs for this Ensembl release
        species_list_gtf = ref_species_options("gtf", database=ENSEMBL_FTP_URL_NV, release=release)
        # Find all available species for FASTAs for this Ensembl release
        species_list_dna = ref_species_options("dna", database=ENSEMBL_FTP_URL_NV, release=release)

        # Find intersection of the two lists
        # (Only species which have GTF and FASTAs available can continue)
        species_list = list(set(species_list_gtf) & set(species_list_dna))

        if save:
            with open("ensembl_iv_species.txt", "w") as tfile:
                tfile.write("\n".join(species_list))

        return sorted(species_list)

    ## Check 'which' parameter
    # If single which passed as string, convert to list
    if isinstance(which, str):
        which = [which]

    # Raise error if several values are passed and 'all' is included
    if len(which) > 1 and "all" in which:
        raise ValueError(
            "Parameter 'which' must be 'all', or any one or a combination of the following: 'gtf', 'cdna', 'dna', 'cds', 'ncrna', 'pep'.\n"
        )
    # Raise error if 'which' argument includes unsupported option
    which_allowed = ["all", "gtf", "cdna", "dna", "cds", "ncrna", "pep"]
    if any(x not in which_allowed for x in which):
        raise ValueError(
            "Parameter 'which' must be 'all', or any one or a combination of the following: 'gtf', 'cdna', 'dna', 'cds', 'ncrna', 'pep'.\n"
        )

    # Species shortcuts
    grch37 = False
    if species == "human":
        species = "homo_sapiens"
    if species == "mouse":
        species = "mus_musculus"
    if species == "human_grch37":
        species = "homo_sapiens"
        grch37 = True

    # In case species was passed with upper case letters
    species = species.lower()

    # GRCh37 database (releases same as standard database)
    if grch37:
        database = ENSEMBL_FTP_URL_GRCH37
        ENS_rel = find_latest_ens_rel(ENSEMBL_FTP_URL)
    # Standard database
    elif species in ref_species_options("dna", database=ENSEMBL_FTP_URL, release=release):
        database = ENSEMBL_FTP_URL
        # Find latest vertebrate Ensembl release
        ENS_rel = find_latest_ens_rel(database)
    # For non-vertebrates, switch to non-vertebrate databases
    else:
        database = ENSEMBL_FTP_URL_NV
        # Find latest NV Ensembl release
        ENS_rel = find_latest_ens_rel(database)

    # If release != None, use user-defined Ensembl release
    if release is not None:
        # Warn user when release is higher than the latest release
        if release > ENS_rel:
            logger.warning(f"Provided Ensembl release number {release} is greater than the latest release ({ENS_rel}).")
        ENS_rel = release

    if not grch37:
        ## Raise error if species not found (both FASTA and GTF have to be available)
        # Find all available species for genome FASTAs for this Ensembl release
        species_list_dna = ref_species_options("dna", database=database, release=ENS_rel)
        # Find all available species for GTFs for this Ensembl release
        species_list_gtf = ref_species_options("gtf", database=database, release=ENS_rel)
        # Find intersection of the two lists
        # (Only species which have GTF and FASTAs available can continue)
        species_list = list(set(species_list_gtf) & set(species_list_dna))

        if species not in species_list:
            raise ValueError(
                f"Species does not match any available species for Ensembl release {ENS_rel}. Please double-check spelling.\n"
                "'gget ref --list_species' -> lists out all available species (Python: 'gget.ref(None, list_species=True)').\n"
                "Combine with `release` argument to define specific Ensembl release (default: latest).\n"
            )

    ## Find kingdom for non-vertebrate species
    if database == ENSEMBL_FTP_URL_NV:
        kingdom = find_nv_kingdom(species, release=ENS_rel)

    ## Get GTF link for this species and release
    if "all" in which or "gtf" in which:
        # Define location of GTF links
        if database == ENSEMBL_FTP_URL_NV:
            gtf_search_url = database + f"release-{ENS_rel}/{kingdom}/gtf/{species}/"
        else:
            gtf_search_url = database + f"release-{ENS_rel}/gtf/{species}/"

        if grch37:
            link_substring = "GRCh37.87.gtf.gz"
        else:
            link_substring = f"{ENS_rel}.gtf.gz"

        # Get link, release date and dataset size
        gtf_str, gtf_date, gtf_size = find_FTP_link(url=gtf_search_url, link_substring=link_substring)
        # Build the final download link
        if not isinstance(gtf_str, type(None)):
            gtf_url = gtf_search_url + gtf_str
        else:
            gtf_url = ""
            gtf_date = " "
            gtf_size = ""

    ## Get cDNA FASTA link for this species and release
    if "all" in which or "cdna" in which:
        if database == ENSEMBL_FTP_URL_NV:
            # Define location of cdna links
            cdna_search_url = database + f"release-{ENS_rel}/{kingdom}/fasta/{species}/cdna/"
        else:
            # Define location of cdna links
            cdna_search_url = database + f"release-{ENS_rel}/fasta/{species}/cdna/"

        # Get link, release date and dataset size
        cdna_str, cdna_date, cdna_size = find_FTP_link(url=cdna_search_url, link_substring="cdna.all.fa")
        # Build the final download link
        if not isinstance(cdna_str, type(None)):
            cdna_url = cdna_search_url + cdna_str
        else:
            cdna_url = ""
            cdna_date = " "
            cdna_size = ""

    ## Get DNA FASTA link for this species and release
    if "all" in which or "dna" in which:
        # Define location of dna links
        if database == ENSEMBL_FTP_URL_NV:
            dna_search_url = database + f"release-{ENS_rel}/{kingdom}/fasta/{species}/dna/"
        else:
            dna_search_url = database + f"release-{ENS_rel}/fasta/{species}/dna/"
        # Get link, release date and dataset size
        dna_str, dna_date, dna_size = find_FTP_link(url=dna_search_url, link_substring=".dna.primary_assembly.fa")

        # Get toplevel if primary assembly not available
        if dna_str is None:
            # Get link, release date and dataset size
            dna_str, dna_date, dna_size = find_FTP_link(url=dna_search_url, link_substring=".dna.toplevel.fa")

        # Build the final download link
        if not isinstance(dna_str, type(None)):
            dna_url = dna_search_url + dna_str
        else:
            dna_url = ""
            dna_date = " "
            dna_size = ""

    ## Get CDS FASTA link for this species and release
    if "all" in which or "cds" in which:
        # Define location of cds links
        if database == ENSEMBL_FTP_URL_NV:
            cds_search_url = database + f"release-{ENS_rel}/{kingdom}/fasta/{species}/cds/"
        else:
            cds_search_url = database + f"release-{ENS_rel}/fasta/{species}/cds/"
        # Get link, release date and dataset size
        cds_str, cds_date, cds_size = find_FTP_link(url=cds_search_url, link_substring="cds.all.fa")
        # Build the final download link
        if not isinstance(cds_str, type(None)):
            cds_url = cds_search_url + cds_str
        else:
            cds_url = ""
            cds_date = " "
            cds_size = ""

    ## Get ncRNA FASTA link for this species and release (if available)
    if "all" in which or "ncrna" in which:
        # Define location of ncRNA links
        if database == ENSEMBL_FTP_URL_NV:
            ncrna_search_url = database + f"release-{ENS_rel}/{kingdom}/fasta/{species}/ncrna/"
        else:
            ncrna_search_url = database + f"release-{ENS_rel}/fasta/{species}/ncrna/"

        html = requests.get(ncrna_search_url)

        # If ncRNA data is not available, HTML requests returns an error code (!= 200)
        if html.status_code == 200:
            soup = BeautifulSoup(html.text, "html.parser")

            # Get all entries from the website
            links = [stuff.text.strip() for stuff in soup.findAll("td")]
            for i, link in enumerate(links):
                # Find the correct link
                if ".ncrna.fa" in link:
                    ncrna_str = link
                    # Get date and size
                    ncrna_date = links[i + 1]
                    ncrna_size = links[i + 2]

            ncrna_url = ncrna_search_url + ncrna_str

        # If the HTML request returned an error code here, I will assume that ncRNA data is not available
        else:
            ncrna_url = ""
            ncrna_date = " "
            ncrna_size = ""

    ## Get pep FASTA link for this species and release
    if "all" in which or "pep" in which:
        # Define location of pep links
        if database == ENSEMBL_FTP_URL_NV:
            pep_search_url = database + f"release-{ENS_rel}/{kingdom}/fasta/{species}/pep/"
        else:
            pep_search_url = database + f"release-{ENS_rel}/fasta/{species}/pep/"
        # Get link, release date and dataset size
        pep_str, pep_date, pep_size = find_FTP_link(url=pep_search_url, link_substring=".pep.all.fa")
        # Build the final download link
        if not isinstance(pep_str, type(None)):
            pep_url = pep_search_url + pep_str
        else:
            pep_url = ""
            pep_date = " "
            pep_size = ""

    ## Return results
    # If FTP=False, return dictionary/json of specified results
    if ftp is False:
        ref_dict: dict[str, dict[str, Any]] = {species: {}}
        for return_val in which:
            if return_val == "all":
                ref_dict = {
                    species: {
                        "transcriptome_cdna": {
                            "ftp": cdna_url,
                            "ensembl_release": int(ENS_rel),
                            "release_date": cdna_date.split(" ")[0],
                            "release_time": cdna_date.split(" ")[1],
                            "bytes": cdna_size,
                        },
                        "genome_dna": {
                            "ftp": dna_url,
                            "ensembl_release": int(ENS_rel),
                            "release_date": dna_date.split(" ")[0],
                            "release_time": dna_date.split(" ")[1],
                            "bytes": dna_size,
                        },
                        "annotation_gtf": {
                            "ftp": gtf_url,
                            "ensembl_release": int(ENS_rel),
                            "release_date": gtf_date.split(" ")[0],
                            "release_time": gtf_date.split(" ")[1],
                            "bytes": gtf_size,
                        },
                        "coding_seq_cds": {
                            "ftp": cds_url,
                            "ensembl_release": int(ENS_rel),
                            "release_date": cds_date.split(" ")[0],
                            "release_time": cds_date.split(" ")[1],
                            "bytes": cds_size,
                        },
                        "non-coding_seq_ncRNA": {
                            "ftp": ncrna_url,
                            "ensembl_release": int(ENS_rel),
                            "release_date": ncrna_date.split(" ")[0],
                            "release_time": ncrna_date.split(" ")[1],
                            "bytes": ncrna_size,
                        },
                        "protein_translation_pep": {
                            "ftp": pep_url,
                            "ensembl_release": int(ENS_rel),
                            "release_date": pep_date.split(" ")[0],
                            "release_time": pep_date.split(" ")[1],
                            "bytes": pep_size,
                        },
                    }
                }
            elif return_val == "gtf":
                dict_temp = {
                    "annotation_gtf": {
                        "ftp": gtf_url,
                        "ensembl_release": int(ENS_rel),
                        "release_date": gtf_date.split(" ")[0],
                        "release_time": gtf_date.split(" ")[1],
                        "bytes": gtf_size,
                    },
                }
                ref_dict[species].update(dict_temp)
            elif return_val == "cdna":
                dict_temp = {
                    "transcriptome_cdna": {
                        "ftp": cdna_url,
                        "ensembl_release": int(ENS_rel),
                        "release_date": cdna_date.split(" ")[0],
                        "release_time": cdna_date.split(" ")[1],
                        "bytes": cdna_size,
                    },
                }
                ref_dict[species].update(dict_temp)
            elif return_val == "dna":
                dict_temp = {
                    "genome_dna": {
                        "ftp": dna_url,
                        "ensembl_release": int(ENS_rel),
                        "release_date": dna_date.split(" ")[0],
                        "release_time": dna_date.split(" ")[1],
                        "bytes": dna_size,
                    },
                }
                ref_dict[species].update(dict_temp)
            elif return_val == "cds":
                dict_temp = {
                    "coding_seq_cds": {
                        "ftp": cds_url,
                        "ensembl_release": int(ENS_rel),
                        "release_date": cds_date.split(" ")[0],
                        "release_time": cds_date.split(" ")[1],
                        "bytes": cds_size,
                    },
                }
                ref_dict[species].update(dict_temp)
            elif return_val == "ncrna":
                dict_temp = {
                    "non-coding_seq_ncRNA": {
                        "ftp": ncrna_url,
                        "ensembl_release": int(ENS_rel),
                        "release_date": ncrna_date.split(" ")[0],
                        "release_time": ncrna_date.split(" ")[1],
                        "bytes": ncrna_size,
                    },
                }
                ref_dict[species].update(dict_temp)
            elif return_val == "pep":
                dict_temp = {
                    "protein_translation_pep": {
                        "ftp": pep_url,
                        "ensembl_release": int(ENS_rel),
                        "release_date": pep_date.split(" ")[0],
                        "release_time": pep_date.split(" ")[1],
                        "bytes": pep_size,
                    },
                }
                ref_dict[species].update(dict_temp)
            else:
                raise ValueError(
                    "Parameter 'which' must be 'all', or any one or a combination of the following: 'gtf', 'cdna', 'dna', 'cds', 'ncrna', 'pep'.\n"
                )

        if save:
            with open("gget_ref_results.json", "w", encoding="utf-8") as file:
                json.dump(ref_dict, file, ensure_ascii=False, indent=4)
        if verbose:
            logger.info(f"Fetching reference information for {species} from Ensembl release: {ENS_rel}.")
        return ref_dict

    # If FTP==True, return only the specified URLs as a list
    if ftp:
        if verbose:
            logger.info(f"Fetching reference information for {species} from Ensembl release: {ENS_rel}.")
        results = []
        for return_val in which:
            if return_val == "all":
                results.append(gtf_url)
                results.append(cdna_url)
                results.append(dna_url)
                results.append(cds_url)
                results.append(ncrna_url)
                results.append(pep_url)
            elif return_val == "gtf":
                results.append(gtf_url)
            elif return_val == "cdna":
                results.append(cdna_url)
            elif return_val == "dna":
                results.append(dna_url)
            elif return_val == "cds":
                results.append(cds_url)
            elif return_val == "ncrna":
                results.append(ncrna_url)
            elif return_val == "pep":
                results.append(pep_url)
            else:
                raise ValueError(
                    "Parameter 'which' must be 'all', or any one or a combination of the following: 'gtf', 'cdna', 'dna', 'cds', 'ncrna', 'pep'.\n"
                )

        if save:
            with open("gget_ref_results.txt", "w") as tfile:
                tfile.write("\n".join(results))

        return results
