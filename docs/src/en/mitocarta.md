[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/mitocarta.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget mitocarta 🫀
Fetch the [MitoCarta3.0](https://www.broadinstitute.org/mitocarta/) inventory of mammalian mitochondrial proteins and pathways from the Broad Institute.  
Return format: JSON (command-line) or data frame (Python).  

MitoCarta3.0 is a curated inventory of genes encoding proteins with strong support of mitochondrial localization, annotated with sub-mitochondrial localization and pathway membership.

The returned table is *tidy* (analysis-ready) rather than the raw Excel: delimited columns — `Synonyms` and `MitoCarta3.0_MitoPathways`, plus the pathways table's `Genes` — are split into lists, which become nested arrays in JSON output.

> `gget mitocarta` needs the optional `xlrd` dependency to read MitoCarta's `.xls` file. Install it with `pip install gget[mitocarta]`.

**Optional arguments**  
`-s` `--species`  
Species to fetch: `human` (default) or `mouse`.  

`-w` `--which`  
Which table to return. Default: `mitocarta`.  
`mitocarta` - The MitoCarta3.0 inventory of mitochondrial genes (one row per mitochondrial gene, with sub-mitochondrial localization, MitoPathways, evidence, and scores).  
`all_genes` - All genes scored for mitochondrial localization (Maestro scores), not only the mitochondrial ones.  
`pathways`  - The MitoPathways hierarchy and the list of genes in each pathway.  

`-o` `--out`  
Path to the file the results will be saved in, e.g. path/to/directory/results.json (or .csv). Default: Standard out.  
Python: `save=True` will save the output in the current working directory.  

**Flags**  
`-csv` `--csv`  
Command-line only. Returns results in CSV format instead of JSON.  
Python: Use `json=True` to return a list of dictionaries instead of a data frame.  

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.  


### Examples

**Fetch the human MitoCarta3.0 mitochondrial gene inventory:**  
```bash
gget mitocarta --species human --csv
```
```python
# Python
import gget
gget.mitocarta(species="human", which="mitocarta")
```
&rarr; Returns the ~1,100 human mitochondrial genes and their MitoCarta3.0 annotations (sub-mitochondrial localization, MitoPathways, evidence, scores).

| HumanGeneID | Symbol | Description    | MitoCarta3.0_List | MitoCarta3.0_SubMitoLocalization | MitoCarta3.0_MitoPathways               |
|-------------|--------|----------------|-------------------|----------------------------------|-----------------------------------------|
| 1537        | CYC1   | cytochrome c1  | 1                 | MIM                              | OXPHOS > Complex&nbsp;III&nbsp;assembly |
| 6390        | SDHB   | ...            | 1                 | MIM                              | OXPHOS, Metabolism                      |

<br/><br/>

**Fetch the MitoPathways hierarchy and their genes:**  
```bash
gget mitocarta --which pathways --csv
```
```python
# Python
gget.mitocarta(which="pathways")
```
&rarr; Returns the MitoPathways and the genes assigned to each pathway.

<br/><br/>

**JSON output.** The command line returns JSON by default (use `--csv` for CSV; in Python use `json=True` for a list of dictionaries). List columns are emitted as arrays:
```json
[
  {
    "MitoPathway": "Mitochondrial central dogma",
    "MitoPathways Hierarchy": "Mitochondrial central dogma",
    "Genes": ["AARS2", "ALKBH1", "ANGEL2", "APEX1", "..."]
  }
]
```

# References
If you use `gget mitocarta` in a publication, please cite the following article:  

- Rath S, Sharma R, Gupta R, et al. MitoCarta3.0: an updated mitochondrial proteome now with sub-organelle localization and pathway annotations. Nucleic Acids Res. 2021 Jan 8;49(D1):D1541-D1547. doi: [10.1093/nar/gkaa1011](https://doi.org/10.1093/nar/gkaa1011). PMID: 33174596; PMCID: PMC7779016.
