[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/archs4.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no es especificado de otra manera. Las banderas son designadas como cierto o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede obtener desde Terminal con la bandera `-h` `--help`.  
# gget archs4 🐁
Encuentra los genes más correlacionados a un gen de interés, o bién, encuentra los tejidos donde un gen se expresa usando la base de datos [ARCHS4](https://maayanlab.cloud/archs4/).  
Produce: Resultados en formato JSON (Terminal) o Dataframe/CSV (Python).  

**Parámetro posicional**  
`gene`  
Nombre corto (símbolo del gen) del gen de interés, p. ej. STAT4.  
Alternativamente: usa la bandera `--ensembl` para ingresar un ID tipo Ensembl, p. ej. ENSG00000138378.  

**Parámetros optionales**  
 `-w` `--which`  
'correlation' (correlación; se usa por defecto) o 'tissue' (tejido).  
'correlation' produce una tabla que contiene los 100 genes más correlacionados con el gen de interés. La correlación de Pearson se calcula de todas las muestras y tejidos en [ARCHS4](https://maayanlab.cloud/archs4/).  
'tissue' produce un atlas de expresión tisular calculado de todas las muestras humanas o de ratón (según lo definido usando el parámetro `--species` (especies)) en [ARCHS4](https://maayanlab.cloud/archs4/).  

`-s` `--species`  
'human' (humano; se usa por defecto) o 'mouse' (ratón).  
Define si se usan muestras humanas o de ratón de [ARCHS4](https://maayanlab.cloud/archs4/).  
(Solo aplica para el atlas de expresión tisular.)  

`-o` `--out`  
Ruta al archivo en el que se guardarán los resultados, p. ej. ruta/al/directorio/resultados.csv (o .json). Por defecto: salida estándar (STDOUT).  
Para Python, use `save=True` para guardar los resultados en el directorio de trabajo actual.  

**Banderas**  
`-e` `--ensembl`  
Usa esta bandera si `gene` se ingresa como ID tipo Ensembl.  

`-csv` `--csv`  
Solo para Terminal. Produce los resultados en formato CSV.  
Para Python, usa `json=True` para obtener los resultados en formato JSON.  

`-q` `--quiet`  
Solo para Terminal. Impide la información de progreso de ser exhibida durante la ejecución del programa.  
Para Python, usa `verbose=False` para impedir la información de progreso de ser exhibida durante la ejecución del programa.  


### Ejemplo
```bash
gget archs4 ACE2
```
```python
# Python
gget.archs4("ACE2")
```
&rarr; Produce los 100 genes más correlacionados con el gen ACE2:  

| gene_symbol     | pearson_correlation     |
| -------------- |-------------------------|
| SLC5A1 | 0.579634 |
| CYP2C18 | 0.576577 |
| . . . | . . . |

<br/><br/>

```bash
gget archs4 -w tissue ACE2
```
```python
# Python
gget.archs4("ACE2", which="tissue")
```
&rarr; Produce la expresión tisular de ACE2 (por defecto, se utilizan datos humanos):  

| id     | min     | q1 |  median | q3 | max |
| ------ |--------| ------ |--------| ------ |--------|
| System.Urogenital/Reproductive System.Kidney.RENAL CORTEX | 0.113644 | 8.274060 | 9.695840 | 10.51670 | 11.21970 |
| System.Digestive System.Intestine.INTESTINAL EPITHELIAL CELL | 0.113644 | 	5.905560 | 9.570450 | 13.26470 | 13.83590 |
| . . . | . . . | . . . | . . . | . . . | . . . |

<br/><br/>
Consulte [este tutorial](https://davetang.org/muse/2023/05/16/check-where-a-gene-is-expressed-from-the-command-line/) de Dave Tang, quien escribió un script R para crear esta visualización con los resultados de `gget archs4` en formato JSON:  

![image](https://github.com/pachterlab/gget/assets/56094636/f2a34a9e-beaa-45a5-a678-d38399dd3017)


#### [Más ejemplos](https://github.com/pachterlab/gget_examples)  

# Citar  
Si utiliza `gget archs4` en una publicación, favor de citar los siguientes artículos:

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Lachmann A, Torre D, Keenan AB, Jagodnik KM, Lee HJ, Wang L, Silverstein MC, Ma’ayan A. Massive mining of publicly available RNA-seq data from human and mouse. Nature Communications 9. Article number: 1366 (2018), doi:10.1038/s41467-018-03751-6

- Bray NL, Pimentel H, Melsted P and Pachter L, Near optimal probabilistic RNA-seq quantification, Nature Biotechnology 34, p 525--527 (2016). [https://doi.org/10.1038/nbt.3519](https://doi.org/10.1038/nbt.3519)
