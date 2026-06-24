[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/rummageo.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python.  The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget rummageo 🧬
Find gene sets from Gene Expression Omnibus (GEO) studies that overlap a query gene set using [RummaGEO](https://rummageo.com/).  
RummaGEO automatically computed differential-expression gene sets ("signatures") from hundreds of thousands of human and mouse GEO studies. `gget rummageo` submits your gene list and returns the gene sets with the most significant overlap (Fisher's exact test).  
Return format: JSON (command-line) or data frame/CSV (Python).

**Positional argument**  
`genes`  
One or more gene symbols, e.g. `STAT1 IRF1 OAS1`.

**Optional arguments**  
`-l` `--limit`  
Maximum number of enriched gene sets to return. Default: 50.  

`-ft` `--filter_term`  
Only return gene sets whose term contains this (case-insensitive) substring. Default: None.  

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
gget rummageo STAT1 STAT2 IRF1 IRF9 OAS1 MX1 ISG15 IFIT1 IFIT3 GBP1
```
```python
# Python
gget.rummageo(["STAT1", "STAT2", "IRF1", "IRF9", "OAS1", "MX1", "ISG15", "IFIT1", "IFIT3", "GBP1"])
```
&rarr; Returns the GEO-derived gene sets with the most significant overlap with the query genes, ranked by p-value.

| rank | term | species | n_overlap | n_genes_in_set | odds_ratio | pval | adj_pval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | GSE223635-8-vs-6-human up | human | 10 | 112 | 555.7 | 2.4e-28 | 4.1e-23 |
| . . . | . . . | . . . | . . . | . . . | . . . | . . . | . . . |

# References
If you use `gget rummageo` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Marino, G. B., et al. (2024). RummaGEO: Automatic Mining of Human and Mouse Gene Sets from GEO. Patterns. [https://doi.org/10.1016/j.patter.2024.101072](https://doi.org/10.1016/j.patter.2024.101072)
