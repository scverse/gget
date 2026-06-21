[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/blat.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget blat 🎯
Encuentra la ubicación genómica de una secuencia de nucleótidos o aminoácidos usando [BLAT](https://genome.ucsc.edu/cgi-bin/hgBlat).  
Produce: Resultados en formato JSON (Terminal) o Dataframe/CSV (Python).  

**Parámetro posicional**  
`sequence`  
Secuencia de nucleótidos o aminoácidos, o una ruta a un archivo tipo FASTA o .txt.  

**Parámetros optionales**  
`-st` `--seqtype`  
'DNA', 'protein', 'translated%20RNA', o 'translated%20DNA'.  
Por defecto: 'DNA' para secuencias de nucleótidos; 'protein' para secuencias de aminoácidos.  

`-a` `--assembly`  
Ensamblaje del genoma. 'human' (hg38) (se usa por defecto), 'mouse' (mm39) (ratón), 'zebrafish' (taeGut2) (pinzón cebra),  
o cualquiera de los ensamblajes de especies disponibles [aquí](https://genome.ucsc.edu/cgi-bin/hgBlat) (use el nombre corto del ensamblado, p. ej. 'hg38').  

`-o` `--out`  
Ruta al archivo en el que se guardarán los resultados, p. ej. ruta/al/directorio/resultados.csv (o .json). Por defecto: salida estándar (STDOUT).  
Para Python, usa `save=True` para guardar los resultados en el directorio de trabajo actual.  

**Banderas**  
`-csv` `--csv`  
Solo para Terminal. Produce los resultados en formato CSV.  
Para Python, usa `json=True` para producir los resultados en formato JSON.  

`-q` `--quiet`  
Solo para Terminal. Impide la información de progreso de ser exhibida durante la ejecución del programa.  
Para Python, usa `verbose=False` para impedir la información de progreso de ser exhibida durante la ejecución del programa.  


### Ejemplo
```bash
gget blat -a taeGut2 MKWMFKEDHSLEHRCVESAKIRAKYPDRVPVIVEKVSGSQIVDIDKRKYLVPSDITVAQFMWIIRKRIQLPSEKAIFLFVDKTVPQSR
```
```python
# Python
gget.blat("MKWMFKEDHSLEHRCVESAKIRAKYPDRVPVIVEKVSGSQIVDIDKRKYLVPSDITVAQFMWIIRKRIQLPSEKAIFLFVDKTVPQSR", assembly="taeGut2")
```
&rarr; Produce los resultados de BLAT para el ensamblaje taeGut2 (pinzón cebra). En este ejemplo, `gget blat` automáticamente detecta esta secuencia como una secuencia de aminoácidos y, por lo tanto, establece el tipo de secuencia (`--seqtype`) como *proteína*.

| genome     | query_size     | aligned_start     | aligned_end        | matches | mismatches | %_aligned | ... |
| -------------- |-------------------------| ------------------------| -------------- | ----------|-----|---|---|
| taeGut2| 88 | 	12 | 88 | 77 | 0 | 87.5 | ... |

#### [Màs ejemplos](https://github.com/pachterlab/gget_examples)

# Citar  
Si utiliza `gget blat` en una publicación, favor de citar los siguientes artículos:

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Kent WJ. BLAT--the BLAST-like alignment tool. Genome Res. 2002 Apr;12(4):656-64. doi: 10.1101/gr.229202. PMID: 11932250; PMCID: PMC187518.
