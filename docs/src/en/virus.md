[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/virus.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget virus 🦠  

Download viral nucleotide sequences, along with rich, linked metadata, from across the International Nucleotide Sequence Database Collaboration ([INSDC](https://www.insdc.org/)), including NCBI, [ENA](ebi.ac.uk/ena/browser/), and [DDBJ](https://www.ddbj.nig.ac.jp/index-e.html) (accessed via [NCBI Virus](https://www.ncbi.nlm.nih.gov/labs/virus/)), with the option to further enrich results using metadata from NCBI GenBank (e.g. gene and protein annotations). `gget virus` applies sequential server-side and local filters to efficiently download customized datasets.  

Return format: FASTA, CSV, and JSONL files saved to an output folder.  

[No-code, shareable Google Colab notebook for querying viral sequences.](https://colab.research.google.com/github/pachterlab/gget_examples/blob/main/gget_virus/gget_virus_colab.ipynb)

This module was written by [Ferdous Nasri](https://github.com/ferbsx).

**Note**: For SARS-CoV-2 and Alphainfluenza (Influenza A) queries, `gget virus` uses NCBI's optimized cached data packages via the [NCBI datasets CLI](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/command-line/datasets/). The datasets CLI binary is bundled with gget for all major platforms—no additional installation required. If you already have the NCBI datasets CLI installed on your system, gget will automatically use your existing installation.

**Positional argument**  
`virus`  
Virus taxon name (e.g. 'Zika virus'), taxon ID (e.g. '2697049'), NCBI accession number (e.g. 'NC\_045512.2'), space-separated list of accessions (e.g. 'NC\_045512.2 MN908947.3 MT020781.1'), or path to a text file containing accession numbers (one per line) (e.g. 'path/to/text.txt').  

Add `--is_accession` when passing an NCBI accession number. Add `--is_sars_cov2` or `is_alphainfluenza` for optimized download of SARS-CoV2 or Alphainfluenza sequences, respectively.  

For SARS-CoV-2 and Alphainfluenza cached downloads, supports:  
  - Single accession: `NC_045512.2`  
  - Space-separated list: `NC_045512.2 MN908947.3 MT020781.1`   
  - Text file path: `accessions.txt` (one accession per line)  

Use flag `--download_all_accessions` to apply filters without searching for a specific virus.  

**Optional arguments**   

_Host filters_  

`--host`  
Filter by host organism name or NCBI Taxonomy ID (e.g., 'human', 'Aedes aegypti', `1335626`).

_Sequence & Gene filters_  

`--nuc_completeness`  
Filter by nucleotide completeness. One of: 'complete' or 'partial'.  
Set to 'complete' to only return nucleotide sequences marked as complete; set to 'partial' to only return sequences that are marked as partial.  

`--min_seq_length`  
Filter by minimum sequence length.

`--max_seq_length`  
Filter by maximum sequence length.

`--min_gene_count`  
Filter by minimum number of genes.  
**Note:** Using this filter automatically enables GenBank metadata retrieval (`-g`).

`--max_gene_count`  
Filter by maximum number of genes.  
**Note:** Using this filter automatically enables GenBank metadata retrieval (`-g`).

`--min_protein_count`  
Filter by minimum number of proteins.

`--max_protein_count`  
Filter by maximum number of proteins.

`--min_mature_peptide_count`  
Filter by minimum number of mature peptides.  
**Note:** Using this filter automatically enables GenBank metadata retrieval (`-g`).

`--max_mature_peptide_count`  
Filter by maximum number of mature peptides.  
**Note:** Using this filter automatically enables GenBank metadata retrieval (`-g`).

`--max_ambiguous_chars`  
Filter by maximum number of ambiguous nucleotide characters (N's).

`--has_proteins`  
Filter for sequences containing specific proteins or genes (e.g., 'spike', 'ORF1ab'). Can be a single protein name or a list of protein names. Any matching protein will keep the sequence.  
Command line: `--has_proteins spike` or `--has_proteins hemagglutinin,neuraminidase` (comma-separated, no spaces)  
Python: `has_proteins="spike"` or `has_proteins=["spike", "ORF1ab"]`  
**Note:** Using this filter automatically enables GenBank metadata retrieval (`-g`).

`--segment`  
Filter for sequences with specific segment(s) (e.g. 'HA', 'NA'). Can be a single segment name or a list of segment names. Any matching segment will keep the sequence.  
Command line: `--segment HA` or `--segment HA,NA,PB1` (comma-separated, no spaces)  
Python: `segment="HA"` or `segment=["HA", "NA", "PB1"]`

`--annotated`  
'true' or 'false'. Filter for sequences that have been annotated with gene/protein information.  
Command line: `--annotated true` to fetch only that have been annotated with gene/protein information, or `--annotated false` to exclude them.  
Python: `annotated=True` or `annotated=False` (`annotated=None` for no filter).

`--lab_passaged`  
'true' or 'false'. Filter for or against lab-passaged samples.   
Command line: `--lab_passaged true` to fetch only lab-passaged samples, or `--lab_passaged false` to exclude them.  
Python: `lab_passaged=True` or `lab_passaged=False` (`lab_passaged=None` for no filter).

`--vaccine_strain`  
Filter for or against vaccine strain sequences.  
Command line: `--vaccine_strain true` to fetch only vaccine strains, or `--vaccine_strain false` to exclude them.  
Python: `vaccine_strain=True` or `vaccine_strain=False` (`vaccine_strain=None` for no filter).

`--provirus`  
Filter for or against proviral/integrated sequences.  
Command line: `--provirus true` to fetch only proviral sequences, or `--provirus false` to exclude them.  
Python: `provirus=True` or `provirus=False` (`provirus=None` for no filter).  
**Note:** Using this filter automatically enables GenBank metadata retrieval (`-g`).


_Date filters_  

`--min_collection_date`  
Filter by minimum sample collection date (YYYY-MM-DD).

`--max_collection_date`  
Filter by maximum sample collection date (YYYY-MM-DD).

`--min_release_date`  
Filter by minimum sequence release date (YYYY-MM-DD).

`--max_release_date`  
Filter by maximum sequence release date (YYYY-MM-DD).

_Location & Submitter filters_

`--geographic_location`  
Filter by geographic location of sample collection (e.g., 'USA', 'Asia').

`--submitter_name`  
Filter by submitter author name. Can be a single name or a list of names. Any matching name will keep the sequence.  
Command line: `--submitter_name "John Doe"` or `--submitter_name "John Doe,Jane Smith"` (comma-separated)  
Python: `submitter_name="John Doe"` or `submitter_name=["John Doe", "Jane Smith"]`

`--submitter_institution`  
Filter by submitter institution. Can be a single institution or a list of institutions. Any matching institution will keep the sequence.  
Command line: `--submitter_institution CDC` or `--submitter_institution CDC,NIH,WHO` (comma-separated, no spaces)  
Python: `submitter_institution="CDC"` or `submitter_institution=["CDC", "NIH", "WHO"]`

`--submitter_country`  
Filter by the country of the sequence submitter. Can be a single country or a list of countries.  
Command line: `--submitter_country USA` or `--submitter_country USA,Germany,Japan` (comma-separated, no spaces)  
Python: `submitter_country="USA"` or `submitter_country=["USA", "Germany", "Japan"]`

`--source_database`  
Filter by source database. One of: 'genbank' or 'refseq'.

_Sample & Isolate filters_

`--isolate`  
Filter by isolate name (e.g. 'Wuhan-hu-1'). Can be a single isolate name or a list of isolate names. Any matching isolate will keep the sequence.  
Command line: `--isolate Wuhan-hu-1` or `--isolate Wuhan-hu-1,LASV_3609` (comma-separated, no spaces)  
Python: `isolate="Wuhan-hu-1"` or `isolate=["Wuhan-hu-1", "LASV_3609"]`

`--isolation_source`  
Filter by isolation source (tissue/specimen/source) (e.g. 'blood', 'serum'). Can be a single source or a list of sources. Any matching source will keep the sequence.  
Command line: `--isolation_source blood` or `--isolation_source blood,serum,plasma` (comma-separated, no spaces)  
Python: `isolation_source="blood"` or `isolation_source=["blood", "serum", "plasma"]`

`--env_source`  
Filter by environmental source (e.g. 'water', 'sewage'). Excludes any sequences with named hosts. Do NOT combine with `--host` filter. Can be a single source or a list of sources. Any matching source will keep the sequence.  
Command line: `--env_source water` or `--env_source water,soil,air` (comma-separated, no spaces)  
Python: `env_source="water"` or `env_source=["water", "soil", "air"]`  
**Note:** Using this filter automatically enables GenBank metadata retrieval (`-g`).

_Virus Classification filters_

`--genotype`  
Filter by genotype (e.g. 'H5N1', 'H3N2'). Can be a single genotype or a list of genotypes. Any matching genotype will keep the sequence.  
Command line: `--genotype H5N1` or `--genotype H5N1,H3N2` (comma-separated, no spaces)  
Python: `genotype="H5N1"` or `genotype=["H5N1", "H3N2"]`  
**Note:** Using this filter automatically enables GenBank metadata retrieval (`-g`).

`--gen_mol_type`  
Filter by genomic molecule type (e.g. 'dsDNA', 'RNA'). Can be a single type or a list of types. Any matching molecule type will keep the sequence.  
Command line: `--gen_mol_type dsDNA` or `--gen_mol_type RNA,dsRNA` (comma-separated, no spaces)  
Python: `gen_mol_type="dsDNA"` or `gen_mol_type=["RNA", "dsRNA"]`  
**Note:** Using this filter automatically enables GenBank metadata retrieval (`-g`).

_SARS-CoV-2 specific filters_

`--lineage`  
Filter by SARS-CoV-2 Pango lineage (e.g. 'B.1.1.7', 'P.1'). Can be a single lineage or a list of lineages. Any matching lineage will keep the sequence.  
Command line: `--lineage B.1.1.7` or `--lineage B.1.1.7,P.1` (comma-separated, no spaces)  
Python: `lineage="B.1.1.7"` or `lineage=["B.1.1.7", "P.1"]`

_Workflow configurations_

`--genbank_batch_size`  
Batch size for GenBank metadata API requests. Default: 200. Larger batches are faster but may be more prone to timeouts.  

`-o` `--out`  
Path to the folder where results will be saved. Default: `./gget_virus_output/{virus}_{timestamp}/` in the current working directory.  
Python: `outfolder="path/to/folder"`

`--baseline`  
Path to a baseline metadata file (CSV, JSONL, JSON, or text) containing accessions to skip. Only new accessions not found in the baseline will be downloaded. Useful for incremental updates or resuming after API failures.  
CSV files must have an 'accession' column. Text files should have one accession per line.  
Python: `baseline_metadata="path/to/previous_metadata.csv"`

`--merge-results`  
When using `--baseline`, merge new results with the baseline into a single combined output file. This is the default behavior.  
Python: `merge_results=True` (default)

`--no-merge`  
When using `--baseline`, output new results separately from baseline instead of merging. Creates `{virus}_new.csv` (new sequences only) and preserves baseline as a reference.  
Python: `merge_results=False`

**Flags**  
`-a` `--is_accession`  
Flag to indicate that the `virus` positional argument is an accession number, a space-separated list of accessions, or a path to a text file containing accession numbers (one per line).  

`--download_all_accessions`   
Use this flag when applying filters without searching for a specific virus (leave `virus` argument empty).     
⚠️ **WARNING**: If you do not specify additional filters, this flag downloads ALL available viral sequences from NCBI (entire Viruses taxonomy, taxon ID 10239). This is an extremely large dataset that can take many hours to download and require significant disk space. Use with caution and ensure you have adequate storage and bandwidth. When this flag is set, the `virus` argument is ignored.

`--is_sars_cov2`  
Use NCBI's optimized cached data packages for a SARS-CoV-2 query. This provides faster and more reliable downloads. The system can auto-detect SARS-CoV-2 taxon-name queries, but for accession-based queries, you must set this flag explicitly.

`--is_alphainfluenza`  
Use NCBI's optimized cached data packages for an Alphainfluenza (Influenza A virus) query. This provides faster and more reliable downloads for large Influenza A datasets. The system can auto-detect Alphainfluenza taxon-name queries, but for accession-based queries, you must set this flag explicitly.

`-g` `--genbank_metadata`  
Fetch and save additional detailed metadata from GenBank, including collection dates, host details, and publication references, in a separate `{virus}_genbank_metadata.csv` file (plus full XML/CSV dumps).  
**Note:** This flag is automatically enabled when using any of the following GenBank-dependent filters: `--has_proteins`, `--gen_mol_type`, `--env_source`, `--genotype`, `--provirus`, `--min_gene_count`, `--max_gene_count`, `--min_mature_peptide_count`, `--max_mature_peptide_count`.

`--proteins_complete`  
Flag to only include sequences where all annotated proteins are complete.  

`-kt` `--keep_temp`  
Flag to keep all intermediate/temporary files generated during processing. By default, only final output files are retained.

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed. 

### Example

```bash
gget virus "Zika virus" --nuc_completeness complete --host human --out zika_data
```

```python
# Python
import gget

gget.virus(
  "Zika virus",
  nuc_completeness="complete",
  host="human",
  outfolder="zika_data"
)
```

→ Downloads complete Zika virus genomes from human hosts. Results are saved in the `zika_data` folder as `Zika_virus_sequences.fasta`, `Zika_virus_metadata.csv`, `Zika_virus_metadata.jsonl`, and `command_summary.txt`.


<br><br>
**Download a specific SARS-CoV-2 reference genome using its accession number:**

```bash
gget virus NC_045512.2 --is_accession --is_sars_cov2
```

```python
# Python
import gget

gget.virus("NC_045512.2", is_accession=True, is_sars_cov2=True)
```

→ Uses the optimized download method for SARS-CoV-2 to fetch the reference genome and its metadata.

<br><br>
**Download SARS-CoV-2 sequences with cached optimization AND GenBank metadata:**

```bash
gget virus "SARS-CoV-2" --host human --nuc_completeness complete --min_seq_length 29000 --genbank_metadata
```

```python
# Python
import gget

gget.virus(
  "SARS-CoV-2", 
  host="human", 
  nuc_completeness="complete",
  min_seq_length=29000,
  genbank_metadata=True,
  is_sars_cov2=True,
  outfolder="covid_data"
)
```

→ Uses cached download for speed (via NCBI's SARS-CoV-2 data packages when available), applies the sequence length filter post-download, and fetches detailed GenBank metadata for all filtered sequences.

<br><br>
**Download Influenza A virus sequences with optimized caching and post-download filtering:**

```bash
gget virus "Influenza A virus" --host human --nuc_completeness complete --max_seq_length 15000 --genbank_metadata --is_alphainfluenza
```

```python
# Python
import gget

gget.virus(
  "Influenza A virus", 
  host="human", 
  nuc_completeness="complete",
  max_seq_length=15000,
  genbank_metadata=True,
  is_alphainfluenza=True,
  outfolder="influenza_a_data"
)
```

→ Uses NCBI's cached data packages for Alphainfluenza to download complete Influenza A genomes from human hosts much faster than the standard API method, then applies the sequence length filter and fetches GenBank metadata.

<br><br>
**Resume a failed download using baseline deduplication:**

```bash
gget virus "SARS-CoV-2" --host human --nuc_completeness complete --baseline previous_run/SARS_CoV_2_metadata.csv --merge-results -o covid_update
```

```python
# Python
import gget

gget.virus(
  "SARS-CoV-2",
  host="human",
  nuc_completeness="complete",
  baseline_metadata="previous_run/SARS_CoV_2_metadata.csv",
  merge_results=True,
  outfolder="covid_update"
)
```

→ Loads accessions from a previous run's metadata file, skips those already downloaded, and merges new results with the baseline into a single combined output.

---

### Output files

`gget virus` saves results in the specified output folder (default: `./gget_virus_output/{virus}_{timestamp}/`). The standard output files are:

| File | Description |
|------|-------------|
| `{virus}_sequences.fasta` | Nucleotide sequences in FASTA format |
| `{virus}_metadata.csv` | Metadata for all sequences in CSV format |
| `{virus}_metadata.jsonl` | Metadata in JSONL format (one JSON object per line) |
| `{virus}_genbank_metadata.csv` | Detailed GenBank metadata (only when `-g` is used or auto-enabled) |
| `{virus}_genbank_metadata_full.xml` | Full GenBank XML dump (only when `-g` is used) |
| `{virus}_genbank_metadata_full.csv` | Full GenBank CSV dump - readable XML format (only when `-g` is used) |
| `command_summary.txt` | Execution summary with statistics, output files, and any errors |

### Command summary file

Every `gget virus` run generates a `command_summary.txt` file in the output folder, providing a complete record of the execution, including the exact command used, dataset statistics, output files with sizes, and details of any errors or failed operations. This is useful for reproducibility, debugging, and manual recovery after partial failures.

**Example `command_summary.txt` for a successful run:**

```
GGET VIRUS COMMAND SUMMARY

Execution Date: 2026-03-15 14:30:22
Output Folder: /home/user/zika_data

--------------------------------------------------------------------------------
SOFTWARE VERSIONS
--------------------------------------------------------------------------------
gget version: 0.28.10
NCBI datasets version: 16.40.2

--------------------------------------------------------------------------------
COMMAND LINE
--------------------------------------------------------------------------------
gget virus "Zika virus" --nuc_completeness complete --host human --out zika_data

--------------------------------------------------------------------------------
EXECUTION STATUS
--------------------------------------------------------------------------------
✅ Command completed successfully

--------------------------------------------------------------------------------
RUNTIME
--------------------------------------------------------------------------------
Total wall-clock time: 4m 12s (252.3 seconds)

--------------------------------------------------------------------------------
MEMORY USAGE
--------------------------------------------------------------------------------
Process RSS (resident memory): 512.4 MB
Process VMS (virtual memory): 1024.8 MB
Process memory percent: 3.2%
System total memory: 16384 MB
System available memory: 12288 MB
System memory used: 25.0%

--------------------------------------------------------------------------------
SEQUENCE STATISTICS
--------------------------------------------------------------------------------
Total records from API: 1523
After metadata filtering: 1523
Final sequences (after all filters): 1523

--------------------------------------------------------------------------------
FILTER BREAKDOWN BY STAGE
--------------------------------------------------------------------------------

No records were filtered out at any stage.

--------------------------------------------------------------------------------
DETAILED STATISTICS
--------------------------------------------------------------------------------
Unique hosts: 1
  - Homo sapiens

Unique geographic locations: 42
  - Brazil
  - Colombia
  - ...

Sequence length range: 10217 - 10839 bp
Average sequence length: 10708 bp

Completeness breakdown:
  - complete: 1523

Source database breakdown:
  - GenBank: 1510
  - RefSeq: 13

--------------------------------------------------------------------------------
OUTPUT FILES
--------------------------------------------------------------------------------
FASTA Sequences: Zika_virus_sequences.fasta (16.02 MB)
CSV Metadata: Zika_virus_metadata.csv (1.85 MB)
JSONL Metadata: Zika_virus_metadata.jsonl (3.41 MB)

END OF SUMMARY
```

<br>

**Example `command_summary.txt` after an API server error:**

```
GGET VIRUS COMMAND SUMMARY

Execution Date: 2026-03-19 21:03:22
Output Folder: /home/user/11632_20260319_210251

--------------------------------------------------------------------------------
COMMAND LINE
--------------------------------------------------------------------------------
gget virus 11632 --nuc_completeness complete --geographic_location Gabon --host human

--------------------------------------------------------------------------------
EXECUTION STATUS
--------------------------------------------------------------------------------
✗ Command failed
Error: HTTP error while fetching virus metadata: 500 Server Error: Internal Server
Error for url: https://api.ncbi.nlm.nih.gov/datasets/v2/virus/taxon/11632/dataset_report
?filter.complete_only=true&filter.host=human&filter.geo_location=Gabon&page_size=1000

🔧 SERVER ERROR DETECTED: NCBI's API is experiencing temporary server-side issues.
This is not a problem with your query.
Try again in a few minutes, or consider using more specific filters to reduce the dataset size.

--------------------------------------------------------------------------------
SEQUENCE STATISTICS
--------------------------------------------------------------------------------
Total records from API: 0
After metadata filtering: 0
Final sequences (after all filters): 0

--------------------------------------------------------------------------------
OUTPUT FILES
--------------------------------------------------------------------------------
No output files generated

END OF SUMMARY
```

<br>

**Example `command_summary.txt` with failed metadata batches and recovery instructions:**

```
GGET VIRUS COMMAND SUMMARY

Execution Date: 2026-04-01 10:15:33
Output Folder: /home/user/hiv_data

--------------------------------------------------------------------------------
COMMAND LINE
--------------------------------------------------------------------------------
gget virus "HIV-1" --host human --nuc_completeness complete

--------------------------------------------------------------------------------
EXECUTION STATUS
--------------------------------------------------------------------------------
✗ Command failed
Error: HTTP error while fetching virus metadata after 15 retries

--------------------------------------------------------------------------------
SEQUENCE STATISTICS
--------------------------------------------------------------------------------
Total records from API: 8500
After metadata filtering: 0
Final sequences (after all filters): 0

--------------------------------------------------------------------------------
💾 PARTIAL METADATA RECOVERY
--------------------------------------------------------------------------------
Partial metadata saved: /home/user/hiv_data/HIV_1_partial_metadata_api_failure.jsonl

Recovery command:
  gget virus HIV-1 --baseline /home/user/hiv_data/HIV_1_partial_metadata_api_failure.jsonl --merge-results -o /home/user/hiv_data

--------------------------------------------------------------------------------
⚠️ FAILED OPERATIONS - MANUAL RETRY REQUIRED
--------------------------------------------------------------------------------

📍 FAILED METADATA BATCHES (2 batches):

   Batch 3: 1000 accessions
   Error: 500 Server Error: Internal Server Error
   API URL: https://api.ncbi.nlm.nih.gov/datasets/v2/virus/taxon/11676/dataset_report?...

   Batch 7: 1000 accessions
   Error: ConnectionError: Connection reset by peer
   API URL: https://api.ncbi.nlm.nih.gov/datasets/v2/virus/taxon/11676/dataset_report?...

📍 PAGINATION TIMEOUTS (1 pages):
   Page 5: 4000 records retrieved
   Error: ReadTimeout: HTTPSConnectionPool read timed out

💡 RECOVERY INSTRUCTIONS:
   1. Copy the URL from above and paste it into your browser
   2. Save the downloaded file manually
   3. Retry the command with updated filters (e.g., stricter date ranges)
   4. If the issue persists, NCBI servers may be temporarily unavailable

   5. RESUME with baseline deduplication:
      gget virus HIV-1 --baseline /home/user/hiv_data/HIV_1_partial_metadata_api_failure.jsonl --merge-results -o /home/user/hiv_data

--------------------------------------------------------------------------------
OUTPUT FILES
--------------------------------------------------------------------------------
No output files generated

END OF SUMMARY
```

<br>

**Example `command_summary.txt` completed with GenBank warnings and failed sequence batches:**

```
GGET VIRUS COMMAND SUMMARY

Execution Date: 2026-03-20 08:45:11
Output Folder: /home/user/ebola_data

--------------------------------------------------------------------------------
COMMAND LINE
--------------------------------------------------------------------------------
gget virus "Ebola virus" --host human --genbank_metadata --out ebola_data

--------------------------------------------------------------------------------
EXECUTION STATUS
--------------------------------------------------------------------------------
Command completed with warnings
⚠️ GenBank metadata retrieval failed: Connection timed out after 5 retries

--------------------------------------------------------------------------------
RUNTIME
--------------------------------------------------------------------------------
Total wall-clock time: 12m 45s (765.2 seconds)

--------------------------------------------------------------------------------
MEMORY USAGE
--------------------------------------------------------------------------------
Process RSS (resident memory): 1024.5 MB
Process VMS (virtual memory): 2048.3 MB
Process memory percent: 6.3%
System total memory: 16384 MB
System available memory: 10240 MB
System memory used: 37.5%

--------------------------------------------------------------------------------
SEQUENCE STATISTICS
--------------------------------------------------------------------------------
Total records from API: 2150
After metadata filtering: 2150
After GenBank metadata filtering: 2130
Final sequences (after all filters): 2130

--------------------------------------------------------------------------------
FILTER BREAKDOWN BY STAGE
--------------------------------------------------------------------------------

GenBank metadata filtering (records excluded):
  genbank_fetch_failed: 20

--------------------------------------------------------------------------------
⚠️ FAILED OPERATIONS - MANUAL RETRY AVAILABLE
--------------------------------------------------------------------------------

📍 FAILED SEQUENCE DOWNLOAD BATCHES (1 batches):

   Batch 4
   Error: 503 Service Unavailable
   Retry URL: https://api.ncbi.nlm.nih.gov/datasets/v2/virus/genome/download?accessions=...

📍 SEQUENCE FETCH FAILURES (1 operations):

   Operation: batch_sequence_download
   Accessions: 20
   Error: ReadTimeout: HTTPSConnectionPool read timed out
   Retry URL: https://api.ncbi.nlm.nih.gov/datasets/v2/virus/genome/download?accessions=...

💡 RECOVERY INSTRUCTIONS:
   1. Copy the URL from above and paste it into your browser
   2. Save the downloaded file manually
   3. Retry the command with updated filters (e.g., stricter date ranges)
   4. If the issue persists, NCBI servers may be temporarily unavailable

--------------------------------------------------------------------------------
OUTPUT FILES
--------------------------------------------------------------------------------
FASTA Sequences: Ebola_virus_sequences.fasta (24.31 MB)
CSV Metadata: Ebola_virus_metadata.csv (2.10 MB)
JSONL Metadata: Ebola_virus_metadata.jsonl (4.56 MB)

END OF SUMMARY
```

The summary file tracks the following failure types, each with actionable details (error messages, URLs for manual retry, recovery commands):

- **API Timeout** — The NCBI API timed out during the initial metadata fetch.
- **Empty API Response** — The API returned no results for the given query.
- **Failed Metadata Batches** — One or more paginated API requests for metadata failed after retries.
- **Pagination Timeouts/Errors** — Specific pages of results timed out or returned errors during pagination.
- **Failed Sequence Download Batches** — One or more batches of sequence downloads (FASTA) failed.
- **Sequence Fetch Failures** — Individual sequence download operations failed.
- **GenBank Metadata Errors** — GenBank metadata retrieval failed (command still completes with a warning).
- **Partial Metadata Recovery** — When the API fails mid-download, partial metadata is saved to a JSONL file with a recovery command to resume using `--baseline`.


#### [More examples](https://github.com/pachterlab/gget_examples/tree/main/gget_virus)

# References

If you use `gget virus` in a publication, please cite the following articles:

  - Nasri, F., Gurev, S., Varilly, P., Ramesh, K., O’Leary, N. A., Cool, J., Renard, B. Y., Sabeti, P. C., & Luebbert, L. (2026). Deterministic access to global viral sequence data enables robust agentic scientific discovery. [arXiv:2606.06749](https://arxiv.org/abs/2606.06749)

  - Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

  - O’Leary, N.A., Cox, E., Holmes, J.B. et al (2024). Exploring and retrieving sequence and metadata for species across the tree of life with NCBI Datasets. Sci Data 11, 732. [https://doi.org/10.1038/s41597-024-03571-y](https://doi.org/10.1038/s41597-024-03571-y)


