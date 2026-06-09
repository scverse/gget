import uuid

# Default (connect, read) timeout in seconds for HTTP requests issued via the
# `requests` library. Centralized so callers without their own retry/timeout
# strategy avoid hanging indefinitely on slow upstreams.
DEFAULT_REQUESTS_TIMEOUT = (10, 60)

# Ensembl REST API server for gget seq and info
ENSEMBL_REST_API = "http://rest.ensembl.org/"
ENSEMBL_FTP_URL = "http://ftp.ensembl.org/pub/"
ENSEMBL_FTP_URL_GRCH37 = "http://ftp.ensembl.org/pub/grch37/"
# Non-vertebrate server
ENSEMBL_FTP_URL_NV = "http://ftp.ensemblgenomes.org/pub/"

# NCBI URL for gget info
NCBI_URL = "https://www.ncbi.nlm.nih.gov"

# NCBI VIRUS REST API URL for gget virus - Version 2 API endpoint
NCBI_API_BASE = "https://api.ncbi.nlm.nih.gov/datasets/v2"

# NCBI E-utilities URL for gget virus
NCBI_EUTILS_BASE_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
NCBI_EUTILS_BASE_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

# UniProt REST API server for gget seq and info
UNIPROT_REST_API = "https://rest.uniprot.org/uniprotkb/search?query="
UNIPROT_IDMAPPING_API = "https://rest.uniprot.org/idmapping"

# RCSB PDB API for gget pdb
RCSB_PDB_API = "https://data.rcsb.org/rest/v1/core/"

# API to get PDB entries from Ensembl IDs
ENS_TO_PDB_API = "https://www.ebi.ac.uk/pdbe/aggregated-api/mappings/ensembl_to_pdb/"

# BLAST API endpoints
BLAST_URL = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
# Generate a random UUID
BLAST_CLIENT = "gget_client-" + str(uuid.uuid4())

# MUSCLE Github repo
MUSCLE_GITHUB_LINK = "https://github.com/rcedgar/muscle.git"

# Enrichr API endpoints
POST_ENRICHR_URL = "https://maayanlab.cloud/speedrichr/api/addList"
GET_ENRICHR_URL = "https://maayanlab.cloud/speedrichr/api/enrich"
POST_BACKGROUND_ID_ENRICHR_URL = "https://maayanlab.cloud/speedrichr/api/addbackground"
GET_BACKGROUND_ENRICHR_URL = "https://maayanlab.cloud/speedrichr/api/backgroundenrich"

POST_ENRICHR_URLS = {
    f"{typ}": f"https://maayanlab.cloud/{typ.capitalize()}Enrichr/addList"
    for typ in ["fly", "yeast", "worm", "fish"]
}
POST_ENRICHR_URLS["human"] = POST_ENRICHR_URL
GET_ENRICHR_URLS = {
    f"{typ}": f"https://maayanlab.cloud/{typ.capitalize()}Enrichr/enrich"
    for typ in ["fly", "yeast", "worm", "fish"]
}
GET_ENRICHR_URLS["human"] = GET_ENRICHR_URL

# ARCHS4 API endpoints
GENECORR_URL = "https://maayanlab.cloud/matrixapi/coltop"
EXPRESSION_URL = "https://maayanlab.cloud/archs4/search/loadExpressionTissue.php?"

# Download links for ELM database
ELM_INSTANCES_FASTA_DOWNLOAD = (
    "http://elm.eu.org/instances.fasta?q=*&taxon=&instance_logic="
)
ELM_INSTANCES_TSV_DOWNLOAD = (
    "http://elm.eu.org/instances.tsv?q=*&taxon=&instance_logic="
)
ELM_CLASSES_TSV_DOWNLOAD = "http://elm.eu.org/elms/elms_index.tsv"
ELM_INTDOMAINS_TSV_DOWNLOAD = "http://elm.eu.org/interactiondomains.tsv"

