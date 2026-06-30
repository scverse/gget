[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/es/pineapple.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget pineapple 🍍
Lista y descarga conjuntos de datos de bioimagen curados y pesos de modelos preentrenados desde [Pineapple](https://github.com/tomouellette/pineapple).  
[Pineapple](https://github.com/tomouellette/pineapple) (por Tom Ouellette) es una herramienta para el perfilado celular basado en imágenes que además cura y estandariza una colección de conjuntos de datos de bioimagen anotados (segmentación y benchmark) y pesos de modelos autosupervisados, alojados en Google Drive. `gget pineapple` te permite explorar este catálogo y descargar los recursos directamente — sin necesidad del binario de Rust.  
Regresa: JSON (línea de comandos) o Dataframe/CSV (Python).

> **Alcance:** `gget pineapple` solo envuelve la descarga de datos de Pineapple. No reimplementa las funciones de procesamiento de imágenes de Pineapple (`process`, `profile`, `neural`, `measure`) — para eso, usa directamente la herramienta [Pineapple](https://github.com/tomouellette/pineapple).

> ⚠️ Por favor revisa la referencia original y la licencia de cada conjunto de datos (mostradas en el catálogo) antes de usarlo. Algunos conjuntos de datos son solo para uso no comercial.

**Parámetro posicional**  
`name`  
Nombre del conjunto de datos/pesos a obtener, p. ej. `vicar_2021` o `dino_vit_small`. Omítelo para listar el catálogo completo de la categoría elegida.

**Parámetros optionales**  
`-c` `--category`  
Categoría del recurso: `segmentation`, `benchmark`, o `weights`. Por defecto: `segmentation`.  

`-od` `--out_dir`  
Directorio en el que se descargará el recurso (se usa con `--download`). Por defecto: directorio actual.  

`-o` `--out`  
Ruta del archivo en el que se guardará la tabla del catálogo, p. ej. ruta/al/directorio/results.csv (o .json). Por defecto: salida estándar.  
Python: `save=True` guardará la salida en el directorio de trabajo actual.

**Banderas**  
`-d` `--download`  
Descarga el recurso (requiere un `name` específico) en `--out_dir`. Los conjuntos de datos son grandes (hasta varios GB); consulta la columna `size_gb`.  

`-csv` `--csv`  
Solo para Terminal. Produce los resultados en formato CSV.  
Para Python, usa `json=True` para producir la salida en formato JSON.

`-q` `--quiet`  
Solo para Terminal. Impide que la información de progreso sea exhibida.  
Para Python, usa `verbose=False` para impedir que la información de progreso sea exhibida.  

### Ejemplos
**Listar los conjuntos de datos de segmentación disponibles:**
```bash
gget pineapple --category segmentation
```
```python
# Python
gget.pineapple(category="segmentation")
```
&rarr; Produce el catálogo de conjuntos de datos de segmentación curados.

| name | category | data_authors | size_gb | license | filename | google_drive_id |
| --- | --- | --- | --- | --- | --- | --- |
| vicar_2021 | segmentation | Vicar et al. 2021 | 0.113 | CC BY 4.0 | vicar-2021.tar.gz | 12tJOlIHZPFqp8GLek_jV__Uhhgsa530_ |
| . . . | . . . | . . . | . . . | . . . | . . . | . . . |

<br/><br/>
**Descargar un conjunto de datos específico:**
```bash
gget pineapple vicar_2021 --download --out_dir ./pineapple_data
```
```python
# Python
gget.pineapple("vicar_2021", download=True, out_dir="./pineapple_data")
```
&rarr; Descarga `vicar-2021.tar.gz` en `./pineapple_data` y produce la entrada del catálogo.

<br/><br/>
**Listar los pesos de modelos preentrenados:**
```bash
gget pineapple --category weights
```
```python
# Python
gget.pineapple(category="weights")
```
&rarr; Produce el catálogo de pesos de modelos autosupervisados preentrenados (p. ej. `dino_vit_small`, `subcell_vit_base`).

# Citar
Si utiliza `gget pineapple` en una publicación, favor de citar el siguiente recurso y las referencias originales de los conjuntos de datos (listadas en la columna `data_authors` del catálogo):  

- Pineapple: scalable processing for image-based cell profiling. [https://github.com/tomouellette/pineapple](https://github.com/tomouellette/pineapple)

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)
