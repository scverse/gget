[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/es/ucsc.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget ucsc 🔎
Obtenga identificadores del [UCSC Genome Browser](https://genome.ucsc.edu/) para un gen o término, de forma similar a `gget search` para Ensembl.  
`gget ucsc` busca en el UCSC Genome Browser un símbolo de gen, número de acceso o término de texto libre y devuelve los identificadores coincidentes (p. ej. identificadores de genes / transcritos conocidos de UCSC) junto con sus posiciones genómicas, agrupados por la pista ("track") de la que provienen.  
Regresa: Resultados en formato JSON (Terminal) o Dataframe/CSV (Python).  

**Parámetro posicional**  
`search_term`  
Símbolo de gen, número de acceso o término de texto libre a buscar, p. ej. `BRCA2`.

**Parámetros opcionales**  
`-g` `--genome`  
Ensamblaje del genoma de UCSC en el que buscar, p. ej. `hg38`, `hg19`, `mm39`. Por defecto: `hg38`.  

`-t` `--track`  
Devolver solo las coincidencias de pistas cuyo nombre contenga esta subcadena (sin distinguir mayúsculas y minúsculas), p. ej. `knownGene`. Por defecto: None.  

`-l` `--limit`  
Número máximo de coincidencias a devolver. Por defecto: None (todas las coincidencias).  

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

### Ejemplo
```bash
gget ucsc BRCA2 --genome hg38 --track knownGene
```
```python
# Python
gget.ucsc("BRCA2", genome="hg38", track="knownGene")
```
&rarr; Devuelve los identificadores de UCSC que coinciden con el término de búsqueda, con sus posiciones genómicas.

| track | ucsc_id | chrom | start | end | name | description |
| --- | --- | --- | --- | --- | --- | --- |
| knownGene | ENST00000380152.8 | chr13 | 32315508 | 32400268 | BRCA2 (ENST00000380152.8) | breast cancer type 2 susceptibility protein |
| . . . | . . . | . . . | . . . | . . . | . . . | . . . |

Un identificador de UCSC (p. ej. un `ucsc_id` de gen conocido) puede consultarse en la página de genes de UCSC, p. ej. `https://genome.ucsc.edu/cgi-bin/hgGene?hgg_gene={ucsc_id}&db=hg38`.

# Referencias
Si utiliza `gget ucsc` en una publicación, por favor cite los siguientes artículos:  

- Kent WJ, Sugnet CW, Furey TS, et al. (2002). The human genome browser at UCSC. Genome Research. [https://doi.org/10.1101/gr.229102](https://doi.org/10.1101/gr.229102)

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)
