from bs4 import BeautifulSoup
import requests
import json

# Custom functions
from .utils import (
    ref_species_options,
    find_latest_ens_rel,
    find_nv_kingdom,
    set_up_logger,
)

logger = set_up_logger()

from .constants import (
    ENSEMBL_FTP_URL,
    ENSEMBL_FTP_URL_NV,
    ENSEMBL_FTP_URL_GRCH37,
    DEFAULT_REQUESTS_TIMEOUT,
)


def find_FTP_link(url, link_substring):
    """
    Helper function for gget ref to find an FTP link, its release date and size.

    Args:
    url             - URL link to FTP subfolder (e.g. GTF) including species and release
    link_to_find    - Unique substring to identify link to find

    Returns the link, date, and size as strings.
    """
    html = requests.get(url, timeout=DEFAULT_REQUESTS_TIMEOUT)

    # Raise error if status code not "OK" Response
    if html.status_code != 200:
        raise RuntimeError(
            f"HTTP response status code {html.status_code}. Please try again.\n"
        )

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


def ref(
    species,
    which="all",
    release=None,
    ftp=False,
    save=False,
    list_species=False,
    list_iv_species=False,
    verbose=True,
):
    """
    Fetch FTPs for reference genomes and annotations by species from Ensembl.

    Args:
    - species         Defines the species for which the reference should be fetched in the format "<genus>_<species>",
                      e.g. species = "homo_sapiens".
                      Supported shortcuts: "human", "mouse", "human_grch37" (accesses the GRCh37 genome assembly)
    - which           Defines which results to return.
                      Default: 'all' -> Returns all available results.
                      Possible entries are one or a combination (as a list of strings) of the following:
                      'gtf' - Returns the annotation (GTF).
                      'cdna' - Returns the trancriptome (cDNA).
                      'dna' - Returns the genome (DNA).
                      'cds - Returns the coding sequences corresponding to Ensembl genes. (Does not contain UTR or intronic sequence.)
                      'cdrna' - Returns transcript sequences corresponding to non-coding RNA genes (ncRNA).
                      'pep' - Returns the protein translations of Ensembl genes.
    - release         Defines the Ensembl release number from which the files are fetched, e.g. release = 104.
                      Default: None -> latest Ensembl release is used
    - ftp             Return only the requested FTP links in a list (default: False).
    - save            Save the results in the local directory (default: False).
    - list_species    If True and `species=None`, returns a list of all available VERTEBRATE species from the Ensembl database (default: False).
                      (Can be combined with the `release` argument to get the available species from a specific Ensembl release.)
    - list_iv_species If True and `species=None`, returns a list of all available INVERTEBRATE species from the Ensembl database (default: False).
                      (Can be combined with the `release` argument to get the available species from a specific Ensembl release.)
    - verbose         True/False whether to print progress information (default: True).

    Returns a dictionary containing the requested URLs with their respective Ensembl version and release date and time.
    (If FTP=True, returns a list containing only the URLs.)
    """
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
        species_list_gtf = ref_species_options(
            "gtf", database=ENSEMBL_FTP_URL_NV, release=release
        )
        # Find all available species for FASTAs for this Ensembl release
        species_list_dna = ref_species_options(
            "dna", database=ENSEMBL_FTP_URL_NV, release=release
        )

        # Find intersection of the two lists
        # (Only species which have GTF and FASTAs available can continue)
        species_list = list(set(species_list_gtf) & set(species_list_dna))

        if save:
            with open("ensembl_iv_species.txt", "w") as tfile:
                tfile.write("\n".join(species_list))

        return sorted(species_list)

    ## Check 'which' parameter
    # If single which passed as string, convert to list
    if type(which) == str:
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
            f"Parameter 'which' must be 'all', or any one or a combination of the following: 'gtf', 'cdna', 'dna', 'cds', 'ncrna', 'pep'.\n"
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
    elif species in ref_species_options(
        "dna", database=ENSEMBL_FTP_URL, release=release
    ):
        database = ENSEMBL_FTP_URL
        # Find latest vertebrate Ensembl release
        ENS_rel = find_latest_ens_rel(database)
    # For non-vertebrates, switch to non-vertebrate databases
    else:
        database = ENSEMBL_FTP_URL_NV
        # Find latest NV Ensembl release
        ENS_rel = find_latest_ens_rel(database)

    # If release != None, use user-defined Ensembl release
    if release != None:
        # Warn user when release is higher than the latest release
        if release > ENS_rel:
            logger.warning(
                f"Provided Ensembl release number {release} is greater than the latest release ({ENS_rel})."
            )
        ENS_rel = release

    if not grch37:
        ## Raise error if species not found (both FASTA and GTF have to be available)
        # Find all available species for genome FASTAs for this Ensembl release
        species_list_dna = ref_species_options(
            "dna", database=database, release=ENS_rel
        )
        # Find all available species for GTFs for this Ensembl release
        species_list_gtf = ref_species_options(
            "gtf", database=database, release=ENS_rel
        )
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
        gtf_str, gtf_date, gtf_size = find_FTP_link(
            url=gtf_search_url, link_substring=link_substring
        )
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
            cdna_search_url = (
                database + f"release-{ENS_rel}/{kingdom}/fasta/{species}/cdna/"
            )
        else:
            # Define location of cdna links
            cdna_search_url = database + f"release-{ENS_rel}/fasta/{species}/cdna/"

        # Get link, release date and dataset size
        cdna_str, cdna_date, cdna_size = find_FTP_link(
            url=cdna_search_url, link_substring="cdna.all.fa"
        )
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
            dna_search_url = (
                database + f"release-{ENS_rel}/{kingdom}/fasta/{species}/dna/"
            )
        else:
            dna_search_url = database + f"release-{ENS_rel}/fasta/{species}/dna/"
        # Get link, release date and dataset size
        dna_str, dna_date, dna_size = find_FTP_link(
            url=dna_search_url, link_substring=".dna.primary_assembly.fa"
        )

        # Get toplevel if primary assembly not available
        if dna_str is None:
            # Get link, release date and dataset size
            dna_str, dna_date, dna_size = find_FTP_link(
                url=dna_search_url, link_substring=".dna.toplevel.fa"
            )

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
            cds_search_url = (
                database + f"release-{ENS_rel}/{kingdom}/fasta/{species}/cds/"
            )
        else:
            cds_search_url = database + f"release-{ENS_rel}/fasta/{species}/cds/"
        # Get link, release date and dataset size
        cds_str, cds_date, cds_size = find_FTP_link(
            url=cds_search_url, link_substring="cds.all.fa"
        )
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
            ncrna_search_url = (
                database + f"release-{ENS_rel}/{kingdom}/fasta/{species}/ncrna/"
            )
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
            pep_search_url = (
                database + f"release-{ENS_rel}/{kingdom}/fasta/{species}/pep/"
            )
        else:
            pep_search_url = database + f"release-{ENS_rel}/fasta/{species}/pep/"
        # Get link, release date and dataset size
        pep_str, pep_date, pep_size = find_FTP_link(
            url=pep_search_url, link_substring=".pep.all.fa"
        )
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
        ref_dict = {species: {}}
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
            logger.info(
                f"Fetching reference information for {species} from Ensembl release: {ENS_rel}."
            )
        return ref_dict

    # If FTP==True, return only the specified URLs as a list
    if ftp:
        if verbose:
            logger.info(
                f"Fetching reference information for {species} from Ensembl release: {ENS_rel}."
            )
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
