[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/es/reactome.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget reactome 🔬
Consulte la base de conocimientos de rutas [Reactome](https://reactome.org/) usando su [API REST ContentService](https://reactome.org/dev/content-service).  
Regresa: JSON/CSV (línea de comandos) o data frame (Python).

`gget reactome` admite varios tipos de consulta, seleccionados con el argumento `resource`:
- `pathways` (por defecto): regresa las rutas de Reactome en las que participa un identificador dado (p. ej. un número de acceso UniProt).
- `search`: búsqueda de texto completo en la base de conocimientos de Reactome (rutas, reacciones, entidades físicas, ...).
- `entity`: regresa los detalles de un ID estable de Reactome (p. ej. `R-HSA-6804754`).
- `interactors`: regresa los interactores moleculares de un identificador (interactores estáticos de IntAct).
- `orthology`: proyecta un ID estable de Reactome a su ortólogo en otra especie (requiere `--species`).
- `event-hierarchy`: regresa la jerarquía completa de rutas/reacciones de una especie.

**Parámetro posicional**  
`query`  
Identificador, término de búsqueda o especie a consultar. Su significado depende de `resource`:
- `resource="pathways"`: un identificador, p. ej. el número de acceso UniProt `P04637`.
- `resource="search"`: un término de búsqueda de texto libre, p. ej. `TP53`.
- `resource="entity"`: un ID estable de Reactome, p. ej. `R-HSA-6804754`.
- `resource="interactors"`: un número de acceso de molécula, p. ej. UniProt `P04637`.
- `resource="orthology"`: un ID estable de Reactome a proyectar, p. ej. `R-HSA-6804754`.
- `resource="event-hierarchy"`: un nombre de especie o ID de taxonomía de NCBI, p. ej. `Homo sapiens`.

**Parámetros opcionales**  
`-r` `--resource`  
Tipo de consulta a realizar. Opciones: `pathways` (por defecto), `search`, `entity`, `interactors`, `orthology`, `event-hierarchy`.  

`-s` `--source`  
Recurso/base de datos del identificador para `resource="pathways"`, p. ej. `UniProt` (por defecto), `Ensembl`, `ChEBI`, `NCBI`.  

`-sp` `--species`  
Especie, como nombre (p. ej. `Homo sapiens`) o ID de taxonomía de NCBI (p. ej. `9606`). Filtra `resource="pathways"` y `resource="search"`; es el **objetivo requerido** para `resource="orthology"`. Por defecto: None.  

`-t` `--types`  
Restringe los resultados de `resource="search"` a uno o más tipos de entrada, p. ej. `Pathway`, `Reaction`, `Protein`. Por defecto: None (todos los tipos).  

`-o` `--out`  
Ruta al archivo en el que se guardarán los resultados, p. ej. ruta/al/directorio/resultados.json. Por defecto: salida estándar (STDOUT).

**Banderas**  
`-csv` `--csv`  
Solo para la Terminal. Regresa los resultados en formato CSV, en lugar de formato JSON.  
Para Python: usa `json=True` para regresar los resultados en formato JSON.

`-q` `--quiet`  
Solo para la Terminal. Impide que la información de progreso se muestre durante la corrida.  
Para Python: usa `verbose=False` para impedir que la información de progreso se muestre durante la corrida.


### Ejemplos

**Obtenga las rutas de Reactome en las que participa una proteína**

```bash
gget reactome P04637 --species "Homo sapiens"
```

```python
import gget
gget.reactome("P04637", species="Homo sapiens")
```

&rarr; Regresa las rutas de Reactome en las que participa la proteína UniProt P04637 (TP53 humano).

| stable_id     | name                                                 | species      | schema_class | in_disease |
|---------------|------------------------------------------------------|--------------|--------------|------------|
| R-HSA-111448  | Activation of NOXA and translocation to mitochondria | Homo sapiens | Pathway      | False      |
| R-HSA-139915  | Activation of PUMA and translocation to mitochondria | Homo sapiens | Pathway      | False      |
| ...           | ...                                                  | ...          | ...          | ...        |

<br/><br/>

**Busque en la base de conocimientos de Reactome**

```bash
gget reactome TP53 -r search -t Pathway -sp "Homo sapiens"
```
```python
import gget
gget.reactome("TP53", resource="search", types="Pathway", species="Homo sapiens")
```

&rarr; Regresa las rutas de Reactome que coinciden con el término de búsqueda "TP53".

| stable_id     | name                          | type    | species      | reactome_id   |
|---------------|-------------------------------|---------|--------------|---------------|
| R-HSA-6804754 | Regulation of TP53 Expression | Pathway | Homo sapiens | R-HSA-6804754 |
| R-HSA-5633007 | Regulation of TP53 Activity   | Pathway | Homo sapiens | R-HSA-5633007 |
| ...           | ...                           | ...     | ...          | ...           |

<br/><br/>

**Obtenga los detalles de una entrada de Reactome por su ID estable**

```bash
gget reactome R-HSA-6804754 -r entity
```
```python
import gget
gget.reactome("R-HSA-6804754", resource="entity")
```

&rarr; Regresa los detalles de la entrada de Reactome R-HSA-6804754.

| stable_id     | name                          | schema_class | species      | in_disease | summation        |
|---------------|-------------------------------|--------------|--------------|------------|------------------|
| R-HSA-6804754 | Regulation of TP53 Expression | Pathway      | Homo sapiens | False      | Transcription... |

<br/><br/>

**Obtenga los interactores moleculares de una proteína**

```bash
gget reactome P04637 -r interactors
```
```python
gget.reactome("P04637", resource="interactors")
```

&rarr; Regresa los interactores de IntAct de P04637 (columnas: `interactor_acc`, `interactor_name`, `score`, `evidences`), p. ej. MDM2, con una puntuación de confianza de la interacción.

<br/><br/>

**Proyecte una ruta a otra especie (ortología)**

```bash
gget reactome R-HSA-6804754 -r orthology -sp "Mus musculus"
```
```python
gget.reactome("R-HSA-6804754", resource="orthology", species="Mus musculus")
```

&rarr; Regresa el ortólogo en ratón de la ruta humana (`R-MMU-6804754`, "Regulation of TP53 Expression", Mus musculus).

<br/><br/>

**Obtenga la jerarquía completa de eventos (rutas/reacciones) de una especie**

```bash
gget reactome "Homo sapiens" -r event-hierarchy
```
```python
gget.reactome("Homo sapiens", resource="event-hierarchy")
```

&rarr; Regresa toda la jerarquía de eventos humana aplanada a una fila por evento (columnas: `stable_id`, `name`, `type`, `species`, `parent_id`, `level`). Es una tabla grande — use `parent_id`/`level` para navegar el árbol.

> El DataFrame regresado guarda la versión de lanzamiento de Reactome en `.attrs["reactome_release"]` (p. ej. `97`) para reproducibilidad.


# Citar
Si utiliza `gget reactome` en una publicación, favor de citar los siguientes artículos:  

- Marc Gillespie, Bijay Jassal, Ralf Stephan, Marija Milacic, Karen Rothfels, Andrea Senff-Ribeiro, Johannes Griss, Cristoffer Sevilla, Lisa Matthews, Chuqiao Gong, Chuan Deng, Thawfeek Varusai, Eliot Ragueneau, Yusra Haider, Bruce May, Veronica Shamovsky, Joel Weiser, Timothy Brunson, Nasim Sanati, Liam Beckman, Xiang Shao, Antonio Fabregat, Konstantinos Sidiropoulos, Julieth Murillo, Guilherme Viteri, Justin Cook, Solomon Shorser, Gary Bader, Emek Demir, Chris Sander, Robin Haw, Guanming Wu, Lincoln Stein, Henning Hermjakob, Peter D'Eustachio (2022). The reactome pathway knowledgebase 2022. Nucleic Acids Research, Volume 50, Issue D1, 7 January 2022, Pages D687–D692, [https://doi.org/10.1093/nar/gkab1028](https://doi.org/10.1093/nar/gkab1028)

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)