# COSMIC API endpoint
COSMIC_GET_URL = "https://cancer.sanger.ac.uk/cosmic/search/"
COSMIC_RELEASE_URL = "https://cancer.sanger.ac.uk/cosmic/release_notes"

# OpenTargets API endpoint
OPENTARGETS_GRAPHQL_API = "https://api.platform.opentargets.org/api/v4/graphql"

# CBIO data
CBIO_CANCER_TYPE_TO_TISSUE_DICTIONARY = {
    "Acute Leukemias of Ambiguous Lineage": "leukemia",
    "Acute Myeloid Leukemia": "leukemia",
    "Acute myeloid leukemia": "leukemia",
    "Adenosarcoma": "mixed",
    "Adrenal Tumor": "adrenal_gland",
    "Adrenocortical Adenoma": "adrenal_gland",
    "Adrenocortical Carcinoma": "adrenal_gland",
    "Adrenocortical carcinoma": "adrenal_gland",
    "Ampullary Cancer": "ampulla",
    "Ampullary Carcinoma": "ampulla",
    "Anal Cancer": "intestine",
    "Appendiceal Cancer": "appendix",
    "B-Lymphoblastic Leukemia/Lymphoma": "lymphoma",
    "Biliary Tract": "biliary_tract",
    "Biliary Tract Cancer, NOS": "biliary_tract",
    "Bladder Cancer": "bladder",
    "Bladder/Urinary Tract Cancer, NOS": "bladder",
    "Blastic Plasmacytoid Dendritic Cell Neoplasm": "immune",
    "Blood Cancer, NOS": "leukemia",
    "Bone Cancer": "bone",
    "Bone Sarcoma": "bone",
    "Bowel Cancer, NOS": "intestine",
    "Brain Cancer": "brain",
    "Breast Cancer": "breast",
    "Breast Carcinoma": "breast",
    "Breast Sarcoma": "breast",
    "CNS Cancer": "brain",
    "Cancer of Unknown Primary": "mixed",
    "Carcinoma of Uterine Cervix": "cervix",
    "Cervical Cancer": "cervix",
    "Cholangiocarcinoma": "biliary_tract",
    "Choroid Plexus Tumor": "brain",
    "Colorectal Cancer": "intestine",
    "Colorectal Carcinoma": "intestine",
    "Cutaneous malignancy of hair matrix cells": "skin",
    "Diffuse Glioma": "brain",
    "Embryonal Tumor": "mixed",
    "Encapsulated Glioma": "brain",
    "Endometrial Cancer": "uterus",
    "Endometrial Carcinoma": "uterus",
    "Ependymomal Tumor": "brain",
    "Esophageal Carcinoma": "esophagus",
    "Esophagogastric Cancer": "esophagus",
    "Essential Thrombocythemia": "plasma",
    "Extrahepatic Cholangiocarcinoma": "biliary_tract",
    "Fibrosarcoma": "soft_tissue",
    "Gallbladder Carcinoma": "gallbladder",
    "Gastric Cancer": "stomach",
    "Gastrointestinal Neuroendocrine Tumor": "intestine",
    "Gastrointestinal Stromal Tumor": "intestine",
    "Germ Cell Tumor": "testicle",
    "Gestational Trophoblastic Disease": "uterus",
    "Glioblastoma": "brain",
    "Glioma": "brain",
    "Head and Neck Cancer": "head_neck",
    "Head and Neck Cancer, NOS": "head_neck",
    "Head and Neck Carcinoma": "head_neck",
    "Hepatobiliary Cancer": "liver",
    "High-grade glioma/astrocytoma": "brain",
    "Histiocytosis": "immune",
    "Hodgkin Lymphoma": "lymphoma",
    "Hodgkin Lymphoma-like PTLD": "lymphoma",
    "Intraductal Papillary Mucinous Neoplasm": "pancreas",
    "Intrahepatic Cholangiocarcinoma": "biliary_tract",
    "Invasive Breast Carcinoma": "breast",
    "Kidney Renal Cell Carcinoma": "kidney",
    "Leukemia": "leukemia",
    "Liver Hepatocellular Carcinoma": "liver",
    "Liver Tumor": "liver",
    "Low-grade glioma/astrocytoma": "brain",
    "Lung Adenocarcinoma": "lung",
    "Lung Cancer": "lung",
    "Lung Cancer, NOS": "lung",
    "Lung cancer": "lung",
    "Lymphoid Neoplasm": "lymph",
    "Malignant Rhabdoid Tumor of the Liver": "liver",
    "Mastocytosis": "immune",
    "Mature B-Cell Neoplasms": "lymphoma",
    "Mature B-cell lymphoma": "lymphoma",
    "Mature T and NK Neoplasms": "immune",
    "Medulloblastoma": "brain",
    "Melanoma": "skin",
    "Meningioma": "brain",
    "Mesothelioma": "soft_tissue",
    "Miscellaneous Brain Tumor": "brain",
    "Miscellaneous Neuroepithelial Tumor": "brain",
    "Mucinous Adenocarcinoma Lymph Node": "lymph",
    "Myelodysplastic Syndromes": "plasma",
    "Myelodysplastic/Myeloproliferative Neoplasms": "plasma",
    "Myeloproliferative Neoplasms": "plasma",
    "Nerve Sheath Tumor": "soft_tissue",
    "Nested stromal epithelial tumor of the liver": "liver",
    "Non Small Cell Lung Cancer": "lung",
    "Non-Germinomatous Germ Cell Tumor": "testicle",
    "Non-Hodgkin Lymphoma": "lymphoma",
    "Non-Seminomatous Germ Cell Tumor": "testicle",
    "Non-Small Cell Lung Cancer": "lung",
    "Ocular Melanoma": "eye",
    "Other": "mixed",
    "Ovarian Cancer": "ovary",
    "Ovarian Carcinoma": "ovary",
    "Ovarian Epithelial Tumor": "ovary",
    "Ovarian Germ Cell Tumor": "ovary",
    "Ovarian/Fallopian Tube Cancer, NOS": "ovary",
    "Pancreatic Cancer": "pancreas",
    "Penile Cancer": "intestine",
    "Peripheral Nervous System": "soft_tissue",
    "Pheochromocytoma": "adrenal_gland",
    "Pineal Tumor": "brain",
    "Pleural Mesothelioma": "soft_tissue",
    "Posttransplant Lymphoproliferative Disorders": "lymphoma",
    "Prostate Cancer": "prostate",
    "Prostate Cancer, NOS": "prostate",
    "Renal Cell Carcinoma": "kidney",
    "Renal Clear Cell Carcinoma": "kidney",
    "Renal Non-Clear Cell Carcinoma": "kidney",
    "Renal cancer": "kidney",
    "Retinoblastoma": "eye",
    "Rhabdoid Cancer": "soft_tissue",
    "Salivary Cancer": "head_neck",
    "Salivary Gland Cancer": "head_neck",
    "Salivary Gland-Type Tumor of the Lung": "lung",
    "Sarcoma": "soft_tissue",
    "Sellar Tumor": "brain",
    "Seminoma": "testicle",
    "Sex Cord Stromal Tumor": "testicle",
    "Skin Cancer, Non-Melanoma": "skin",
    "Small Bowel Cancer": "intestine",
    "Small Bowel Carcinoma": "intestine",
    "Small Cell Lung Cancer": "lung",
    "Soft Tissue Myoepithelial Carcinoma": "soft_tissue",
    "Soft Tissue Sarcoma": "soft_tissue",
    "Soft Tissue Tumor": "soft_tissue",
    "T-Lymphoblastic Leukemia/Lymphoma": "leukemia",
    "Teratoma with Malignant Transformation": "testicle",
    "Thymic Epithelial Tumor": "thymus",
    "Thymic Tumor": "thymus",
    "Thyroid Cancer": "thyroid",
    "Thyroid Carcinoma": "thyroid",
    "Urothelial Carcinoma": "bladder",
    "Uterine Corpus Endometrial Carcinoma": "uterus",
    "Uterine Endometrioid Carcinoma": "uterus",
    "Uterine Sarcoma": "uterus",
    "Vaginal Cancer": "intestine",
    "Wilms Tumor": "kidney",
}

