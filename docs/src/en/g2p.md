[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/g2p.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python.  The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget g2p 🧬➜🧪
Query the [Genomics 2 Proteins (G2P) portal](https://g2p.broadinstitute.org/) to link genes/proteins to residue-level structural and functional annotations, the gene–transcript–protein–isoform–structure map, and isoform alignments.

The per-residue feature table is rich (~140 columns), including AlphaFold pLDDT, DSSP secondary structure, accessible surface area, UniProt sites (active/binding/domain/...), PhosphoSitePlus PTMs, fpocket / af2bind / p2rank pocket predictions, intra- and inter-chain hydrogen bonds, non-bonded interactions, disulfide bonds and salt bridges (from PDB and AlphaFold), the PFES (Protein Feature Enrichment Score) sub-scores used by G2P for missense variant interpretation, and per-residue MaveDB experimental functional scores. See the [`g2p-bis` documentation](https://github.com/broadinstitute/g2p-bis) for column descriptions.

> Note: this module wraps the *public* G2P REST API. The variant overlays shown in the portal's web UI (gnomAD, ClinVar, HGMD) are not exposed by the public API and are therefore not available via `gget g2p` — use the portal directly for those.

Returns: A data frame with the requested G2P information, or `None` if the query failed (network error, invalid arguments, or unknown gene/UniProt pair).

This module was written by [Elarwei](https://github.com/Elarwei001).

At least one of `gene` or `--uniprot_id` is required — the other is resolved automatically via the UniProt REST API and cached. When resolution happens, the chosen pair is logged and prepended to the returned data frame as `Resolved Gene` / `Resolved UniProt` columns. Gene-symbol → accession lookup is approximate (it picks the canonical reviewed human Swiss-Prot entry only); for non-human organisms, unreviewed entries, or a specific isoform, pass `--uniprot_id` explicitly.

**Arguments (at least one of `gene` / `--uniprot_id` required)**  
`gene` (positional)  
Gene symbol, e.g. BRCA1. If omitted, resolved from `--uniprot_id`.  

`-u` `--uniprot_id`  
UniProt accession, e.g. P38398. If omitted, resolved from `gene`. For `--resource alignment` this is the canonical isoform (e.g. P01130-1) and is **required** (gene→UniProt lookup returns the base accession and cannot disambiguate isoforms).  
Tip: find a gene's UniProt ID with [`gget info`](info.md).  

**Optional arguments**  
`-r` `--resource`  
Defines the type of information to return (default: 'features'):  
`features`: Per-residue protein feature table (~140 columns: AlphaFold pLDDT, UniProt sites, secondary structure, predicted pockets, PTMs, PFES, MaveDB scores, ...).  
`map`: Gene → transcript → protein isoform → structure map (UniProt/Ensembl/RefSeq/PDB identifiers). The comma-joined `PDB Ids` column is augmented with a parsed `PDB Ids List` column (`list[str]`) for direct consumption (e.g. with [`gget pdb`](pdb.md)).  
`alignment`: Residue-level sequence alignment between two isoforms (requires `--isoform`; `--uniprot_id` is the canonical isoform).  

`-i` `--isoform`  
Alternative isoform UniProt accession (e.g. P01130-2). Required when `--resource alignment`. Default: None.  

`--residues`  
Restrict the result to specific residue positions (applies to `--resource features` / `alignment` only). Command line: comma-separated list and/or inclusive ranges, e.g. `185,1775,1812` or `100-200` or `1-50,185`. Python: `int`, `list[int]`, `range`, or `set[int]`. Default: None (return all residues).

`-o` `--out`  
Path to the file the results will be saved in, e.g. path/to/directory/results.json. Default: Standard out.  
Python: `save=True` will save the output as a CSV in the current working directory; `out="path/to/file.csv"` writes to an explicit path and takes precedence over `save`.

**Flags**  
`-csv` `--csv`  
Command-line only. Returns results in CSV format instead of JSON.  
Python: Use `json=False` (default) to return a data frame.  

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.  

### Examples
```bash
# Per-residue protein features for BRCA1 (AlphaFold pLDDT, UniProt sites, ...).
# The gene symbol is optional — it can be resolved from the UniProt accession.
gget g2p -u P38398
```
```python
# Python
gget.g2p(uniprot_id="P38398", resource="features")
```
&rarr; Returns a data frame with one row per residue of the BRCA1 protein (UniProt P38398) and its structural/functional annotations.  

<br/><br/>

```bash
# Same query, with the gene symbol passed explicitly
gget g2p BRCA1 -u P38398
```
```python
# Python
gget.g2p("BRCA1", uniprot_id="P38398", resource="features")
```

<br/><br/>

```bash
# Symmetric: only the gene symbol — UniProt accession is resolved automatically
# (canonical reviewed human Swiss-Prot entry).
gget g2p BRCA1
```
```python
# Python
gget.g2p("BRCA1")
```
&rarr; Same as above. The resolved `P38398` is logged and added as a `Resolved UniProt` column.

<br/><br/>

```bash
# Score only specific residue positions
gget g2p BRCA1 -u P38398 --residues 185,1775,1812
```
```python
# Python
gget.g2p("BRCA1", uniprot_id="P38398", residues=[185, 1775, 1812])
gget.g2p("BRCA1", uniprot_id="P38398", residues=range(100, 200))
```
&rarr; Returns only the requested residues from the per-residue feature table.

<br/><br/>

```bash
# Gene -> transcript -> isoform -> structure map (CSV)
gget g2p -u P38398 -r map --csv
```
```python
# Python
gget.g2p(uniprot_id="P38398", resource="map")
```
&rarr; Returns the mapping of BRCA1 to its UniProt isoforms, Ensembl/RefSeq identifiers, and PDB structures.  

<br/><br/>

```bash
# Residue-level alignment between two LDLR isoforms
gget g2p -u P01130-1 -r alignment -i P01130-2
```
```python
# Python
gget.g2p(uniprot_id="P01130-1", resource="alignment", isoform="P01130-2")
```
&rarr; Returns the residue-level alignment between LDLR isoforms P01130-1 and P01130-2.  

# References
If you use `gget g2p` in a publication, please cite the following articles:

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Kwon, S., Safer, J., Nguyen, D.T., et al. Genomics 2 Proteins portal: a resource and discovery tool for linking genetic screening outputs to protein sequences and structures. Nature Methods (2024). [https://doi.org/10.1038/s41592-024-02409-0](https://doi.org/10.1038/s41592-024-02409-0)
