[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/g2p.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python.  The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget g2p 🧬➜🧪
Query the [Genomics 2 Proteins (G2P) portal](https://g2p.broadinstitute.org/) to link genes/proteins to residue-level structural and functional annotations (e.g. AlphaFold pLDDT, UniProt sites, predicted pockets, PTMs), the gene–transcript–protein–isoform–structure map, and isoform alignments.  

Returns: A data frame with the requested G2P information.  

This module was written by [Elarwei](https://github.com/Elarwei001).

**Positional argument**  
`gene`  
Gene symbol, e.g. BRCA1.  

**Other required arguments**  
`-u` `--uniprot_id`  
UniProt accession, e.g. P38398. For `--resource alignment` this is the canonical isoform (e.g. P01130-1).  
Tip: find a gene's UniProt ID with [`gget info`](info.md).  

**Optional arguments**  
`-r` `--resource`  
Defines the type of information to return (default: 'features'):  
`features`: Per-residue protein feature table (AlphaFold pLDDT, UniProt sites, secondary structure, predicted pockets, PTMs, etc.).  
`map`: Gene → transcript → protein isoform → structure map (UniProt/Ensembl/RefSeq/PDB identifiers).  
`alignment`: Residue-level sequence alignment between two isoforms (requires `--isoform`; `--uniprot_id` is the canonical isoform).  

`-i` `--isoform`  
Alternative isoform UniProt accession (e.g. P01130-2). Required when `--resource alignment`. Default: None.  

`-o` `--out`  
Path to the file the results will be saved in, e.g. path/to/directory/results.json. Default: Standard out.  
Python: `save=True` will save the output in the current working directory.  

**Flags**  
`-csv` `--csv`  
Command-line only. Returns results in CSV format instead of JSON.  
Python: Use `json=False` (default) to return a data frame.  

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.  

### Examples
```bash
# Per-residue protein features for BRCA1 (AlphaFold pLDDT, UniProt sites, ...)
gget g2p BRCA1 -u P38398
```
```python
# Python
gget.g2p("BRCA1", uniprot_id="P38398", resource="features")
```
&rarr; Returns a data frame with one row per residue of the BRCA1 protein (UniProt P38398) and its structural/functional annotations.  

<br/><br/>

```bash
# Gene -> transcript -> isoform -> structure map (CSV)
gget g2p BRCA1 -u P38398 -r map --csv
```
```python
# Python
gget.g2p("BRCA1", uniprot_id="P38398", resource="map")
```
&rarr; Returns the mapping of BRCA1 to its UniProt isoforms, Ensembl/RefSeq identifiers, and PDB structures.  

<br/><br/>

```bash
# Residue-level alignment between two LDLR isoforms
gget g2p LDLR -u P01130-1 -r alignment -i P01130-2
```
```python
# Python
gget.g2p("LDLR", uniprot_id="P01130-1", resource="alignment", isoform="P01130-2")
```
&rarr; Returns the residue-level alignment between LDLR isoforms P01130-1 and P01130-2.  

# References
If you use `gget g2p` in a publication, please cite the following articles:

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Kwon, S., Safer, J., Nguyen, D.T., et al. Genomics 2 Proteins portal: a resource and discovery tool for linking genetic screening outputs to protein sequences and structures. Nature Methods (2024). [https://doi.org/10.1038/s41592-024-02409-0](https://doi.org/10.1038/s41592-024-02409-0)
