[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/es/alliance.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget alliance 🧬
Consulte la [Alliance of Genome Resources](https://www.alliancegenome.org/), que integra datos de las principales bases de datos de organismos modelo (humano, ratón, rata, pez cebra, mosca, gusano, levadura, y más).  
`gget alliance` tiene dos modos, elegidos automáticamente según la entrada:
- Si la entrada es un **identificador de gen** de Alliance (p. ej. `HGNC:1101`, `MGI:109337`, `RGD:2219`, `ZFIN:...`, `FB:...`, `WB:...`, `SGD:...`), se devuelven los detalles del gen.
- De lo contrario, la entrada se usa como una **búsqueda de texto libre** y se devuelven los objetos coincidentes de la `--category` indicada.

Regresa: Resultados en formato JSON (Terminal) o Dataframe/CSV (Python).  

**Parámetro posicional**  
`search_term`  
Identificador de gen de Alliance (p. ej. `HGNC:1101`) o un término de búsqueda de texto libre.

**Parámetros opcionales**  
`-c` `--category`  
Categoría para las búsquedas de texto libre: una de `gene`, `allele`, `disease`, `go`, `variant`, `model`, o `all` para no filtrar. Por defecto: `gene`.  

`-l` `--limit`  
Número máximo de resultados para las búsquedas de texto libre. Por defecto: 10.  

`-o` `--out`  
Ruta al archivo en el que se guardarán los resultados, p. ej. path/to/directory/results.csv (o .json). Por defecto: salida estándar.  
Python: `save=True` guardará los resultados en el directorio de trabajo actual.  

**Banderas**  
`-csv` `--csv`  
Solo Terminal. Devuelve los resultados en formato CSV.  
Python: Use `json=True` para devolver los resultados en formato JSON.  

`-q` `--quiet`  
Solo Terminal. Impide que se muestre la información de progreso.  
Python: Use `verbose=False` para impedir que se muestre la información de progreso.  

### Ejemplos
**Buscar genes en distintos organismos modelo:**
```bash
gget alliance brca2
```
```python
# Python
gget.alliance("brca2")
```
&rarr; Devuelve una tabla de genes que coinciden con el término de búsqueda en las bases de datos miembro de Alliance.

| id | symbol | name | species | category | so_term_name |
| --- | --- | --- | --- | --- | --- |
| HGNC:1101 | BRCA2 | BRCA2 DNA repair associated | Homo sapiens | gene_search_result | protein_coding_gene |
| MGI:109337 | Brca2 | breast cancer 2 | Mus musculus | gene_search_result | protein_coding_gene |

<br/><br/>
**Obtener un solo gen por su identificador de Alliance:**
```bash
gget alliance HGNC:1101
```
```python
# Python
gget.alliance("HGNC:1101")
```
&rarr; Devuelve los detalles del gen.

| id | symbol | name | species | taxon | gene_type | synonyms | data_provider |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HGNC:1101 | BRCA2 | BRCA2 DNA repair associated | Homo sapiens | NCBITaxon:9606 | protein_coding_gene | ['FAD', ...] | RGD |

# Referencias
Si utiliza `gget alliance` en una publicación, por favor cite los siguientes artículos:  

- Alliance of Genome Resources Consortium. (2024). Updates to the Alliance of Genome Resources central infrastructure. Genetics. [https://doi.org/10.1093/genetics/iyae049](https://doi.org/10.1093/genetics/iyae049)

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)