CBIO_CANCER_TYPE_ACRONYM_TO_TISSUE_DICTIONARY = {
    "acbc": "breast",
    "acc": "adrenal_gland",
    "acyc": "adenoid",
    "aml": "leukemia",
    "ampca": "ampulla",
    "angs": "endothelial",
    "apad": "appendix",
    "bcc": "skin",
    "bfn": "breast",
    "biliary_tract": "biliary_tract",
    "blca": "bladder",
    "bll": "leukemia",
    "bowel": "intestine",
    "brain": "brain",
    "brca": "breast",
    "breast": "breast",
    "ccrcc": "kidney",
    "cervix": "cervix",
    "cesc": "cervix",
    "chol": "biliary_tract",
    "chrcc": "kidney",
    "cllsll": "leukemia",
    "coad": "intestine",
    "coadread": "intestine",
    "cscc": "skin",
    "desm": "skin",
    "difg": "brain",
    "dlbclnos": "lymphoma",
    "egc": "esophagus",
    "es": "bone",
    "esca": "esophagus",
    "escc": "esophagus",
    "gbc": "gallbladder",
    "gbm": "brain",
    "gist": "stomach",
    "hcc": "liver",
    "hccihch": "liver",
    "hdcn": "immune",
    "head_neck": "head_neck",
    "hgsoc": "ovary",
    "hnsc": "head_neck",
    "ihch": "liver",
    "lgsoc": "ovary",
    "liad": "liver",
    "luad": "lung",
    "lung": "lung",
    "lusc": "lung",
    "lymph": "lymph",
    "mbc": "breast",
    "mbl": "brain",
    "mbn": "lymphoma",
    "mcl": "lymphoma",
    "mds": "leukemia",
    "mel": "skin",
    "mixed": "mixed",
    "mng": "head_neck",
    "mnm": "leukemia",
    "mpn": "leukemia",
    "mpnst": "soft_tissue",
    "mrt": "kidney",
    "mtnn": "lymphoma",
    "myeloid": "leukemia",
    "nbl": "adrenal_gland",
    "nccrcc": "kidney",
    "nhl": "lymphoma",
    "npc": "head_neck",
    "nsclc": "lung",
    "nsgct": "testicle",
    "nst": "brain",
    "odg": "brain",
    "ovary": "ovary",
    "paac": "pancreas",
    "paad": "pancreas",
    "pact": "pancreas",
    "pancreas": "pancreas",
    "panet": "pancreas",
    "past": "brain",
    "pcm": "plasma",
    "pcnsl": "lymphoma",  # brain?
    "plmeso": "lung",
    "prad": "prostate",
    "prcc": "kidney",
    "prostate": "prostate",
    "rbl": "eye",
    "rms": "muscle",
    "scco": "ovary",
    "sclc": "lung",
    "skcm": "skin",
    "soft_tissue": "soft_tissue",
    "stad": "stomach",
    "stmyec": "soft_tissue",
    "stomach": "stomach",
    "testis": "testicle",
    "tet": "thymus",
    "thpa": "thyroid",
    "thym": "thymus",
    "thyroid": "thyroid",
    "uccc": "uterus",
    "ucec": "uterus",
    "ucs": "uterus",
    "um": "eye",
    "urcc": "kidney",
    "usarc": "uterus",
    "utuc": "bladder",
    "vsc": "cervix",
    "wt": "kidney",
}
