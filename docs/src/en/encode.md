[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/encode.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python.  The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget encode 🧫
Query and download data from the [ENCODE project](https://www.encodeproject.org/).  
`gget encode` has two modes, chosen automatically from the input:
- If the input is an ENCODE **accession** (e.g. `ENCSR000AKS` for an experiment or `ENCFF000BXK` for a file), the matching object is fetched and its file(s) are returned (with download URLs). Use `--download` to fetch the files.
- Otherwise, the input is used as a **free-text search** against the ENCODE search endpoint and the matching objects of the given `--type` are returned.

Return format: JSON (command-line) or data frame/CSV (Python).

**Positional argument**  
`search_term`  
ENCODE accession (e.g. `ENCSR000AKS` or `ENCFF000BXK`) or a free-text search term.

**Optional arguments**  
`-t` `--type`  
ENCODE object type for free-text searches, e.g. `Experiment`, `File`, `Biosample`. Default: `Experiment`.  

`-l` `--limit`  
Maximum number of results for free-text searches. Default: 10.  

`-a` `--assembly`  
Only return files for this genome assembly, e.g. `GRCh38`. Default: None.  

`-ff` `--file_format`  
Only return files of this format, e.g. `bam`, `fastq`, `bigWig`. Default: None.  

`-ot` `--output_type`  
Only return files of this output type, e.g. `alignments`. Default: None.  

`-od` `--out_dir`  
Directory to download files into (used with `--download`). Default: current directory.  

`-o` `--out`  
Path to the file the results table will be saved in, e.g. path/to/directory/results.csv (or .json). Default: Standard out.  
Python: `save=True` will save the output in the current working directory.

**Flags**  
`-d` `--download`  
Download the returned files into the directory given by `--out_dir`. Only supported for ENCODE accessions (experiments/files).  

`-csv` `--csv`  
Command-line only. Returns results in CSV format.  
Python: Use `json=True` to return output in JSON format.

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.  

### Examples
**Search for experiments:**
```bash
gget encode "CTCF K562"
```
```python
# Python
gget.encode("CTCF K562")
```
&rarr; Returns a table of ENCODE experiments matching the search term.

| accession | assay_title | biosample_summary | target | description | status | lab |
| --- | --- | --- | --- | --- | --- | --- |
| ENCSR... | TF ChIP-seq | Homo sapiens K562 | CTCF | ... | released | ... |

<br/><br/>
**List the files of an experiment (filtered to GRCh38 BAMs):**
```bash
gget encode ENCSR000AKS --assembly GRCh38 --file_format bam
```
```python
# Python
gget.encode("ENCSR000AKS", assembly="GRCh38", file_format="bam")
```
&rarr; Returns a table of files (with download URLs) for the experiment.

| file_accession | file_format | output_type | assembly | file_size | status | url |
| --- | --- | --- | --- | --- | --- | --- |
| ENCFF... | bam | alignments | GRCh38 | 123456 | released | https://www.encodeproject.org/files/ENCFF.../@@download/ENCFF....bam |

<br/><br/>
**Download the files into a directory:**
```bash
gget encode ENCSR000AKS --file_format bam --download --out_dir ./encode_data
```
```python
# Python
gget.encode("ENCSR000AKS", file_format="bam", download=True, out_dir="./encode_data")
```
&rarr; Downloads the matching files into `./encode_data`.

# References
If you use `gget encode` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- ENCODE Project Consortium. (2012). An integrated encyclopedia of DNA elements in the human genome. Nature. [https://doi.org/10.1038/nature11247](https://doi.org/10.1038/nature11247)
