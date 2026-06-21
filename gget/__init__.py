"""gget: efficient querying of genomic databases."""

import logging
from importlib.metadata import PackageNotFoundError, version

from .gget_8cube import gene_expression, psi_block, specificity
from .gget_alphafold import alphafold
from .gget_archs4 import archs4
from .gget_bgee import bgee
from .gget_blast import blast
from .gget_blat import blat
from .gget_cbio import cbio_plot, cbio_search
from .gget_cellxgene import cellxgene
from .gget_cosmic import cosmic
from .gget_diamond import diamond
from .gget_elm import elm
from .gget_enrichr import enrichr
from .gget_gpt import gpt
from .gget_info import info
from .gget_muscle import muscle
from .gget_mutate import mutate
from .gget_opentargets import opentargets
from .gget_pdb import pdb
from .gget_ref import ref
from .gget_search import search
from .gget_seq import seq
from .gget_setup import setup
from .gget_virus import virus

# Mute numexpr threads info
logging.getLogger("numexpr").setLevel(logging.WARNING)

try:
    __version__ = version("gget")
except PackageNotFoundError:
    __version__ = "unknown"

__author__ = "Laura Luebbert"
__email__ = "lauralubbert@gmail.com"
