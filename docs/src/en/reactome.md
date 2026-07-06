[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/reactome.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget reactome 🔬
Query the [Reactome](https://reactome.org/) pathway knowledgebase using its [ContentService REST API](https://reactome.org/dev/content-service).  
Return format: JSON/CSV (command-line) or data frame (Python).

`gget reactome` supports several kinds of queries, selected with the `resource` argument:
- `pathways` (default): return the Reactome pathways a given identifier (e.g. a UniProt accession) participates in.
- `search`: full-text search of the Reactome knowledgebase (pathways, reactions, physical entities, ...).
- `entity`: return details for a Reactome stable ID (e.g. `R-HSA-6804754`).
- `interactors`: return the molecular interactors of an identifier (IntAct static interactors).
- `orthology`: project a Reactome stable ID to its ortholog in another species (requires `--species`).
- `event-hierarchy`: return the full pathway/reaction hierarchy for a species.

**Positional argument**  
`query`  
Identifier, search term or species to query. Its meaning depends on `resource`:
- `resource="pathways"`: an identifier, e.g. UniProt accession `P04637`.
- `resource="search"`: a free-text search term, e.g. `TP53`.
- `resource="entity"`: a Reactome stable ID, e.g. `R-HSA-6804754`.
- `resource="interactors"`: a molecule accession, e.g. UniProt `P04637`.
- `resource="orthology"`: a Reactome stable ID to project, e.g. `R-HSA-6804754`.
- `resource="event-hierarchy"`: a species name or NCBI taxonomy ID, e.g. `Homo sapiens`.

**Optional arguments**  
`-r` `--resource`  
Type of query to perform. Options: `pathways` (default), `search`, `entity`, `interactors`, `orthology`, `event-hierarchy`.  

`-s` `--source`  
Identifier resource/database for `resource="pathways"`, e.g. `UniProt` (default), `Ensembl`, `ChEBI`, `NCBI`.  

`-sp` `--species`  
Species, as a name (e.g. `Homo sapiens`) or NCBI taxonomy ID (e.g. `9606`). Filters `resource="pathways"` and `resource="search"`; is the **required target** for `resource="orthology"`. Default: None.  

`-t` `--types`  
Restrict `resource="search"` results to one or more entry types, e.g. `Pathway`, `Reaction`, `Protein`. Default: None (all types).  

`-o` `--out`  
Path to the file the results will be saved in, e.g. path/to/directory/results.json. Default: Standard out.

**Flags**  
`-csv` `--csv`  
Command-line only. Returns the output in CSV format, instead of JSON format.  
Python: Use `json=True` to return output in JSON format.

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.


### Examples

**Get the Reactome pathways a protein participates in**

```bash
gget reactome P04637 --species "Homo sapiens"
```

```python
import gget
gget.reactome("P04637", species="Homo sapiens")
```

&rarr; Returns the Reactome pathways the UniProt protein P04637 (human TP53) participates in.

| stable_id     | name                                                 | species      | schema_class | in_disease |
|---------------|------------------------------------------------------|--------------|--------------|------------|
| R-HSA-111448  | Activation of NOXA and translocation to mitochondria | Homo sapiens | Pathway      | False      |
| R-HSA-139915  | Activation of PUMA and translocation to mitochondria | Homo sapiens | Pathway      | False      |
| ...           | ...                                                  | ...          | ...          | ...        |

<br/><br/>

**Search the Reactome knowledgebase**

```bash
gget reactome TP53 -r search -t Pathway -sp "Homo sapiens"
```
```python
import gget
gget.reactome("TP53", resource="search", types="Pathway", species="Homo sapiens")
```

&rarr; Returns Reactome pathways matching the search term "TP53".

| stable_id     | name                          | type    | species      | reactome_id   |
|---------------|-------------------------------|---------|--------------|---------------|
| R-HSA-6804754 | Regulation of TP53 Expression | Pathway | Homo sapiens | R-HSA-6804754 |
| R-HSA-5633007 | Regulation of TP53 Activity   | Pathway | Homo sapiens | R-HSA-5633007 |
| ...           | ...                           | ...     | ...          | ...           |

<br/><br/>

**Get details for a Reactome entry by stable ID**

```bash
gget reactome R-HSA-6804754 -r entity
```
```python
import gget
gget.reactome("R-HSA-6804754", resource="entity")
```

&rarr; Returns details for the Reactome entry R-HSA-6804754.

| stable_id     | name                          | schema_class | species      | in_disease | summation        |
|---------------|-------------------------------|--------------|--------------|------------|------------------|
| R-HSA-6804754 | Regulation of TP53 Expression | Pathway      | Homo sapiens | False      | Transcription... |

<br/><br/>

**Get the molecular interactors of a protein**

```bash
gget reactome P04637 -r interactors
```
```python
gget.reactome("P04637", resource="interactors")
```

&rarr; Returns the IntAct interactors of P04637 (columns: `interactor_acc`, `interactor_name`, `score`, `evidences`), e.g. MDM2, with an interaction confidence score.

<br/><br/>

**Project a pathway to another species (orthology)**

```bash
gget reactome R-HSA-6804754 -r orthology -sp "Mus musculus"
```
```python
gget.reactome("R-HSA-6804754", resource="orthology", species="Mus musculus")
```

&rarr; Returns the mouse ortholog of the human pathway (`R-MMU-6804754`, "Regulation of TP53 Expression", Mus musculus).

<br/><br/>

**Get the full event (pathway/reaction) hierarchy for a species**

```bash
gget reactome "Homo sapiens" -r event-hierarchy
```
```python
gget.reactome("Homo sapiens", resource="event-hierarchy")
```

&rarr; Returns the entire human event hierarchy flattened to one row per event (columns: `stable_id`, `name`, `type`, `species`, `parent_id`, `level`). This is a large table — use `parent_id`/`level` to navigate the tree.

> The returned DataFrame's `.attrs["reactome_release"]` records the Reactome release version (e.g. `97`) for reproducibility.


# References
If you use `gget reactome` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Marc Gillespie, Bijay Jassal, Ralf Stephan, Marija Milacic, Karen Rothfels, Andrea Senff-Ribeiro, Johannes Griss, Cristoffer Sevilla, Lisa Matthews, Chuqiao Gong, Chuan Deng, Thawfeek Varusai, Eliot Ragueneau, Yusra Haider, Bruce May, Veronica Shamovsky, Joel Weiser, Timothy Brunson, Nasim Sanati, Liam Beckman, Xiang Shao, Antonio Fabregat, Konstantinos Sidiropoulos, Julieth Murillo, Guilherme Viteri, Justin Cook, Solomon Shorser, Gary Bader, Emek Demir, Chris Sander, Robin Haw, Guanming Wu, Lincoln Stein, Henning Hermjakob, Peter D'Eustachio (2022). The reactome pathway knowledgebase 2022. Nucleic Acids Research, Volume 50, Issue D1, 7 January 2022, Pages D687–D692, [https://doi.org/10.1093/nar/gkab1028](https://doi.org/10.1093/nar/gkab1028)
