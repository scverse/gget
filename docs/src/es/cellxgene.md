[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/cellxgene.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Las banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget cellxgene 🍱  
Query data de la base de datos [CZ CELLxGENE Discover](https://cellxgene.cziscience.com/) usando [CZ CELLxGENE Discover Census](https://github.com/chanzuckerberg/cellxgene-census).  
Produce: Un objeto AnnData que contiene la matriz de recuentos de genes y los metadatos de resultados de single cell RNA-seq de los tejidos/genes/etcetera previamente definidos.  

Antes de usar `gget cellxgene` por primera vez, corre `gget setup cellxgene` / `gget.setup("cellxgene")` (ver también [`gget setup`](setup.md)).  

**Parámetros opcionales**  
`-s` `--species`  
'homo_sapiens' o 'mus_musculus'. Por defecto: 'homo_sapiens'.  

`-g` `--gene`  
Str o lista de genes de interés o ID(s) tipo Ensembl. Por defecto: None (ninguno).  
Atención: Utilice la bandera `-e / --ensembl` (Python: `ensembl=True`) cuando ingrese ID(s) tipo Ensembl.  
Atención: ¡Los símbolos de genes distinguen mayúsculas y minúsculas! Usa la capitalización canónica al pasar símbolos de genes; p. ej., ‘PAX7’ (humano), ‘Pax7’ (ratón).  
Ver https://cellxgene.cziscience.com/gene-expression para ejemplos de genes.  

`-cv` `--census_version`  
Versión del CZ CELLxGENE Discover Census (str), p. ej. "2023-05-15", o "latest" (ultima) o "stable" (estable). Por defecto: "stable" (estable).  

`-cn` `--column_names`  
Lista de columnas de metadatos a obtener (almacenadas en AnnData.obs).  
Por defecto: ['dataset_id', 'assay', 'suspension_type', 'sex', 'tissue_general', 'tissue', 'cell_type']  
Para más opciones, ver: https://api.cellxgene.cziscience.com/curation/ui/#/ -> 'Schemas' -> 'dataset'  

`-o` `--out`  
Ruta al archivo para guardar el objeto AnnData formato .h5ad (o .csv con bandera `-mo / --meta_only`).  
¡Requerido cuando se usa desde Terminal!  

**Banderas**  
`-e` `--ensembl`  
Usa esta bandera si `gene` se ingresa como ID tipo Ensembl.  

`-mo` `--meta_only`  
Solo produce la tabla (Dataframe) con metadatos (corresponde a AnnData.obs).  

`-q` `--quiet`  
Solo para Terminal. Impide la información de progreso de ser exhibida durante la ejecución del programa.  
Para Python, usa `verbose=False` para impedir la información de progreso de ser exhibida durante la ejecución del programa.  

**Parámetros opcionales correspondientes a los atributos de metadatos de CZ CELLxGENE Discover**  
`--tissue`  
Str o lista de tejido(s), p. ej. ['lung', 'blood']. Por defecto: None.  
Ver https://cellxgene.cziscience.com/gene-expression para ejemplos de tejidos.  

`--cell_type`  
Str o lista de tipo(s) de célula(s), p. ej. ['mucus secreting cell', 'neuroendocrine cell']. Por defecto: None.  
Ver https://cellxgene.cziscience.com/gene-expression y seleccione un tejido para ejemplos de tipos de células.  

`--development_stage`  
Str o lista de etapa(s) de desarrollo. Por defecto: None.  

`--disease`  
Str o lista de enfermedad(es). Por defecto: None.  

`--sex`  
Str o lista de sexo(s), p. ej. 'female' (femenina). Por defecto: None.  

`--dataset_id`  
Str o lista de CELLxGENE ID(s). Por defecto: None.  

`--tissue_general_ontology_term_id`  
Str o lista de tejido(s) del tipo high-level UBERON ID. Por defecto: None.  
Tejidos y sus IDs tipo UBERON se enumeran [aquí](https://github.com/chanzuckerberg/single-cell-data-portal/blob/9b94ccb0a2e0a8f6182b213aa4852c491f6f6aff/backend/wmg/data/tissue_mapper.py).  

`--tissue_general`  
Str o lista de tejido(s) del tipo high-level. Por defecto: None.  
Tejidos y sus IDs de UBERON se enumeran [aquí](https://github.com/chanzuckerberg/single-cell-data-portal/blob/9b94ccb0a2e0a8f6182b213aa4852c491f6f6aff/backend/wmg/data/tissue_mapper.py).  

`--tissue_ontology_term_id`  
Str o lista de ID(s) de 'tissue ontology term' como están definidos en el [esquema de datos del CELLxGENE](https://github.com/chanzuckerberg/single-cell-curation/tree/main/schema). Por defecto: None.  

`--assay_ontology_term_id`  
Str o lista de ID(s) de 'assay ontology term' como están definidos en el [esquema de datos del CELLxGENE](https://github.com/chanzuckerberg/single-cell-curation/tree/main/schema). Por defecto: None.  

`--assay`  
Str o lista de 'assays' (métodos) como están definidos en el [esquema de datos del CELLxGENE](https://github.com/chanzuckerberg/single-cell-curation/tree/main/schema). Por defecto: None.  

`--cell_type_ontology_term_id`  
Str o lista de ID(s) de 'celltype ontology term' como están definidos en el [esquema de datos del CELLxGENE](https://github.com/chanzuckerberg/single-cell-curation/tree/main/schema). Por defecto: None.  

`--development_stage_ontology_term_id`  
Str o lista de ID(s) de 'development stage ontology term' como están definidos en el [esquema de datos del CELLxGENE](https://github.com/chanzuckerberg/single-cell-curation/tree/main/schema). Por defecto: None.  

`--disease_ontology_term_id`  
Str o lista de ID(s) de 'disease ontology term' como están definidos en el [esquema de datos del CELLxGENE](https://github.com/chanzuckerberg/single-cell-curation/tree/main/schema). Por defecto: None.  

`--donor_id`  
Str o lista de ID(s) de 'donor' (donador) como están definidos en el [esquema de datos del CELLxGENE](https://github.com/chanzuckerberg/single-cell-curation/tree/main/schema). Por defecto: None.  

`--self_reported_ethnicity_ontology_term_id`  
Str o lista de ID(s) de 'self-reported ethnicity ontology' como están definidos en el [esquema de datos del CELLxGENE](https://github.com/chanzuckerberg/single-cell-curation/tree/main/schema). Por defecto: None.  

`--self_reported_ethnicity`  
Str o lista de etnias autoinformadas como están definidas en el [esquema de datos del CELLxGENE](https://github.com/chanzuckerberg/single-cell-curation/tree/main/schema). Por defecto: None.  

`--sex_ontology_term_id`  
Str o lista de ID(s) de 'sex ontology' como están definidos en el [esquema de datos del CELLxGENE](https://github.com/chanzuckerberg/single-cell-curation/tree/main/schema). Por defecto: None.  

`--suspension_type`  
Str o lista de tipo(s) de suspensión como están definidos en el [esquema de datos del CELLxGENE](https://github.com/chanzuckerberg/single-cell-curation/tree/main/schema). Por defecto: None.  


### Ejemplo
```bash
gget cellxgene --gene ACE2 ABCA1 SLC5A1 --tissue lung --cell_type 'mucus secreting cell' 'neuroendocrine cell' -o example_adata.h5ad
```
```python
# Python
adata = gget.cellxgene(
    gene = ["ACE2", "ABCA1", "SLC5A1"],
    tissue = "lung",
    cell_type = ["mucus secreting cell", "neuroendocrine cell"]
)
adata
```
&rarr; Produce un objeto AnnData que contiene la matriz de recuentos de scRNAseq de los genes ACE2, ABCA1 y SLC5A1 en 3322 células secretoras de mucosidad y neuroendocrinas pulmonares humanas y sus metadatos correspondientes.

<br/><br/>

Obtiene solo los metadatos (corresponde a AnnData.obs):  
```bash
gget cellxgene --meta_only --gene ENSMUSG00000015405 --ensembl --tissue lung --species mus_musculus -o example_meta.csv
```
```python
# Python
df = gget.cellxgene(
    meta_only = True,
    gene = "ENSMUSG00000015405",
    ensembl = True,
    tissue = "lung",  
    species = "mus_musculus"
)
df
```
&rarr; Produce solo los metadatos de los conjuntos de datos de ENSMUSG00000015405 (ACE2), los cuales corresponden a células pulmonares murinas.  

Ver también: [https://chanzuckerberg.github.io/cellxgene-census/notebooks/api_demo/census_gget_demo.html](https://chanzuckerberg.github.io/cellxgene-census/notebooks/api_demo/census_gget_demo.html)

# Citar  
Si utiliza `gget cellxgene` en una publicación, favor de citar los siguientes artículos:

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Chanzuckerberg Initiative. (n.d.). CZ CELLxGENE Discover. Retrieved [insert date here], from [https://cellxgene.cziscience.com/](https://cellxgene.cziscience.com/)
