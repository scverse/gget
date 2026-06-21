[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/cosmic.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python.  The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget cosmic 🪐
Search for genes, mutations, and other factors associated with cancer using the [COSMIC](https://cancer.sanger.ac.uk/cosmic) (Catalogue Of Somatic Mutations In Cancer) database.  
Return format: JSON (command-line) or data frame/CSV (Python) when `download_cosmic=False`. When `download_cosmic=True`, downloads the requested database into the specified folder.  

This module was originally written in part by [@AubakirovArman](https://github.com/AubakirovArman) (information querying) and [@josephrich98](https://github.com/josephrich98) (database download).  

NOTE: License fees apply for the commercial use of COSMIC. You can read more about licensing COSMIC data [here](https://cancer.sanger.ac.uk/cosmic/license).  

NOTE: When using this module for the first time, first download a COSMIC database to obtain `cosmic_tsv_path` (see examples below).  

**Positional argument (for querying information)**  
`searchterm`  
Search term, which can be a mutation, or gene name (or Ensembl ID), or sample, etc.  
Examples: 'EGFR', 'ENST00000275493', 'c.650A>T', 'p.Q217L', 'COSV51765119', 'BT2012100223LNCTB' (sample ID)  
NOTE: (Python only) Set to `None` when downloading COSMIC databases with `download_cosmic=True`.  

**Required argument (for querying information)**  
`-ctp` `--cosmic_tsv_path`  
Path to the COSMIC database tsv file, e.g. 'path/to/CancerMutationCensus_AllData_v101_GRCh37.tsv'.  
This file is downloaded when downloading COSMIC databases using the arguments described below.  
NOTE: This is a required argument when `download_cosmic=False`.  

**Optional arguments (for querying information)**  
`-l` `--limit`  
Limits number of hits to return. Default: 100.  

`-csv` `--csv`  
Command-line only. Returns results in CSV format.  
Python: Use `json=True` to return output in JSON format.  

**Flags (for downloading COSMIC databases)**  
`-d` `--download_cosmic`  
Switches into database download mode.  

`-gm` `--gget_mutate`  
Creates a modified version of the COSMIC database for use with [`gget mutate`](mutate.md).  

**Optional arguments (for downloading COSMIC databases)**  
`-cp` `--cosmic_project`  
'cancer' (default), 'cancer_example', 'census', 'resistance', 'cell_line', 'genome_screen', or 'targeted_screen'  
Type of COSMIC database to download:  

| cosmic_project  | Description                                                           | Notes                                                                              | Size   |
|-----------------|-----------------------------------------------------------------------|------------------------------------------------------------------------------------|--------|
| cancer          | Cancer Mutation Census (CMC) (most commonly used COSMIC mutation set) | Only available for GRCh37. Most feature-rich schema (takes the longest to search). | 2 GB   |
| cancer_example  | Example CMC subset provided for testing and demonstration             | Downloadable without a COSMIC account. Minimal dataset.                            | 2.5 MB |
| census          | COSMIC census of curated somatic mutations in known cancer genes      | Smaller curated set of known cancer drivers.                                       | 630 MB |
| resistance      | Mutations associated with drug resistance                             | Helpful for pharmacogenomics research.                                             | 1.6 MB |
| cell_line       | Cell Lines Project mutation data                                      | Sample metadata often available.                                                   | 2.7 GB |
| genome_screen   | Mutations from genome screening efforts                               | Includes less curated data, good for large-scale screens.                          |  |
| targeted_screen | Mutations from targeted screening panels                              | Focused panel datasets, good for clinical settings.                                |  |  

`-cv` `--cosmic_version`  
Version of the COSMIC database. Default: None -> Defaults to latest version.  

`-gv` `--grch_version`  
Version of the human GRCh reference genome the COSMIC database was based on (37 or 38). Default: 37  

`--email`
Email for COSMIC login. Helpful for avoiding required input upon running gget COSMIC. Default: None

`--password`
Password for COSMIC login. Helpful for avoiding required input upon running gget COSMIC, but password will be stored in plain text in the script. Default: None

**Additional arguments for the `--gget_mutate` flag**  
`--keep_genome_info`
Whether to keep genome information in the modified database for use with `gget mutate`. Default: False

`--remove_duplicates`
Whether to remove duplicate rows from the modified database for use with `gget mutate`. Default: False

`--seq_id_column`
(str) Name of the seq_id column in the csv file created by `gget_mutate`. Default: "seq_ID"

`--mutation_column`
(str) Name of the mutation column in the csv file created by `gget_mutate`. Default: "mutation"

`--mut_id_column`
(str) Name of the mutation_id column in the csv file created by `gget_mutate`. Default: "mutation_id"

**Optional arguments (general)**  
`-o` `--out`  
Path to the file (or folder when downloading databases with the `download_cosmic` flag) the results will be saved in, e.g. 'path/to/results.json'.  
Defaults:  
-> When `download_cosmic=False`: Results will be returned to standard out  
-> When `download_cosmic=True`: Database will be downloaded into current working directory  

**Flags (general)**  
`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.  


### Examples
#### Download the COSMIC "cancer" database and query information
```bash
# The download_cosmic command will ask for your COSMIC email and password and only needs to be run once
gget cosmic --download_cosmic --cosmic_project cancer

gget cosmic EGFR --cosmic_tsv_path 'CancerMutationCensus_AllData_Tsv_v101_GRCh37/CancerMutationCensus_AllData_v101_GRCh37.tsv'
```
```python
# Python
# The download_cosmic command will ask for your COSMIC email and password and only needs to be run once
gget.cosmic(searchterm=None, download_cosmic=True, cosmic_project="cancer")

gget.cosmic("EGFR", cosmic_tsv_path="CancerMutationCensus_AllData_Tsv_v101_GRCh37/CancerMutationCensus_AllData_v101_GRCh37.tsv")
```

&rarr; The first command downloads the requested COSMIC database of the latest COSMIC release into the current working directory. The second command searches the database for mutations associated with the 'EGFR' gene and returns results in the following format:

| GENE_NAME | ACCESSION_NUMBER | ONC_TSG | Mutation_CDS | Mutation_AA |  ... |
| ---- | ---- | ---- | ---- | ---- | ---- |
| EGFR | ENST00000275493.2 | oncogene | c.650A>T | p.Q217L | ... |
| EGFR | ENST00000275493.2 | oncogene | c.966C>T | p.G322= | ... |
| ... | ... | ... | ... | ... | ... |

#### Download the COSMIC "census" database and query information
```bash
# The download_cosmic command will ask for your COSMIC email and password and only needs to be run once
gget cosmic --download_cosmic --cosmic_project census

gget cosmic EGFR --cosmic_tsv_path 'Cosmic_MutantCensus_Tsv_v101_GRCh37/Cosmic_MutantCensus_v101_GRCh37.tsv'
```
```python
# Python
# The download_cosmic command will ask for your COSMIC email and password and only needs to be run once
gget.cosmic(searchterm=None, download_cosmic=True, cosmic_project="cancer")

gget.cosmic("EGFR", cosmic_tsv_path="Cosmic_MutantCensus_Tsv_v101_GRCh37/Cosmic_MutantCensus_v101_GRCh37.tsv")
```

&rarr; The first command downloads the requested COSMIC database of the latest COSMIC release into the current working directory. The second command searches the database for mutations associated with the 'EGFR' gene and returns results in the following format:

| GENE_SYMBOL | COSMIC_GENE_ID | MUTATION_DESCRIPTION | MUTATION_CDS | Mutation_AA | MUTATION_SOMATIC_STATUS | ... |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| EGFR | COSG35617 | inframe_deletion | c.2235_2249del | 	p.E746_A750del | Reported in another cancer sample as somatic | ... |
| EGFR | COSG35617 | missense_variant | c.2573T>G | p.L858R | Reported in another cancer sample as somatic | ... |
| ... | ... | ... | ... | ... | ... | ... |


# References
If you use `gget cosmic` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Tate JG, Bamford S, Jubb HC, Sondka Z, Beare DM, Bindal N, Boutselakis H, Cole CG, Creatore C, Dawson E, Fish P, Harsha B, Hathaway C, Jupe SC, Kok CY, Noble K, Ponting L, Ramshaw CC, Rye CE, Speedy HE, Stefancsik R, Thompson SL, Wang S, Ward S, Campbell PJ, Forbes SA. COSMIC: the Catalogue Of Somatic Mutations In Cancer. Nucleic Acids Res. 2019 Jan 8;47(D1):D941-D947. doi: [10.1093/nar/gky1015](https://doi.org/10.1093/nar/gky1015). PMID: 30371878; PMCID: PMC6323903.
