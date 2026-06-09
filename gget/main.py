import argparse
import sys
from datetime import datetime
from typing import Optional

import pandas as pd

# Get current date and time for alphafold default foldername
dt_string = datetime.now().strftime("%Y_%m_%d-%H_%M")

import os
import json
import subprocess

from .utils import set_up_logger

logger = set_up_logger()

from .__init__ import __version__

# Module functions
from .gget_ref import ref
from .gget_search import search
from .gget_info import info
from .gget_seq import seq
from .gget_muscle import muscle
from .gget_blast import blast
from .gget_blat import blat
from .gget_enrichr import enrichr
from .gget_archs4 import archs4
from .gget_alphafold import alphafold
from .gget_setup import setup
from .gget_pdb import pdb
from .gget_gpt import gpt
from .gget_cellxgene import cellxgene
from .gget_elm import elm
from .gget_diamond import diamond
from .gget_cosmic import cosmic
from .gget_mutate import mutate
from .gget_opentargets import opentargets, OPENTARGETS_RESOURCES
from .gget_cbio import cbio_plot, cbio_search
from .gget_bgee import bgee
from .gget_8cube import specificity, psi_block, gene_expression
from .gget_virus import virus


# Custom formatter for help messages that preserved the text formatting and adds the default value to the end of the help message
class CustomHelpFormatter(argparse.RawTextHelpFormatter):
    def _get_help_string(self, action):
        help_str = action.help if action.help else ""
        if (
            "%(default)" not in help_str
            and action.default is not argparse.SUPPRESS
            and action.default is not None
            # default information can be deceptive or confusing for boolean flags.
            # For example, `--quiet` says "Does not print progress information. (default: True)" even though
            # the default action is to NOT be quiet (to the user, the default is False).
            and not isinstance(action, argparse._StoreTrueAction)
            and not isinstance(action, argparse._StoreFalseAction)
        ):
            help_str += " (default: %(default)s)"
        return help_str


def convert_to_list(*args):
    args_list = list(args)
    return args_list


def int_or_str(value):
    try:
        return int(value)
    except ValueError:
        return value
    
def str_to_bool_or_none(value):
    if value is None or value.lower() in ('none', 'null', ''):
        return None
    if value.lower() in ('true', 'yes', 't', '1'):
        return True
    if value.lower() in ('false', 'no', 'f', '0'):
        return False
    # If it's not a clear boolean/None, treat as a string or raise error
    return value 


def parse_opentargets_filter(filter_arg):
    if "=" not in filter_arg:
        raise argparse.ArgumentTypeError(
            "OpenTargets filters must be passed as COLUMN=VALUE, e.g. 'disease.id=EFO_0000274'."
        )

    filter_key, filter_value = filter_arg.split("=", 1)
    filter_key = filter_key.strip()
    filter_value = filter_value.strip()

    if not filter_key:
        raise argparse.ArgumentTypeError(
            "OpenTargets filter column name cannot be empty."
        )

    return filter_key, int_or_str(str_to_bool_or_none(filter_value))


