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
from .gget_g2p import g2p
from .gget_gpt import gpt
from .gget_cellxgene import cellxgene
from .gget_elm import elm
from .gget_diamond import diamond
from .gget_cosmic import cosmic
from .gget_mutate import mutate
from .gget_opentargets import opentargets
from .gget_cbio import cbio_plot, cbio_search
from .gget_bgee import bgee
from .gget_8cube import specificity, psi_block, gene_expression
from .gget_virus import virus

import logging

# Mute numexpr threads info
logging.getLogger("numexpr").setLevel(logging.WARNING)


# Get version number from the config file
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError  # For Python <3.8

try:
    __version__ = version("gget")
except PackageNotFoundError:
    __version__ = "unknown"


__author__ = "Laura Luebbert"
__email__ = "lauralubbert@gmail.com"
