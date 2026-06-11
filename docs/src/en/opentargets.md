[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/opentargets.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget opentargets 🎯
Fetch associated diseases or drugs from [OpenTargets](https://platform.opentargets.org/) using Ensembl IDs.  
Return format: JSON/CSV (command-line) or data frame (Python).  

This module was written by [Sam Wagenaar](https://github.com/techno-sam).  

**Positional argument**  
`ens_id`  
Ensembl gene ID, e.g ENSG00000169194.

**Optional arguments**  
`-r` `--resource`  
Defines the type of information to return in the output. Default: 'diseases'.  
Possible resources are:

| Resource           | Return Value                                                      | Valid Filters                                     | Sources                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
|--------------------|-------------------------------------------------------------------|---------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `diseases`         | Associated diseases                                               | None                                              | Various:<ul><li>[Open&nbsp;Targets](https://genetics.opentargets.org/)</li><li>[ChEMBL](https://www.ebi.ac.uk/chembl/)</li><li>[Europe&nbsp;PMC](http://europepmc.org/)</li></ul>etc.                                                                                                                                                                                                                                                                                                              |
| `drugs`            | Associated drugs                                                  | `disease_id`                                      | [ChEMBL](https://www.ebi.ac.uk/chembl/)                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `tractability`     | Tractability data                                                 | None                                              | [Open&nbsp;Targets](https://platform-docs.opentargets.org/target/tractability)                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `pharmacogenetics` | Pharmacogenetic responses                                         | `drug_id`                                         | [PharmGKB](https://www.pharmgkb.org/)                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `expression`       | Gene expression data (by tissues, organs, and anatomical systems) | `tissue_id`<br/>`anatomical_system`<br/>`organ`   | <ul><li>[ExpressionAtlas](https://www.ebi.ac.uk/gxa/home)</li><li>[HPA](https://www.proteinatlas.org/)</li><li>[GTEx](https://www.gtexportal.org/home/)</li></ul>                                                                                                                                                                                                                                                                                                                                  |
| `depmap`           | DepMap gene&rarr;disease-effect data.                             | `tissue_id`                                       | [DepMap&nbsp;Portal](https://depmap.org/portal/)                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `interactions`     | Protein&rlarr;protein interactions                                | `protein_a_id`<br/>`protein_b_id`<br/>`gene_b_id` | <ul><li>[Open&nbsp;Targets](https://platform-docs.opentargets.org/target/molecular-interactions)</li><li>[IntAct](https://platform-docs.opentargets.org/target/molecular-interactions#intact)</li><li>[Signor](https://platform-docs.opentargets.org/target/molecular-interactions#signor)</li><li>[Reactome](https://platform-docs.opentargets.org/target/molecular-interactions#reactome)</li><li>[String](https://platform-docs.opentargets.org/target/molecular-interactions#string)</li></ul> |

`-l` `--limit`  
Limit the number of results, e.g 10. Default: No limit.  
Note: Not compatible with the `tractability` and `depmap` resources.

`-o` `--out`  
Path to the JSON file the results will be saved in, e.g. path/to/directory/results.json. Default: Standard out.  
Python: `save=True` will save the output in the current working directory.

`--filters`  
Filter results by exact equality using returned OpenTargets column names. Pass multiple filters by repeating the flag, e.g. '--filter disease.id=EFO_0000274 --filter drug.id=CHEMBL1743081'. Nested fields use dot notation, matching the column names returned by the API.

**Flags**  
`-csv` `--csv`  
Command-line only. Returns the output in CSV format, instead of JSON format.
Python: Use `json=True` to return output in JSON format.

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.

`-or` `--or`  
Command-line only. Filters are combined with OR logic. Default: AND logic.

`wrap_text`  
Python only. `wrap_text=True` displays data frame with wrapped text for easy reading (default: False).  


### Examples

**Get associated diseases for a specific gene:**  
```bash
gget opentargets ENSG00000169194 -r diseases -l 1
```
```python
# Python
import gget
gget.opentargets('ENSG00000169194', resource='diseases', limit=1)
```
&rarr; Returns the top disease associated with the gene ENSG00000169194.

| id            | name               | description                                                           | score            |
|---------------|--------------------|-----------------------------------------------------------------------|------------------|
| EFO_0000274   | atopic&nbsp;eczema | A chronic inflammatory genetically determined disease of the skin ... | 0.66364347241831 |

<br/><br/>

**Get associated drugs for a specific gene:**  
```bash
gget opentargets ENSG00000169194 -r drugs -l 2
```
```python
# Python
import gget
gget.opentargets('ENSG00000169194', resource='drugs', limit=2)
```

&rarr; Returns the top 2 drugs associated with the gene ENSG00000169194.

| id            | name         | type     | action_mechanism                    | description                                                  | synonyms                                           | trade_names           | disease_id  | disease_name                  | trial_phase | trial_status | trial_ids     | approved |
|---------------|--------------|----------|-------------------------------------|--------------------------------------------------------------|----------------------------------------------------|-----------------------|-------------|-------------------------------|-------------|--------------|---------------|----------|
| CHEMBL1743081 | TRALOKINUMAB | Antibody | Interleukin&#8209;13&nbsp;inhibitor | Antibody drug with a maximum clinical trial phase of IV ...  | ['CAT-354', 'Tralokinumab']                        | ['Adbry', 'Adtralza'] | EFO_0000274 | atopic&nbsp;eczema            | 4           |              | []            | True     |
| CHEMBL4297864 | CENDAKIMAB   | Antibody | Interleukin&#8209;13&nbsp;inhibitor | Antibody drug with a maximum clinical trial phase of III ... | [ABT-308, Abt-308, CC-93538, Cendakimab, RPC-4046] | []                    | EFO_0004232 | eosinophilic&nbsp;esophagitis | 3           | Recruiting   | [NCT04991935] | False    |

*Note: Returned `trial_ids` are [ClinicalTrials.gov](https://clinicaltrials.gov) identifiers*

<br/><br/>

**Get tractability data for a specific gene:**  
```bash
gget opentargets ENSG00000169194 -r tractability
```
```python
# Python
import gget
gget.opentargets('ENSG00000169194', resource='tractability')
```

&rarr; Returns tractability data for the gene ENSG00000169194.

| label                 | modality       |
|-----------------------|----------------|
| High-Quality Pocket   | Small molecule |
| Approved Drug         | Antibody       |
| GO CC high conf       | Antibody       |
| UniProt loc med conf  | Antibody       |
| UniProt SigP or TMHMM | Antibody       |

<br/><br/>

**Get pharmacogenetic responses for a specific gene:**
```bash
gget opentargets ENSG00000169194 -r pharmacogenetics -l 1
```
```python
# Python
import gget
gget.opentargets('ENSG00000169194', resource='pharmacogenetics', limit=1)
```

&rarr; Returns pharmacogenetic responses for the gene ENSG00000169194.

| rs_id     | genotype_id       | genotype | variant_consequence_id | variant_consequence_label | drugs                                                                                                                                   | phenotype                                                               | genotype_annotation                                                                                          | response_category | direct_target | evidence_level | source   | literature |
|-----------|-------------------|----------|------------------------|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|-------------------|---------------|----------------|----------|------------|
| rs1295686 | 5_132660151_T_T,T | TT       | SO:0002073             | no_sequence_alteration    | &nbsp;&nbsp;&nbsp;&nbsp;id&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;name<br/>0&nbsp;&nbsp;None&nbsp;&nbsp;hepatitis&nbsp;vaccines | increased risk for non&#8209;immune response to the hepatitis B vaccine | Patients with the TT genotype may be at increased risk for non-immune response to the hepatitis B vaccine... | efficacy          | False         | 3              | pharmgkb | [21111021] |

*Note: Returned `literature` ids are [Europe PMC](https://europepmc.org/article/med/) identifiers*

<br/><br/>

**Get tissues where a gene is most expressed:**
```bash
gget opentargets ENSG00000169194 -r expression -l 2
```
```python
# Python
import gget
gget.opentargets('ENSG00000169194', resource='expression', limit=2)
```

&rarr; Returns the top 2 tissues where the gene ENSG00000169194 is most expressed.

| tissue_id      | tissue_name                           | rna_zscore | rna_value | rna_unit | rna_level | anatomical_systems                                                   | organs                                                 |
|----------------|---------------------------------------|------------|-----------|----------|-----------|----------------------------------------------------------------------|--------------------------------------------------------|
| UBERON_0000473 | testis                                | 5          | 1026      |          | 3         | [reproductive&nbsp;system]                                           | [reproductive&nbsp;organ, reproductive&nbsp;structure] |
| CL_0000542     | EBV&#8209;transformed&nbsp;lymphocyte | 1          | 54        |          | 2         | [hemolymphoid&nbsp;system, immune&nbsp;system, lymphoid&nbsp;system] | [immune organ]                                         |

<br/><br/>

**Get DepMap gene-disease effect data for a specific gene:**
```bash
gget opentargets ENSG00000169194 -r depmap
```
```python
# Python
import gget
gget.opentargets('ENSG00000169194', resource='depmap')
```

&rarr; Returns DepMap gene-disease effect data for the gene ENSG00000169194.

| depmap_id        | expression | effect   | tissue_id      | tissue_name | cell_line_name | disease_cell_line_id | disease_name         | mutation |
|------------------|------------|----------|----------------|-------------|----------------|----------------------|----------------------|----------|
| ACH&#8209;001532 | 0.176323   | 0.054950 | UBERON_0002113 | kidney      | JMU-RTK-2      | None                 | Rhabdoid&nbsp;Cancer | None     |

<br/><br/>

**Get protein-protein interactions for a specific gene:**
```bash
gget opentargets ENSG00000169194 -r interactions -l 2
```
```python
# Python
import gget
gget.opentargets('ENSG00000169194', resource='interactions', limit=2)
```

&rarr; Returns the top 2 protein-protein interactions for the gene ENSG00000169194.

| evidence_score | evidence_count | source_db | protein_a_id    | gene_a_id       | gene_a_symbol | role_a                | taxon_a | protein_b_id    | gene_b_id       | gene_b_symbol | role_b                | taxon_b |
|----------------|----------------|-----------|-----------------|-----------------|---------------|-----------------------|---------|-----------------|-----------------|---------------|-----------------------|---------|
| 0.999          | 3              | string    | ENSP00000304915 | ENSG00000169194 | IL13          | unspecified&nbsp;role | 9606    | ENSP00000379111 | ENSG00000077238 | IL4R          | unspecified&nbsp;role | 9606    |
| 0.999          | 3              | string    | ENSP00000304915 | ENSG00000169194 | IL13          | unspecified&nbsp;role | 9606    | ENSP00000360730 | ENSG00000131724 | IL13RA1       | unspecified&nbsp;role | 9606    |

<br/><br/>

**Get protein-protein interactions for a specific gene, filtering by protein and gene IDs:**
```bash
gget opentargets ENSG00000169194 -r interactions -fpa P35225 --filter_gene_b ENSG00000077238
```
```python
# Python
import gget
gget.opentargets('ENSG00000169194', resource='interactions', filters={'protein_a_id': 'P35225', 'gene_b_id': 'ENSG00000077238'})
```

&rarr; Returns protein-protein interactions for the gene ENSG00000169194, where the first protein is P35225 **and** the second gene is ENSG00000077238.

| evidence_score | evidence_count | source_db | protein_a_id | gene_a_id       | gene_a_symbol | role_a                | taxon_a | protein_b_id | gene_b_id       | gene_b_symbol | role_b                | taxon_b |
|----------------|----------------|-----------|--------------|-----------------|---------------|-----------------------|---------|--------------|-----------------|---------------|-----------------------|---------|
| None           | 3              | reactome  | P35225       | ENSG00000169194 | IL13          | unspecified&nbsp;role | 9606    | P24394       | ENSG00000077238 | IL4R          | unspecified&nbsp;role | 9606    |
| None           | 2              | signor    | P35225       | ENSG00000169194 | IL13          | regulator             | 9606    | P24394       | ENSG00000077238 | IL4R          | regulator&nbsp;target | 9606    |

<br/><br/>

**Get protein-protein interactions for a specific gene, filtering by protein or gene IDs:**
```bash
gget opentargets ENSG00000169194 -r interactions -fpa P35225 --filter_gene_b ENSG00000077238 ENSG00000111537 --or -l 5
```
```python
# Python
import gget
gget.opentargets(
    'ENSG00000169194',
    resource='interactions',
    filters={'protein_a_id': 'P35225', 'gene_b_id': ['ENSG00000077238', 'ENSG00000111537']},
    filter_mode='or',
    limit=5
)
```

&rarr; Returns protein-protein interactions for the gene ENSG00000169194, where the first protein is P35225 **or** the second gene is either ENSG00000077238 or ENSG00000111537.

| evidence_score | evidence_count | source_db | protein_a_id    | gene_a_id       | gene_a_symbol | role_a                | taxon_a | protein_b_id    | gene_b_id       | gene_b_symbol | role_b                | taxon_b |
|----------------|----------------|-----------|-----------------|-----------------|---------------|-----------------------|---------|-----------------|-----------------|---------------|-----------------------|---------|
| 0.999          | 3              | string    | ENSP00000304915 | ENSG00000169194 | IL13          | unspecified&nbsp;role | 9606    | ENSP00000379111 | ENSG00000077238 | IL4R          | unspecified&nbsp;role | 9606    |
| 0.961          | 2              | string    | ENSP00000304915 | ENSG00000169194 | IL13          | unspecified&nbsp;role | 9606    | ENSP00000229135 | ENSG00000111537 | IFNG          | unspecified&nbsp;role | 9606    |
| 0.800          | 9              | intact    | P35225          | ENSG00000169194 | IL13          | unspecified&nbsp;role | 9606    | Q14627          | ENSG00000123496 | IL13RA2       | unspecified&nbsp;role | 9606    |
| 0.740          | 6              | intact    | P35225          | ENSG00000169194 | IL13          | unspecified&nbsp;role | 9606    | P78552          | ENSG00000131724 | IL13RA1       | unspecified&nbsp;role | 9606    |
| 0.400          | 1              | intact    | P35225          | ENSG00000169194 | IL13          | unspecified&nbsp;role | 9606    | Q86XT9          | ENSG00000149932 | TMEM219       | stimulator            | 9606    |



#### [More examples](https://github.com/pachterlab/gget_examples)

# References
If you use `gget opentargets` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Ochoa D, Hercules A, Carmona M, Suveges D, Baker J, Malangone C, Lopez I, Miranda A, Cruz-Castillo C, Fumis L, Bernal-Llinares M, Tsukanov K, Cornu H, Tsirigos K, Razuvayevskaya O, Buniello A, Schwartzentruber J, Karim M, Ariano B, Martinez Osorio RE, Ferrer J, Ge X, Machlitt-Northen S, Gonzalez-Uriarte A, Saha S, Tirunagari S, Mehta C, Roldán-Romero JM, Horswell S, Young S, Ghoussaini M, Hulcoop DG, Dunham I, McDonagh EM. The next-generation Open Targets Platform: reimagined, redesigned, rebuilt. Nucleic Acids Res. 2023 Jan 6;51(D1):D1353-D1359. doi: [10.1093/nar/gkac1046](https://doi.org/10.1093/nar/gkac1046). PMID: 36399499; PMCID: PMC9825572.