def main():
    """
    Function containing argparse parsers and arguments to allow the use of gget from the terminal.
    """
    # Define parent parser
    parent_parser = argparse.ArgumentParser(
        description=f"gget v{__version__}", add_help=False
    )
    # Initiate subparsers
    parent_subparsers = parent_parser.add_subparsers(dest="command")
    # Define parent (not sure why I need both parent parser and parent, but otherwise it does not work)
    parent = argparse.ArgumentParser(add_help=False)

    # Add custom help argument to parent parser
    parent_parser.add_argument(
        "-h", "--help", action="store_true", help="Print manual."
    )
    # Add custom version argument to parent parser
    parent_parser.add_argument(
        "-v", "--version", action="store_true", help="Print version."
    )

    ## gget ref subparser
    ref_desc = "Fetch FTPs for reference genomes and annotations by species."
    parser_ref = parent_subparsers.add_parser(
        "ref",
        parents=[parent],
        description=ref_desc,
        help=ref_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # ref parser arguments
    parser_ref.add_argument(
        "species",
        type=str,
        nargs="?",
        default=None,
        help=(
            "Species or database to be searched. Species should be passed in the format 'genus_species', e.g. 'homo_sapiens'.\n"
            "Supported shortcuts: 'human', 'mouse', 'human_grch37' (accesses the GRCh37 genome assembly)"
        ),
    )
    parser_ref.add_argument(
        "-l",
        "--list_species",
        default=False,
        action="store_true",
        required=False,
        help=(
            "List all available vertebrate species from the Ensembl database.\n"
            "(Combine with `--release` to get the available species from a specific Ensembl release.)"
        ),
    )
    parser_ref.add_argument(
        "-liv",
        "--list_iv_species",
        default=False,
        action="store_true",
        required=False,
        help=(
            "List all available invertebrate species from the Ensembl database.\n"
            "(Combine with `--release` to get the available species from a specific Ensembl release.)"
        ),
    )
    parser_ref.add_argument(
        "-w",
        "--which",
        default="all",
        type=str,
        required=False,
        help=(
            "Defines which results to return.\n"
            "Default: 'all' -> Returns all available results.\n"
            "Possible entries are one or a combination (as a comma-separated list) of the following:\n"
            "'gtf' - Returns the annotation (GTF).\n"
            "'cdna' - Returns the trancriptome (cDNA).\n"
            "'dna' - Returns the genome (DNA).\n"
            "'cds - Returns the coding sequences corresponding to Ensembl genes. (Does not contain UTR or intronic sequence.)\n"
            "'cdrna' - Returns transcript sequences corresponding to non-coding RNA genes (ncRNA).\n"
            "'pep' - Returns the protein translations of Ensembl genes.\n"
            "Example: '-w dna,gtf'"
        ),
    )
    parser_ref.add_argument(
        "-r",
        "--release",
        default=None,
        type=int,
        required=False,
        help="Ensembl release the FTPs will be fetched from, e.g. 104 (default: latest Ensembl release).",
    )
    parser_ref.add_argument(
        "-ftp",
        "--ftp",
        default=False,
        action="store_true",
        required=False,
        help="Return only the FTP link(s).",
    )
    parser_ref.add_argument(
        "-d",
        "--download",
        default=False,
        action="store_true",
        required=False,
        help="Download FTPs to the directory specified by --out_dir using curl.",
    )
    parser_ref.add_argument(
        "-od",
        "--out_dir",
        type=str,
        required=False,
        help=(
            "Path to the directory the FTPs will be saved in, e.g. path/to/directory.\n"
            "Default: Current working directory."
        ),
    )
    parser_ref.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to the file the results will be saved in, e.g. path/to/directory/results.json.\n"
            "Default: Standard out."
        ),
    )
    parser_ref.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )
    parser_ref.add_argument(
        "-s",
        "--species",
        type=str,
        required=False,
        dest="species_deprecated",
        help="DEPRECATED - use positional argument instead. Species for which the FTPs will be fetched, e.g. homo_sapiens.",
    )

    ## gget search subparser
    search_desc = (
        "Fetch gene and transcript IDs from Ensembl using free-form search terms."
    )
    parser_gget = parent_subparsers.add_parser(
        "search",
        parents=[parent],
        description=search_desc,
        help=search_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # Search parser arguments
    parser_gget.add_argument(
        "searchwords",
        type=str,
        nargs="+",
        help="One or more free form search words, e.g. gaba, nmda.",
    )
    parser_gget.add_argument(
        "-s",
        "--species",
        type=str,
        required=True,
        help=(
            "Species or database to be queried, e.g. 'homo_sapiens' or 'arabidopsis_thaliana'.\n"
            "To pass a specific database, pass the name of the CORE database, e.g. 'mus_musculus_dba2j_core_105_1'.\n"
            "All available core databases can be found here:\n"
            "Vertebrates: http://ftp.ensembl.org/pub/current/mysql/\n"
            "Invertebrates: http://ftp.ensemblgenomes.org/pub/current/ + kingdom + mysql/\n"
            "Supported shortcuts: 'human', 'mouse'."
        ),
    )
    parser_gget.add_argument(
        "-r",
        "--release",
        default=None,
        type=int,
        required=False,
        help=(
            "Defines the Ensembl release number from which the files are fetched, e.g. 104.\n"
            "Note: Does not apply to invertebrate species (you can pass a specific core database (which include a release number) to the species argument instead).\n"
            "This argument is overwritten if a specific database (which includes a release number) is passed to the species argument.\n"
            "Default: None -> latest Ensembl release is used."
        ),
    )
    parser_gget.add_argument(
        "-t",
        "--id_type",
        choices=["gene", "transcript"],
        default="gene",
        type=str,
        required=False,
        help=(
            "'gene': Returns genes that match the searchwords. (default).\n"
            "'transcript': Returns transcripts that match the searchwords."
        ),
    )
    parser_gget.add_argument(
        "-ao",
        "--andor",
        choices=["and", "or"],
        default="or",
        type=str,
        required=False,
        help=(
            "'or': Gene descriptions must include at least one of the searchwords (default).\n"
            "'and': Only return genes whose descriptions include all searchwords."
        ),
    )
    parser_gget.add_argument(
        "-l",
        "--limit",
        type=int,
        default=None,
        required=False,
        help="Limits the number of results, e.g. 10 (default: None).",
    )
    parser_gget.add_argument(
        "-csv",
        "--csv",
        default=True,
        action="store_false",
        required=False,
        help="Returns results in csv format instead of json.",
    )
    parser_gget.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to the file the results will be saved in, e.g. path/to/directory/results.json.\n"
            "Default: Standard out."
        ),
    )
    parser_gget.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )
    parser_gget.add_argument(
        "-sw",
        "--searchwords",
        type=str,
        nargs="*",
        required=False,
        dest="sw_deprecated",
        help="DEPRECATED - use positional argument instead. One or more free form search words, e.g. gaba, nmda.",
    )
    parser_gget.add_argument(
        "--seqtype",
        default=None,
        type=str,
        required=False,
        help="DEPRECATED - use argument 'id_type' instead.",
    )
    parser_gget.add_argument(
        "-j",
        "--json",
        default=False,
        action="store_true",
        required=False,
        help="DEPRECATED - json is now the default output format (convert to csv using flag [--csv]).",
    )
    ## gget elm subparser
    elm_desc = "Locally predicts Eukaryotic Linear Motifs from an amino acid sequence or UniProt Acc using data from the ELM database (http://elm.eu.org/media/Elm_academic_license.pdf)."
    parser_elm = parent_subparsers.add_parser(
        "elm",
        parents=[parent],
        description=elm_desc,
        help=elm_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # elm parser arguments
    parser_elm.add_argument(
        "sequence",
        type=str,
        help="Amino acid sequence or Uniprot Acc. If Uniprot Acc, use flag '--uniprot'.",
    )
    parser_elm.add_argument(
        "-u",
        "--uniprot",
        default=False,
        action="store_true",
        required=False,
        help="Use this flag if input is a Uniprot Acc instead of an amino acid sequence.",
    )
    parser_elm.add_argument(
        "-s",
        "--sensitivity",
        type=str,
        default="very-sensitive",
        required=False,
        choices=[
            "fast",
            "mid-sensitive",
            "sensitive",
            "more-sensitive",
            "very-sensitive",
            "ultra-sensitive",
        ],
        help="Sensitivity of DIAMOND alignment.",
    )
    parser_elm.add_argument(
        "-t",
        "--threads",
        type=int,
        default=1,
        required=False,
        help="Number of threads used in DIAMOND alignment.",
    )
    parser_elm.add_argument(
        "-bin",
        "--diamond_binary",
        type=str,
        default=None,
        required=False,
        help="Path to DIAMOND binary. Default: None -> Uses DIAMOND binary installed with gget.",
    )
    parser_elm.add_argument(
        "-e",
        "--expand",
        default=False,
        action="store_true",
        required=False,
        help="Expand the information returned in the regex data frame to include the protein names, organisms, and references that the motif was orignally validated on.",
    )
    parser_elm.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )
    parser_elm.add_argument(
        "-csv",
        "--csv",
        default=True,
        action="store_false",
        required=False,
        help="Returns results in csv format instead of json.",
    )
    parser_elm.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to folder to save results in, e.g. path/to/directory.\n"
            "Default: Standard out."
        ),
    )
    # gget diamond parser
    diamond_desc = "Align multiple protein or translated DNA sequences using DIAMOND."
    parser_diamond = parent_subparsers.add_parser(
        "diamond",
        parents=[parent],
        description=diamond_desc,
        help=diamond_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    parser_diamond.add_argument(
        "query",
        type=str,
        nargs="+",
        help="Sequences (str or list) or path to FASTA file containing sequences to be aligned against the reference.",
    )
    parser_diamond.add_argument(
        "-ref",
        "--reference",
        type=str,
        nargs="+",
        required=True,
        help="Reference sequences (str or list) or path to FASTA file containing reference sequences. Add `-x` flag if reference sequences are amino acid sequences and query sequences are nucleotide sequences.",
    )
    parser_diamond.add_argument(
        "-x",
        "--translated",
        default=False,
        action="store_true",
        required=False,
        help="Perform translated alignment of nucleotide sequences to amino acid reference sequences.",
    )
    parser_diamond.add_argument(
        "-db",
        "--diamond_db",
        type=str,
        default=None,
        required=False,
        help=(
            "Path to save DIAMOND database created from reference.\n"
            "Default: None -> Temporary db file will be deleted after alignment or saved in 'out' if 'out' is provided."
        ),
    )
    parser_diamond.add_argument(
        "-s",
        "--sensitivity",
        choices=[
            "fast",
            "mid-sensitive",
            "sensitive",
            "more-sensitive",
            "very-sensitive",
            "ultra-sensitive",
        ],
        default="very-sensitive",
        type=str,
        required=False,
        help=(
            "One of the following:'fast', 'mid-sensitive', 'sensitive', 'more-sensitive', 'very-sensitive' or 'ultra-sensitive'.\n"
            "Sensitivity of DIAMOND alignment. Default: 'very-sensitive'."
        ),
    )
    parser_diamond.add_argument(
        "-t",
        "--threads",
        default=1,
        type=int,
        required=False,
        help="Number of threads to use for alignment.",
    )
    parser_diamond.add_argument(
        "-bin",
        "--diamond_binary",
        type=str,
        default=None,
        required=False,
        help=(
            "Path to DIAMOND binary,  e.g. path/bins/Linux/diamond.\n"
            "Default: None -> Uses DIAMOND binary installed with gget."
        ),
    )
    parser_diamond.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )
    parser_diamond.add_argument(
        "-csv",
        "--csv",
        default=True,
        action="store_false",
        required=False,
        help="Returns results in csv format instead of json.",
    )
    parser_diamond.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to folder to save DIAMOND results in, e.g. path/to/directory/results.json.\n"
            "Default: Standard out, temporary files are deleted."
        ),
    )

    ## gget info subparser
    info_desc = "Fetch gene and transcript metadata using Ensembl IDs."
    parser_info = parent_subparsers.add_parser(
        "info",
        parents=[parent],
        description=info_desc,
        help=info_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # info parser arguments
    parser_info.add_argument(
        "ens_ids",
        type=str,
        nargs="+",
        help="One or more Ensembl, WormBase, or FlyBase IDs.",
    )
    parser_info.add_argument(
        "-n",
        "--ncbi",
        default=True,
        action="store_false",
        required=False,
        help="TURN OFF results from NCBI database.",
    )
    parser_info.add_argument(
        "-u",
        "--uniprot",
        default=True,
        action="store_false",
        required=False,
        help="TURN OFF results from UniProt database.",
    )
    parser_info.add_argument(
        "-csv",
        "--csv",
        default=True,
        action="store_false",
        required=False,
        help="Returns results in csv format instead of json.",
    )
    parser_info.add_argument(
        "-pdb",
        "--pdb",
        default=False,
        action="store_true",
        required=False,
        help="Also returns PDB IDs (might increase run time).",
    )
    parser_info.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )
    parser_info.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to file the results will be saved as, e.g. path/to/directory/results.json.\n"
            "Default: Standard out."
        ),
    )
    parser_info.add_argument(
        "-eo",
        "--ensembl_only",
        default=False,
        action="store_true",
        required=False,
        help="DEPRECATED - only returns results from Ensembl (excludes PDB, UniProt, and NCBI results).",
    )
    parser_info.add_argument(
        "-id",
        "--ens_ids",
        type=str,
        nargs="+",
        required=False,
        dest="id_deprecated",
        help="DEPRECATED - use positional argument instead. One or more Ensembl, WormBase or FlyBase IDs).",
    )
    parser_info.add_argument(
        "-j",
        "--json",
        default=False,
        action="store_true",
        required=False,
        help="DEPRECATED - json is now the default output format (convert to csv using flag [--csv]).",
    )
    parser_info.add_argument(
        "-e",
        "--expand",
        default=False,
        action="store_true",
        required=False,
        help=("DEPRECATED - gget info now always returns all available information."),
    )

    ## gget seq subparser
    seq_desc = "Fetch nucleotide or amino acid sequence (FASTA) of a gene (and all isoforms) or transcript by Ensembl, WormBase or FlyBase ID. "
    parser_seq = parent_subparsers.add_parser(
        "seq",
        parents=[parent],
        description=seq_desc,
        help=seq_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # seq parser arguments
    parser_seq.add_argument(
        "ens_ids",
        type=str,
        nargs="+",
        help="One or more Ensembl, WormBase, or FlyBase IDs.",
    )
    parser_seq.add_argument(
        "-t",
        "--translate",
        default=False,
        action="store_true",
        required=False,
        help=(
            "Returns amino acid sequences from UniProt. (Otherwise returns nucleotide sequences from Ensembl.)"
        ),
    )
    parser_seq.add_argument(
        "-iso",
        "--isoforms",
        default=False,
        action="store_true",
        required=False,
        help="Returns sequences of all known transcripts (default: False). (Only for gene IDs.)",
    )
    parser_seq.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to the FASTA file the results will be saved in, e.g. path/to/directory/results.fa.\n"
            "Default: Standard out."
        ),
    )
    parser_seq.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )
    parser_seq.add_argument(
        "-id",
        "--ens_ids",
        type=str,
        nargs="+",
        required=False,
        dest="id_deprecated",
        help="DEPRECATED - use positional argument instead. One or more Ensembl, WormBase or FlyBase IDs.",
    )
    parser_seq.add_argument(
        "--seqtype",
        default=None,
        type=str,
        required=False,
        help="DEPRECATED - use True/False flag 'translate' instead.",
    )
    parser_seq.add_argument(
        "--transcribe",
        default=None,
        action="store_true",
        required=False,
        help="DEPRECATED - use True/False flag 'translate' instead.",
    )

    ## gget muscle subparser
    muscle_desc = "Align multiple nucleotide or amino acid sequences against each other (using the Muscle v5 algorithm)."
    parser_muscle = parent_subparsers.add_parser(
        "muscle",
        parents=[parent],
        description=muscle_desc,
        help=muscle_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # muscle parser arguments
    parser_muscle.add_argument(
        "fasta",
        type=str,
        nargs="+",
        help="List of sequences or path to fasta file containing the sequences to be aligned.",
    )
    parser_muscle.add_argument(
        "-s5",
        "--super5",
        default=False,
        action="store_true",
        required=False,
        help="If True, align input using Super5 algorithm instead of PPP algorithm to decrease time and memory. Use for large inputs (a few hundred sequences).",
    )
    parser_muscle.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        default=None,
        help=(
            "Path to save an 'aligned FASTA' (.afa) file with the results, e.g. path/to/directory/results.afa."
            "Default: 'None' -> Standard out in Clustal format."
        ),
    )
    parser_muscle.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )
    parser_muscle.add_argument(
        "-fa",
        "--fasta",
        type=str,
        required=False,
        dest="fasta_deprecated",
        help="DEPRECATED - use positional argument instead. Path to fasta file containing the sequences to be aligned.",
    )

    ## gget blast subparser
    blast_desc = "BLAST a nucleotide or amino acid sequence against any BLAST database."
    parser_blast = parent_subparsers.add_parser(
        "blast",
        parents=[parent],
        description=blast_desc,
        help=blast_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # blast parser arguments
    parser_blast.add_argument(
        "sequence",
        type=str,
        help="Sequence (str) or path to fasta file.",
    )
    parser_blast.add_argument(
        "-p",
        "--program",
        choices=["blastn", "blastp", "blastx", "tblastn", "tblastx"],
        default="default",
        type=str,
        required=False,
        help=(
            "'blastn', 'blastp', 'blastx', 'tblastn', or 'tblastx'. "
            "Default: 'blastn' for nucleotide sequences; 'blastp' for amino acid sequences."
        ),
    )
    parser_blast.add_argument(
        "-db",
        "--database",
        choices=[
            "nt",
            "nr",
            "refseq_rna",
            "refseq_protein",
            "swissprot",
            "pdbaa",
            "pdbnt",
        ],
        default="default",
        type=str,
        required=False,
        help=(
            "'nt', 'nr', 'refseq_rna', 'refseq_protein', 'swissprot', 'pdbaa', or 'pdbnt'. "
            "Default: 'nt' for nucleotide sequences; 'nr' for amino acid sequences. "
            "More info on BLAST databases: https://ncbi.github.io/blast-cloud/blastdb/available-blastdbs.html"
        ),
    )
    parser_blast.add_argument(
        "-l",
        "--limit",
        type=int,
        default=50,
        required=False,
        help="int or None. Limits number of hits to return. Default 50.",
    )
    parser_blast.add_argument(
        "-e",
        "--expect",
        type=float,
        default=10.0,
        required=False,
        help="float or None. An expect value cutoff. Default 10.0.",
    )
    parser_blast.add_argument(
        "-lcf",
        "--low_comp_filt",
        default=False,
        action="store_true",
        required=False,
        help="Turn on low complexity filter. Default off.",
    )
    parser_blast.add_argument(
        "-mbo",
        "--megablast_off",
        default=True,
        action="store_false",
        required=False,
        help="Turn off MegaBLAST algorithm. Default on (blastn only).",
    )
    parser_blast.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Do not print progress information.",
    )
    parser_blast.add_argument(
        "-csv",
        "--csv",
        default=True,
        action="store_false",
        required=False,
        help="Returns results in csv format instead of json.",
    )
    parser_blast.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to the file the results will be saved in, e.g. path/to/directory/results.json.\n"
            "Default: Standard out."
        ),
    )
    parser_blast.add_argument(
        "-seq",
        "--sequence",
        type=str,
        required=False,
        dest="seq_deprecated",
        help="DEPRECATED - use positional argument instead. Sequence (str) or path to fasta file.",
    )
    parser_blast.add_argument(
        "-j",
        "--json",
        default=False,
        action="store_true",
        required=False,
        help="DEPRECATED - json is now the default output format (convert to csv using flag [--csv]).",
    )

    ## gget blat subparser
    blat_desc = (
        "BLAT a nucleotide or amino acid sequence against any BLAT UCSC assembly."
    )
    parser_blat = parent_subparsers.add_parser(
        "blat",
        parents=[parent],
        description=blat_desc,
        help=blat_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # blat parser arguments
    parser_blat.add_argument(
        "sequence",
        type=str,
        help="Sequence (str) or path to fasta file.",
    )
    parser_blat.add_argument(
        "-st",
        "--seqtype",
        choices=["DNA", "protein", "translated%20RNA", "translated%20DNA"],
        default="default",
        type=str,
        required=False,
        help=(
            "'DNA', 'protein', 'translated%%20RNA', or 'translated%%20DNA'. "
            "Default: 'DNA' for nucleotide sequences; 'protein' for amino acid sequences."
        ),
    )
    parser_blat.add_argument(
        "-a",
        "--assembly",
        default="human",
        type=str,
        required=False,
        help=(
            "'human' (assembly hg38) (default), 'mouse' (assembly mm39), "
            "or any of the species assemblies available at https://genome.ucsc.edu/cgi-bin/hgBlat "
            "(use short assembly name as listed after the '/'). "
        ),
    )
    parser_blat.add_argument(
        "-csv",
        "--csv",
        default=True,
        action="store_false",
        required=False,
        help="Returns results in csv format instead of json.",
    )
    parser_blat.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to the csv file the results will be saved in, e.g. path/to/directory/results.csv."
            "Default: Standard out."
        ),
    )
    parser_blat.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )
    parser_blat.add_argument(
        "-seq",
        "--sequence",
        type=str,
        required=False,
        dest="seq_deprecated",
        help="DEPRECATED - use positional argument instead. Sequence (str) or path to fasta file.",
    )
    parser_blat.add_argument(
        "-j",
        "--json",
        default=False,
        action="store_true",
        required=False,
        help="DEPRECATED - json is now the default output format (convert to csv using flag [--csv]).",
    )

    ## gget enrichr subparser
    enrichr_desc = "Perform an enrichment analysis on a list of genes using Enrichr."
    parser_enrichr = parent_subparsers.add_parser(
        "enrichr",
        parents=[parent],
        description=enrichr_desc,
        help=enrichr_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # enrichr parser arguments
    parser_enrichr.add_argument(
        "genes",
        type=str,
        nargs="+",
        help="List of gene symbols or Ensembl gene IDs to perform enrichment analysis on.",
    )
    parser_enrichr.add_argument(
        "-db",
        "--database",
        type=str,
        required=True,
        help=(
            "'pathway', 'transcription', 'ontology', 'diseases_drugs', 'celltypes', 'kinase_interactions'"
            "or any database listed at: https://maayanlab.cloud/Enrichr/#libraries"
            " or the species-specific libraries listed in the documentation"
        ),
    )
    parser_enrichr.add_argument(
        "-s",
        "--species",
        type=str,
        choices=["human", "mouse", "fly", "yeast", "worm", "fish"],
        default="human",
        required=False,
        help="Enrichr variant to query. Default: 'human'.",
    )
    parser_enrichr.add_argument(
        "-bkg_l",
        "--background_list",
        type=str,
        nargs="*",
        default=None,
        required=False,
        help="List of gene names/Ensembl IDs to be used as background genes. ONLY SUPPORTED FOR HUMAN/MOUSE SPECIES",
    )
    parser_enrichr.add_argument(
        "-bkg",
        "--background",
        default=False,
        action="store_true",
        required=False,
        help="If True, use set of >20,000 default background genes listed here: https://github.com/pachterlab/gget/blob/main/gget/constants/enrichr_bkg_genes.txt. ONLY SUPPORTED FOR HUMAN/MOUSE SPECIES",
    )
    parser_enrichr.add_argument(
        "-e",
        "--ensembl",
        default=False,
        action="store_true",
        required=False,
        help="Add this flag if genes are given as Ensembl gene IDs.",
    )
    parser_enrichr.add_argument(
        "-e_b",
        "--ensembl_bkg",
        default=False,
        action="store_true",
        required=False,
        help="Add this flag if background genes are given as Ensembl gene IDs.",
    )
    parser_enrichr.add_argument(
        "-ko",
        "--kegg_out",
        type=str,
        default=None,
        required=False,
        help="Path to file to save the highlighted KEGG pathway image, e.g. path/to/folder/kegg_pathway.png.",
    )
    parser_enrichr.add_argument(
        "-kr",
        "--kegg_rank",
        type=int,
        default=1,
        required=False,
        help="Candidate pathway rank to be plotted in KEGG pathway image.",
    )
    parser_enrichr.add_argument(
        "-csv",
        "--csv",
        default=True,
        action="store_false",
        required=False,
        help="Returns results in csv format instead of json.",
    )
    parser_enrichr.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to the csv file the results will be saved in, e.g. path/to/directory/results.csv."
            "Default: Standard out."
        ),
    )
    parser_enrichr.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )
    parser_enrichr.add_argument(
        "-g",
        "--genes",
        type=str,
        nargs="+",
        required=False,
        dest="genes_deprecated",
        help="DEPRECATED - use positional argument instead. List of gene symbols or Ensembl gene IDs to perform enrichment analysis on.",
    )

    parser_enrichr.add_argument(
        "-j",
        "--json",
        default=False,
        action="store_true",
        required=False,
        help="DEPRECATED - json is now the default output format (convert to csv using flag [--csv]).",
    )

    ## gget archs4 subparser
    archs4_desc = "Find the most correlated genes or the tissue expression atlas of a gene using data from the human and mouse RNA-seq database ARCHS4 (https://maayanlab.cloud/archs4/)."
    parser_archs4 = parent_subparsers.add_parser(
        "archs4",
        parents=[parent],
        description=archs4_desc,
        help=archs4_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # archs4 parser arguments
    parser_archs4.add_argument(
        "gene",
        type=str,
        help="Gene symbol or Ensembl gene ID of gene of interest, e.g. 'STAT4'.",
    )
    parser_archs4.add_argument(
        "-e",
        "--ensembl",
        default=False,
        action="store_true",
        required=False,
        help="Add this flag if gene is given as an Ensembl gene ID.",
    )
    parser_archs4.add_argument(
        "-w",
        "--which",
        choices=[
            "correlation",
            "tissue",
        ],
        default="correlation",
        type=str,
        required=False,
        help=(
            "'correlation' (default) or 'tissue'.\n"
            "- 'correlation' returns a gene correlation table that contains the 100 most correlated genes to the gene of interest. The Pearson correlation is calculated over all samples and tissues in ARCHS4.\n"
            "- 'tissue' returns a tissue expression atlas calculated from human or mouse samples (as defined by 'species') in ARCHS4."
        ),
    )
    parser_archs4.add_argument(
        "-gc",
        "--gene_count",
        default=100,
        type=int,
        required=False,
        help=(
            "Number of correlated genes to return (default: 100).\n"
            "(Only for gene correlation.)"
        ),
    )
    parser_archs4.add_argument(
        "-s",
        "--species",
        choices=[
            "human",
            "mouse",
        ],
        default="human",
        type=str,
        required=False,
        help="'human' (default) or 'mouse'. (Only for tissue expression atlas.)",
    )
    parser_archs4.add_argument(
        "-csv",
        "--csv",
        default=True,
        action="store_false",
        required=False,
        help="Returns results in csv format instead of json.",
    )
    parser_archs4.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to the csv file the results will be saved in, e.g. path/to/directory/results.csv.\n"
            "Default: Standard out."
        ),
    )
    parser_archs4.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )
    parser_archs4.add_argument(
        "-g",
        "--gene",
        type=str,
        required=False,
        dest="gene_deprecated",
        help="DEPRECATED - use positional argument instead. Gene symbol or Ensembl gene ID of gene of interest (str), e.g. 'STAT4'.",
    )
    parser_archs4.add_argument(
        "-j",
        "--json",
        default=False,
        action="store_true",
        required=False,
        help="DEPRECATED - json is now the default output format (convert to csv using flag [--csv]).",
    )

    ## gget setup subparser
    setup_desc = "Install third-party dependencies for a specified gget module."
    parser_setup = parent_subparsers.add_parser(
        "setup",
        parents=[parent],
        description=setup_desc,
        help=setup_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # setup parser arguments
    parser_setup.add_argument(
        "module",
        type=str,
        choices=["alphafold", "gpt", "cellxgene", "elm", "cbio"],
        help=(
            "gget module for which dependencies should be installed, e.g. 'alphafold'. "
            "Currently supported modules: 'alphafold', 'gpt', 'cellxgene', 'elm', 'cbio'."
        ),
    )

    parser_setup.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )

    parser_setup.add_argument(
        "-o",
        "--out",
        type=str,
        default=None,
        required=False,
        help="Path to folder where downloaded files are saved (currently only applies when module='elm'). Default: Files are saved inside the gget installation folder.",
    )

    ## gget alphafold subparser
    alphafold_desc = "Predicts the structure of a protein using a simplified version of AlphaFold v2.3.0 (https://doi.org/10.1038/s41586-021-03819-2)."
    parser_alphafold = parent_subparsers.add_parser(
        "alphafold",
        parents=[parent],
        description=alphafold_desc,
        help=alphafold_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # alphafold parser arguments
    parser_alphafold.add_argument(
        "sequence",
        type=str,
        nargs="+",
        help="Sequence (str), list of sequences, or path to fasta file.",
    )
    parser_alphafold.add_argument(
        "-mfm",
        "--multimer_for_monomer",
        default=False,
        action="store_true",
        required=False,
        help="Use multimer model for a monomer.",
    )
    parser_alphafold.add_argument(
        "-mr",
        "--multimer_recycles",
        default=3,
        type=int,
        required=False,
        help=(
            "The multimer model will continue recycling until the predictions stop changing, up to the limit set here.\n"
            "For higher accuracy, at the potential cost of longer inference times, set this to 20."
        ),
    )
    parser_alphafold.add_argument(
        "-r",
        "--relax",
        default=False,
        action="store_true",
        required=False,
        help="AMBER relax the best model.",
    )
    parser_alphafold.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to folder the predicted aligned error (json) and the prediction (PDB) will be saved in.\n"
            "Default: ./[date_time]_gget_alphafold_prediction"
        ),
    )
    parser_alphafold.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )

    ## gget pdb subparser
    pdb_desc = "Query RCSB PDB for the protein structutre/metadata of a given PDB ID."
    parser_pdb = parent_subparsers.add_parser(
        "pdb",
        parents=[parent],
        description=pdb_desc,
        help=pdb_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # alphafold parser arguments
    parser_pdb.add_argument(
        "pdb_id",
        type=str,
        help="PDB ID to be queried, e.g. '7S7U'.",
    )
    parser_pdb.add_argument(
        "-r",
        "--resource",
        default="pdb",
        type=str,
        choices=[
            "pdb",
            "entry",
            "pubmed",
            "assembly",
            "branched_entity",
            "nonpolymer_entity",
            "polymer_entity",
            "uniprot",
            "branched_entity_instance",
            "polymer_entity_instance",
            "nonpolymer_entity_instance",
        ],
        required=False,
        help=(
            "Defines type of information to be returned.\n\n"
            '"pdb": Returns the protein structure in PDB format.\n'
            '"entry": Information about PDB structures at the top level of PDB structure hierarchical data organization.\n'
            '"pubmed": Get PubMed annotations (data integrated from PubMed) for a given entry\'s primary citation.\n'
            '"assembly": Information about PDB structures at the quaternary structure level.\n'
            '"branched_entity": Get branched entity description (define entity ID as "identifier").\n'
            '"nonpolymer_entity": Get non-polymer entity data (define entity ID as "identifier").\n'
            '"polymer_entity": Get polymer entity data (define entity ID as "identifier").\n'
            '"uniprot": Get UniProt annotations for a given macromolecular entity (define entity ID as "identifier").\n'
            '"branched_entity_instance": Get branched entity instance description (define chain ID as "identifier").\n'
            '"polymer_entity_instance": Get polymer entity instance (a.k.a chain) data (define chain ID as "identifier").\n'
            '"nonpolymer_entity_instance": Get non-polymer entity instance description (define chain ID as "identifier").'
        ),
    )
    parser_pdb.add_argument(
        "-i",
        "--identifier",
        default=None,
        type=str,
        required=False,
        help=(
            "Can be used to define assembly, entity or chain ID if applicable (default: None).\n"
            "Assembly/entity IDs are numbers (e.g. 1), and chain IDs are letters (e.g. A)."
        ),
    )
    parser_pdb.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to the file the results will be saved in, e.g. path/to/directory/7S7U.pdb or path/to/directory/7S7U_entry.json.\n"
            "Resource 'pdb' is returned in PDB format. All other resources are returned in JSON format.\n"
            "Default: Standard out."
        ),
    )

    # gpt parser arguments
    gpt_desc = "Generates natural language text based on a given prompt using the OpenAI API's 'openai.ChatCompletion.create' endpoint."
    parser_gpt = parent_subparsers.add_parser(
        "gpt",
        parents=[parent],
        description=gpt_desc,
        help=gpt_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    parser_gpt.add_argument(
        "prompt",
        type=str,
        help="The input prompt to generate text from.",
    )
    parser_gpt.add_argument(
        "api_key",
        type=str,
        help="Your OpenAI API key (see: https://platform.openai.com/account/api-keys)",
    )
    parser_gpt.add_argument(
        "-m",
        "--model",
        type=str,
        default="gpt-3.5-turbo",
        required=False,
        help="The name of the GPT model to use (defaults to 'gpt-3.5-turbo') (see: https://platform.openai.com/docs/models/gpt-4)",
    )
    parser_gpt.add_argument(
        "-temp",
        "--temperature",
        type=float,
        default=1,
        required=False,
        help="Value between 0 and 2.0 that controls the level of randomness and creativity in the generated text.",
    )
    parser_gpt.add_argument(
        "-tp",
        "--top_p",
        type=float,
        default=1,
        required=False,
        help="Controls the diversity of the generated text as an alternative to sampling with temperature.",
    )
    parser_gpt.add_argument(
        "-s",
        "--stop",
        type=str,
        default=None,
        required=False,
        help="A sequence of tokens to mark the end of the generated text.",
    )
    parser_gpt.add_argument(
        "-mt",
        "--max_tokens",
        type=int,
        default=200,
        required=False,
        help="Controls the maximum length of the generated text, in tokens.",
    )
    parser_gpt.add_argument(
        "-pp",
        "--presence_penalty",
        type=float,
        default=0,
        required=False,
        help="Number between -2.0 and 2.0. Higher values result increase the model's likelihood to talk about new topics.",
    )
    parser_gpt.add_argument(
        "-fp",
        "--frequency_penalty",
        type=float,
        default=0,
        required=False,
        help="Number between -2.0 and 2.0. Higher values decrease the model's likelihood to repeat the same line verbatim.",
    )
    parser_gpt.add_argument(
        "-lb",
        "--logit_bias",
        type=dict,
        default=None,
        required=False,
        help="A dictionary that specifies a bias towards certain tokens in the generated text.",
    )
    parser_gpt.add_argument(
        "-o",
        "--out",
        type=str,
        default=None,
        required=False,
        help="The file name to save the generated text to (defaults to printing the output to the console)",
    )
    parser_gpt.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Do not print progress information.",
    )

    # cellxgene parser arguments
    cellxgene_desc = (
        "Query data from CZ CELLxGENE Discover (https://cellxgene.cziscience.com/)."
    )
    parser_cellxgene = parent_subparsers.add_parser(
        "cellxgene",
        parents=[parent],
        description=cellxgene_desc,
        help=cellxgene_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    parser_cellxgene.add_argument(
        "-o",
        "--out",
        type=str,
        required=True,
        help="Path to save the generated AnnData .h5ad file (or .csv with --meta_only).",
    )
    parser_cellxgene.add_argument(
        "-cv",
        "--census_version",
        default="stable",
        type=str,
        required=False,
        help="Census version, e.g. '2023-05-15' or 'latest' or 'stable'.",
    )
    parser_cellxgene.add_argument(
        "-s",
        "--species",
        default="homo_sapiens",
        type=str,
        choices=["homo_sapiens", "mus_musculus"],
        required=False,
        help="Choice of 'homo_sapiens' or 'mus_musculus'.",
    )
    parser_cellxgene.add_argument(
        "-g",
        "--gene",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help=(
            "Str or space-separated list of gene name(s) or Ensembl ID(s), e.g. ACE2 SLC5A1 or ENSG00000130234 ENSG00000100170\n"
            "NOTE: Set ensembl=True when providing Ensembl ID(s) instead of gene name(s).\n"
            "NOTE: Gene symbols are case sensitive! Use canonical casing, e.g., 'PAX7' (human), 'Pax7' (mouse)."
        ),
    )
    parser_cellxgene.add_argument(
        "-e",
        "--ensembl",
        default=False,
        action="store_true",
        required=False,
        help="Use this flag when genes are provided as Ensembl IDs.",
    )
    parser_cellxgene.add_argument(
        "-cn",
        "--column_names",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help=(
            "List of metadata columns to return (stored in .obs).\n"
            "For more options see: https://api.cellxgene.cziscience.com/curation/ui/#/ -> Schemas -> dataset.\n"
            "Default: ['dataset_id', 'assay', 'suspension_type', 'sex', 'tissue_general', 'tissue', 'cell_type', 'disease']"
        ),
    )
    parser_cellxgene.add_argument(
        "-mo",
        "--meta_only",
        default=True,
        action="store_false",
        required=False,
        help="Only returns metadata dataframe (corresponds to AnnData.obs).",
    )
    parser_cellxgene.add_argument(
        "--tissue",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of tissue(s), e.g. lung blood",
    )
    parser_cellxgene.add_argument(
        "--cell_type",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of cell_type(s), e.g. 'mucus secreting cell' 'neuroendocrine cell'",
    )
    parser_cellxgene.add_argument(
        "--development_stage",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of development_stage(s).",
    )
    parser_cellxgene.add_argument(
        "--disease",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of disease(s).",
    )
    parser_cellxgene.add_argument(
        "--sex",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of sex(es).",
    )
    parser_cellxgene.add_argument(
        "-is",
        "--include_secondary",
        default=True,
        action="store_false",
        required=False,
        help="Do not restrict results to the canonical instance of the cellular observation.",
    )
    parser_cellxgene.add_argument(
        "--dataset_id",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of CELLxGENE dataset ID(s).",
    )
    parser_cellxgene.add_argument(
        "--tissue_general_ontology_term_id",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help=(
            "Str or space-separated list of high-level tissue UBERON ID(s)."
            "Also see: https://github.com/chanzuckerberg/single-cell-data-portal/blob/9b94ccb0a2e0a8f6182b213aa4852c491f6f6aff/backend/wmg/data/tissue_mapper.py"
        ),
    )
    parser_cellxgene.add_argument(
        "--tissue_general",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help=(
            "Str or space-separated list of high-level tissue label(s)."
            "Also see: https://github.com/chanzuckerberg/single-cell-data-portal/blob/9b94ccb0a2e0a8f6182b213aa4852c491f6f6aff/backend/wmg/data/tissue_mapper.py"
        ),
    )
    parser_cellxgene.add_argument(
        "--tissue_ontology_term_id",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of tissue ontology term ID(s).",
    )
    parser_cellxgene.add_argument(
        "--assay_ontology_term_id",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of assay ontology term ID(s).",
    )
    parser_cellxgene.add_argument(
        "--assay",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of assay(s).",
    )
    parser_cellxgene.add_argument(
        "--cell_type_ontology_term_id",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of celltype ontology term ID(s).",
    )
    parser_cellxgene.add_argument(
        "--development_stage_ontology_term_id",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of development stage ontology term ID(s).",
    )
    parser_cellxgene.add_argument(
        "--disease_ontology_term_id",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of disease ontology term ID(s).",
    )
    parser_cellxgene.add_argument(
        "--donor_id",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of donor ID(s).",
    )
    parser_cellxgene.add_argument(
        "--self_reported_ethnicity_ontology_term_id",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of self reported ethnicity ontology ID(s).",
    )
    parser_cellxgene.add_argument(
        "--self_reported_ethnicity",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of self reported ethnicity.",
    )
    parser_cellxgene.add_argument(
        "--sex_ontology_term_id",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of sex ontology ID(s).",
    )
    parser_cellxgene.add_argument(
        "--suspension_type",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Str or space-separated list of suspension type(s).",
    )
    parser_cellxgene.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Do not print progress information.",
    )

    # cosmic parser arguments
    cosmic_desc = "Query information about genes, mutations, etc. associated with cancers from the COSMIC database."
    parser_cosmic = parent_subparsers.add_parser(
        "cosmic",
        parents=[parent],
        description=cosmic_desc,
        help=cosmic_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    parser_cosmic.add_argument(
        "searchterm",
        type=str,
        nargs="?",
        default=None,
        help=(
            "Search term, which can be a mutation, gene name (or Ensembl ID), sample, etc."
            "Examples: EGFR, ENST00000275493, c.650A>T, p.Q217L, COSV51765119, BT2012100223LNCTB (sample ID)"
        ),
    )
    parser_cosmic.add_argument(
        "-ctp",
        "--cosmic_tsv_path",
        default=None,
        type=str,
        required=False,
        help=(
            "Path to the COSMIC mutation tsv file, e.g. 'path/to/CancerMutationCensus_AllData_v101_GRCh37.tsv'.\n"
            "This file is downloaded when downloading COSMIC databases using the arguments described above.\n"
            "NOTE: This is a required argument when download_cosmic=False."
        ),
    )
    parser_cosmic.add_argument(
        "-l",
        "--limit",
        default=100,
        type=int,
        required=False,
        help="Number of hits to return.",
    )
    parser_cosmic.add_argument(
        "-csv",
        "--csv",
        default=True,
        action="store_false",
        required=False,
        help="Returns results in csv format instead of json.",
    )
    parser_cosmic.add_argument(
        "-d",
        "--download_cosmic",
        default=False,
        action="store_true",
        required=False,
        help="Switch into database download mode.",
    )
    parser_cosmic.add_argument(
        "-cp",
        "--cosmic_project",
        choices=[
            "cancer",
            "cancer_example",
            "census",
            "cell_line",
            "resistance",
            "genome_screen",
            "targeted_screen",
        ],
        default=None,
        type=str,
        required=False,
        help=(
            "Type of COSMIC database (only for use with --download_cosmic). Default: 'cancer'. One of the following:\n"
            "| cosmic_project  | Description                                                           | Notes                                                                              | Size   |\n"
            "|-----------------|-----------------------------------------------------------------------|------------------------------------------------------------------------------------|--------|\n"
            "| cancer          | Cancer Mutation Census (CMC) (most commonly used COSMIC mutation set) | Only available for GRCh37. Most feature-rich schema (takes the longest to search). | 2 GB   |\n"
            "| cancer_example  | Example CMC subset provided for testing and demonstration             | Downloadable without a COSMIC account. Minimal dataset.                            | 2.5 MB |\n"
            "| census          | COSMIC census of curated somatic mutations in known cancer genes      | Smaller curated set of known cancer drivers.                                       | 630 MB |\n"
            "| resistance      | Mutations associated with drug resistance                             | Helpful for pharmacogenomics research.                                             | 1.6 MB |\n"
            "| cell_line       | Cell Lines Project mutation data                                      | Sample metadata often available.                                                   | 2.7 GB |\n"
            "| genome_screen   | Mutations from genome screening efforts                               | Includes less curated data, good for large-scale screens.                          |  |\n"
            "| targeted_screen | Mutations from targeted screening panels                              | Focused panel datasets, good for clinical settings.                                |  |"
        ),
    )
    parser_cosmic.add_argument(
        "-cv",
        "--cosmic_version",
        default=None,
        type=int,
        required=False,
        help="Version of the COSMIC database (only for use with --download_cosmic). Default: None -> Defaults to latest version.",
    )
    parser_cosmic.add_argument(
        "-gv",
        "--grch_version",
        default=37,
        type=int,
        choices=[37, 38],
        required=False,
        help="Version of the human GRCh reference genome (only for use with --download_cosmic).",
    )
    parser_cosmic.add_argument(
        "--email",
        type=str,
        required=False,
        help="Email for COSMIC login. Helpful for avoiding required input upon running gget COSMIC. Default: None",
    )
    parser_cosmic.add_argument(
        "--password",
        type=str,
        required=False,
        help="Password for COSMIC login. Helpful for avoiding required input upon running gget COSMIC, but password will be stored in plain text in the script. Default: None",
    )
    parser_cosmic.add_argument(
        "-gm",
        "--gget_mutate",
        default=False,
        action="store_true",
        required=False,
        help="Create a modified version of the database for use with gget mutate (only for use with --download_cosmic).",
    )
    parser_cosmic.add_argument(
        "--keep_genome_info",
        default=False,
        action="store_true",
        required=False,
        help="Whether to keep genome information (e.g. location of mutation in the genome) in the modified database for use with gget mutate (only for use with --download_cosmic).",
    )
    parser_cosmic.add_argument(
        "--remove_duplicates",
        default=False,
        action="store_true",
        required=False,
        help="Whether to remove duplicated rows from the modified database for use with gget mutate (only for use with --download_cosmic).",
    )
    parser_cosmic.add_argument(
        "--seq_id_column",
        default="seq_ID",
        type=str,
        required=False,
        help="Whether to remove duplicated rows from the modified database for use with gget mutate (only for use with --download_cosmic).",
    )
    parser_cosmic.add_argument(
        "--mutation_column",
        default="mutation",
        type=str,
        required=False,
        help="Whether to remove duplicated rows from the modified database for use with gget mutate (only for use with --download_cosmic).",
    )
    parser_cosmic.add_argument(
        "--mut_id_column",
        default="mutation_id",
        type=str,
        required=False,
        help="Whether to remove duplicated rows from the modified database for use with gget mutate (only for use with --download_cosmic).",
    )
    parser_cosmic.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        default=None,
        help=(
            "Path to the file (or folder when downloading databases with the download_cosmic flag) the results will be saved in, e.g. path/to/results.json.\n"
            "Defaults: \n"
            "-> When download_cosmic=False: Results will be returned to standard out\n"
            "-> When download_cosmic=True: Database will be downloaded into current working directory"
        ),
    )
    parser_cosmic.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Do not print progress information.",
    )

    # mutate parser arguments
    mutate_desc = "Mutate nucleotide sequences based on provided mutations."
    parser_mutate = parent_subparsers.add_parser(
        "mutate",
        parents=[parent],
        description=mutate_desc,
        help=mutate_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    parser_mutate.add_argument(
        "sequences",
        type=str,
        nargs="+",
        help=(
            "(str) Path to the fasta file containing the sequences to be mutated, e.g., 'seqs.fa'.\n"
            "Sequence identifiers following the '>' character must correspond to the identifiers\n"
            "in the seq_ID column of 'mutations'.\n"
            "NOTE: Only string until first space or dot will be used as sequence identifier\n"
            "- Version numbers of Ensembl IDs will be ignored.\n\n"
            "Example:\n"
            ">seq1 (or ENSG00000106443)\n"
            "ACTGCGATAGACT\n"
            ">seq2\n"
            "AGATCGCTAG\n\n"
            "Alternatively: Input sequence(s) as a string or list, e.g. 'AGCTAGCT' or 'ACTGCTAGCT' 'AGCTAGCT'."
        ),
    )
    parser_mutate.add_argument(
        "-m",
        "--mutations",
        type=str,
        nargs="+",
        required=True,
        help=(
            "Path to csv or tsv file (e.g., 'mutations.csv') containing information about the mutations in the following format:\n\n"
            "| mutation             | mut_ID | seq_ID |\n"
            "| c.1252C>T            | mut1   | seq1   | -> Apply mutation 1 to sequence 1\n"
            "| c.2239_2253inv       | mut2   | seq2   | -> Apply mutation 2 to sequence 2\n"
            "| c.2239_2253inv       | mut2   | seq3   | -> Apply mutation 2 to sequence 3\n"
            "| c.2239_2253delinsAAT | mut3   | seq3   | -> Apply mutation 3 to sequence 3\n"
            "| ...                  | ...    | ...    |\n\n"
            "'mutation' = Column containing the mutations to be performed written in standard mutation annotation (see below)\n"
            "'mut_ID' = Column containing an identifier for each mutation (optional)\n"
            "'seq_ID' = Column containing the identifiers of the sequences to be mutated\n"
            "(sequence IDs must correspond to the string following the > character in the input fasta; do NOT include spaces or dots)\n\n"
            "Alternatively: Input mutation(s) as a string or list, e.g. 'c.2C>T' or 'c.2C>T' 'c.1A>C'\n\n"
            "NOTE: Enclose individual mutation annotations in quotation marks to prevent terminal parsing errors.\n"
            "If a list is passed, the number of mutations must equal the number of input sequences."
        ),
    )
    parser_mutate.add_argument(
        "-mc",
        "--mut_column",
        default="mutation",
        type=str,
        required=False,
        help="Name of the column containing the mutations to be performed in 'mutations'.",
    )
    parser_mutate.add_argument(
        "-sic",
        "--seq_id_column",
        default="seq_ID",
        type=str,
        required=False,
        help="Name of the column containing the IDs of the sequences to be mutated in 'mutations'.",
    )
    parser_mutate.add_argument(
        "-mic",
        "--mut_id_column",
        default=None,
        type=str,
        required=False,
        help="Name of the column containing the IDs of each mutation in 'mutations'. Default: Same as 'mut_column'.",
    )
    parser_mutate.add_argument(
        "-k",
        "--k",
        default=None,
        type=int,
        required=False,
        help="Length of sequences flanking the mutation. If k is None or k > total length of the sequence, the entire sequence will be kept. Default: None",
    )
    parser_mutate.add_argument(
        "-o",
        "--out",
        default=None,
        type=str,
        required=False,
        help=(
            "Path to output fasta file containing the mutated sequences, e.g., 'path/to/output_fasta.fa'.\n"
            "Default: None -> returns a list of the mutated sequences to standard out.\n"
            "The identifiers (following the '>') of the mutated sequences in the output fasta will be '>[seq_ID]_[mut_ID]'."
        ),
    )
    parser_mutate.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Do not print progress information.",
    )

    ## opentargets parser arguments
    opentargets_desc = (
        "Query the Open Targets Platform with a gene for associated drugs, diseases, tractability stats,"
        " pharmacogenetic responses, expression data, DepMap effects, and protein-protein interaction data."
    )
    parser_opentargets = parent_subparsers.add_parser(
        "opentargets",
        parents=[parent],
        description=opentargets_desc,
        help=opentargets_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    parser_opentargets.add_argument(
        "ens_id",
        type=str,
        help="Ensembl gene ID, e.g. ENSG00000169194.",
    )
    parser_opentargets.add_argument(
        "-r",
        "--resource",
        choices=OPENTARGETS_RESOURCES,
        default="diseases",
        type=str,
        required=False,
        help="Type of information to be returned.",
    )
    parser_opentargets.add_argument(
        "-l",
        "--limit",
        default=None,
        type=int,
        required=False,
        help="Limits the number of results, e.g. 10 (default: None). Note: Not compatible with the 'tractability' and 'depmap' resources",
    )
    parser_opentargets.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to the file the results will be saved in, e.g. path/to/directory/results.json.\n"
            "Default: Standard out."
        ),
    )
    parser_opentargets.add_argument(
        "-f",
        "--filter",
        type=parse_opentargets_filter,
        action="append",
        required=False,
        default=None,
        metavar="COLUMN=VALUE",
        help=(
            "Filter results by exact equality using returned OpenTargets column names.\n"
            "Pass multiple filters by repeating the flag, e.g. '--filter disease.id=EFO_0000274 --filter drug.id=CHEMBL1743081'.\n"
            "Nested fields use dot notation, matching the column names returned by the API."
        ),
    )
    parser_opentargets.add_argument(
        "-csv",
        "--csv",
        default=False,
        action="store_true",
        required=False,
        help="Returns results in csv format instead of json.",
    )
    parser_opentargets.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )
    ## cbio parser arguments
    cbio_desc = "Plot cancer genomics heatmaps using data from cBioPortal using Ensembl IDs or gene names"
    parser_cbio = parent_subparsers.add_parser(
        "cbio",
        parents=[parent],
        description=cbio_desc,
        help=cbio_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    parser_cbio_subparsers = parser_cbio.add_subparsers(
        dest="subcommand", help="Subcommand to execute."
    )
    parser_cbio_search = parser_cbio_subparsers.add_parser(
        "search",
        description="Search for genes in cBioPortal.",
        help="Find cBioPortal study IDs by keyword.",
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    parser_cbio_search.add_argument(
        "keywords",
        type=str,
        nargs="+",
        help="Keywords to search for in cBioPortal.",
    )
    parser_cbio_plot = parser_cbio_subparsers.add_parser(
        "plot",
        description="Plot a heatmap of cancer genomics data.",
        help="Plot a heatmap of cancer genomics data.",
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    parser_cbio_plot.add_argument(
        "-s",
        "--study_ids",
        type=str,
        nargs="+",
        help="Space-separated list of cBioPortal study IDs, e.g. `msk_impact_2017 egc_msk_2023`",
        required=True,
    )
    parser_cbio_plot.add_argument(
        "-g",
        "--genes",
        type=str,
        nargs="+",
        help="Space-separated list of gene names or Ensembl IDs, e.g. `NOTCH3 ENSG00000108375`",
        required=True,
    )
    parser_cbio_plot.add_argument(
        "-st",
        "--stratification",
        type=str,
        choices=["tissue", "cancer_type", "cancer_type_detailed", "study_id", "sample"],
        help="Column to stratify the heatmap by.",
        default="tissue",
        required=False,
    )
    parser_cbio_plot.add_argument(
        "-vt",
        "--variation_type",
        type=str,
        choices=[
            "mutation_occurrences",
            "cna_nonbinary",
            "sv_occurrences",
            "cna_occurrences",
            "Consequence",
        ],
        help="Type of variation to plot",
        default="mutation_occurrences",
        required=False,
    )
    parser_cbio_plot.add_argument(
        "-f",
        "--filter",
        type=str,
        default=None,
        help="Filter the heatmap by a specific value in a specific column, e.g. `tissue:intestine`",
        required=False,
    )
    parser_cbio_plot.add_argument(
        "-dd",
        "--data_dir",
        type=str,
        default="gget_cbio_cache",
        help="Directory to store downloaded data (default: ./gget_cbio_cache)",
        required=False,
    )
    parser_cbio_plot.add_argument(
        "-fd",
        "--figure_dir",
        type=str,
        default="gget_cbio_figures",
        help="Directory to store generated figures (default: ./gget_cbio_figures)",
        required=False,
    )
    parser_cbio_plot.add_argument(
        "-fn",
        "--filename",
        type=str,
        default=None,
        help="Filename for the generated figure, relative to `figure_dir` (default: auto-generated)",
        required=False,
    )
    parser_cbio_plot.add_argument(
        "-t",
        "--title",
        type=str,
        default=None,
        help="Title for the generated figure (default: auto-generated)",
        required=False,
    )
    parser_cbio_plot.add_argument(
        "-dpi",
        "--dpi",
        type=int,
        default=100,
        help="DPI of the generated figures (default: 100)",
        required=False,
    )
    parser_cbio_plot.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )
    parser_cbio_plot.add_argument(
        "-nc",
        "--no_confirm",
        default=False,
        action="store_true",
        required=False,
        help="Skip confirmation before downloading data.",
    )
    parser_cbio_plot.add_argument(
        "-sh",
        "--show",
        default=False,
        action="store_true",
        required=False,
        help="Show the plot in a window",
    )

    ## bgee parser arguments
    bgee_desc = "Query the Bgee database for orthology and gene expression data using Ensembl IDs."
    parser_bgee = parent_subparsers.add_parser(
        "bgee",
        parents=[parent],
        description=bgee_desc,
        help=bgee_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    parser_bgee.add_argument(
        "ens_id",
        type=str,
        nargs="+",
        help="Ensembl gene ID, e.g. ENSG00000169194 or ENSSSCG00000014725. When 'type=expression' you can also input multiple Ensembl IDs.",
    )
    parser_bgee.add_argument(
        "-t",
        "--type",
        type=str,
        choices=["orthologs", "expression"],
        help="Type of information to be returned.",
        default="orthologs",
        required=False,
    )
    parser_bgee.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to the file the results will be saved in, e.g. path/to/directory/results.json.\n"
            "Default: Standard out."
        ),
    )
    parser_bgee.add_argument(
        "-csv",
        "--csv",
        default=False,
        action="store_true",
        required=False,
        help="Returns results in csv format instead of json.",
    )
    parser_bgee.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information.",
    )

    ## gget 8cube subparser
    cube_desc = "Query 8cubeDB (https://eightcubedb.onrender.com/)."
    parser_8cube = parent_subparsers.add_parser(
        "8cube",
        parents=[parent],
        description=cube_desc,
        help=cube_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )

    # Subcommands under "8cube"
    cube_subparsers = parser_8cube.add_subparsers(dest="cube_command")

    spec_desc = "Retrieve ψ and ζ specificity metrics for one or more genes."
    parser_cube_spec = cube_subparsers.add_parser(
        "specificity",
        description=spec_desc,
        help=spec_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )

    parser_cube_spec.add_argument(
        "genes", nargs="+", help="Gene symbols or Ensembl IDs."
    )

    parser_cube_spec.add_argument(
        "-csv",
        "--csv",
        default=True,
        action="store_false",
        help="Return CSV instead of JSON.",
    )

    parser_cube_spec.add_argument("-o", "--out", type=str, help="Output file path.")

    parser_cube_spec.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        help="Does not print progress information.",
    )

    psib_desc = "Retrieve ψ_block (psi-block) specificity scores."
    parser_cube_psib = cube_subparsers.add_parser(
        "psi_block",
        description=psib_desc,
        help=psib_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )

    parser_cube_psib.add_argument(
        "genes", nargs="+", help="Gene symbols or Ensembl IDs."
    )

    parser_cube_psib.add_argument(
        "-al",
        "--analysis_level",
        required=True,
        help="Analysis level, e.g. 'Kidney' or 'Across_tissues'.",
    )

    parser_cube_psib.add_argument(
        "-at",
        "--analysis_type",
        required=True,
        help="Partition type, e.g. 'Sex:Celltype'.",
    )

    parser_cube_psib.add_argument(
        "-csv",
        "--csv",
        default=True,
        action="store_false",
        help="Return CSV instead of JSON.",
    )

    parser_cube_psib.add_argument("-o", "--out", type=str, help="Output file path.")

    parser_cube_psib.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        help="Does not print progress information.",
    )

    expr_desc = "Retrieve mean and variance of normalized expression values for one or more genes."
    parser_cube_expr = cube_subparsers.add_parser(
        "expression",
        description=expr_desc,
        help=expr_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )

    parser_cube_expr.add_argument(
        "genes", nargs="+", help="Gene symbols or Ensembl IDs."
    )

    parser_cube_expr.add_argument(
        "-al", "--analysis_level", required=True, help="Analysis level, e.g. 'Kidney'."
    )

    parser_cube_expr.add_argument(
        "-at",
        "--analysis_type",
        required=True,
        help="Partition type, e.g. 'Sex:Celltype'.",
    )

    parser_cube_expr.add_argument(
        "-csv",
        "--csv",
        default=True,
        action="store_false",
        help="Return CSV instead of JSON.",
    )

    parser_cube_expr.add_argument("-o", "--out", type=str, help="Output file path.")

    parser_cube_expr.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        help="Does not print progress information.",
    )
        
    ## gget virus subparser
    virus_desc = "Download virus genome datasets and associated GenBank metadata from the NCBI Virus database."
    parser_virus = parent_subparsers.add_parser(
        "virus",
        parents=[parent],
        description=virus_desc,
        help=virus_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )
    # virus parser arguments
    parser_virus.add_argument(
        "virus",
        type=str,
        nargs="?",
        default=None,
        help="Virus taxon name/ID to query, e.g. 'SARS-CoV-2', 'zika virus', or taxon ID '1335626'.\n"
             "When using --is_accession flag, can also be:\n"
             "  - Single accession: 'NC_038294.1'\n"
             "  - Space-separated accessions: 'NC_038294.1 NC_045512.2'\n"
             "  - Path to text file: 'accessions.txt' (one accession per line)\n"
             "For SARS-CoV-2 and Alphainfluenza cached downloads, multiple accessions are fully supported.",
    )
    parser_virus.add_argument(
        "-a",
        "--is_accession",
        default=False,
        action="store_true",
        required=False,
        help="Treat the virus argument as an accession number (single, space-separated list, or text file path with one accession per line).\n"
             "Single: 'NC_038294.1' | List: 'NC_038294.1 NC_045512.2' | File: 'accessions.txt'\n"
             "For SARS-CoV-2 and Alphainfluenza cached downloads, multiple accessions are fully supported.",
    )
    parser_virus.add_argument(
        "-o",
        "--out",
        type=str,
        required=False,
        help=(
            "Path to the output folder where results will be saved, e.g. path/to/directory.\n"
            "Default: A directory named 'gget_virus_output' in the current working directory."
        ),
    )
    parser_virus.add_argument(
        "--host",
        type=str,
        required=False,
        help="Host organism name (scientific or common) at any taxonomic rank or NCBI Taxonomy ID filter, e.g. 'human', 'mouse', '1335626'. Place in quotation marks if multiple words.",
    )
    parser_virus.add_argument(
        "--nuc_completeness",
        type=str,
        choices=["complete", "partial"],
        required=False,
        help="Nucleotide completeness filter: 'complete' or 'partial'.",
    )
    parser_virus.add_argument(
        "--source_database",
        type=str,
        required=False,
        help="Source database filter: 'refseq' or 'genbank'.",
    )
    parser_virus.add_argument(
        "--min_seq_length",
        type=int,
        required=False,
        help="Minimum sequence length filter (in base pairs).",
    )
    parser_virus.add_argument(
        "--max_seq_length",
        type=int,
        required=False,
        help="Maximum sequence length filter (in base pairs).",
    )
    parser_virus.add_argument(
        "--geographic_location",
        type=str,
        required=False,
        help="Specific geographic location filter (country or continent), e.g. 'Germany', 'Asia'.",
    )
    parser_virus.add_argument(
        "--submitter_country",
        type=str,
        required=False,
        help="Submitter country filter.",
    )
    parser_virus.add_argument(
        "--submitter_name",
        type=str,
        required=False,
        help="Submitter name filter. Can be a single name (e.g., 'John Doe') or comma-separated list (e.g., 'John Doe,Jane Smith'). Any matching name will keep the sequence.",
    )
    parser_virus.add_argument(
        "--submitter_institution",
        type=str,
        required=False,
        help="Submitter institution filter. Can be a single institution name (e.g., 'CDC') or comma-separated list (e.g., 'CDC,NIH,WHO'). Any matching institution will keep the sequence.",
    )
    parser_virus.add_argument(
        "--annotated",
        type=str_to_bool_or_none,
        nargs='?',
        const=True,
        required=False,
        default=None,
        help="Annotation status filter: 'true' or 'false' or None. True will keep only sequences with annotations, False will keep only sequences without annotations, and None (default) will not filter based on annotation status.",
    )
    # parser_virus.add_argument(
    #     "--refseq_only",
    #     default=False,
    #     action="store_true",
    #     required=False,
    #     help="Only fetch RefSeq genomes. If not set, both RefSeq and GenBank genomes will be fetched.",
    # )
    parser_virus.add_argument(
        "--min_release_date",
        type=str,
        required=False,
        help="Minimum release date filter (YYYY-MM-DD format).",
    )
    parser_virus.add_argument(
        "--max_release_date",
        type=str,
        required=False,
        help="Maximum release date filter (YYYY-MM-DD format).",
    )
    parser_virus.add_argument(
        "--min_collection_date",
        type=str,
        required=False,
        help="Minimum collection date filter (YYYY-MM-DD format).",
    )
    parser_virus.add_argument(
        "--max_collection_date",
        type=str,
        required=False,
        help="Maximum collection date filter (YYYY-MM-DD format).",
    )
    parser_virus.add_argument(
        "--max_ambiguous_chars",
        type=int,
        required=False,
        help="Maximum number of ambiguous nucleotide characters ('N') allowed.",
    )
    parser_virus.add_argument(
        "--min_gene_count",
        type=int,
        required=False,
        help="Minimum number of genes filter.",
    )
    parser_virus.add_argument(
        "--max_gene_count",
        type=int,
        required=False,
        help="Maximum number of genes filter.",
    )
    parser_virus.add_argument(
        "--min_protein_count",
        type=int,
        required=False,
        help="Minimum protein count filter.",
    )
    parser_virus.add_argument(
        "--max_protein_count",
        type=int,
        required=False,
        help="Maximum protein count filter.",
    )
    parser_virus.add_argument(
        "--min_mature_peptide_count",
        type=int,
        required=False,
        help="Minimum mature peptide count filter.",
    )
    parser_virus.add_argument(
        "--max_mature_peptide_count",
        type=int,
        required=False,
        help="Maximum mature peptide count filter.",
    )
    parser_virus.add_argument(
        "--has_proteins",
        type=str,
        required=False,
        help="Filter for sequences containing specific protein(s)/gene(s). Can be a single protein name (e.g., 'spike') or comma-separated list (e.g., 'hemagglutinin,neuraminidase'). Any matching protein will keep the sequence.",
    )
    parser_virus.add_argument(
        "--proteins_complete",
        action="store_true",
        default=False,
        required=False,
        help="Filter for sequences with complete protein annotations (protein_count > 0 or gene_count > 0).",
    )
    parser_virus.add_argument(
        "--segment",
        type=str,
        required=False,
        help="Filter for sequences with specific segment(s). Can be a single segment name (e.g., 'HA') or comma-separated list (e.g., 'HA,NA,PB1'). Any matching segment will keep the sequence.",
    )
    parser_virus.add_argument(
        "--isolate",
        type=str,
        required=False,
        help="Isolate name filter. Can be a single isolate name (e.g., 'Wuhan-hu-1') or comma-separated list (e.g., 'Wuhan-hu-1,LASV_3609'). Any matching isolate will keep the sequence.",
    )
    parser_virus.add_argument(
        "--vaccine_strain",
        default=None,
        type=str_to_bool_or_none,
        nargs='?',
        const=True,
        required=False,
        help="Vaccine strain filter: 'true' or 'false' or None. True will only keep sequences marked as vaccine strains. False filters out vaccine strains. and None (Default) will not filter based on vaccine strain status.",
    )
    parser_virus.add_argument(
        "--lab_passaged",
        type=str_to_bool_or_none,
        nargs='?',
        const=True,
        required=False,
        default=None,
        help="Lab passaging status filter: 'true' or 'false' or None. True will only keep sequences that have been lab passaged. False filters out sequences that have been lab passaged. None (Default) will not filter based on lab passaging status.",
    )
    parser_virus.add_argument(
        "--provirus",
        type=str_to_bool_or_none,
        nargs='?',
        const=True,
        required=False,
        default=None,
        help="Proviral or integrated status filter: 'true' or 'false' or None. True will only keep proviral sequences. False filters out proviral sequences. None (Default) will not filter based on proviral status.",
    )
    parser_virus.add_argument(
        "--isolation_source",
        type=str,
        required=False,
        help="Isolation source filter, or 'Tissue/ Specimen / Source' filter, e.g. 'blood'. Can be a single source name (e.g., 'blood') or comma-separated list (e.g., 'blood,serum,plasma'). Any matching source will keep the sequence.",
    )
    parser_virus.add_argument(
        "--env_source",
        type=str,
        required=False,
        help="Environmental source filter, e.g. 'water' or 'sewage'. Excludes any sequences with named hosts. Do NOT combine with host filter. Can be a single source name (e.g., 'water') or comma-separated list (e.g., 'water,soil,air'). Any matching source will keep the sequence.",
    )
    parser_virus.add_argument(
        "--genotype",
        type=str,
        required=False,
        help="Genotype filter, e.g. 'H5N1'. Can be a single genotype (e.g., 'H5N1') or comma-separated list (e.g., 'H5N1,H3N2'). Any matching genotype will keep the sequence.",
    )
    parser_virus.add_argument(
        "--gen_mol_type",
        type=str,
        required=False,
        help="Genomic molecule type filter. Can be a single type name (e.g., 'dsDNA') or comma-separated list (e.g., 'RNA,dsRNA'). Any matching molecule type will keep the sequence.",
    )
    parser_virus.add_argument(
        "-g",
        "--genbank_metadata",
        default=False,
        action="store_true",
        required=False,
        help="Also fetch detailed GenBank metadata for the sequences that pass all filters. The metadata will be saved in separate CSV and XML files. Automatically turned on if GenBank-level filters are used.",
    )
    parser_virus.add_argument(
        "--genbank_batch_size",
        default=200,
        type=int,
        required=False,
        help="Maximum number of accessions to fetch in each GenBank metadata request. Smaller batches are slower but more reliable for large datasets. Only used when --genbank_metadata is True. Default: 200",
    )
    parser_virus.add_argument(
        "--download_all_accessions",
        default=False,
        action="store_true",
        required=False,
        help="Download ALL virus accessions from NCBI (entire Viruses taxonomy). WARNING: This is a very large dataset that can take an hour or more and require significant disk space. When set, the virus argument is ignored.",
    )

    parser_virus.add_argument(
        "--is_sars_cov2",
        default=False,
        action="store_true",
        required=False,
        help="When using SARS-CoV-2 accessions, use this tag so the code optimizes in using the correct SARS-CoV-2 pathway.",
    )
    parser_virus.add_argument(
        "--lineage",
        type=str,
        required=False,
        help="Only for SARS-CoV-2 pangolineages. Can be a single lineage name (e.g., 'P.1') or comma-separated list (e.g., 'B.1.1.7,P.1'). Any matching lineage will keep the sequence.",
    )
    parser_virus.add_argument(
        "--is_alphainfluenza",
        default=False,
        action="store_true",
        required=False,
        help="When querying Alphainfluenza (Influenza A), use this tag so the code optimizes by using NCBI's cached data packages for faster downloads.",
    )
    parser_virus.add_argument(
        "--_skip_cache",
        default=False,
        action="store_true",
        required=False,
        help=argparse.SUPPRESS,  # Hidden parameter for internal/testing use
    )
    parser_virus.add_argument(
        "-kt",
        "--keep_temp",
        default=False,
        action="store_true",
        required=False,
        help="Save all output files, including intermediate files.",
    )
    parser_virus.add_argument(
        "--baseline",
        type=str,
        required=False,
        default=None,
        dest="baseline_metadata",
        help="Path to a baseline metadata file (CSV/JSONL/JSON/text) containing accessions to skip.\n"
             "Only new accessions (not in baseline) will be downloaded.\n"
             "Useful for incremental updates or resuming after API failures.\n"
             "CSV files must have an 'accession' column. Text files: one accession per line.",
    )
    parser_virus.add_argument(
        "--merge-results",
        default=True,
        action="store_true",
        dest="merge_results",
        required=False,
        help="When using --baseline, merge new results with baseline into a single output file (default behavior).",
    )
    parser_virus.add_argument(
        "--no-merge",
        default=False,
        action="store_true",
        dest="no_merge",
        required=False,
        help="When using --baseline, output new results separately from baseline.\n"
             "Creates {virus}_new.csv (new sequences only) and {virus}_baseline_provided.csv (reference).",
    )
    parser_virus.add_argument(
        "--api_key",
        type=str,
        required=False,
        default=None,
        help="NCBI API key for higher E-utilities rate limits (10 requests/sec vs 3/sec without).\n"
             "Obtain a free key from https://www.ncbi.nlm.nih.gov/account/settings/\n"
             "Can also be set via the NCBI_API_KEY environment variable.\n"
             "If not provided, requests continue at the lower default rate limit.",
    )
    parser_virus.add_argument(
        "-q",
        "--quiet",
        default=True,
        action="store_false",
        required=False,
        help="Does not print progress information. For large datasets, it is recommended to not use this flag, to monitor progress.",
    )

    ### Define return values
    args = parent_parser.parse_args()

    # Help return
    if args.help:
        # Retrieve all subparsers from the parent parser
        subparsers_actions = [
            action
            for action in parent_parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        for subparsers_action in subparsers_actions:
            # Get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print("Subparser '{}'".format(choice))
                print(subparser.format_help())
        sys.exit(0)

    # Version return
    if args.version:
        print(f"gget version: {__version__}")
        sys.exit(0)

    # Show help when no arguments are given
    if len(sys.argv) == 1:
        parent_parser.print_help(sys.stderr)
        sys.exit(0)

    # Show module specific help if only module but no further arguments are given
    command_to_parser = {
        "ref": parser_ref,
        "search": parser_gget,
        "info": parser_info,
        "seq": parser_seq,
        "muscle": parser_muscle,
        "blast": parser_blast,
        "blat": parser_blat,
        "enrichr": parser_enrichr,
        "archs4": parser_archs4,
        "setup": parser_setup,
        "alphafold": parser_alphafold,
        "pdb": parser_pdb,
        "gpt": parser_gpt,
        "cellxgene": parser_cellxgene,
        "elm": parser_elm,
        "diamond": parser_diamond,
        "cosmic": parser_cosmic,
        "mutate": parser_mutate,
        "opentargets": parser_opentargets,
        "cbio": parser_cbio,
        "bgee": parser_bgee,
        "8cube": parser_8cube,
        "virus": parser_virus,
    }

    if len(sys.argv) == 2:
        if sys.argv[1] in command_to_parser:
            command_to_parser[sys.argv[1]].print_help(sys.stderr)
        else:
            parent_parser.print_help(sys.stderr)
        sys.exit(0)

    ## cellxgene return
    if args.command == "cellxgene":
        cellxgene(
            species=args.species,
            gene=args.gene,
            ensembl=args.ensembl,
            column_names=args.column_names,
            meta_only=args.meta_only,
            tissue=args.tissue,
            cell_type=args.cell_type,
            development_stage=args.development_stage,
            disease=args.disease,
            sex=args.sex,
            is_primary_data=args.include_secondary,
            dataset_id=args.dataset_id,
            tissue_general_ontology_term_id=args.tissue_general_ontology_term_id,
            tissue_general=args.tissue_general,
            assay_ontology_term_id=args.assay_ontology_term_id,
            assay=args.assay,
            cell_type_ontology_term_id=args.cell_type_ontology_term_id,
            development_stage_ontology_term_id=args.development_stage_ontology_term_id,
            disease_ontology_term_id=args.disease_ontology_term_id,
            donor_id=args.donor_id,
            self_reported_ethnicity_ontology_term_id=args.self_reported_ethnicity_ontology_term_id,
            self_reported_ethnicity=args.self_reported_ethnicity,
            sex_ontology_term_id=args.sex_ontology_term_id,
            suspension_type=args.suspension_type,
            tissue_ontology_term_id=args.tissue_ontology_term_id,
            census_version=args.census_version,
            verbose=args.quiet,
            out=args.out,
        )

    ## gpt return
    if args.command == "gpt":
        gpt_results = gpt(
            prompt=args.prompt,
            api_key=args.api_key,
            model=args.model,
            temperature=args.temperature,
            top_p=args.top_p,
            stop=args.stop,
            max_tokens=args.max_tokens,
            presence_penalty=args.presence_penalty,
            frequency_penalty=args.frequency_penalty,
            logit_bias=args.logit_bias,
            out=args.out,
            verbose=args.quiet,
        )

        if args.out is None:
            sys.stdout.write(gpt_results)

    ## blat return
    if args.command == "blat":
        # Handle deprecated flags for backwards compatibility
        if args.seq_deprecated and args.sequence:
            logger.warning(
                "The [-seq][--sequence] argument is deprecated, using positional argument [sequence] instead."
            )
        if args.seq_deprecated and not args.sequence:
            args.sequence = args.seq_deprecated
            logger.warning(
                "The [-seq][--sequence] argument is deprecated, please use positional argument [sequence] instead."
            )
        if not args.seq_deprecated and not args.sequence:
            parser_blat.error("the following arguments are required: sequence")

        # Run gget blast function
        blat_results = blat(
            sequence=args.sequence,
            seqtype=args.seqtype,
            assembly=args.assembly,
            json=args.csv,
            verbose=args.quiet,
        )

        # Check if the function returned something
        if not isinstance(blat_results, type(None)):
            # Save blat results if args.out specified
            if args.out and not args.csv:
                # Create saving directory
                directory = "/".join(args.out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)
                # Save to csv
                blat_results.to_csv(args.out, index=False)

            if args.out and args.csv:
                # Create saving directory
                directory = "/".join(args.out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)
                # Save json
                with open(args.out, "w", encoding="utf-8") as f:
                    json.dump(blat_results, f, ensure_ascii=False, indent=4)

            # Print results if no directory specified
            if not args.out and not args.csv:
                blat_results.to_csv(sys.stdout, index=False)
            if not args.out and args.csv:
                print(json.dumps(blat_results, ensure_ascii=False, indent=4))

    ## blast return
    if args.command == "blast":
        # Handle deprecated flags for backwards compatibility
        if args.seq_deprecated and args.sequence:
            logger.warning(
                "The [-seq][--sequence] argument is deprecated, using positional argument [sequence] instead."
            )
        if args.seq_deprecated and not args.sequence:
            args.sequence = args.seq_deprecated
            logger.warning(
                "The [-seq][--sequence] argument is deprecated, please use positional argument [sequence] instead."
            )
        if not args.seq_deprecated and not args.sequence:
            parser_blast.error("the following arguments are required: sequence")

        # Run gget blast function
        blast_results = blast(
            sequence=args.sequence,
            program=args.program,
            database=args.database,
            limit=args.limit,
            expect=args.expect,
            low_comp_filt=args.low_comp_filt,
            megablast=args.megablast_off,
            verbose=args.quiet,
            json=args.csv,
        )

        # Check if the function returned something
        if not isinstance(blast_results, type(None)):
            # Save blast results if args.out specified
            if args.out and not args.csv:
                # Create saving directory
                directory = "/".join(args.out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)
                # Save to csv
                blast_results.to_csv(args.out, index=False)

            if args.out and args.csv:
                # Create saving directory
                directory = "/".join(args.out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)
                # Save json
                with open(args.out, "w", encoding="utf-8") as f:
                    json.dump(blast_results, f, ensure_ascii=False, indent=4)

            # Print results if no directory specified
            if not args.out and not args.csv:
                blast_results.to_csv(sys.stdout, index=False)
            if not args.out and args.csv:
                print(json.dumps(blast_results, ensure_ascii=False, indent=4))

    ## mutate return
    if args.command == "mutate":
        if isinstance(args.sequences, list) and len(args.sequences) == 1:
            seqs = args.sequences[0]
        else:
            seqs = args.sequences

        if isinstance(args.mutations, list) and len(args.mutations) == 1:
            muts = args.mutations[0]
        else:
            muts = args.mutations

        # Run mutate function (automatically saves output)
        mutate_results = mutate(
            sequences=seqs,
            mutations=muts,
            k=args.k,
            mut_column=args.mut_column,
            mut_id_column=args.mut_id_column,
            seq_id_column=args.seq_id_column,
            out=args.out,
            verbose=args.quiet,
        )

        # Print list of mutated sequences if any are returned (this should only happen when out=None)
        if mutate_results:
            for mut_seq in mutate_results:
                print(mut_seq)

    ## cosmic return
    if args.command == "cosmic":
        # Run gget cosmic function
        cosmic_results = cosmic(
            searchterm=args.searchterm,
            cosmic_tsv_path=args.cosmic_tsv_path,
            limit=args.limit,
            json=args.csv,
            download_cosmic=args.download_cosmic,
            cosmic_project=args.cosmic_project,
            cosmic_version=args.cosmic_version,
            grch_version=args.grch_version,
            email=args.email,
            password=args.password,
            gget_mutate=args.gget_mutate,
            keep_genome_info=args.keep_genome_info,
            remove_duplicates=args.remove_duplicates,
            seq_id_column=args.seq_id_column,
            mutation_column=args.mutation_column,
            mut_id_column=args.mut_id_column,
            out=args.out,
            verbose=args.quiet,
        )

        # Check if the function returned something
        if not isinstance(cosmic_results, type(None)):
            # # Save cosmic results if args.out specified
            # if args.out and not args.csv:
            #     # Create saving directory
            #     directory = "/".join(args.out.split("/")[:-1])
            #     if directory != "":
            #         os.makedirs(directory, exist_ok=True)
            #     # Save to csv
            #     cosmic_results.to_csv(args.out, index=False)

            # if args.out and args.csv:
            #     # Create saving directory
            #     directory = "/".join(args.out.split("/")[:-1])
            #     if directory != "":
            #         os.makedirs(directory, exist_ok=True)
            #     # Save json
            #     with open(args.out, "w", encoding="utf-8") as f:
            #         json.dump(cosmic_results, f, ensure_ascii=False, indent=4)

            # Print results if no directory specified
            if not args.out and not args.csv:
                cosmic_results.to_csv(sys.stdout, index=False)
            if not args.out and args.csv:
                print(json.dumps(cosmic_results, ensure_ascii=False, indent=4))

    ## archs4 return
    if args.command == "archs4":
        # Handle deprecated flags for backwards compatibility
        if args.gene_deprecated and args.gene:
            logger.warning(
                "The [-g][--gene] argument is deprecated, using positional argument [gene] instead."
            )
        if args.gene_deprecated and not args.gene:
            args.gene = args.gene_deprecated
            logger.warning(
                "The [-g][--gene] argument is deprecated, please use positional argument [gene] instead."
            )
        if not args.gene_deprecated and not args.gene:
            parser_archs4.error("the following arguments are required: gene")

        # Run gget archs4 function
        archs4_results = archs4(
            gene=args.gene,
            ensembl=args.ensembl,
            which=args.which,
            gene_count=args.gene_count,
            species=args.species,
            json=args.csv,
            verbose=args.quiet,
        )

        # Check if the function returned something
        if not isinstance(archs4_results, type(None)):
            # Save archs4 results if args.out specified
            if args.out and not args.csv:
                # Create saving directory
                directory = "/".join(args.out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)
                # Save to csv
                archs4_results.to_csv(args.out, index=False)

            if args.out and args.csv:
                # Create saving directory
                directory = "/".join(args.out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)
                # Save json
                with open(args.out, "w", encoding="utf-8") as f:
                    json.dump(archs4_results, f, ensure_ascii=False, indent=4)

            # Print results if no directory specified
            if not args.out and not args.csv:
                archs4_results.to_csv(sys.stdout, index=False)
            if not args.out and args.csv:
                print(json.dumps(archs4_results, ensure_ascii=False, indent=4))

    ## muscle return
    if args.command == "muscle":
        # Handle deprecated flags for backwards compatibility
        if args.fasta_deprecated and args.fasta:
            logger.warning(
                "The [-fa][--fasta] argument is deprecated, using positional argument [fasta] instead."
            )
        if args.fasta_deprecated and not args.fasta:
            args.fasta = args.fasta_deprecated
            logger.warning(
                "The [-fa][--fasta] argument is deprecated, please use positional argument [fasta] instead."
            )
        if not args.fasta_deprecated and not args.fasta:
            parser_muscle.error("the following arguments are required: fasta")

        muscle(fasta=args.fasta, super5=args.super5, out=args.out, verbose=args.quiet)

    ## elm return
    if args.command == "elm":
        ortho, regex = elm(
            sequence=args.sequence,
            uniprot=args.uniprot,
            sensitivity=args.sensitivity,
            threads=args.threads,
            diamond_binary=args.diamond_binary,
            expand=args.expand,
            verbose=args.quiet,
            json=args.csv,
            out=args.out,
        )
        # Print results if no directory specified
        if not args.out and not args.csv:
            ortho.to_csv(sys.stdout, index=False)
            regex.to_csv(sys.stdout, index=False)
        if not args.out and args.csv:
            print(json.dumps(ortho, ensure_ascii=False, indent=4))
            print(json.dumps(regex, ensure_ascii=False, indent=4))

    ## diamond return
    if args.command == "diamond":
        diamond_results = diamond(
            query=args.query,
            reference=args.reference,
            translated=args.translated,
            diamond_db=args.diamond_db,
            sensitivity=args.sensitivity,
            threads=args.threads,
            diamond_binary=args.diamond_binary,
            verbose=args.quiet,
            json=args.csv,
            out=args.out,
        )

        # Print results if no directory specified
        if not args.out and not args.csv:
            diamond_results.to_csv(sys.stdout, index=False)
        if not args.out and args.csv:
            print(json.dumps(diamond_results, ensure_ascii=False, indent=4))

    ## ref return
    if args.command == "ref":
        # Return all vertebrate available species
        if args.list_species:
            species_list = ref(
                species=None, release=args.release, list_species=args.list_species
            )
            # Save in specified directory if -o specified
            if args.out:
                directory = "/".join(args.out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)
                with open(args.out, "w") as tfile:
                    tfile.write("\n".join(species_list))
            else:
                for species in species_list:
                    print(species)

        # Return all invertebrate available species
        elif args.list_iv_species:
            species_list = ref(
                species=None, release=args.release, list_iv_species=args.list_iv_species
            )
            # Save in specified directory if -o specified
            if args.out:
                directory = "/".join(args.out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)
                with open(args.out, "w") as tfile:
                    tfile.write("\n".join(species_list))
            else:
                for species in species_list:
                    print(species)

        # Handle deprecated flags for backwards compatibility
        if args.species_deprecated and args.species:
            logger.warning(
                "The [-s][--species] argument is deprecated, using positional argument [species] instead."
            )
        if args.species_deprecated and not args.species:
            args.species = args.species_deprecated
            logger.warning(
                "The [-s][--species] argument is deprecated, please use positional argument [species] instead."
            )

        # Raise error if neither species nor list flag passed
        if (
            args.species is None
            and args.list_species is False
            and args.list_iv_species is False
        ):
            parser_ref.error(
                "the following arguments are required: species \n"
                "'gget ref --list_species' -> lists out all available vertebrate species. \n"
                "'gget ref --list_iv_species' -> lists out all available invertebrate species. \n"
                "Combine with '-r [int]' to define a specific Ensembl release (default: latest release). "
            )

        ## Clean up 'which' entry if passed
        # Split by comma
        which_clean = args.which.split(",")

        if args.species:
            # Query Ensembl for requested FTPs using function ref
            ref_results = ref(
                species=args.species,
                which=which_clean,
                release=args.release,
                ftp=args.ftp,
                verbose=args.quiet,
            )

            # Print or save list of URLs (ftp=True)
            if args.ftp:
                # Save in specified directory if -o specified
                if args.out:
                    directory = "/".join(args.out.split("/")[:-1])
                    if directory != "":
                        os.makedirs(directory, exist_ok=True)
                    with open(args.out, "w") as tfile:
                        tfile.write("\n".join(ref_results))

                # Print results if no directory specified
                else:
                    # Print results
                    for ref_res in ref_results:
                        print(ref_res)

                # Either way, download the files if download flag is set
                if args.download:
                    if args.out_dir is not None and args.out_dir != "":
                        os.makedirs(args.out_dir, exist_ok=True)

                    # Download list of URLs
                    for link in ref_results:
                        if args.out_dir:
                            subprocess.run(["curl", "--output-dir", args.out_dir, "-O", link], check=True)
                        else:
                            subprocess.run(["curl", "-O", link], check=True)

            # Print or save json file (ftp=False)
            else:
                # Save in specified directory if -o specified
                if args.out:
                    directory = "/".join(args.out.split("/")[:-1])
                    if directory != "":
                        os.makedirs(directory, exist_ok=True)
                    with open(args.out, "w", encoding="utf-8") as f:
                        json.dump(ref_results, f, ensure_ascii=False, indent=4)

                # Print results if no directory specified
                else:
                    print(json.dumps(ref_results, ensure_ascii=False, indent=4))

                # Either way, download the files if download flag is set
                if args.download:
                    if args.out_dir is not None and args.out_dir != "":
                        os.makedirs(args.out_dir, exist_ok=True)

                    # Download the URLs from the dictionary
                    for sp in ref_results:
                        for ftp_type in ref_results[sp]:
                            link = ref_results[sp][ftp_type]["ftp"]
                            if args.out_dir:
                                subprocess.run(["curl", "--output-dir", args.out_dir, "-O", link], check=True)
                            else:
                                subprocess.run(["curl", "-O", link], check=True)

    ## search return
    if args.command == "search":
        # Handle deprecated flags for backwards compatibility
        if args.sw_deprecated and args.searchwords:
            logger.warning(
                "The [-sw][--searchwords] argument is deprecated, using positional argument [searchwords] instead."
            )
        if args.sw_deprecated and not args.searchwords:
            args.searchwords = args.sw_deprecated
            logger.warning(
                "The [-sw][--searchwords] argument is deprecated, please use positional argument [searchwords] instead."
            )
        if not args.sw_deprecated and not args.searchwords:
            parser_gget.error("the following arguments are required: searchwords")

        ## Clean up args.searchwords
        sw_clean = []
        # Split by comma (spaces are automatically split by nargs:"+")
        for sw in args.searchwords:
            sw_clean.append(sw.split(","))
        # Flatten which_clean
        sw_clean_final = [item for sublist in sw_clean for item in sublist]
        # Remove empty strings resulting from split
        while "" in sw_clean_final:
            sw_clean_final.remove("")

        # Query Ensembl for genes based on species and searchwords using function search
        gget_results = search(
            sw_clean_final,
            species=args.species,
            release=args.release,
            id_type=args.id_type,
            seqtype=args.seqtype,
            andor=args.andor,
            limit=args.limit,
            json=args.csv,
            verbose=args.quiet,
        )

        # Save search results if args.out specified
        if args.out and not args.csv:
            # Create saving directory
            directory = "/".join(args.out.split("/")[:-1])
            if directory != "":
                os.makedirs(directory, exist_ok=True)
            # Save to csv
            gget_results.to_csv(args.out, index=False)

        if args.out and args.csv:
            # Create saving directory
            directory = "/".join(args.out.split("/")[:-1])
            if directory != "":
                os.makedirs(directory, exist_ok=True)
            # Save json
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(gget_results, f, ensure_ascii=False, indent=4)

        # Print results if no directory specified
        if not args.out and not args.csv:
            gget_results.to_csv(sys.stdout, index=False)
        if not args.out and args.csv:
            print(json.dumps(gget_results, ensure_ascii=False, indent=4))

    ## enrichr return
    if args.command == "enrichr":
        # Handle deprecated flags for backwards compatibility
        if args.genes_deprecated and args.genes:
            logger.warning(
                "The [-g][--genes] argument is deprecated, using positional argument [genes] instead."
            )
        if args.genes_deprecated and not args.genes:
            args.genes = args.genes_deprecated
            logger.warning(
                "The [-g][--genes] argument is deprecated, please use positional argument [genes] instead."
            )
        if not args.genes_deprecated and not args.genes:
            parser_enrichr.error("the following arguments are required: genes")

        ## Clean up args.genes
        genes_clean = []
        # Split by comma (spaces are automatically split by nargs:"+")
        for gene in args.genes:
            genes_clean.append(gene.split(","))
        # Flatten genes_clean
        genes_clean_final = [item for sublist in genes_clean for item in sublist]
        # Remove empty strings resulting from split
        while "" in genes_clean_final:
            genes_clean_final.remove("")

        bkg_genes_clean_final = None
        if args.background_list:
            ## Clean up args.bkg_l
            bkg_genes_clean = []
            # Split by comma (spaces are automatically split by nargs:"+")
            for gene in args.background_list:
                bkg_genes_clean.append(gene.split(","))
            # Flatten bkg_genes_clean
            bkg_genes_clean_final = [
                item for sublist in bkg_genes_clean for item in sublist
            ]
            # Remove empty strings resulting from split
            while "" in genes_clean_final:
                bkg_genes_clean_final.remove("")

        # Submit Enrichr query
        enrichr_results = enrichr(
            genes=genes_clean_final,
            species=args.species,
            background=args.background,
            background_list=bkg_genes_clean_final,
            database=args.database,
            ensembl=args.ensembl,
            ensembl_bkg=args.ensembl_bkg,
            kegg_out=args.kegg_out,
            kegg_rank=args.kegg_rank,
            json=args.csv,
            verbose=args.quiet,
        )

        # Check if the function returned something
        if enrichr_results is not None:
            # Save enrichr results if args.out specified
            if args.out and not args.csv:
                # Create saving directory
                directory = "/".join(args.out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)
                # Save to csv
                enrichr_results.to_csv(args.out, index=False)

            if args.out and args.csv:
                # Create saving directory
                directory = "/".join(args.out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)
                # Save json
                with open(args.out, "w", encoding="utf-8") as f:
                    json.dump(enrichr_results, f, ensure_ascii=False, indent=4)

            # Print results if no directory specified
            if not args.out and not args.csv:
                enrichr_results.to_csv(sys.stdout, index=False)
            if not args.out and args.csv:
                print(json.dumps(enrichr_results, ensure_ascii=False, indent=4))

    ## info return
    if args.command == "info":
        # Handle deprecated flags for backwards compatibility
        if args.id_deprecated and args.ens_ids:
            logger.warning(
                "The [-id][--ens_ids] argument is deprecated, using positional argument [ens_ids] instead."
            )
        if args.id_deprecated and not args.ens_ids:
            args.ens_ids = args.id_deprecated
            logger.warning(
                "The [-id][--genes] argument is deprecated, please use arguments [ens_ids] instead."
            )
        if args.ensembl_only:
            logger.warning(
                "The [-eo][--ensembl_only] argument is deprecated, please use arguments [ncbi] and [uniprot] instead."
            )
        if not args.id_deprecated and not args.ens_ids:
            parser_info.error("the following arguments are required: ens_ids")

        ## Clean up args.ens_ids
        ids_clean = []
        # Split by comma (spaces are automatically split by nargs:"+")
        for id_ in args.ens_ids:
            ids_clean.append(id_.split(","))
        # Flatten which_clean
        ids_clean_final = [item for sublist in ids_clean for item in sublist]
        # Remove empty strings resulting from split
        while "" in ids_clean_final:
            ids_clean_final.remove("")

        # Look up requested Ensembl IDs
        info_results = info(
            ids_clean_final,
            ncbi=args.ncbi,
            uniprot=args.uniprot,
            pdb=args.pdb,
            ensembl_only=args.ensembl_only,
            expand=args.expand,
            json=args.csv,
            verbose=args.quiet,
        )

        # Check if the function returned something
        if not isinstance(info_results, type(None)):
            # Save info results if args.out specified
            if args.out and not args.csv:
                # Create saving directory
                directory = "/".join(args.out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)
                # Save to csv
                info_results.to_csv(args.out, index=False)

            if args.out and args.csv:
                # Create saving directory
                directory = "/".join(args.out.split("/")[:-1])
                if directory != "":
                    os.makedirs(directory, exist_ok=True)
                # Save json
                with open(args.out, "w", encoding="utf-8") as f:
                    json.dump(info_results, f, ensure_ascii=False, indent=4)

            # Print results if no directory specified
            if not args.out and not args.csv:
                info_results.to_csv(sys.stdout, index=False)
            if not args.out and args.csv:
                print(json.dumps(info_results, ensure_ascii=False, indent=4))

    ## seq return
    if args.command == "seq":
        # Handle deprecated flags for backwards compatibility
        if args.id_deprecated and args.ens_ids:
            logger.warning(
                "The [-id][--ens_ids] argument is deprecated, using positional argument [ens_ids] instead."
            )
        if args.id_deprecated and not args.ens_ids:
            args.ens_ids = args.id_deprecated
            logger.warning(
                "The [-id][--ens_ids] argument is deprecated, please use positional argument [ens_ids] instead."
            )
        if not args.id_deprecated and not args.ens_ids:
            parser_seq.error("the following arguments are required: ens_ids")

        ## Clean up args.ens_ids
        ids_clean = []
        # Split by comma (spaces are automatically split by nargs:"+")
        for id_ in args.ens_ids:
            ids_clean.append(id_.split(","))
        # Flatten which_clean
        ids_clean_final = [item for sublist in ids_clean for item in sublist]
        # Remove empty strings resulting from split
        while "" in ids_clean_final:
            ids_clean_final.remove("")

        # Look up requested Ensembl IDs
        seq_results = seq(
            ids_clean_final,
            translate=args.translate,
            seqtype=args.seqtype,
            isoforms=args.isoforms,
            transcribe=args.transcribe,
            verbose=args.quiet,
        )

        # Save in specified directory if -o specified
        if args.out and seq_results != None:
            directory = "/".join(args.out.split("/")[:-1])
            if directory != "":
                os.makedirs(directory, exist_ok=True)
            file = open(args.out, "w")
            for element in seq_results:
                file.write(element + "\n")
            file.close()

        # Print results if no directory specified
        else:
            if seq_results != None:
                for seq_res in seq_results:
                    print(seq_res)

    ## setup return
    if args.command == "setup":
        setup(args.module, verbose=args.quiet, out=args.out)

    ## alphafold return
    if args.command == "alphafold":
        if args.out:
            directory = "/".join(args.out.split("/")[:-1])
            if directory != "":
                os.makedirs(directory, exist_ok=True)
            saving_dir = args.out
        else:
            saving_dir = f"{dt_string}_gget_alphafold_prediction"

        alphafold(
            args.sequence,
            out=saving_dir,
            multimer_for_monomer=args.multimer_for_monomer,
            multimer_recycles=args.multimer_recycles,
            relax=args.relax,
            plot=False,
            show_sidechains=False,
            verbose=args.quiet,
        )

    ## pdb return
    if args.command == "pdb":
        pdb_results = pdb(
            pdb_id=args.pdb_id,
            resource=args.resource,
            identifier=args.identifier,
        )

        if pdb_results:
            if args.resource == "pdb":
                if args.out:
                    # Create saving directory
                    directory = "/".join(args.out.split("/")[:-1])
                    if directory != "":
                        os.makedirs(directory, exist_ok=True)

                    # Save PDB file
                    with open(args.out, "w") as f:
                        f.write(pdb_results)
                else:
                    print(pdb_results)

            else:
                if args.out:
                    # Create saving directory
                    directory = "/".join(args.out.split("/")[:-1])
                    if directory != "":
                        os.makedirs(directory, exist_ok=True)

                    # Save json
                    with open(args.out, "w", encoding="utf-8") as f:
                        json.dump(pdb_results, f, ensure_ascii=False, indent=4)
                else:
                    print(json.dumps(pdb_results, ensure_ascii=False, indent=4))

    ## opentargets return
    if args.command == "opentargets":
        filters = dict(args.filter) if args.filter is not None else None

        opentargets_results = opentargets(
            ensembl_id=args.ens_id,
            resource=args.resource,
            limit=args.limit,
            verbose=args.quiet,
            filters=filters,
        )

        if args.out is not None and args.out != "":
            # Make saving directory
            directory = os.path.dirname(args.out)
            if directory != "":
                os.makedirs(directory, exist_ok=True)

            # Save json
            with open(args.out, "w", encoding="utf-8") as f:
                if args.csv:
                    opentargets_results.to_csv(f, index=False)
                else:
                    opentargets_results.to_json(
                        f, orient="records", force_ascii=False, indent=4
                    )
        else:
            if args.csv:
                opentargets_results.to_csv(sys.stdout, index=False)
            else:
                print(
                    opentargets_results.to_json(
                        orient="records", force_ascii=False, indent=4
                    )
                )

    ## cbio return
    if args.command == "cbio":
        if args.subcommand == "search":
            cbio_results = cbio_search(convert_to_list(*args.keywords))
            print(json.dumps(cbio_results, ensure_ascii=False, indent=4))
        elif args.subcommand == "plot":
            cbio_plot(
                args.study_ids,
                args.genes,
                stratification=args.stratification,
                variation_type=args.variation_type,
                filter=args.filter.split(":", 1) if args.filter else None,
                data_dir=args.data_dir,
                figure_dir=args.figure_dir,
                dpi=args.dpi,
                verbose=args.quiet,
                confirm_download=not args.no_confirm,
                show=args.show,
                figure_filename=args.filename,
                figure_title=args.title,
            )

    ## bgee return
    if args.command == "bgee":
        bgee_results: pd.DataFrame = bgee(
            args.ens_id,
            type=args.type,
            verbose=args.quiet,
        )

        if args.out is not None and args.out != "":
            # Make saving directory
            directory = os.path.dirname(args.out)
            if directory != "":
                os.makedirs(directory, exist_ok=True)

            # Save json
            with open(args.out, "w", encoding="utf-8") as f:
                if args.csv:
                    bgee_results.to_csv(f, index=False)
                else:
                    bgee_results.to_json(
                        f, orient="records", force_ascii=False, indent=4
                    )
        else:
            if args.csv:
                bgee_results.to_csv(sys.stdout, index=False)
            else:
                print(
                    bgee_results.to_json(orient="records", force_ascii=False, indent=4)
                )

    ## 8cube return
    if args.command == "8cube":
        from .gget_8cube import specificity, psi_block, gene_expression

        if args.cube_command is None:
            parser_8cube.error(
                "Please specify a subcommand: specificity, psi_block, or expression"
            )

        # SPECIFICITY
        if args.cube_command == "specificity":
            results = specificity(
                gene_list=args.genes,
                json=args.csv,  # JSON default
                save=False,
                verbose=args.quiet,
            )

            # Save
            if args.out:
                directory = os.path.dirname(args.out)
                if directory:
                    os.makedirs(directory, exist_ok=True)

                if not args.csv: # args.csv stores False
                    pd.DataFrame(results).to_csv(args.out, index=False)
                else:
                    with open(args.out, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=4)
                return

            # Print to STDOUT
            if not args.csv: # args.csv stores False
                pd.DataFrame(results).to_csv(sys.stdout, index=False)
            else:
                print(json.dumps(results, ensure_ascii=False, indent=4))
            return

        # PSI BLOCK
        if args.cube_command == "psi_block":
            results = psi_block(
                gene_list=args.genes,
                analysis_level=args.analysis_level,
                analysis_type=args.analysis_type,
                json=args.csv,
                save=False,
                verbose=args.quiet,
            )

            if args.out:
                directory = os.path.dirname(args.out)
                if directory:
                    os.makedirs(directory, exist_ok=True)

                if not args.csv: # args.csv stores False
                    pd.DataFrame(results).to_csv(args.out, index=False)
                else:
                    with open(args.out, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=4)
                return

            if not args.csv: # args.csv stores False
                pd.DataFrame(results).to_csv(sys.stdout, index=False)
            else:
                print(json.dumps(results, ensure_ascii=False, indent=4))
            return

        # EXPRESSION
        if args.cube_command == "expression":
            results = gene_expression(
                gene_list=args.genes,
                analysis_level=args.analysis_level,
                analysis_type=args.analysis_type,
                json=args.csv,
                save=False,
                verbose=args.quiet,
            )

            if args.out:
                directory = os.path.dirname(args.out)
                if directory:
                    os.makedirs(directory, exist_ok=True)

                if not args.csv: # args.csv stores False
                    pd.DataFrame(results).to_csv(args.out, index=False)
                else:
                    with open(args.out, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=4)
                return

            if not args.csv: # args.csv stores False
                pd.DataFrame(results).to_csv(sys.stdout, index=False)
            else:
                print(json.dumps(results, ensure_ascii=False, indent=4))
            return

    ## virus return
    if args.command == "virus":
        # Parse has_proteins argument - convert comma-separated string to list
        has_proteins_arg = args.has_proteins
        if has_proteins_arg and ',' in has_proteins_arg:
            has_proteins_arg = [p.strip() for p in has_proteins_arg.split(',')]
        
        segment_arg = args.segment
        if segment_arg and ',' in segment_arg:
            segment_arg = [s.strip() for s in segment_arg.split(',')]

        isolate_arg = args.isolate
        if isolate_arg and ',' in isolate_arg:
            isolate_arg = [i.strip() for i in isolate_arg.split(',')]

        submitter_name_arg = args.submitter_name
        if submitter_name_arg and ',' in submitter_name_arg:
            submitter_name_arg = [a.strip() for a in submitter_name_arg.split(',')]

        submitter_institution_arg = args.submitter_institution
        if submitter_institution_arg and ',' in submitter_institution_arg:
            submitter_institution_arg = [i.strip() for i in submitter_institution_arg.split(',')]

        submitter_country_arg = args.submitter_country
        if submitter_country_arg and ',' in submitter_country_arg:
            submitter_country_arg = [c.strip() for c in submitter_country_arg.split(',')]
        
        env_source_arg = args.env_source
        if env_source_arg and ',' in env_source_arg:
            env_source_arg = [e.strip() for e in env_source_arg.split(',')]

        lineage_arg = args.lineage
        if lineage_arg and ',' in lineage_arg:
            lineage_arg = [l.strip() for l in lineage_arg.split(',')]

        genotype_arg = args.genotype
        if genotype_arg and ',' in genotype_arg:
            genotype_arg = [g.strip() for g in genotype_arg.split(',')]

        isolation_source_arg = args.isolation_source
        if isolation_source_arg and ',' in isolation_source_arg:
            isolation_source_arg = [i.strip() for i in isolation_source_arg.split(',')]

        gen_mol_type_arg = args.gen_mol_type
        if gen_mol_type_arg and ',' in gen_mol_type_arg:
            gen_mol_type_arg = [g.strip() for g in gen_mol_type_arg.split(',')]

        # Determine merge_results: --no-merge overrides --merge-results
        merge_results_arg = True  # default
        if args.no_merge:
            merge_results_arg = False

        virus(
            virus=args.virus,
            is_accession=args.is_accession,
            outfolder=args.out,
            host=args.host,
            min_seq_length=args.min_seq_length,
            max_seq_length=args.max_seq_length,
            min_gene_count=args.min_gene_count,
            max_gene_count=args.max_gene_count,
            nuc_completeness=args.nuc_completeness,
            has_proteins=has_proteins_arg,
            proteins_complete=args.proteins_complete,
            lab_passaged=args.lab_passaged,
            geographic_location=args.geographic_location,
            submitter_country=submitter_country_arg,
            min_collection_date=args.min_collection_date,
            max_collection_date=args.max_collection_date,
            source_database=args.source_database,
            annotated=args.annotated,
            # refseq_only=args.refseq_only,
            keep_temp=args.keep_temp,
            min_release_date=args.min_release_date,
            max_release_date=args.max_release_date,
            min_mature_peptide_count=args.min_mature_peptide_count,
            max_mature_peptide_count=args.max_mature_peptide_count,
            min_protein_count=args.min_protein_count,
            max_protein_count=args.max_protein_count,
            max_ambiguous_chars=args.max_ambiguous_chars,
            is_sars_cov2=args.is_sars_cov2,
            is_alphainfluenza=args.is_alphainfluenza,
            segment=segment_arg,
            vaccine_strain=args.vaccine_strain,
            lineage=lineage_arg,
            genbank_metadata=args.genbank_metadata,
            genbank_batch_size=args.genbank_batch_size,
            download_all_accessions=args.download_all_accessions,
            _skip_cache=args._skip_cache,
            provirus=args.provirus,
            isolate=isolate_arg,
            genotype=genotype_arg,
            isolation_source=isolation_source_arg,
            env_source=env_source_arg,
            submitter_name=submitter_name_arg,
            submitter_institution=submitter_institution_arg,
            gen_mol_type=gen_mol_type_arg,
            baseline_metadata=args.baseline_metadata,
            merge_results=merge_results_arg,
            api_key=args.api_key,
            verbose=args.quiet,
        )
