[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/opentargets.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget opentargets 🎯
Fetch associated diseases or drugs from [OpenTargets](https://platform.opentargets.org/) using Ensembl IDs.  
Return format: JSON/CSV (command-line) or data frame (Python).  

This module was written by [Sam Wagenaar](https://github.com/techno-sam).  

> ⚠️ **Change as of gget v0.30.8 — `resource="expression"` output is different.** OpenTargets retired the old `target.expressions` field, so `gget opentargets -r expression` now returns OpenTargets' `baselineExpression` data instead. **The output columns changed**: results are now per-biosample (tissue *and/or* cell type) summary statistics (`median`, `min`, `q1`, `q3`, `max`, `unit`) with `tissueBiosample.*` / `celltypeBiosample.*` identifiers and `datasourceId` / `datatypeId` — replacing the old per-tissue `tissue.*` / `rna.*` (z-score) columns, which no longer exist upstream. A gene can have thousands of biosamples; use `--filters` (e.g. `datasourceId`, `datatypeId`) or `--limit` to narrow the result. See the baseline expression example below.

**Positional argument**  
`ens_id`  
Ensembl gene ID, e.g ENSG00000169194.

**Optional arguments**  
`-r` `--resource`  
Defines the type of information to return in the output. Default: 'diseases'.  
Possible resources are:

| Resource           | Return Value                                                      | Valid Filters                                     | Sources                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
|--------------------|-------------------------------------------------------------------|---------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `diseases`         | Associated diseases, phenotypes & traits (EFO-mapped) with the overall association `score` (0–1) | None                                              | Various:<ul><li>[Open&nbsp;Targets](https://genetics.opentargets.org/)</li><li>[ChEMBL](https://www.ebi.ac.uk/chembl/)</li><li>[Europe&nbsp;PMC](http://europepmc.org/)</li></ul>etc.                                                                                                                                                                                                                                                                                                              |
| `drugs`            | Associated drugs                                                  | `drug.drugType`<br/>`drug.maximumClinicalStage`   | [ChEMBL](https://www.ebi.ac.uk/chembl/)                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `tractability`     | Tractability data                                                 | None                                              | [Open&nbsp;Targets](https://platform-docs.opentargets.org/target/tractability)                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `pharmacogenetics` | Pharmacogenetic responses                                         | `datasourceId`<br/>`pgxCategory`<br/>`evidenceLevel` | [PharmGKB](https://www.pharmgkb.org/)                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `expression`       | Baseline expression per biosample (tissue/cell type) with summary statistics | `tissueBiosample.biosampleId`<br/>`datasourceId`<br/>`datatypeId` | <ul><li>[GTEx](https://www.gtexportal.org/home/)</li><li>[ExpressionAtlas](https://www.ebi.ac.uk/gxa/home)</li><li>single-cell datasets</li></ul>                                                                                                                                                                                                                                                                                                                                  |
| `depmap`           | DepMap gene&rarr;disease-effect data.                             | `tissueId`<br/>`diseaseFromSource`                | [DepMap&nbsp;Portal](https://depmap.org/portal/)                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `interactions`     | Protein&rlarr;protein interactions                                | `sourceDatabase`<br/>`targetB.id`<br/>`targetB.approvedSymbol` | <ul><li>[Open&nbsp;Targets](https://platform-docs.opentargets.org/target/molecular-interactions)</li><li>[IntAct](https://platform-docs.opentargets.org/target/molecular-interactions#intact)</li><li>[Signor](https://platform-docs.opentargets.org/target/molecular-interactions#signor)</li><li>[Reactome](https://platform-docs.opentargets.org/target/molecular-interactions#reactome)</li><li>[String](https://platform-docs.opentargets.org/target/molecular-interactions#string)</li></ul> |

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

| score              | disease.id     | disease.name       | disease.description                                                      |
|--------------------|----------------|--------------------|-------------------------------------------------------------------------|
| 0.7279798021712002 | MONDO_0004980  | atopic&nbsp;eczema | A common chronic pruritic inflammatory skin disease with a strong ...   |

> **Understanding the `score` column and disease IDs** ([issue #168](https://github.com/scverse/gget/issues/168))
> - `score` is OpenTargets' **overall target–disease association score** — a single value between 0 and 1 that aggregates the evidence across *all* data types and data sources. It is **not** a per-data-source score. The OpenTargets website shows, in addition, a per-data-type breakdown (genetic associations, somatic mutations, known drugs, animal models, etc.) in its "Associations" view; `gget opentargets` currently returns only the aggregated `score`, so a single gget row corresponds to one whole row of that web table.
> - `disease.id` is an [EFO](https://www.ebi.ac.uk/efo/) ontology ID. OpenTargets maps every associated trait to EFO, which imports terms from several ontologies. As a result the returned IDs are **not exclusively diseases**: they can be MONDO disease terms (`MONDO_*`), Human Phenotype Ontology phenotypes (`HP_*`), Orphanet rare diseases (`Orphanet_*`), or EFO measurements/traits (`EFO_*`, e.g. biomarker or blood-measurement traits). `gget opentargets` returns the associations **exactly as OpenTargets reports them**, without dropping non-disease terms. To keep only MONDO disease terms, filter the returned data frame, e.g. `df[df["disease.id"].str.startswith("MONDO")]`.

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

| drug.id       | drug.name    | drug.drugType | drug.mechanismsOfAction.rows        | drug.description                                              | drug.synonyms                          | drug.tradeNames | drug.maximumClinicalStage | drug.indications.rows                                                            |
|---------------|--------------|---------------|-------------------------------------|--------------------------------------------------------------|----------------------------------------|-----------------|---------------------------|---------------------------------------------------------------------------------|
| CHEMBL1743035 | LEBRIKIZUMAB | Antibody      | Interleukin&#8209;13&nbsp;inhibitor | Antibody drug with a maximum clinical stage of Approval ...  | ['Lebrikizumab', 'MILR-1444A', ...]    | Ebglyss         | APPROVAL                  | [{'id': 'MONDO_0004980', 'name': 'atopic eczema'}, {'id': 'MONDO_0004979', 'name': 'asthma'}, ...] |
| CHEMBL1742985 | ANRUKINZUMAB | Antibody      | Interleukin&#8209;13&nbsp;inhibitor | Antibody drug with a maximum clinical stage of Phase 2 ...   | ['Anrukinzumab', 'IMA-638']            | []              | PHASE2                    | [{'id': 'MONDO_0005101', 'name': 'ulcerative colitis'}, ...]                    |

*Note: associated diseases/indications are nested under `drug.indications.rows` (each a `{'id', 'name'}` dict); the `drug.id` values are [ChEMBL](https://www.ebi.ac.uk/chembl/) identifiers.*

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

| modality | label               | value |
|----------|---------------------|-------|
| SM       | Approved Drug       | False |
| SM       | High-Quality Pocket | True  |
| AB       | Approved Drug       | True  |
| AB       | Advanced Clinical   | False |

*Note: `modality` is `SM` (small molecule), `AB` (antibody), `PR` (PROTAC), `OC` (other clinical), etc.; `value` is a boolean indicating whether the target meets that tractability bucket.*

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

| variantId       | genotypeId         | genotype | drugs                                       | phenotypeText                              | genotypeAnnotationText                    | pgxCategory | isDirectTarget | evidenceLevel | datasourceId | literature | variantFunctionalConsequence.id | variantFunctionalConsequence.label |
|-----------------|--------------------|----------|---------------------------------------------|--------------------------------------------|-------------------------------------------|-------------|----------------|---------------|--------------|------------|---------------------------------|------------------------------------|
| 5_132657117_C_T | 5_132657117_C_C,T  | CT       | {'id': 'CHEMBL535', 'name': 'SUNITINIB'}    | decreased severity of drug-induced toxicity | Patients with renal cell carcinoma and ... | toxicity    | False          | 3             | clinpgx      | 26387812   | SO:0001631                      | upstream_gene_variant              |

*Note: `drugs` is a `{'id', 'name'}` dict (or list of them); `literature` ids are [Europe PMC](https://europepmc.org/article/med/) identifiers.*

<br/><br/>

**Get baseline expression of a gene across biosamples (tissues / cell types):**
```bash
gget opentargets ENSG00000169194 -r expression -l 2
```
```python
# Python
import gget
gget.opentargets('ENSG00000169194', resource='expression', limit=2)
```

&rarr; Returns baseline expression summary statistics for the gene ENSG00000169194 per biosample.

| median   | min | q1       | q3       | max     | unit                        | datasourceId   | datatypeId    | tissueBiosample.biosampleId | tissueBiosample.biosampleName | celltypeBiosample.biosampleId | celltypeBiosample.biosampleName |
|----------|-----|----------|----------|---------|-----------------------------|----------------|---------------|-----------------------------|-------------------------------|-------------------------------|---------------------------------|
| 0.066891 | 0   | 0.028268 | 0.142208 | 1.69407 | TPM                         | gtex           | bulk&nbsp;rna-seq | UBERON_0000007              | pituitary&nbsp;gland          | None                          | None                            |
| 0.0      | 0   | 0.0      | 0.0      | 0.0     | CPM(pseudobulk&nbsp;sum)    | tabula_sapiens | scrna-seq     | UBERON_0000016              | endocrine&nbsp;pancreas       | CL_0000115                    | endothelial&nbsp;cell           |

*Note: bulk sources (e.g. GTEx) populate only `tissueBiosample.*` (`celltypeBiosample.*` is `None`); single-cell sources (e.g. Tabula Sapiens) populate both.*

> **Note (OpenTargets API change):** OpenTargets retired the per-tissue `target.expressions` field (it now returns nothing) and moved baseline expression to the paginated `target.baselineExpression` field. `gget opentargets -r expression` now returns per-biosample expression summary statistics (`median`, `min`, `q1`, `q3`, `max`) from the current sources (e.g. GTEx bulk RNA-seq and single-cell datasets), with `tissueBiosample`/`celltypeBiosample` identifiers and `datasourceId`/`datatypeId` so results can be filtered. The returned columns therefore differ from earlier gget versions. A gene can have thousands of biosamples; OpenTargets returns at most 3000 per request, so for genes that exceed this a warning is logged and you should narrow the query with `--filters` (e.g. `datasourceId` or `datatypeId`). Use `--limit` to fetch fewer rows.

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

| tissueId       | tissueName | cellLineName | expression  | diseaseFromSource     | depmapId    | geneEffect  |
|----------------|------------|--------------|-------------|-----------------------|-------------|-------------|
| UBERON_0000977 | pleura     | NCI-H2452    | 0.0223550275 | Pleural&nbsp;Mesothelioma | ACH-000092  | 0.0368397422 |

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

| score | count | sourceDatabase | intA            | intABiologicalRole    | intB            | intBBiologicalRole    | targetA.id      | targetA.approvedSymbol | speciesA.taxonId | targetB.id      | targetB.approvedSymbol | speciesB.taxonId |
|-------|-------|----------------|-----------------|-----------------------|-----------------|-----------------------|-----------------|------------------------|------------------|-----------------|------------------------|------------------|
| 0.999 | 3     | string         | ENSP00000304915 | unspecified&nbsp;role | ENSP00000360730 | unspecified&nbsp;role | ENSG00000169194 | IL13                   | 134              | ENSG00000131724 | IL13RA1                | 134              |
| 0.999 | 3     | string         | ENSP00000304915 | unspecified&nbsp;role | ENSP00000361004 | unspecified&nbsp;role | ENSG00000169194 | IL13                   | 134              | ENSG00000123496 | IL13RA2                | 134              |

<br/><br/>

**Get protein-protein interactions for a specific gene, filtered by column values:**

Filters use the generic `--filter key=value` flag (CLI) / `filters={...}` argument (Python), where the keys are the exact returned column names. Multiple filters are combined with **AND** (exact equality). (The previous `filter_mode`/OR option and the `-fpa`/`--filter_gene_b` shortcuts were removed in v0.30.5.)
```bash
gget opentargets ENSG00000169194 -r interactions --filter sourceDatabase=string --filter targetB.approvedSymbol=IL13RA1
```
```python
# Python
import gget
gget.opentargets('ENSG00000169194', resource='interactions', filters={'sourceDatabase': 'string', 'targetB.approvedSymbol': 'IL13RA1'})
```

&rarr; Returns the `string`-sourced interactions of IL13 where the partner is IL13RA1.

| score | count | sourceDatabase | intA            | intABiologicalRole    | intB            | intBBiologicalRole    | targetA.id      | targetA.approvedSymbol | speciesA.taxonId | targetB.id      | targetB.approvedSymbol | speciesB.taxonId |
|-------|-------|----------------|-----------------|-----------------------|-----------------|-----------------------|-----------------|------------------------|------------------|-----------------|------------------------|------------------|
| 0.999 | 3     | string         | ENSP00000304915 | unspecified&nbsp;role | ENSP00000360730 | unspecified&nbsp;role | ENSG00000169194 | IL13                   | 134              | ENSG00000131724 | IL13RA1                | 134              |



#### [More examples](https://github.com/pachterlab/gget_examples)

# References
If you use `gget opentargets` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Ochoa D, Hercules A, Carmona M, Suveges D, Baker J, Malangone C, Lopez I, Miranda A, Cruz-Castillo C, Fumis L, Bernal-Llinares M, Tsukanov K, Cornu H, Tsirigos K, Razuvayevskaya O, Buniello A, Schwartzentruber J, Karim M, Ariano B, Martinez Osorio RE, Ferrer J, Ge X, Machlitt-Northen S, Gonzalez-Uriarte A, Saha S, Tirunagari S, Mehta C, Roldán-Romero JM, Horswell S, Young S, Ghoussaini M, Hulcoop DG, Dunham I, McDonagh EM. The next-generation Open Targets Platform: reimagined, redesigned, rebuilt. Nucleic Acids Res. 2023 Jan 6;51(D1):D1353-D1359. doi: [10.1093/nar/gkac1046](https://doi.org/10.1093/nar/gkac1046). PMID: 36399499; PMCID: PMC9825572.
