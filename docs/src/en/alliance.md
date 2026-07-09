[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/alliance.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python.  The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget alliance 🧬
Query the [Alliance of Genome Resources](https://www.alliancegenome.org/), which integrates data from the major model organism databases (human, mouse, rat, zebrafish, fly, worm, yeast, and more).  
`gget alliance` has two modes, chosen automatically from the input:
- If the input is an Alliance **gene ID** (e.g. `HGNC:1101`, `MGI:109337`, `RGD:2219`, `ZFIN:...`, `FB:...`, `WB:...`, `SGD:...`), the gene's details are returned.
- Otherwise, the input is used as a **free-text search** and the matching objects of the given `--category` are returned.

Return format: JSON (command-line) or data frame/CSV (Python).

**Positional argument**  
`search_term`  
Alliance gene ID (e.g. `HGNC:1101`) or a free-text search term.

**Optional arguments**  
`-c` `--category`  
Category for free-text searches: one of `gene`, `allele`, `disease`, `go`, `variant`, `model`, or `all` for no filter. Default: `gene`.  

`-l` `--limit`  
Maximum number of results for free-text searches. Default: 10.  

`-o` `--out`  
Path to the file the results will be saved in, e.g. path/to/directory/results.csv (or .json). Default: Standard out.  
Python: `save=True` will save the output in the current working directory.

**Flags**  
`-csv` `--csv`  
Command-line only. Returns results in CSV format.  
Python: Use `json=True` to return output in JSON format.

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.  

### Examples
**Search for genes across model organisms:**
```bash
gget alliance brca2
```
```python
# Python
gget.alliance("brca2")
```
&rarr; Returns a table of genes matching the search term across Alliance member databases.

| id | symbol | name | species | category | so_term_name |
| --- | --- | --- | --- | --- | --- |
| HGNC:1101 | BRCA2 | BRCA2 DNA repair associated | Homo sapiens | gene_search_result | protein_coding_gene |
| MGI:109337 | Brca2 | breast cancer 2 | Mus musculus | gene_search_result | protein_coding_gene |

<br/><br/>
**Fetch a single gene by its Alliance ID:**
```bash
gget alliance HGNC:1101
```
```python
# Python
gget.alliance("HGNC:1101")
```
&rarr; Returns the gene's details.

| id | symbol | name | species | taxon | gene_type | synonyms | data_provider |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HGNC:1101 | BRCA2 | BRCA2 DNA repair associated | Homo sapiens | NCBITaxon:9606 | protein_coding_gene | ['FAD', ...] | RGD |

# References
If you use `gget alliance` in a publication, please cite the following articles:  

- Alliance of Genome Resources Consortium. (2024). Updates to the Alliance of Genome Resources central infrastructure. Genetics. [https://doi.org/10.1093/genetics/iyae049](https://doi.org/10.1093/genetics/iyae049)

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)
