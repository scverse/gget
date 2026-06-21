[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/bgee.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget bgee 🐝
Fetch orthology and gene expression data from [Bgee](https://www.bgee.org/) using Ensembl IDs.  
Return format: JSON/CSV (command-line) or data frame (Python).

> If you are specifically interested in human gene expression data, consider using [gget opentargets](./opentargets.md) or [gget archs4](./archs4.md) instead.
> **gget bgee** has less data, but supports more species.

This module was written by [Sam Wagenaar](https://github.com/techno-sam) with edits from [Kateřina Večerková](https://github.com/vecerkovakaterina).

**Positional argument**  
`ens_id`  
Ensembl gene ID, e.g. ENSG00000169194 or ENSSSCG00000014725.  
When `type=expression` you can also input a list of multiple Ensembl IDs.  

NOTE: Some of the species in [Bgee](https://www.bgee.org/) are not in Ensembl or Ensembl metazoa, and for those you can use NCBI gene IDs, e.g. 118215821 (a gene in _Anguilla anguilla_).

**Optional arguments**  
`-t` `--type`  
Type of data to fetch. Options: `orthologs` (default), `expression`.  

`-o` `--out`  
Path to the JSON file the results will be saved in, e.g. path/to/directory/results.json. Default: Standard out.

**Flags**  
`-csv` `--csv`  
Command-line only. Returns the output in CSV format, instead of JSON format.  
Python: Use `json=True` to return output in JSON format.

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.


### Examples

**Get orthologs for a gene**

```bash
gget bgee ENSSSCG00000014725
```

```python
import gget
gget.bgee("ENSSSCG00000014725")
```

&rarr; Returns orthologs for the gene with Ensembl ID ENSSSCG00000014725.

| gene_id            | gene_name    | species_id | genus   | species    |
|--------------------|--------------|------------|---------|------------|
| 734881             | hbb1         | 8355       | Xenopus | laevis     |
| ENSFCAG00000038029 | LOC101098159 | 9685       | Felis   | catus      |
| ENSBTAG00000047356 | LOC107131172 | 9913       | Bos     | taurus     |
| ENSOARG00000019163 | LOC101105437 | 9940       | Ovis    | aries      |
| ENSXETG00000025667 | hbg1         | 8364       | Xenopus | tropicalis |
| ...                | ...          | ...        | ...     | ...        |

<br/><br/>

**Get gene expression data for a gene**

```bash
gget bgee ENSSSCG00000014725 -t expression
```
```python
import gget
gget.bgee("ENSSSCG00000014725", type="expression")
```

&rarr; Returns gene expression data for the gene with Ensembl ID ENSSSCG00000014725.

| anat_entity_id | anat_entity_name            | score | score_confidence | expression_state |
|----------------|-----------------------------|-------|------------------|------------------|
| UBERON:0000178 | blood                       | 99.98 | high             | expressed        |
| UBERON:0002106 | spleen                      | 99.96 | high             | expressed        |
| UBERON:0002190 | subcutaneous adipose tissue | 99.70 | high             | expressed        |
| UBERON:0005316 | endocardial endothelium     | 99.61 | high             | expressed        |
| UBERON:0002107 | liver                       | 99.27 | high             | expressed        |
| ...            | ...                         | ...   | ...              | ...              |

<br/><br/>

**Get gene expression data for multiple genes**

```bash
gget bgee ENSBTAG00000047356 ENSBTAG00000018317 -t expression
```
```python
import gget
gget.bgee(["ENSBTAG00000047356", "ENSBTAG00000018317"], type="expression")
```

&rarr; Returns gene expression data for the genes ENSBTAG00000047356 and ENSBTAG00000018317.

| anat_entity_id | anat_entity_name            | score | score_confidence | expression_state |
|----------------|-----------------------------|-------|------------------|------------------|
| UBERON:0001017 | central nervous system      | 92.15 | high             | expressed        |
| UBERON:0002616 | regional part of brain      | 79.01 | high             | expressed        |
| BGEE:0000000   | anatomical entity and cellular component | 89.12 | high| expressed        |
| ...            | ...                         | ...   | ...              | ...              |


#### [More examples](https://github.com/pachterlab/gget_examples)

# References
If you use `gget bgee` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Frederic B Bastian, Julien Roux, Anne Niknejad, Aurélie Comte, Sara S Fonseca Costa, Tarcisio Mendes de Farias, Sébastien Moretti, Gilles Parmentier, Valentine Rech de Laval, Marta Rosikiewicz, Julien Wollbrett, Amina Echchiki, Angélique Escoriza, Walid H Gharib, Mar Gonzales-Porta, Yohan Jarosz, Balazs Laurenczy, Philippe Moret, Emilie Person, Patrick Roelli, Komal Sanjeev, Mathieu Seppey, Marc Robinson-Rechavi (2021). The Bgee suite: integrated curated expression atlas and comparative transcriptomics in animals. Nucleic Acids Research, Volume 49, Issue D1, 8 January 2021, Pages D831–D847, [https://doi.org/10.1093/nar/gkaa793](https://doi.org/10.1093/nar/gkaa793)
