[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/es/mitocarta.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget mitocarta 🫀
Obtenga el inventario [MitoCarta3.0](https://www.broadinstitute.org/mitocarta/) de proteínas y vías mitocondriales de mamíferos del Broad Institute.  
Regresa: JSON (línea de comandos) o un data frame (Python).  

MitoCarta3.0 es un inventario curado de genes que codifican proteínas con fuerte respaldo de localización mitocondrial, anotados con la localización submitocondrial y la pertenencia a vías.

La tabla que se regresa está *ordenada* (*tidy*, lista para análisis) en lugar del Excel sin procesar: las columnas delimitadas — `Synonyms` y `MitoCarta3.0_MitoPathways`, además de la columna `Genes` de la tabla de vías — se dividen en listas, que se convierten en arreglos anidados en la salida JSON.

> `gget mitocarta` necesita la dependencia opcional `xlrd` para leer el archivo `.xls` de MitoCarta. Instálala con `pip install gget[mitocarta]`.

**Parámetros optionales**  
`-s` `--species`  
Especie a obtener: `human` (por defecto) o `mouse`.  

`-w` `--which`  
Qué tabla regresar. Por defecto: `mitocarta`.  
`mitocarta` - El inventario MitoCarta3.0 de genes mitocondriales (una fila por gen mitocondrial, con localización submitocondrial, MitoPathways, evidencia, y puntuaciones).  
`all_genes` - Todos los genes puntuados para localización mitocondrial (puntuaciones Maestro), no solo los mitocondriales.  
`pathways`  - La jerarquía de MitoPathways y la lista de genes en cada vía.  

`-o` `--out`  
Ruta al archivo en el que se guardarán los resultados, p. ej. ruta/al/directorio/resultados.json (o .csv). Por defecto: salida estándar (STDOUT).  
Para Python, usa `save=True` para guardar los resultados en el directorio de trabajo actual.  

**Banderas**  
`-csv` `--csv`  
Solo para Terminal. Produce los resultados en formato CSV en lugar de JSON.  
Para Python, usa `json=True` para producir una lista de diccionarios en lugar de un data frame.  

`-q` `--quiet`  
Solo para Terminal. Impide la información de progreso de ser exhibida durante la ejecución del programa.  
Para Python, usa `verbose=False` para impedir la información de progreso de ser exhibida durante la ejecución del programa.  


### Ejemplos

**Obtenga el inventario de genes mitocondriales MitoCarta3.0 humano:**  
```bash
gget mitocarta --species human --csv
```
```python
# Python
import gget
gget.mitocarta(species="human", which="mitocarta")
```
&rarr; Regresa los ~1,100 genes mitocondriales humanos y sus anotaciones MitoCarta3.0 (localización submitocondrial, MitoPathways, evidencia, puntuaciones).

| HumanGeneID | Symbol | Description    | MitoCarta3.0_List | MitoCarta3.0_SubMitoLocalization | MitoCarta3.0_MitoPathways               |
|-------------|--------|----------------|-------------------|----------------------------------|-----------------------------------------|
| 1537        | CYC1   | cytochrome c1  | 1                 | MIM                              | OXPHOS > Complex&nbsp;III&nbsp;assembly |
| 6390        | SDHB   | ...            | 1                 | MIM                              | OXPHOS, Metabolism                      |

<br/><br/>

**Obtenga la jerarquía de MitoPathways y sus genes:**  
```bash
gget mitocarta --which pathways --csv
```
```python
# Python
gget.mitocarta(which="pathways")
```
&rarr; Regresa los MitoPathways y los genes asignados a cada vía.

<br/><br/>

**Salida JSON.** La línea de comandos regresa JSON por defecto (usa `--csv` para CSV; en Python usa `json=True` para una lista de diccionarios). Las columnas de tipo lista se emiten como arreglos:
```json
[
  {
    "MitoPathway": "Mitochondrial central dogma",
    "MitoPathways Hierarchy": "Mitochondrial central dogma",
    "Genes": ["AARS2", "ALKBH1", "ANGEL2", "APEX1", "..."]
  }
]
```

# Citar
Si utiliza `gget mitocarta` en una publicación, favor de citar el siguiente artículo:  

- Rath S, Sharma R, Gupta R, et al. MitoCarta3.0: an updated mitochondrial proteome now with sub-organelle localization and pathway annotations. Nucleic Acids Res. 2021 Jan 8;49(D1):D1541-D1547. doi: [10.1093/nar/gkaa1011](https://doi.org/10.1093/nar/gkaa1011). PMID: 33174596; PMCID: PMC7779016.
