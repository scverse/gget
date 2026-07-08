[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/ucsc.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python.  The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget ucsc 🔎
Fetch [UCSC Genome Browser](https://genome.ucsc.edu/) IDs for a gene or term, similar to `gget search` for Ensembl.  
`gget ucsc` searches the UCSC Genome Browser for a gene symbol, accession, or free-text term and returns the matching identifiers (e.g. UCSC known gene / transcript IDs) together with their genomic positions, grouped by the track they come from.  
Return format: JSON (command-line) or data frame/CSV (Python).

**Positional argument**  
`search_term`  
Gene symbol, accession, or free-text term to search for, e.g. `BRCA2`.

**Optional arguments**  
`-g` `--genome`  
UCSC genome assembly to search, e.g. `hg38`, `hg19`, `mm39`. Default: `hg38`.  

`-t` `--track`  
Only return matches from tracks whose name contains this (case-insensitive) substring, e.g. `knownGene`. Default: None.  

`-l` `--limit`  
Maximum number of matches to return. Default: None (all matches).  

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

### Example
```bash
gget ucsc BRCA2 --genome hg38 --track knownGene
```
```python
# Python
gget.ucsc("BRCA2", genome="hg38", track="knownGene")
```
&rarr; Returns the UCSC IDs matching the search term, with their genomic positions.

| track | ucsc_id | chrom | start | end | name | description |
| --- | --- | --- | --- | --- | --- | --- |
| knownGene | ENST00000380152.8 | chr13 | 32315508 | 32400268 | BRCA2 (ENST00000380152.8) | breast cancer type 2 susceptibility protein |
| . . . | . . . | . . . | . . . | . . . | . . . | . . . |

A UCSC ID (e.g. a known gene `ucsc_id`) can be inspected on the UCSC gene page, e.g. `https://genome.ucsc.edu/cgi-bin/hgGene?hgg_gene={ucsc_id}&db=hg38`.

# References
If you use `gget ucsc` in a publication, please cite the following articles:  

- Kent WJ, Sugnet CW, Furey TS, et al. (2002). The human genome browser at UCSC. Genome Research. [https://doi.org/10.1101/gr.229102](https://doi.org/10.1101/gr.229102)

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)
