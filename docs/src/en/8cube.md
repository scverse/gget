[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/8cube.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.
# gget 8cube 🔬

<a href="https://www.biorxiv.org/content/10.1101/2025.04.21.649844">
  <img
    align="right"
    width="500"
    alt="Screenshot 2026-01-19 at 5 34 43 PM"
    src="https://github.com/user-attachments/assets/1fa9b68f-27e3-4f94-a46d-4f2d4df36b11"
  />
</a>

Query [**8cubeDB**](https://eightcubedb.onrender.com/) (snRNA-sequencing data of 8 different mouse strains, tissues, and individuals (four of each sex)) for gene-level specificity metrics and normalized expression values.  

Return format: JSON (command-line) or data frame/CSV (Python).

This module was written by [Nikhila Swarna](https://github.com/nikkiswarna).

<br clear="right" />

---

# gget 8cube specificity 🎯

Retrieve **ψ** and **ζ** specificity statistics for one or more genes.

```
gget 8cube specificity <GENES...>
```

**Positional argument**  
`genes`  
Gene symbols or Ensembl gene IDs. Multiple genes allowed.

**Optional arguments**  
`-csv` `--csv`  
Returns CSV instead of JSON (command-line only).  
Python: Use `json=False` (default DataFrame) or `json=True` for JSON.

`-o` `--out`  
Output file path (CSV or .json depending on `--csv`).  
Python: `save=True` saves automatically to the current directory.

**Flags**  
`-q` `--quiet`  
Suppresses progress information.
Python: use `verbose=False`.

### Example

```bash
gget 8cube specificity Acsm2 ENSMUSG00000046623.9
```

```python
# Python
from gget.gget_8cube import specificity
specificity(["Acsm2", "ENSMUSG00000046623.9"])
```

→ Returns ψ and ζ specificity values for **Acsm2**.

---

# gget 8cube psi_block 🧩

Retrieve **ψ-block** (block-level specificity) values for one or more genes.

```
gget 8cube psi_block <GENES...> --analysis_level <LEVEL> --analysis_type <TYPE>
```

**Positional argument**  
`genes`  
Gene symbols or Ensembl IDs.

**Required arguments**  
`-al` `--analysis_level`  
Biological analysis level (e.g., `Kidney`, `Across_tissues`).

`-at` `--analysis_type`  
Partition type (e.g., `Sex:Celltype`, `Sex:Strain`).

**Optional arguments**  
`-csv` `--csv`  
Return CSV instead of JSON.  
Python: use `json=True` for JSON.

`-o` `--out`  
Output file location.

**Flags**  
`-q` `--quiet`  
Suppress progress printing.

### Example

```bash
gget 8cube psi_block Acsm2 \
    --analysis_level Kidney \
    --analysis_type "Sex:Celltype"
```

```python
# Python
from gget.gget_8cube import psi_block
psi_block(["Acsm2"], analysis_level="Kidney", analysis_type="Sex:Celltype")
```

→ Returns ψ-block partition-level specificity scores for **Acsm2**.

---

# gget 8cube expression 📊

Retrieve **mean and variance of normalized expression values** for one or more genes.

```
gget 8cube expression <GENES...> --analysis_level <LEVEL> --analysis_type <TYPE>
```

**Positional argument**  
`genes`  
Gene symbols or Ensembl IDs. Multiple accepted.

**Required arguments**  
`-al` `--analysis_level`  
Biological grouping (e.g., `Kidney`, `Across_tissues`).

`-at` `--analysis_type`  
Partition layout (e.g., `Sex:Celltype`).

**Optional arguments**  
`-csv` `--csv`  
Return CSV instead of JSON.  
Python: use `json=True`.

`-o` `--out`  
Output file path.

**Flags**  
`-q` `--quiet`  
Suppress progress messages.

### Example

```bash
gget 8cube expression ENSMUSG00000046623.9 \
    --analysis_level Across_tissues \
    --analysis_type Strain
```

```python
# Python
from gget.gget_8cube import gene_expression
gene_expression(["ENSMUSG00000046623.9"], analysis_level="Across_tissues", analysis_type="Strain")
```

→ Returns normalized expression values grouped by cell type and sex.

---

# Example workflow

```bash
# Specificity
gget 8cube specificity Gjb4

# ψ-block specificity
gget 8cube psi_block Gjb4 --analysis_level Across_tissues --analysis_type Strain

# Expression values
gget 8cube expression Gjb4 --analysis_level Across_tissues --analysis_type Strain
```

---

# Python API
```python
from gget.gget_8cube import specificity, psi_block, gene_expression
```
or
```python
from gget import specificity, psi_block, gene_expression
```
---

# Notes

* Works with gene symbols **and** Ensembl IDs (with or without version numbers).
* All three functions accept **multiple genes** at once.
* Default Python output is a **pandas DataFrame**; use `json=True` for JSON.
* CLI defaults to **JSON**, unless `--csv` is used.

---

# References

If you use `gget 8cube` in a publication, please cite:

* **Swarna NP, et al.**
  *Determining gene specificity from multivariate single-cell RNA sequencing data* (2025).
  [https://doi.org/10.1101/2025.11.21.689845](https://doi.org/10.1101/2025.11.21.689845)

* **Luebbert, L., & Pachter, L. (2023).**
  *Efficient querying of genomic reference databases with gget.* Bioinformatics.
  [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

* **Rebboah E, et al.**
  *Systematic cell-type resolved transcriptomes of 8 tissues in 8 lab and wild-derived mouse strains captures global and local expression variation* (2025).
  [https://doi.org/10.1101/2025.04.21.649844](https://doi.org/10.1101/2025.04.21.649844)
